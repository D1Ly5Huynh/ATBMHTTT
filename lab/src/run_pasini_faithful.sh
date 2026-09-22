#!/usr/bin/env bash
# Replication sát artifact Pasini: đúng data/10, đúng src/, đúng hyperparams.
# Chạy từ bất kỳ đâu. Cần Oracle :5555 (uvicorn app.main:app).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ART="$ROOT/artifact/Adversarial_RL_XSS"
PY="$ROOT/.venv/bin/python"
cd "$ART"
export PYTHONUNBUFFERED=1

usage() {
  echo "usage: $0 detectors|ppo-lstm|ppo-lstm-fast|eval-lstm|ppo-lstm-oracle|ppo-lstm-oracle-fast|oracle-up"
  exit 1
}

cmd="${1:-}"
case "$cmd" in
  oracle-up)
    exec "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 5555
    ;;
  detectors)
    for m in lstm mlp cnn; do
      "$PY" src/train_detector.py \
        --trainset data/10/detectors/train.csv \
        --valset data/10/detectors/val.csv \
        --vocabulary data/10/vocabulary.csv \
        --model "$m" --seed 42 --runs_folder runs \
        --epochs 150 --patience 10 --lr 0.001 --batch_size 16 \
        --embedding_dim 8 --vocab_size 0.1
      RUN=$(ls -d "runs/$m/10/run_"* | sort -t_ -k2 -n | tail -1)
      "$PY" src/test_detector.py \
        --testset data/10/detectors/test.csv \
        --vocab_file data/10/vocabulary.csv \
        --model "$m" --checkpoint_folder "$RUN" --seed 42
    done
    ;;
  ppo-lstm)
    "$PY" src/train_adversarial_agent.py \
      --trainset data/10/adversarial_agents/train.csv \
      --valset data/10/adversarial_agents/val.csv \
      --config_detector runs/lstm/10/run_0/config.json \
      --runs_folder adversarial_agent --seed 42 --timesteps 250000
    ;;
  ppo-lstm-fast)
    # Val reward đã plateau từ 50k (5.82). Eval 32 episode thay 721.
    "$PY" src/train_adversarial_agent.py \
      --trainset data/10/adversarial_agents/train.csv \
      --valset data/10/adversarial_agents/val.csv \
      --config_detector runs/lstm/10/run_0/config.json \
      --runs_folder adversarial_agent_fast --seed 42 --timesteps 50000 \
      --n_eval_episodes 32 --skip_env_check
    ;;
  ppo-lstm-oracle)
    "$PY" src/train_adversarial_agent.py \
      --trainset data/10/adversarial_agents/train.csv \
      --valset data/10/adversarial_agents/val.csv \
      --config_detector runs/lstm/10/run_0/config.json \
      --runs_folder adversarial_agent_oracle --seed 42 --timesteps 250000 \
      --oracle_guided_reward
    ;;
  ppo-lstm-oracle-fast)
    "$PY" src/train_adversarial_agent.py \
      --trainset data/10/adversarial_agents/train.csv \
      --valset data/10/adversarial_agents/val.csv \
      --config_detector runs/lstm/10/run_0/config.json \
      --runs_folder adversarial_agent_oracle_fast --seed 42 --timesteps 50000 \
      --oracle_guided_reward --n_eval_episodes 32 --skip_env_check
    ;;
  eval-lstm)
    CKPT="${2:-runs/lstm/10/run_0/adversarial_agent/run_0/best_model.zip}"
    "$PY" src/test_adversarial_agent.py \
      --testset data/10/adversarial_agents/test.csv \
      --config_detector runs/lstm/10/run_0/config.json \
      --checkpoint "$CKPT" --seed 42
    FOLDER="$(dirname "$CKPT")"
    "$PY" src/test_validity_mutated_dataset.py \
      --dataset "$FOLDER/empirical_study_set.csv" \
      --vocab data/10/vocabulary.csv --seed 42
    "$PY" src/analyze_validity.py --dataset "$FOLDER/validity.csv" --seed 42
    ;;
  *) usage ;;
esac
