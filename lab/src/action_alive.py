#!/usr/bin/env python3
"""Measure parser_alive vs browser_alive for A1–A27 on seed payloads."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from actions import ACTION_META, apply_action  # noqa: E402
from oracle import JsdomOracle, parser_changed  # noqa: E402

LAB_ROOT = SRC.parent
SEEDS = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '<a href="javascript:alert(1)">x</a>',
]


def main() -> None:
    out_csv = LAB_ROOT / "data" / "action_alive.csv"
    rows = []
    with JsdomOracle() as oracle:
        for seed in SEEDS:
            base = oracle.evaluate(seed)
            rows.append(
                {
                    "action": "A0",
                    "seed": seed,
                    "mutated": seed,
                    "changed": False,
                    "parser_alive": base.parser_changed,
                    "browser_alive": base.executed,
                }
            )
            for action_id in range(1, 28):
                mutated = apply_action(action_id, seed, rng=random.Random(0))
                result = oracle.evaluate(mutated)
                rows.append(
                    {
                        "action": ACTION_META[action_id]["name"],
                        "seed": seed,
                        "mutated": mutated,
                        "changed": mutated != seed,
                        "parser_alive": result.parser_changed or parser_changed(mutated),
                        "browser_alive": result.executed,
                    }
                )
                print(
                    f"{ACTION_META[action_id]['name']:4} "
                    f"changed={mutated != seed!s:5} "
                    f"parser={result.parser_changed!s:5} "
                    f"exec={result.executed!s:5} "
                    f"{mutated[:80]!r}",
                    flush=True,
                )

    import pandas as pd

    df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    summary = []
    for action_id in range(1, 28):
        name = ACTION_META[action_id]["name"]
        sub = df[df["action"] == name]
        summary.append(
            {
                "action": name,
                "group": ACTION_META[action_id]["group"],
                "paper": ACTION_META[action_id]["paper"],
                "changed_any": bool(sub["changed"].any()),
                "browser_alive_any": bool(sub["browser_alive"].any()),
                "parser_alive_any": bool(sub["parser_alive"].any()),
                "browser_alive_rate": float(sub["browser_alive"].mean()),
            }
        )
    report = LAB_ROOT / "data" / "action_alive_summary.json"
    report.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out_csv} and {report}")


if __name__ == "__main__":
    main()
