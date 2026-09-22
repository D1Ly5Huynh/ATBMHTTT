#!/usr/bin/env python3
"""Wilcoxon signed-rank on paired P3 vs P4 ER (n=3 seeds). No scipy required."""

from __future__ import annotations

import json
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]


def signed_rank(diffs: list[float]) -> dict:
    pairs = [(abs(d), d) for d in diffs if d != 0]
    pairs.sort()
    ranks = []
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + 1 + j + 1) / 2
        for k in range(i, j + 1):
            ranks.append(avg if pairs[k][1] > 0 else -avg)
        i = j + 1
    w_plus = sum(r for r in ranks if r > 0)
    w_minus = -sum(r for r in ranks if r < 0)
    n = len(pairs)
    # Exact two-sided p for n<=10: 2 * (# sign patterns with |W+| >= observed) / 2^n
    from itertools import product

    obs = max(w_plus, w_minus)
    extreme = 0
    abs_ranks = [abs(r) for r in ranks]
    for signs in product([-1, 1], repeat=n):
        wp = sum(s * r for s, r in zip(signs, abs_ranks) if s > 0)
        if wp >= obs - 1e-12:
            extreme += 1
    p = min(1.0, 2 * extreme / (2**n)) if n else 1.0
    return {
        "n_nonzero": n,
        "w_plus": w_plus,
        "w_minus": w_minus,
        "p_two_sided_exact": p,
        "note": "n=3 (1 zero dropped → n=2). Power is negligible; report as descriptive.",
    }


def main() -> None:
    p3 = [0.0025, 0.005, 0.015]
    p4 = [0.0025, 0.0025, 0.0025]
    diffs = [a - b for a, b in zip(p3, p4)]
    out = {
        "metric": "ER on 400 agent-test payloads",
        "p3_er": p3,
        "p4_er": p4,
        "diffs_p3_minus_p4": diffs,
        "wilcoxon": signed_rank(diffs),
        "reading": "P4 ER is <= P3 on every seed. Test cannot reject at 0.05 with n=2.",
    }
    path = LAB / "data" / "wilcoxon_p3p4.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
