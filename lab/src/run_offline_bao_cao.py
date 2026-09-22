#!/usr/bin/env python3
"""Chạy lưới Pasini 10 seed offline (localhost) và xuất bảng dán báo cáo.

Không cần internet. Dùng .venv, artifact data/10, Oracle FastAPI 127.0.0.1:5555.
Job đã có results.json thì SKIP, không train lại.

Cách chạy (từ bất kỳ thư mục nào):

    # Chỉ xuất số đã có trên đĩa (không train, an toàn khi lưới đang chạy)
    /home/kali/Desktop/ATBMHTTT/.venv/bin/python -u \\
        /home/kali/Desktop/ATBMHTTT/lab/src/run_offline_bao_cao.py --export-only

    # Bật Oracle local nếu chưa có, chạy nốt 10 seed, xuất khi xong
    /home/kali/Desktop/ATBMHTTT/.venv/bin/python -u \\
        /home/kali/Desktop/ATBMHTTT/lab/src/run_offline_bao_cao.py --run

File ra:
    lab/runs/pasini_faithful/bao_cao/snapshot.json
    lab/runs/pasini_faithful/bao_cao/10seed_jobs.csv
    lab/runs/pasini_faithful/bao_cao/BANG_DAN_BAO_CAO.txt
    huong_dan/BANG_KET_QUA_THI_NGHIEM.txt   (bản copy dán Word)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ART = ROOT / "artifact" / "Adversarial_RL_XSS"
PY = ROOT / ".venv" / "bin" / "python"
OUT = ROOT / "lab" / "runs" / "pasini_faithful" / "bao_cao"
PASTE = ROOT / "huong_dan" / "BANG_KET_QUA_THI_NGHIEM.txt"
ORACLE_DOCS = "http://127.0.0.1:5555/docs"
ORACLE_PID = ROOT / "lab" / "runs" / "pasini_faithful" / "oracle_5555.pid"

SEEDS = list(range(42, 52))
MODELS = ("lstm", "mlp", "cnn")

# Paper Pasini JSS 2026, PDF v2, trung bình 10 seed (để đối chiếu, không phải số lab).
PAPER = {
    False: {
        "lstm": {"er": 0.9862, "rr_e": 0.0634, "rr_v": 0.9731, "or_v": 0.4749},
        "mlp": {"er": 0.9973, "rr_e": 0.0707, "rr_v": 0.9784, "or_v": 0.4476},
        "cnn": {"er": 0.9825, "rr_e": 0.0636, "rr_v": 0.9257, "or_v": 0.4385},
    },
    True: {
        "lstm": {"er": 0.9813, "rr_v": 0.0001},
        "mlp": {"er": 0.9737, "rr_v": 0.0011},
        "cnn": {"er": 0.9689, "rr_v": 0.0008},
    },
}

REUSE = {
    ("lstm", 42, False): ART / "runs/lstm/10/run_0/adversarial_agent/run_0",
    ("lstm", 42, True): ART / "runs/lstm/10/run_0/adversarial_agent_oracle/run_0",
    ("mlp", 42, False): ART / "runs/mlp/10/run_0/adversarial_agent/run_0",
    ("mlp", 42, True): ART / "runs/mlp/10/run_0/adversarial_agent_oracle/run_1",
    ("cnn", 42, False): ART / "runs/cnn/10/run_0/adversarial_agent/run_0",
    ("cnn", 42, True): ART / "runs/cnn/10/run_0/adversarial_agent_oracle/run_1",
}


def pct(x, digits=2) -> str:
    if x is None:
        return "—"
    return f"{float(x) * 100:.{digits}f}".replace(".", ",") + "%"


def dest_dir(model: str, seed: int, oracle: bool) -> Path:
    folder = f"agent_oracle_s{seed}" if oracle else f"agent_s{seed}"
    return ART / "runs" / model / "10" / "run_0" / folder / "run_0"


def job_folder(model: str, seed: int, oracle: bool) -> Path:
    key = (model, seed, oracle)
    if key in REUSE and (REUSE[key] / "results.json").exists():
        return REUSE[key]
    return dest_dir(model, seed, oracle)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_job(model: str, seed: int, oracle: bool) -> dict:
    folder = job_folder(model, seed, oracle)
    row = {
        "model": model,
        "seed": seed,
        "oracle": oracle,
        "folder": str(folder),
        "status": "missing",
    }
    rj = read_json(folder / "results.json")
    rr = read_json(folder / "ruin_rate.json")
    if rj:
        row["status"] = "done"
        row.update(rj)
    elif (folder / "best_model.zip").exists():
        row["status"] = "incomplete"
    if rr:
        row.update(rr)
        if "rr_rq2" not in row and rr:
            pass
    return row


def collect_grid() -> list[dict]:
    rows = []
    for oracle in (False, True):
        for model in MODELS:
            for seed in SEEDS:
                rows.append(collect_job(model, seed, oracle))
    return rows


def mean_std(xs: list[float]) -> tuple[float | None, float | None]:
    if not xs:
        return None, None
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return m, var**0.5


def means_from_rows(rows: list[dict]) -> dict:
    out = {}
    for oracle in (False, True):
        for model in MODELS:
            sub = [r for r in rows if r["model"] == model and r["oracle"] is oracle]
            done = [r for r in sub if r.get("status") == "done" and "escape_rate" in r]
            ers = [float(r["escape_rate"]) for r in done]
            rre = [float(r["rr_rq1"]) for r in done if r.get("rr_rq1") is not None]
            rrv = [float(r["rr_rq2"]) for r in done if r.get("rr_rq2") is not None]
            orv = [float(r["mutated_none_rate"]) for r in done if r.get("mutated_none_rate") is not None]
            em, es = mean_std(ers)
            rm, rs = mean_std(rrv)
            out[f"{model}_oracle={oracle}"] = {
                "n_done": len(done),
                "n_total": 10,
                "n_er": len(ers),
                "er_mean": em,
                "er_std": es,
                "n_rr_e": len(rre),
                "rr_e_mean": mean_std(rre)[0],
                "rr_e_std": mean_std(rre)[1],
                "n_rrv": len(rrv),
                "rrv_mean": rm,
                "rrv_std": rs,
                "n_orv": len(orv),
                "orv_mean": mean_std(orv)[0],
                "orv_std": mean_std(orv)[1],
            }
    return out


def load_table4() -> dict:
    out = {}
    for model in MODELS:
        p = ART / "runs" / model / "10" / "run_0" / "test_results.json"
        out[model] = read_json(p)
    return out


def load_branch_b() -> dict:
    p3 = read_json(ROOT / "lab" / "runs" / "p3" / "p3_eval.json")
    p4 = read_json(ROOT / "lab" / "runs" / "p4" / "p4_eval.json")
    ddqn = read_json(ROOT / "lab" / "runs" / "p4" / "ddqn_eval.json")
    det = read_json(ROOT / "lab" / "runs" / "p3" / "detector_metrics.json")
    filt = read_json(ROOT / "lab" / "data" / "filter_report.json")
    tasr = read_json(ROOT / "lab" / "data" / "tasr_report.json")
    p5 = read_json(ROOT / "lab" / "data" / "p5_complete.json")
    return {
        "filter": filt,
        "detector": det.get("test", {}),
        "p3": p3,
        "p4_ppo": [x for x in p4.get("p4", p4.get("ppo", [])) if x.get("algo") == "ppo"]
        if isinstance(p4, dict)
        else [],
        "p4_raw": p4,
        "ddqn": ddqn,
        "tasr_84": tasr.get("summary", {}),
        "p5": {
            "diverse_pl1_tasr": (p5.get("diverse_pl1") or {}).get("tasr"),
            "triples_pl1_tasr": (p5.get("triples_pl1") or {}).get("tasr"),
            "transfer_p3_pl1_tasr": ((p5.get("transfer_p3") or {}).get("pl1") or {}).get("tasr"),
        },
    }


def oracle_up() -> bool:
    try:
        urllib.request.urlopen(ORACLE_DOCS, timeout=3).read()
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def start_oracle() -> subprocess.Popen | None:
    if oracle_up():
        return None
    if not PY.exists():
        raise SystemExit(f"thiếu venv: {PY}")
    logf = ROOT / "lab" / "runs" / "pasini_faithful" / "oracle_5555.log"
    logf.parent.mkdir(parents=True, exist_ok=True)
    fh = open(logf, "ab")
    proc = subprocess.Popen(
        [str(PY), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "5555"],
        cwd=str(ART),
        stdout=fh,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    ORACLE_PID.write_text(str(proc.pid) + "\n", encoding="utf-8")
    for _ in range(40):
        if oracle_up():
            print(f"Oracle :5555 lên (pid {proc.pid})", flush=True)
            return proc
        if proc.poll() is not None:
            raise SystemExit(f"Oracle chết ngay, xem {logf}")
        time.sleep(0.5)
    raise SystemExit("Oracle không trả /docs sau 20s")


def live_pids(needle: str) -> list[int]:
    me = os.getpid()
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
    except subprocess.CalledProcessError:
        return []
    found = []
    for line in out.splitlines():
        if needle not in line:
            continue
        if "grep" in line:
            continue
        try:
            pid = int(line.split(None, 1)[0])
        except ValueError:
            continue
        if pid != me:
            found.append(pid)
    return found


def snapshot() -> dict:
    rows = collect_grid()
    done = sum(1 for r in rows if r.get("status") == "done")
    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "artifact": str(ART),
        "pin": "a299bb6",
        "timesteps": 250000,
        "seeds": SEEDS,
        "n_jobs": 60,
        "n_done": done,
        "progress_pct": round(100.0 * done / 60.0, 1),
        "table4": load_table4(),
        "means": means_from_rows(rows),
        "rows": rows,
        "branch_b": load_branch_b(),
        "paper": PAPER,
        "note": (
            "Nhánh A = artifact data/10 + LabelEncoder từng mẫu + Oracle DOM. "
            "Nhánh B = lab JSDOM, không trộn ER với nhánh A. "
            "Paper = trung bình 10 seed; lab seed 42 đủ Table 4 + RQ3."
        ),
    }


def write_csv(rows: list[dict], path: Path) -> None:
    fields = [
        "model",
        "seed",
        "oracle",
        "status",
        "escape_rate",
        "rr_rq1",
        "rr_rq2",
        "mutated_none_rate",
        "rr_original",
        "original_none_rate",
        "mean_reward",
        "folder",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _mean_line(means: dict, key: str, field: str) -> str:
    m = means.get(key) or {}
    val, std, n = m.get(f"{field}_mean"), m.get(f"{field}_std"), m.get(f"n_{field}", m.get("n_er"))
    if val is None:
        return "— (chưa đủ job)"
    return f"{pct(val)} ± {pct(std)}  (n={n})"


def render_txt(snap: dict) -> str:
    means = snap["means"]
    t4 = snap["table4"]
    b = snap["branch_b"]
    filt = b.get("filter") or {}
    det = b.get("detector") or {}
    p3 = b.get("p3") or {}
    ddqn = b.get("ddqn") or {}
    tasr = b.get("tasr_84") or {}
    lines = []
    a = lines.append
    a("BẢNG KẾT QUẢ THÍ NGHIỆM — dán vào báo cáo đồ án ATBMHTTT")
    a("Sinh từ lab/src/run_offline_bao_cao.py — số đọc từ đĩa, không bịa.")
    a(f"Thời điểm: {snap['generated_at']}")
    a(f"Artifact pin: {snap['pin']}   |   10-seed: {snap['n_done']}/60 job ({snap['progress_pct']}%)")
    a("Không trộn nhánh A (~99%) với nhánh B (~1%).")
    a("")
    a("=" * 78)
    a("1) NHÁNH A — Table 4 detector (data/10, seed 42, test n=1802)")
    a("=" * 78)
    a(f"{'Mạng':<10} {'Precision':>12} {'Recall':>10} {'Accuracy':>12} {'F1':>12}")
    a(f"{'Paper':<10} {'99,67%':>12} {'100%':>10} {'99,83%':>12} {'99,83%':>12}")
    for model in MODELS:
        d = t4.get(model) or {}
        if not d:
            a(f"{model:<10} {'—':>12}")
            continue
        a(
            f"{model:<10} {pct(d.get('precision')):>12} {pct(d.get('recall')):>10} "
            f"{pct(d.get('accuracy')):>12} {pct(d.get('f1score')):>12}"
        )
    a("Cả ba mạng lab: TP=901 FP=3 TN=898 FN=0 (nếu Table 4 trùng).")
    a("")
    a("=" * 78)
    a("2) NHÁNH A — PPO không Oracle (replication). Paper = tb 10 seed; lab = seed đã xong")
    a("=" * 78)
    a(f"{'Mạng':<8} {'ER paper':>12} {'ER lab tb':>22} {'RR(V) paper':>14} {'RR(V) lab tb':>22}")
    for model in MODELS:
        p = PAPER[False][model]
        k = f"{model}_oracle=False"
        a(
            f"{model:<8} {pct(p['er']):>12} {_mean_line(means, k, 'er'):>22} "
            f"{pct(p['rr_v']):>14} {_mean_line(means, k, 'rrv'):>22}"
        )
    a("")
    a("Từng seed (ER).  status=done mới có số.")
    a(f"{'model':<6} {'seed':>5} {'oracle':>7} {'status':<12} {'ER':>10} {'RR(E)':>10} {'RR(V)':>10} {'OR(V)':>10}")
    for r in snap["rows"]:
        if r["oracle"]:
            continue
        a(
            f"{r['model']:<6} {r['seed']:>5} {'no':>7} {r.get('status',''):<12} "
            f"{pct(r.get('escape_rate')):>10} {pct(r.get('rr_rq1')):>10} "
            f"{pct(r.get('rr_rq2')):>10} {pct(r.get('mutated_none_rate')):>10}"
        )
    a("")
    a("=" * 78)
    a("3) NHÁNH A — RQ3 Oracle-in-loop (code −5)")
    a("=" * 78)
    a(f"{'Mạng':<8} {'ER paper':>12} {'ER lab tb':>22} {'RR(V) paper':>14} {'RR(V) lab tb':>22}")
    for model in MODELS:
        p = PAPER[True][model]
        k = f"{model}_oracle=True"
        a(
            f"{model:<8} {pct(p['er']):>12} {_mean_line(means, k, 'er'):>22} "
            f"{pct(p['rr_v']):>14} {_mean_line(means, k, 'rrv'):>22}"
        )
    a("")
    a("Từng seed RQ3:")
    a(f"{'model':<6} {'seed':>5} {'status':<12} {'ER':>10} {'RR(V)':>10} {'OR(V)':>10}")
    for r in snap["rows"]:
        if not r["oracle"]:
            continue
        a(
            f"{r['model']:<6} {r['seed']:>5} {r.get('status',''):<12} "
            f"{pct(r.get('escape_rate')):>10} {pct(r.get('rr_rq2')):>10} "
            f"{pct(r.get('mutated_none_rate')):>10}"
        )
    a("")
    a("Câu được: Trên đúng artifact data/10, tái lập ER ~99% và RQ3 ER>96% với RR≈0 theo Oracle DOM.")
    a("Câu cấm: coi ER 99% sau Oracle DOM là XSS còn chạy JavaScript.")
    a("")
    a("=" * 78)
    a("4) NHÁNH B — JSDOM, token-id cố định (không trộn với mục 2–3)")
    a("=" * 78)
    w1 = filt.get("w1_parser_only_ratio")
    a(
        f"Mereani: gốc {filt.get('input')} | độc {filt.get('malicious_in')} | "
        f"giữ execute {filt.get('malicious_exec')} | parser-only {filt.get('malicious_parser_only')} "
        f"(W1={pct(w1)}) | RR gốc={filt.get('rr_malicious_kept')}"
    )
    a(
        f"LSTM test: acc={pct(det.get('acc'))} P={pct(det.get('precision'))} "
        f"R={pct(det.get('recall'))} F1={pct(det.get('f1'))}"
    )
    a(f"P3 PPO ER tb 3 seed × 20k = {pct(p3.get('er_mean_20k_three_seeds'))}")
    for row in p3.get("ppo") or []:
        a(
            f"  seed {row.get('seed')}  steps={row.get('timesteps')}  "
            f"ER={pct(row.get('er'))}  RR(E)={pct(row.get('rr_e'))}  OR(V)={row.get('or_v')}"
        )
    p4_rows = (b.get("p4_raw") or {}).get("p4") or []
    p4_ppo = [x for x in p4_rows if x.get("algo") == "ppo"]
    if p4_ppo:
        er4 = sum(float(x["er"]) for x in p4_ppo) / len(p4_ppo)
        a(f"P4 PPO + R_exec ER=TASR tb = {pct(er4)}  RR=0  (n={len(p4_ppo)})")
        for row in p4_ppo:
            a(
                f"  seed {row.get('seed')}  ER=TASR={pct(row.get('er'))}  "
                f"RR(E)={pct(row.get('rr_e'))}"
            )
    a(f"P4 Dueling DQN ER/TASR tb = {pct(ddqn.get('er_mean'))}  RR=0")
    for row in ddqn.get("ddqn") or []:
        a(f"  seed {row.get('seed')}  ER=TASR={pct(row.get('er'))}  RR(E)={pct(row.get('rr_e'))}")
    pl1 = (tasr.get("pl1") or {}) if isinstance(tasr, dict) else {}
    app = (tasr.get("app") or {}) if isinstance(tasr, dict) else {}
    a(f"P5 catalog 84 /html: CRS PL1 TASR={pct(pl1.get('tasr'))}  App TASR={pct(app.get('tasr'))}")
    a(f"P5 mở rộng: diverse PL1 TASR={pct((b.get('p5') or {}).get('diverse_pl1_tasr'))}")
    a("")
    a("Câu được: Khi khép token-id, PPO Table 2 không còn ER ~99%. CRS lab TASR=0.")
    a("Câu cấm: replication Chen 99%; SAC; bypass CRS; HTTP 200 = TASR.")
    a("")
    a("=" * 78)
    a("5) GHI CHÚ 10 SEED")
    a("=" * 78)
    a("Thiếu job → status missing/incomplete. RR trống = RecursionError DOM (giữ ER, không bịa RR).")
    a("Khi n_done=60, thay bảng 4.3–4.4 trong báo cáo bằng dòng 'ER lab tb' ở mục 2–3.")
    a("File máy: lab/runs/pasini_faithful/bao_cao/")
    a("")
    return "\n".join(lines) + "\n"


def export(snap: dict | None = None) -> dict:
    snap = snap or snapshot()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "snapshot.json").write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(snap["rows"], OUT / "10seed_jobs.csv")
    text = render_txt(snap)
    (OUT / "BANG_DAN_BAO_CAO.txt").write_text(text, encoding="utf-8")
    PASTE.parent.mkdir(parents=True, exist_ok=True)
    PASTE.write_text(text, encoding="utf-8")
    summary = {
        "n_jobs": snap["n_jobs"],
        "timesteps": snap["timesteps"],
        "n_eval": 32,
        "n_done": snap["n_done"],
        "rows": snap["rows"],
        "means": snap["means"],
    }
    (ROOT / "lab" / "runs" / "pasini_faithful" / "seed10_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Xuất {snap['n_done']}/60 job  →  {OUT / 'BANG_DAN_BAO_CAO.txt'}", flush=True)
    print(f"Bản dán Word                 →  {PASTE}", flush=True)
    return snap


def run_grid() -> None:
    sys.path.insert(0, str(HERE))
    import run_pasini_10seed as grid  # noqa: WPS433 — same folder helper

    os.chdir(ART)
    grid.oracle_up()
    grid.log("=== 10SEED START (run_offline_bao_cao) ===")
    for oracle in (False, True):
        for model in MODELS:
            for seed in SEEDS:
                tag = f"{model} seed={seed} oracle={oracle}"
                grid.log(f"=== JOB {tag} ===")
                metrics = grid.train_eval(model, seed, oracle)
                grid.log(
                    json.dumps(
                        {
                            k: metrics.get(k)
                            for k in ("escape_rate", "rr_rq1", "rr_rq2", "mutated_none_rate")
                        }
                    )
                )
                export()
    grid.log("=== 10SEED END ===")
    export()


def main() -> None:
    ap = argparse.ArgumentParser(description="Offline 10-seed Pasini + xuất bảng báo cáo")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--export-only", action="store_true", help="chỉ đọc đĩa, không train")
    g.add_argument("--run", action="store_true", help="chạy nốt 10 seed rồi xuất")
    ap.add_argument("--no-start-oracle", action="store_true", help="không tự bật uvicorn :5555")
    args = ap.parse_args()
    if not args.run:
        export()
        return

    others = live_pids("run_pasini_10seed.py")
    if others:
        print(
            f"Đang có orchestrator 10-seed pid={others}. Không train trùng.\n"
            "Đã xuất số hiện có. Khi lưới xong, chạy lại --export-only.",
            flush=True,
        )
        export()
        raise SystemExit(2)

    if not args.no_start_oracle:
        start_oracle()
    elif not oracle_up():
        raise SystemExit("Oracle :5555 down. Bỏ --no-start-oracle hoặc chạy run_pasini_faithful.sh oracle-up")
    run_grid()


if __name__ == "__main__":
    main()
