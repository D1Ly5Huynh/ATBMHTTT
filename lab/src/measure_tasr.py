#!/usr/bin/env python3
"""Do Escape / TASR / Delta tren CRS PL1/PL2 + DOMPurify. Lab localhost."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from actions import ACTION_META, apply_action  # noqa: E402
from crs_client import APP, CRS_PL1, CRS_PL2, fetch, stack_up  # noqa: E402
from oracle import JsdomOracle  # noqa: E402

LAB_ROOT = SRC.parent
SEEDS = [
    ("script", "<script>alert(1)</script>"),
    ("img", "<img src=x onerror=alert(1)>"),
    ("jsurl", '<a href="javascript:alert(1)">x</a>'),
]


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
    return {
        "n": len(rows),
        "counts": counts,
        "escape": escape,
        "tasr": tasr,
        "delta": escape - tasr,
        "gate_pl1_exec": any(r["label"] == "BYPASS_EXEC" for r in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", action="store_true", help="them chuoi 2 action")
    parser.add_argument("--mereani", type=int, default=0, help="lay N mau agent test")
    parser.add_argument("--sink", default="/html", help="sink chinh, mac dinh /html")
    parser.add_argument(
        "--only",
        default="",
        help="chi do cac target: pl1,pl2,app,purify (trong, = tat ca)",
    )
    args = parser.parse_args()

    health = stack_up()
    if not all(health.values()):
        raise SystemExit(f"stack chua san: {health}")

    jobs: list[dict] = []
    rng = random.Random(0)
    for seed_name, seed in SEEDS:
        jobs.append({"family": "seed", "name": seed_name, "payload": seed})
        for action_id in range(1, 28):
            mutated = apply_action(action_id, seed, rng=rng)
            jobs.append(
                {
                    "family": "A",
                    "name": f"{seed_name}+{ACTION_META[action_id]['name']}",
                    "payload": mutated,
                }
            )
        if args.pairs:
            keepers = [1, 2, 3, 4, 8, 11, 14, 15, 18, 19, 21, 22, 23, 27]
            for a in keepers:
                for b in keepers:
                    p = apply_action(a, seed, rng=rng)
                    p = apply_action(b, p, rng=rng)
                    jobs.append(
                        {
                            "family": "AA",
                            "name": f"{seed_name}+{ACTION_META[a]['name']}+{ACTION_META[b]['name']}",
                            "payload": p,
                        }
                    )

    if args.mereani:
        csv_path = LAB_ROOT / "data" / "splits" / "adversarial_agents" / "test.csv"
        import pandas as pd

        df = pd.read_csv(csv_path)
        mal = df[df["Class"] == "Malicious"]["Payloads"].astype(str).tolist()
        jobs.extend(
            {
                "family": "mereani",
                "name": f"m{i}",
                "payload": p,
            }
            for i, p in enumerate(mal[: args.mereani])
        )

    all_targets = [
        ("pl1", CRS_PL1, args.sink),
        ("pl2", CRS_PL2, args.sink),
        ("app", APP, args.sink),
        ("purify", APP, "/purify" + args.sink),
    ]
    if args.only.strip():
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        targets = [t for t in all_targets if t[0] in wanted]
        if not targets:
            raise SystemExit(f"unknown --only {args.only}")
    else:
        targets = all_targets

    rows_by_target: dict[str, list[dict]] = {k: [] for k, *_ in targets}
    gate_examples: list[dict] = []

    with JsdomOracle() as oracle:
        for i, job in enumerate(jobs, start=1):
            payload = job["payload"]
            if len(payload) > 3500:
                continue
            for key, base, path in targets:
                hit = fetch(base, path, payload)
                executed = False
                hooks: list = []
                if hit.ok:
                    result = oracle.evaluate_document(hit.body)
                    executed = result.executed
                    hooks = result.hooks
                label = classify(hit.status, executed)
                row = {
                    "family": job["family"],
                    "name": job["name"],
                    "target": key,
                    "path": path,
                    "status": hit.status,
                    "label": label,
                    "executed": executed,
                    "hooks": [h.get("name") for h in hooks[:4]],
                    "payload": payload[:300],
                }
                rows_by_target[key].append(row)
                if key == "pl1" and label == "BYPASS_EXEC":
                    gate_examples.append(row)
            if i % 50 == 0:
                print(f"processed {i}/{len(jobs)} gate_pl1={len(gate_examples)}", flush=True)

    report = {
        "health": health,
        "sink": args.sink,
        "jobs": len(jobs),
        "summary": {k: summarize(v) for k, v in rows_by_target.items()},
        "gate_pl1_bypass_exec_n": len(gate_examples),
        "gate_pl1_examples": gate_examples[:20],
    }
    out_json = LAB_ROOT / "data" / "tasr_report.json"
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    import pandas as pd

    flat = [row for rows in rows_by_target.values() for row in rows]
    pd.DataFrame(flat).to_csv(LAB_ROOT / "data" / "tasr_rows.csv", index=False)
    print(json.dumps(report["summary"], indent=2))
    print("gate_pl1_bypass_exec_n", len(gate_examples))
    if gate_examples:
        print("example", json.dumps(gate_examples[0], ensure_ascii=False)[:500])
    else:
        print("GATE CHUA DAT: khong co BYPASS_EXEC tren CRS PL1")


if __name__ == "__main__":
    main()
