# Kết quả P3 — replication protocol (LSTM + PPO, chưa Oracle)

Mục tiêu: lặp **protocol** Pasini (detector DL, vocab 10%, PPO, reward +10/−1, không Oracle). Không copy ER 99%.

## Detector LSTM

- Vocab 10% token phổ biến: **1191** (kèm `<pad>`, `None`)
- Pad 40 (paper 200; trung vị token = 6)
- Embed 8, hidden 128, BCE + sigmoid
- **Adam** 1e-3 — SGD paper kẹt acc 50%. Đây là lệch đã ghi.
- Early stop epoch 39, best val loss 0.229

Test (`splits/detectors/test.csv`, n=2168):

| Acc | Precision | Recall | F1 |
|---:|---:|---:|---:|
| 0.991 | 0.990 | 0.992 | 0.991 |

Gần Table 4 Pasini (~99.8%) về độ lớn, không trùng tuyệt đối 3 mạng.

## PPO vs detector (không Oracle trong reward)

Agent test: 400 mẫu Malicious đầu của `splits/adversarial_agents/test.csv`.

FN **không đột biến**: 1/400 = **0.25%** (sàn ER).

| Seed | Timesteps | Escape | ER | RR(E) | OR(V) trên E |
|---:|---:|---:|---:|---:|---:|
| 42 | 20k | 1 | 0.25% | 0 | 0.75 |
| 43 | 20k | 2 | 0.50% | 0 | 0.28 |
| 44 | 20k | 6 | 1.50% | 0.33 | 0.40 |
| 45 | 80k | 8 | 2.00% | 0.12 | 0.43 |

ER trung bình 20k × 3 seed = **0.75%**. 80k chỉ lên **2%**. Pasini: **>96%**.

## Đọc kết quả (quan trọng)

Không tái lập được ER cao của paper. Đó **không** phải train hỏng.

1. Token id **cố định theo vocab** (artifact `LabelEncoder.fit_transform` từng mẫu — mapping không ổn định).
2. Action lab **giữ XSS**; preprocess `.lower()` + `unescape` + `unquote` **hủy** mixed-case và entity trước khi LSTM thấy.
3. Dataset đã lọc oracle thực thi → token `<script>` / `alert(` nằm trong 10% vocab, khó OOV.

Các mẫu **có** escape thì OR(V) cao (28–75%) → lối tắt TH2 **tồn tại**, nhưng hiếm khi đóng bug implement.

Câu viết: *“Khi khép lối token-id không ổn định và mutation bị preprocess đảo, PPO Table 2 không còn ER ~99%. Số escape còn lại mang OOV cao, đúng cơ chế TH2.”*

Không viết: *“replication thành công ER 99%”*.

## Lệnh

```bash
cd lab
../.venv/bin/python src/run_p3.py --phase vocab
../.venv/bin/python src/run_p3.py --phase detector
../.venv/bin/python src/run_p3.py --phase ppo --timesteps 20000 --ppo-seeds 42,43,44
../.venv/bin/python src/run_p3.py --phase eval --ppo-seeds 42,43,44 --max-eval 400
```

Checkpoint: `lab/runs/p3/lstm.pt`, `ppo_seed*.zip`.
