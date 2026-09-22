#!/usr/bin/env python3
"""Scan TAP-B + extra mutations against CRS PL1/app. Localhost only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from catalog_ext import EXT_ACTIONS, TAP_B  # noqa: E402
from crs_client import APP, CRS_PL1, fetch, stack_up  # noqa: E402
from oracle import JsdomOracle  # noqa: E402

LAB = SRC.parent
SEEDS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    '<a href="javascript:alert(1)">x</a>',
]


def classify(status: int, executed: bool) -> str:
    if status == 403:
        return "BLOCK"
    if 200 <= status < 300 and executed:
        return "BYPASS_EXEC"
    if 200 <= status < 300:
        return "BYPASS_NOEXEC"
    return "ERROR"


def main() -> None:
    if not all(stack_up().values()):
        raise SystemExit("stack down")
    rows = []
    jobs = [("tap_b", name, p) for name, p in enumerate(TAP_B)]
    jobs += [("tap_b", f"raw{i}", p) for i, p in enumerate(TAP_B)]
    # unique tap_b once
    jobs = [("tap_b", f"b{i}", p) for i, p in enumerate(TAP_B)]
    for seed in SEEDS:
        for name, fn in EXT_ACTIONS.items():
            jobs.append(("ext", f"{name}|{seed[:20]}", fn(seed)))
    with JsdomOracle() as oracle:
        for fam, name, payload in jobs:
            for target, base in ("pl1", CRS_PL1), ("app", APP):
                hit = fetch(base, "/html", payload)
                executed = False
                if hit.ok:
                    executed = oracle.evaluate_document(hit.body).executed
                label = classify(hit.status, executed)
                row = {
                    "family": fam,
                    "name": str(name),
                    "target": target,
                    "status": hit.status,
                    "label": label,
                    "executed": executed,
                    "payload": payload[:240],
                }
                rows.append(row)
                if target == "pl1" and label == "BYPASS_EXEC":
                    print("GATE", name, payload[:120], flush=True)
    pl1 = [r for r in rows if r["target"] == "pl1"]
    app = [r for r in rows if r["target"] == "app"]
    summary = {
        "n_pl1": len(pl1),
        "pl1_counts": {k: sum(1 for r in pl1 if r["label"] == k) for k in ("BLOCK", "BYPASS_NOEXEC", "BYPASS_EXEC", "ERROR")},
        "app_exec": sum(1 for r in app if r["label"] == "BYPASS_EXEC"),
        "gate": any(r["label"] == "BYPASS_EXEC" for r in pl1),
        "pl1_exec_examples": [r for r in pl1 if r["label"] == "BYPASS_EXEC"][:15],
        "pl1_200": [r for r in pl1 if r["status"] == 200][:15],
    }
    out = LAB / "data" / "ext_crs_scan.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
