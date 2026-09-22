#!/usr/bin/env bash
# Remaining faithful replication: MLP PPO, CNN PPO, LSTM oracle-guided, then eval+RR.
set -euo pipefail
ART=/home/kali/Desktop/ATBMHTTT/artifact/Adversarial_RL_XSS
PY=/home/kali/Desktop/ATBMHTTT/.venv/bin/python
LOG=/home/kali/Desktop/ATBMHTTT/lab/runs/pasini_faithful/train_rest.log
cd "$ART"
export PYTHONUNBUFFERED=1

eval_and_rr() {
  local cfg="$1" ckpt="$2" tag="$3"
  echo "=== EVAL $tag $(date -Is) ==="
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

{
  echo "=== REST START $(date -Is) ==="

  echo "=== PPO MLP $(date -Is) ==="
  "$PY" src/train_adversarial_agent.py \
    --trainset data/10/adversarial_agents/train.csv \
    --valset data/10/adversarial_agents/val.csv \
    --config_detector runs/mlp/10/run_0/config.json \
    --runs_folder adversarial_agent --seed 42 --timesteps 250000
  eval_and_rr runs/mlp/10/run_0/config.json \
    runs/mlp/10/run_0/adversarial_agent/run_0/best_model.zip mlp

  echo "=== PPO CNN $(date -Is) ==="
  "$PY" src/train_adversarial_agent.py \
    --trainset data/10/adversarial_agents/train.csv \
    --valset data/10/adversarial_agents/val.csv \
    --config_detector runs/cnn/10/run_0/config.json \
    --runs_folder adversarial_agent --seed 42 --timesteps 250000
  eval_and_rr runs/cnn/10/run_0/config.json \
    runs/cnn/10/run_0/adversarial_agent/run_0/best_model.zip cnn

  echo "=== PPO LSTM ORACLE $(date -Is) ==="
  "$PY" src/train_adversarial_agent.py \
    --trainset data/10/adversarial_agents/train.csv \
    --valset data/10/adversarial_agents/val.csv \
    --config_detector runs/lstm/10/run_0/config.json \
    --runs_folder adversarial_agent_oracle --seed 42 --timesteps 250000 \
    --oracle_guided_reward
  eval_and_rr runs/lstm/10/run_0/config.json \
    runs/lstm/10/run_0/adversarial_agent_oracle/run_0/best_model.zip lstm_oracle

  echo "=== REST END $(date -Is) ==="
} >> "$LOG" 2>&1
