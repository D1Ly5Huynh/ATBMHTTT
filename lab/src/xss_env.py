"""Gymnasium env: 27 Table-2 actions vs LSTM detector.

P3 reward: +10 detector-evade / -1 caught.
P4 R_exec: -2 if oracle says not XSS; +10 only if evade AND still executes.
"""

from __future__ import annotations

import random
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from gymnasium import spaces

from actions import apply_action
from dl_preprocess import encode_payload, load_vocab
from lstm_detector import LSTMDetector

MAX_STEPS = 15
N_ACTIONS = 27
RUIN_REWARD = -2.0


class XSSDetectEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        payloads: list[str],
        vocab_path: Path,
        ckpt_path: Path,
        embedding_dim: int = 8,
        max_steps: int = MAX_STEPS,
        sequential: bool = False,
        device: str = "cpu",
        oracle_reward: bool = False,
        oracle=None,
    ) -> None:
        super().__init__()
        self.payloads = list(payloads)
        self.max_steps = max_steps
        self.sequential = sequential
        self.oracle_reward = oracle_reward
        self._own_oracle = False
        self.oracle = oracle
        if oracle_reward and self.oracle is None:
            from oracle import JsdomOracle

            self.oracle = JsdomOracle()
            self.oracle.start()
            self._own_oracle = True
        self._seq_i = 0
        self.device = torch.device(device)
        vocab = load_vocab(vocab_path)
        self.token_to_id = {tok: i for i, tok in enumerate(vocab)}
        self.none_id = self.token_to_id["None"]
        self.pad_id = self.token_to_id.get("<pad>", 0)
        self.model = LSTMDetector(len(vocab), embedding_dim).to(self.device)
        self.model.load_state_dict(torch.load(ckpt_path, map_location=self.device))
        self.model.eval()
        self.action_space = spaces.Discrete(N_ACTIONS)
        self.observation_space = spaces.Box(
            low=0, high=N_ACTIONS, shape=(max_steps,), dtype=np.int32
        )
        self.payload = ""
        self.original = ""
        self.state = np.zeros(max_steps, dtype=np.int32)
        self.t = 0
        self.success = False
        self.escaped_payload = ""
        self.last_executed = False
        self.action_trace: list[int] = []
        self._oracle_cache: dict[str, bool] = {}

    def _malicious(self, payload: str) -> bool:
        ids = encode_payload(payload, self.token_to_id, self.none_id).unsqueeze(0)
        with torch.no_grad():
            score = float(self.model(ids.to(self.device), pad_id=self.pad_id).item())
        return score >= 0.5

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if options and "payload" in options:
            self.payload = options["payload"]
        elif self.sequential:
            self.payload = self.payloads[self._seq_i % len(self.payloads)]
            self._seq_i += 1
        else:
            self.payload = random.choice(self.payloads)
        self.original = self.payload
        self.state = np.zeros(self.max_steps, dtype=np.int32)
        self.t = 0
        self.success = False
        self.escaped_payload = ""
        self.last_executed = False
        self.action_trace = []
        return self.state.copy(), {}

    def _executed(self, payload: str) -> bool:
        if self.oracle is None:
            return True
        hit = self._oracle_cache.get(payload)
        if hit is None:
            hit = bool(self.oracle.evaluate(payload).executed)
            if len(self._oracle_cache) < 20000:
                self._oracle_cache[payload] = hit
        return hit

    def close(self):
        if self._own_oracle and self.oracle is not None:
            self.oracle.close()
            self.oracle = None
            self._own_oracle = False

    def step(self, action):
        action = int(action)
        try:
            self.payload = apply_action(action + 1, self.payload, rng=random.Random(action + self.t))
        except Exception:
            pass
        if self.t < self.max_steps:
            self.state[self.t] = action + 1
        self.action_trace.append(action + 1)
        self.t += 1
        evaded = not self._malicious(self.payload)
        executed = True
        if self.oracle_reward:
            executed = self._executed(self.payload)
        self.last_executed = executed
        terminated = False
        truncated = False
        reward = -1.0
        self.success = False
        if self.oracle_reward and not executed:
            reward = RUIN_REWARD
            if evaded or self.t >= self.max_steps:
                terminated = evaded
                truncated = (not evaded) and self.t >= self.max_steps
        elif evaded:
            reward = 10.0
            terminated = True
            self.success = True
            self.escaped_payload = self.payload
        elif self.t >= self.max_steps:
            truncated = True
        return self.state.copy(), reward, terminated, truncated, {
            "executed": executed,
            "evaded": evaded,
        }
