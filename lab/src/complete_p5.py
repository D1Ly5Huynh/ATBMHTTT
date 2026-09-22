#!/usr/bin/env python3
"""Finish P5: diverse Table-2 vs CRS, LSTM-agent transfer, optional Playwright."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from actions import ACTION_META, apply_action  # noqa: E402
from crs_client import APP, CRS_PL1, CRS_PL2, fetch, stack_up  # noqa: E402
from decode import XSS_HINT, injection_candidates  # noqa: E402
from oracle import JsdomOracle  # noqa: E402

LAB = SRC.parent
DATA = LAB / "data"
KEEP3 = [1, 4, 14, 18, 21, 23, 27]


def classify(status: int, executed: bool) -> str:
    if status == 403:
        return "BLOCK"
    if 200 <= status < 300 and executed:
        return "BYPASS_EXEC"
    if 200 <= status < 300:
        return "BYPASS_NOEXEC"
    return "ERROR"


def summarize(rows: list[dict]) -> dict:
    n = len(rows) or 1
    counts = {"BLOCK": 0, "BYPASS_NOEXEC": 0, "BYPASS_EXEC": 0, "ERROR": 0}
    for row in rows:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
    escape = (counts["BYPASS_EXEC"] + counts["BYPASS_NOEXEC"]) / n
    tasr = counts["BYPASS_EXEC"] / n
    examples = [r for r in rows if r["label"] == "BYPASS_EXEC"][:10]
    return {
        "n": len(rows),
        "counts": counts,
        "escape": escape,
        "tasr": tasr,
        "delta": escape - tasr,
        "gate_pl1_exec": bool(examples),
        "examples": examples,
    }


def probe(base: str, path: str, payload: str, oracle: JsdomOracle) -> dict:
    if len(payload) > 3500:
        return {"status": 0, "label": "ERROR", "executed": False, "payload": payload[:200]}
    hit = fetch(base, path, payload)
    executed = False
    if hit.ok:
        executed = oracle.evaluate_document(hit.body).executed
    return {
        "status": hit.status,
        "label": classify(hit.status, executed),
        "executed": executed,
        "payload": payload[:300],
    }


def diverse_table2(n_base: int, oracle: JsdomOracle) -> list[dict]:
    df = pd.read_csv(DATA / "mereani_exec_oracle.csv")
    mal = df[df["Class"] == "Malicious"]
    bases = []
    for rec in mal.itertuples(index=False):
        raw = str(rec.Payloads)
        decoded = str(getattr(rec, "decoded", raw))
        cands = injection_candidates(raw) or [decoded]
        pick = next((c for c in cands if XSS_HINT.search(c)), decoded)
        if pick and len(pick) < 2500:
            bases.append(pick)
        if len(bases) >= n_base:
            break
    rng = random.Random(0)
    rows = []
    for i, base_payload in enumerate(bases):
        jobs = [base_payload] + [
            apply_action(aid, base_payload, rng=rng) for aid in range(1, 28)
        ]
        for payload in jobs:
            row = probe(CRS_PL1, "/html", payload, oracle)
            row.update({"family": "diverse_table2", "base_i": i})
            rows.append(row)
            if row["label"] == "BYPASS_EXEC":
                print("GATE", row["payload"][:160], flush=True)
        if (i + 1) % 10 == 0:
            print(f"diverse {i+1}/{len(bases)} exec={sum(r['label']=='BYPASS_EXEC' for r in rows)}", flush=True)
    return rows


def triples(oracle: JsdomOracle) -> list[dict]:
    seeds = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
    ]
    rng = random.Random(0)
    rows = []
    for seed in seeds:
        for a in KEEP3:
            for b in KEEP3:
                for c in KEEP3:
                    p = seed
                    for aid in (a, b, c):
                        p = apply_action(aid, p, rng=rng)
                    row = probe(CRS_PL1, "/html", p, oracle)
                    row.update({"family": "triple", "name": f"A{a}+A{b}+A{c}"})
                    rows.append(row)
                    if row["label"] == "BYPASS_EXEC":
                        print("GATE triple", row["name"], flush=True)
    return rows


def transfer(n: int, zip_path: Path, algo: str, oracle: JsdomOracle) -> list[dict]:
    from stable_baselines3 import DQN, PPO

    from xss_env import XSSDetectEnv

    df = pd.read_csv(DATA / "splits" / "adversarial_agents" / "test.csv")
    payloads = df[df["Class"] == "Malicious"]["Payloads"].astype(str).tolist()[:n]
    env = XSSDetectEnv(
        payloads,
        LAB / "runs" / "p3" / "vocab.json",
        LAB / "runs" / "p3" / "lstm.pt",
        sequential=True,
        oracle_reward=False,
    )
    loader = PPO.load if algo == "ppo" else DQN.load
    model = loader(str(zip_path), device="cpu")
    rows = []
    for payload in payloads:
        obs, _ = env.reset(options={"payload": payload})
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = env.step(int(action))
            done = terminated or truncated
        mutated = env.escaped_payload or env.payload
        for key, base in ("pl1", CRS_PL1), ("pl2", CRS_PL2), ("app", APP):
            row = probe(base, "/html", mutated, oracle)
            row.update(
                {
                    "family": "transfer",
                    "algo": algo,
                    "zip": zip_path.name,
                    "target": key,
                    "lstm_success": env.success,
                }
            )
            rows.append(row)
    env.close()
    return rows


def playwright_check(payloads: list[str]) -> dict:
    script = LAB / "oracle" / "pw_check.mjs"
    if not script.exists():
        return {"ok": False, "reason": "no_script"}
    import subprocess

    try:
        proc = subprocess.run(
            ["node", str(script)],
            input="\n".join(json.dumps({"payload": p}) for p in payloads),
            text=True,
            capture_output=True,
            timeout=120,
            cwd=str(LAB),
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        return {"ok": False, "reason": str(err)}
    if proc.returncode != 0:
        return {
            "ok": False,
            "reason": (proc.stderr or proc.stdout)[-500:],
        }
    hits = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            hits.append(json.loads(line))
    n = len(hits) or 1
    agree = sum(1 for h in hits if h.get("executed"))
    return {"ok": True, "n": len(hits), "executed": agree, "rate": agree / n, "rows": hits}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bases", type=int, default=40)
    parser.add_argument("--transfer-n", type=int, default=80)
    parser.add_argument("--skip-triples", action="store_true")
    parser.add_argument("--skip-playwright", action="store_true")
    args = parser.parse_args()
    health = stack_up()
    if not all(health.values()):
        raise SystemExit(f"stack down {health}")

    out: dict = {"health": health}
    with JsdomOracle() as oracle:
        print("=== diverse Table 2 on decoded Mereani → PL1 ===", flush=True)
        diverse = diverse_table2(args.bases, oracle)
        out["diverse_pl1"] = summarize(diverse)

        if not args.skip_triples:
            print("=== 3-action keepers → PL1 ===", flush=True)
            trip = triples(oracle)
            out["triples_pl1"] = summarize(trip)

        print("=== transfer P3 PPO → CRS/app ===", flush=True)
        t3 = transfer(
            args.transfer_n,
            LAB / "runs" / "p3" / "ppo_seed42.zip",
            "ppo",
            oracle,
        )
        out["transfer_p3"] = {
            k: summarize([r for r in t3 if r["target"] == k]) for k in ("pl1", "pl2", "app")
        }

        print("=== transfer P4 PPO-oracle → CRS/app ===", flush=True)
        t4 = transfer(
            args.transfer_n,
            LAB / "runs" / "p4" / "ppo_oracle_seed42.zip",
            "ppo",
            oracle,
        )
        out["transfer_p4"] = {
            k: summarize([r for r in t4 if r["target"] == k]) for k in ("pl1", "pl2", "app")
        }

        pd.DataFrame(diverse + (trip if not args.skip_triples else []) + t3 + t4).to_csv(
            DATA / "p5_complete_rows.csv", index=False
        )

    if not args.skip_playwright:
        app_exec = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            '<a href="javascript:alert(1)">x</a>',
        ]
        print("=== playwright hold-out ===", flush=True)
        out["playwright"] = playwright_check(app_exec)

    gate = bool(
        out.get("diverse_pl1", {}).get("gate_pl1_exec")
        or out.get("triples_pl1", {}).get("gate_pl1_exec")
        or out.get("transfer_p3", {}).get("pl1", {}).get("gate_pl1_exec")
        or out.get("transfer_p4", {}).get("pl1", {}).get("gate_pl1_exec")
    )
    out["gate_pl1_bypass_exec"] = gate
    (DATA / "p5_complete.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "playwright" or True}, indent=2)[:5000])
    print("GATE_PL1_BYPASS_EXEC", gate)


if __name__ == "__main__":
    main()
