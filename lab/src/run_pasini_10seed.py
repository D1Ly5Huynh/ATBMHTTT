#!/usr/bin/env python3
"""10-seed Pasini grid on data/10. 250k steps, eval 32 (test ER still 901).

Seed 42 already has 250k runs — reused, not retrained.
Does not touch lab/ JSDOM branch.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifact" / "Adversarial_RL_XSS"
PY = ROOT / ".venv" / "bin" / "python"
LOG = ROOT / "lab" / "runs" / "pasini_faithful" / "train_10seed.log"
SUMMARY = ROOT / "lab" / "runs" / "pasini_faithful" / "seed10_summary.json"

SEEDS = list(range(42, 52))
MODELS = ("lstm", "mlp", "cnn")
TIMESTEPS = 250_000
N_EVAL = 32
ENDPOINT = "http://127.0.0.1:5555/vuln_backend/1.0/endpoint/"

# 250k runs already on disk (do not redo).
REUSE = {
    ("lstm", 42, False): ART / "runs/lstm/10/run_0/adversarial_agent/run_0",
    ("lstm", 42, True): ART / "runs/lstm/10/run_0/adversarial_agent_oracle/run_0",
    ("mlp", 42, False): ART / "runs/mlp/10/run_0/adversarial_agent/run_0",
    ("mlp", 42, True): ART / "runs/mlp/10/run_0/adversarial_agent_oracle/run_1",
    ("cnn", 42, False): ART / "runs/cnn/10/run_0/adversarial_agent/run_0",
    ("cnn", 42, True): ART / "runs/cnn/10/run_0/adversarial_agent_oracle/run_1",
}


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = msg + "\n"
    sys.stdout.write(line)
    sys.stdout.flush()
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line)


def oracle_up() -> None:
    last: Exception | None = None
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:5555/docs", timeout=5).read()
            return
        except Exception as e:  # noqa: BLE001 — wait for uvicorn
            last = e
            time.sleep(2)
    raise SystemExit(f"oracle down: {last}")


def dest_dir(model: str, seed: int, oracle: bool) -> Path:
    folder = f"agent_oracle_s{seed}" if oracle else f"agent_s{seed}"
    return ART / "runs" / model / "10" / "run_0" / folder / "run_0"


def read_metrics(folder: Path) -> dict:
    out = {"folder": str(folder)}
    rj = folder / "results.json"
    rr = folder / "ruin_rate.json"
    if rj.exists():
        out.update(json.loads(rj.read_text()))
    if rr.exists():
        out.update(json.loads(rr.read_text()))
    return out


def run(cmd: list[str]) -> int:
    log("$ " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ART))
    return p.returncode


def maybe_rr(dest: Path, key: tuple) -> None:
    """Retry RQ1/RQ2 validity if train/eval finished but ruin_rate.json is missing."""
    if (dest / "ruin_rate.json").exists():
        return
    emp = dest / "empirical_study_set.csv"
    if not emp.exists():
        return
    log(f"RR_RETRY {key} -> {dest}")
    rc = run(
        [
            str(PY),
            "src/test_validity_mutated_dataset.py",
            "--dataset",
            str(emp.relative_to(ART)),
            "--vocab",
            "data/10/vocabulary.csv",
            "--seed",
            "42",
        ]
    )
    if rc == 0:
        run(
            [
                str(PY),
                "src/analyze_validity.py",
                "--dataset",
                str((dest / "validity.csv").relative_to(ART)),
                "--seed",
                "42",
            ]
        )
    else:
        log(f"RR_FAIL {key}")


def train_eval(model: str, seed: int, oracle: bool) -> dict:
    key = (model, seed, oracle)
    if key in REUSE and (REUSE[key] / "results.json").exists():
        log(f"REUSE {key} -> {REUSE[key]}")
        maybe_rr(REUSE[key], key)
        return read_metrics(REUSE[key])

    dest = dest_dir(model, seed, oracle)
    if (dest / "results.json").exists():
        log(f"SKIP exists {dest}")
        maybe_rr(dest, key)
        return read_metrics(dest)
    if dest.exists():
        log(f"INCOMPLETE rm {dest}")
        shutil.rmtree(dest)

    folder_name = f"agent_oracle_s{seed}" if oracle else f"agent_s{seed}"
    cfg = ART / "runs" / model / "10" / "run_0" / "config.json"
    cmd = [
        str(PY),
        "src/train_adversarial_agent.py",
        "--trainset",
        "data/10/adversarial_agents/train.csv",
        "--valset",
        "data/10/adversarial_agents/val.csv",
        "--config_detector",
        str(cfg.relative_to(ART)),
        "--runs_folder",
        folder_name,
        "--seed",
        str(seed),
        "--timesteps",
        str(TIMESTEPS),
        "--n_eval_episodes",
        str(N_EVAL),
        "--skip_env_check",
    ]
    if oracle:
        cmd.append("--oracle_guided_reward")
    rc = run(cmd)
    if rc != 0:
        raise SystemExit(f"train failed {key} rc={rc}")

    ckpt = dest / "best_model.zip"
    if not ckpt.exists():
        # get_last_run_number may have created run_1 if run_0 existed empty
        parent = dest.parent
        runs = sorted(parent.glob("run_*"), key=lambda p: int(p.name.split("_")[1]))
        ckpt = runs[-1] / "best_model.zip"
        dest = runs[-1]
    rc = run(
        [
            str(PY),
            "src/test_adversarial_agent.py",
            "--testset",
            "data/10/adversarial_agents/test.csv",
            "--config_detector",
            str(cfg.relative_to(ART)),
            "--checkpoint",
            str(ckpt.relative_to(ART)),
            "--seed",
            "42",
        ]
    )
    if rc != 0:
        raise SystemExit(f"eval failed {key} rc={rc}")

    emp = dest / "empirical_study_set.csv"
    if emp.exists():
        rc = run(
            [
                str(PY),
                "src/test_validity_mutated_dataset.py",
                "--dataset",
                str(emp.relative_to(ART)),
                "--vocab",
                "data/10/vocabulary.csv",
                "--seed",
                "42",
            ]
        )
        if rc == 0:
            run(
                [
                    str(PY),
                    "src/analyze_validity.py",
                    "--dataset",
                    str((dest / "validity.csv").relative_to(ART)),
                    "--seed",
                    "42",
                ]
            )
        else:
            log(f"RR_FAIL {key}")
    return read_metrics(dest)


def mean_std(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return float("nan"), float("nan")
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return m, var**0.5


def main() -> None:
    os.chdir(ART)
    oracle_up()
    log("=== 10SEED START ===")
    rows: list[dict] = []
    for oracle in (False, True):
        for model in MODELS:
            for seed in SEEDS:
                tag = f"{model} seed={seed} oracle={oracle}"
                log(f"=== JOB {tag} ===")
                metrics = train_eval(model, seed, oracle)
                metrics.update({"model": model, "seed": seed, "oracle": oracle})
                rows.append(metrics)
                log(json.dumps({k: metrics.get(k) for k in ("escape_rate", "rr_rq1", "rr_rq2", "mutated_none_rate")}))

    summary: dict = {"n_jobs": len(rows), "timesteps": TIMESTEPS, "n_eval": N_EVAL, "rows": rows, "means": {}}
    for oracle in (False, True):
        for model in MODELS:
            sub = [r for r in rows if r.get("model") == model and r.get("oracle") is oracle]
            ers = [float(r["escape_rate"]) for r in sub if "escape_rate" in r]
            rrs = [float(r["rr_rq2"]) for r in sub if "rr_rq2" in r]
            em, es = mean_std(ers)
            rm, rs = mean_std(rrs)
            summary["means"][f"{model}_oracle={oracle}"] = {
                "n_er": len(ers),
                "er_mean": em,
                "er_std": es,
                "n_rrv": len(rrs),
                "rrv_mean": rm,
                "rrv_std": rs,
            }
    SUMMARY.write_text(json.dumps(summary, indent=2))
    log(json.dumps(summary["means"], indent=2))
    log("=== 10SEED END ===")


if __name__ == "__main__":
    main()
