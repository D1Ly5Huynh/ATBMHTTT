#!/usr/bin/env python3
"""Dueling DQN, Oracle-in-loop, 3 seeds — same env as P4."""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from dl_preprocess import load_vocab, oov_rate  # noqa: E402
from oracle import JsdomOracle  # noqa: E402
from xss_env import N_ACTIONS, XSSDetectEnv  # noqa: E402

LAB = SRC.parent
RUNS = LAB / "runs" / "p4"
SPLIT = LAB / "data" / "splits"


class DuelingQ(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int, hidden: int = 128) -> None:
        super().__init__()
        self.feat = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.val = nn.Linear(hidden, 1)
        self.adv = nn.Linear(hidden, n_actions)

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        z = self.feat(obs)
        value = self.val(z)
        adv = self.adv(z)
        return value + adv - adv.mean(dim=1, keepdim=True)


def train_seed(seed: int, timesteps: int, payloads: list[str]) -> Path:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    env = XSSDetectEnv(
        payloads,
        LAB / "runs" / "p3" / "vocab.json",
        LAB / "runs" / "p3" / "lstm.pt",
        oracle_reward=True,
    )
    obs_dim = int(np.prod(env.observation_space.shape))
    q = DuelingQ(obs_dim, N_ACTIONS)
    tgt = DuelingQ(obs_dim, N_ACTIONS)
    tgt.load_state_dict(q.state_dict())
    opt = torch.optim.Adam(q.parameters(), lr=1e-3)
    buf: deque = deque(maxlen=20000)
    obs, _ = env.reset()
    eps0, eps1, decay = 1.0, 0.05, timesteps
    batch = 64
    gamma = 0.99
    for t in range(1, timesteps + 1):
        eps = eps1 + (eps0 - eps1) * max(0.0, 1.0 - t / decay)
        if random.random() < eps:
            action = int(env.action_space.sample())
        else:
            with torch.no_grad():
                qv = q(torch.tensor(obs, dtype=torch.float32).unsqueeze(0))
                action = int(qv.argmax(dim=1).item())
        nxt, reward, term, trunc, _ = env.step(action)
        done = term or trunc
        buf.append((obs.copy(), action, float(reward), nxt.copy(), float(done)))
        obs = nxt
        if done:
            obs, _ = env.reset()
        if len(buf) >= batch and t % 4 == 0:
            sample = random.sample(buf, batch)
            ob = torch.tensor(np.array([s[0] for s in sample]), dtype=torch.float32)
            ac = torch.tensor([s[1] for s in sample], dtype=torch.long)
            rw = torch.tensor([s[2] for s in sample], dtype=torch.float32)
            nx = torch.tensor(np.array([s[3] for s in sample]), dtype=torch.float32)
            dn = torch.tensor([s[4] for s in sample], dtype=torch.float32)
            pred = q(ob).gather(1, ac.unsqueeze(1)).squeeze(1)
            with torch.no_grad():
                nxt_a = q(nx).argmax(dim=1)
                tgt_q = tgt(nx).gather(1, nxt_a.unsqueeze(1)).squeeze(1)
                y = rw + gamma * (1.0 - dn) * tgt_q
            loss = F.smooth_l1_loss(pred, y)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(q.parameters(), 1.0)
            opt.step()
        if t % 500 == 0:
            tgt.load_state_dict(q.state_dict())
    env.close()
    RUNS.mkdir(parents=True, exist_ok=True)
    path = RUNS / f"ddqn_oracle_seed{seed}.pt"
    torch.save({"state": q.state_dict(), "obs_dim": obs_dim, "seed": seed}, path)
    print(json.dumps({"algo": "ddqn", "seed": seed, "timesteps": timesteps, "path": str(path)}), flush=True)
    return path


def eval_seed(path: Path, payloads: list[str]) -> dict:
    blob = torch.load(path, map_location="cpu")
    q = DuelingQ(blob["obs_dim"], N_ACTIONS)
    q.load_state_dict(blob["state"])
    q.eval()
    env = XSSDetectEnv(
        payloads,
        LAB / "runs" / "p3" / "vocab.json",
        LAB / "runs" / "p3" / "lstm.pt",
        sequential=True,
        oracle_reward=False,
    )
    vocab = load_vocab(LAB / "runs" / "p3" / "vocab.json")
    vocab_set = set(vocab) - {"None", "<pad>"}
    n_escape = exec_alive = none_n = tok_n = 0
    with JsdomOracle() as oracle:
        for payload in payloads:
            obs, _ = env.reset(options={"payload": payload})
            done = False
            while not done:
                with torch.no_grad():
                    action = int(q(torch.tensor(obs, dtype=torch.float32).unsqueeze(0)).argmax(dim=1).item())
                obs, _, term, trunc, _ = env.step(action)
                done = term or trunc
            if env.success:
                n_escape += 1
                nn, nt = oov_rate(env.escaped_payload, vocab_set)
                none_n += nn
                tok_n += nt
                if oracle.evaluate(env.escaped_payload).executed:
                    exec_alive += 1
    env.close()
    n = max(len(payloads), 1)
    return {
        "algo": "ddqn",
        "seed": blob["seed"],
        "n": len(payloads),
        "n_escape": n_escape,
        "er": n_escape / n,
        "tasr": exec_alive / n,
        "rr_e": (1.0 - exec_alive / n_escape) if n_escape else None,
        "or_v": (none_n / tok_n) if tok_n else None,
        "exec_alive_among_escape": exec_alive,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--timesteps", type=int, default=20000)
    parser.add_argument("--max-eval", type=int, default=400)
    parser.add_argument("--phase", choices=["train", "eval", "all"], default="all")
    args = parser.parse_args()
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    train_df = pd.read_csv(SPLIT / "adversarial_agents" / "train.csv")
    payloads = train_df[train_df["Class"] == "Malicious"]["Payloads"].astype(str).tolist()
    test_df = pd.read_csv(SPLIT / "adversarial_agents" / "test.csv")
    test = test_df[test_df["Class"] == "Malicious"]["Payloads"].astype(str).tolist()[: args.max_eval]
    if args.phase in {"train", "all"}:
        for seed in seeds:
            train_seed(seed, args.timesteps, payloads)
    if args.phase in {"eval", "all"}:
        rows = []
        for seed in seeds:
            path = RUNS / f"ddqn_oracle_seed{seed}.pt"
            row = eval_seed(path, test)
            rows.append(row)
            print(json.dumps(row), flush=True)
        summary = {
            "ddqn": rows,
            "er_mean": sum(r["er"] for r in rows) / len(rows),
            "tasr_mean": sum(r["tasr"] for r in rows) / len(rows),
        }
        (RUNS / "ddqn_eval.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
