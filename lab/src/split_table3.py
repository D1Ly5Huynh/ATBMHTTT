#!/usr/bin/env python3
"""Split the execution-filtered Mereani set in the spirit of Pasini Table 3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

LAB_ROOT = Path(__file__).resolve().parents[1]
DATA = LAB_ROOT / "data"


def split_class(df: pd.DataFrame, seed: int, frac_train: float, frac_val: float):
    shuffled = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n = len(shuffled)
    n_train = int(n * frac_train)
    n_val = int(n * frac_val)
    train = shuffled.iloc[:n_train]
    val = shuffled.iloc[n_train : n_train + n_val]
    test = shuffled.iloc[n_train + n_val :]
    return train, val, test


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DATA / "mereani_exec_oracle.csv")
    parser.add_argument("--outdir", type=Path, default=DATA / "splits")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    mal = df[df["Class"] == "Malicious"].copy()
    ben = df[df["Class"] == "Benign"].copy()

    mal = mal.sample(frac=1.0, random_state=args.seed)
    half = len(mal) // 2
    det_mal = mal.iloc[:half]
    agent_mal = mal.iloc[half:]

    ben = ben.sample(n=len(det_mal), random_state=args.seed)

    det_mal_tr, det_mal_va, det_mal_te = split_class(det_mal, args.seed, 0.64, 0.16)
    det_ben_tr, det_ben_va, det_ben_te = split_class(ben, args.seed + 1, 0.64, 0.16)
    ag_tr, ag_va, ag_te = split_class(agent_mal, args.seed + 2, 0.64, 0.16)

    out = {
        "detectors/train.csv": pd.concat([det_mal_tr, det_ben_tr], ignore_index=True),
        "detectors/val.csv": pd.concat([det_mal_va, det_ben_va], ignore_index=True),
        "detectors/test.csv": pd.concat([det_mal_te, det_ben_te], ignore_index=True),
        "adversarial_agents/train.csv": ag_tr,
        "adversarial_agents/val.csv": ag_va,
        "adversarial_agents/test.csv": ag_te,
    }

    summary = {}
    args.outdir.mkdir(parents=True, exist_ok=True)
    for rel, frame in out.items():
        path = args.outdir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        shuffled = frame.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
        shuffled.to_csv(path, index=False)
        summary[rel] = shuffled["Class"].value_counts().to_dict()
        summary[rel]["n"] = int(len(shuffled))

    report = {
        "malicious_filtered": int(len(mal)),
        "benign_undersampled_to": int(len(ben)),
        "rr_malicious": 0.0,
        "splits": summary,
    }
    (args.outdir / "split_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
