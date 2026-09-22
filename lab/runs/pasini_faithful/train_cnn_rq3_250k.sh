#!/usr/bin/env bash
# CNN RQ3 oracle-in-loop 250k, seed 42 — khớp LSTM/MLP (không dùng 50k fast).
set -euo pipefail
ART=/home/kali/Desktop/ATBMHTTT/artifact/Adversarial_RL_XSS
PY=/home/kali/Desktop/ATBMHTTT/.venv/bin/python
LOG=/home/kali/Desktop/ATBMHTTT/lab/runs/pasini_faithful/train_cnn_rq3_250k.log
OUT=/home/kali/Desktop/ATBMHTTT/lab/runs/pasini_faithful/cnn_oracle_250k
cd "$ART"
export PYTHONUNBUFFERED=1
export PYTHONWARNINGS=ignore

{
  echo "=== CNN RQ3 250k START $(date -Is) ==="
  "$PY" - <<'PY'
import urllib.request
urllib.request.urlopen("http://127.0.0.1:5555/docs", timeout=5)
print("oracle_ok")
PY

  echo "=== TRAIN cnn oracle 250k seed=42 $(date -Is) ==="
  "$PY" src/train_adversarial_agent.py \
    --trainset data/10/adversarial_agents/train.csv \
    --valset data/10/adversarial_agents/val.csv \
    --config_detector runs/cnn/10/run_0/config.json \
    --runs_folder adversarial_agent_oracle \
    --seed 42 \
    --timesteps 250000 \
    --n_eval_episodes 32 \
    --skip_env_check \
    --oracle_guided_reward

  CKPT=$(ls -d runs/cnn/10/run_0/adversarial_agent_oracle/run_* | sort -t_ -k2 -n | tail -1)
  echo "=== EVAL cnn oracle 250k ckpt=$CKPT $(date -Is) ==="
  "$PY" src/test_adversarial_agent.py \
    --testset data/10/adversarial_agents/test.csv \
    --config_detector runs/cnn/10/run_0/config.json \
    --checkpoint "$CKPT/best_model.zip" --seed 42

  echo "=== RR cnn oracle 250k $(date -Is) ==="
  "$PY" src/test_validity_mutated_dataset.py \
    --dataset "$CKPT/empirical_study_set.csv" \
    --vocab data/10/vocabulary.csv --seed 42
  "$PY" src/analyze_validity.py --dataset "$CKPT/validity.csv" --seed 42

  mkdir -p "$OUT"
  cp -f "$CKPT/results.json" "$OUT/results.json"
  cp -f "$CKPT/ruin_rate.json" "$OUT/ruin_rate.json"
  echo "CKPT=$CKPT" > "$OUT/source.txt"
  echo "=== RESULTS ==="
  cat "$CKPT/results.json"
  cat "$CKPT/ruin_rate.json"
  echo "=== CNN RQ3 250k END $(date -Is) ==="
} >> "$LOG" 2>&1
