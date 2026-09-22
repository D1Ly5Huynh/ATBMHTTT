#!/usr/bin/env bash
# Đẩy coverage paper: RQ3 MLP+CNN seed 42, LSTM no-oracle seed 43/44.
# Fast: 50k bước, eval 32 episode (val đã plateau từ 50k).
set -euo pipefail
ART=/home/kali/Desktop/ATBMHTTT/artifact/Adversarial_RL_XSS
PY=/home/kali/Desktop/ATBMHTTT/.venv/bin/python
LOG=/home/kali/Desktop/ATBMHTTT/lab/runs/pasini_faithful/train_95.log
cd "$ART"
export PYTHONUNBUFFERED=1

latest_run() {
  ls -d "$1"/run_* 2>/dev/null | sort -t_ -k2 -n | tail -1
}

eval_and_rr() {
  local cfg="$1" ckpt="$2" tag="$3"
  echo "=== EVAL $tag $(date -Is) ckpt=$ckpt ==="
  "$PY" src/test_adversarial_agent.py \
    --testset data/10/adversarial_agents/test.csv \
    --config_detector "$cfg" \
    --checkpoint "$ckpt" --seed 42
  local folder
  folder="$(dirname "$ckpt")"
  echo "=== RR $tag $(date -Is) ==="
  "$PY" src/test_validity_mutated_dataset.py \
    --dataset "$folder/empirical_study_set.csv" \
    --vocab data/10/vocabulary.csv --seed 42
  "$PY" src/analyze_validity.py --dataset "$folder/validity.csv" --seed 42
  cat "$folder/ruin_rate.json"
  cat "$folder/results.json"
}

train_ppo() {
  local cfg="$1" folder="$2" seed="$3" extra="${4:-}"
  echo "=== PPO cfg=$cfg folder=$folder seed=$seed extra=$extra $(date -Is) ==="
  "$PY" src/train_adversarial_agent.py \
    --trainset data/10/adversarial_agents/train.csv \
    --valset data/10/adversarial_agents/val.csv \
    --config_detector "$cfg" \
    --runs_folder "$folder" --seed "$seed" --timesteps 50000 \
    --n_eval_episodes 32 --skip_env_check $extra
}

{
  echo "=== 95 START $(date -Is) ==="
  # Oracle smoke
  "$PY" - <<'PY'
import urllib.request
urllib.request.urlopen("http://127.0.0.1:5555/docs", timeout=5)
print("oracle_ok")
PY

  train_ppo runs/mlp/10/run_0/config.json adversarial_agent_oracle 42 --oracle_guided_reward
  CKPT="$(latest_run runs/mlp/10/run_0/adversarial_agent_oracle)/best_model.zip"
  eval_and_rr runs/mlp/10/run_0/config.json "$CKPT" mlp_oracle_s42

  train_ppo runs/cnn/10/run_0/config.json adversarial_agent_oracle 42 --oracle_guided_reward
  CKPT="$(latest_run runs/cnn/10/run_0/adversarial_agent_oracle)/best_model.zip"
  eval_and_rr runs/cnn/10/run_0/config.json "$CKPT" cnn_oracle_s42

  train_ppo runs/lstm/10/run_0/config.json adversarial_agent 43
  CKPT="$(latest_run runs/lstm/10/run_0/adversarial_agent)/best_model.zip"
  eval_and_rr runs/lstm/10/run_0/config.json "$CKPT" lstm_s43

  train_ppo runs/lstm/10/run_0/config.json adversarial_agent 44
  CKPT="$(latest_run runs/lstm/10/run_0/adversarial_agent)/best_model.zip"
  eval_and_rr runs/lstm/10/run_0/config.json "$CKPT" lstm_s44

  echo "=== 95 END $(date -Is) ==="
} >> "$LOG" 2>&1
