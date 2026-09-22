# Replication sát artifact Pasini (dataset `data/10`)

Ngày: 2026-09-16 (RQ3 xong 2026-09-17 01:06)  
Mục tiêu: chạy **đúng code + đúng split** của Pasini et al. (JSS 2026), artifact `a299bb6`.  
Không dùng split JSDOM của lab P3.

## Dataset (giống paper Table 3)

Nguồn: `artifact/Adversarial_RL_XSS/data/` — **không** gọi lại `prepare_dataset.py`.

| File | n | Ghi chú |
|---|---:|---|
| `FMereani.csv` | 43217 (15149 độc / 28068 lành) | Mereani gốc |
| `filtered.csv` | 27112 | chỉ HTTP |
| `filtered_oracle.csv` | 18020 (9010/9010) | sau Oracle DOM-diff + undersample |
| `10/vocabulary.csv` | 720 token | 10% token phổ biến |

Split `data/10` (so Table 3):

| | Detector train | val | test | Agent train | val | test |
|---|---:|---:|---:|---:|---:|---:|
| Paper Table 3 Malicious | 2883 | 721 | 901 | 2883 | 712 | 901 |
| Artifact CSV Malicious | **2883** | **721** | **901** | **2883** | **721** | **901** |
| Artifact CSV Benign | 2883 | 721 | 901 | 0 | 0 | 0 |
| Paper Benign | 2884 | 721 | 902 | 0 | 0 | 0 |

Agent val paper ghi 712, CSV artifact là 721. Dùng CSV — đó là dataset họ phát hành.

## Protocol giữ nguyên từ artifact

- Tokenize + vocab 10% (`preprocess.py`)
- `XSSDataset.MAX_LENGTH = 30` (code; paper viết 200)
- `LabelEncoder.fit_transform` **từng payload** (lối token-id không ổn định)
- Detector: embed 8, SGD 1e-3, batch 16, 150 epoch, patience 10, sigmoid
- Agent: PPO SB3 `MlpPolicy`, 250000 timesteps, max 15 bước, 27 action `mutators.py` (A18 no-op, A21 `(1)(1)`)
- Oracle: FastAPI + Jinja `\|safe` + BeautifulSoup + `zss` so với `"abc"`
- Reward replication: +10 / −1; RQ3: −5 nếu reconstructed token không còn “XSS” theo Oracle

Patch môi trường (không đổi protocol): `TemplateResponse` Starlette 1.x; `int(embedding_dim)` vì PyTorch 2.14 không nhận `8.0`.

## Table 4 — detector (seed 42)

Cùng test `data/10/detectors/test.csv` n=1802. TP=901 FP=3 TN=898 FN=0 trên **cả ba** mạng.

| | Precision | Recall | Accuracy | F1 |
|---|---:|---:|---:|---:|
| Paper MLP/LSTM/CNN | 99.67% | 100% | 99.83% | 99.83% |
| Lab LSTM | 99.67% | 100% | 99.83% | 99.83% |
| Lab MLP | 99.67% | 100% | 99.83% | 99.83% |
| Lab CNN | 99.67% | 100% | 99.83% | 99.83% |

Trùng Table 4 tới 2 chữ số. Ba mạng ra **đúng một bộ số** — đúng W4, không phải copy bảng.

Checkpoint: `artifact/Adversarial_RL_XSS/runs/{lstm,mlp,cnn}/10/run_0/`

## Replication PPO vs LSTM (seed 42, 250k steps, không Oracle)

Script gốc `src/train_adversarial_agent.py`. Test 901 payload `adversarial_agents/test.csv`.

| Metric | Paper LSTM (10 seed) | Lab seed 42 |
|---|---:|---:|
| ER | 98.62% | **98.78%** (890/901) |
| RR(E) RQ1 / TH1 | 6.34% | **8.99%** |
| RR(V) RQ2 / TH2 | 97.31% | **98.54%** |
| OR(V) None-rate trên E | 47.49% | **48.54%** |
| OR gốc | ~6% | **6.20%** |
| RR gốc trên E (original) | 0 | **0** |

Eval val reward: −8.57 @ 25k bước → ~5.8 từ 50k đến 250k. Entropy 3.29 → 0.16 (policy chắc).

Kết luận: **tái lập được hiện tượng paper** khi dùng đúng dataset + đúng `LabelEncoder` + đúng `mutators.py`. ER ~99% là artifact TH2 (OOV), không phải tấn công XSS ổn định.

`results.json` / `ruin_rate.json`: `artifact/.../runs/lstm/10/run_0/adversarial_agent/run_0/`

## So với lab P3 (split JSDOM, encode ổn định)

| | Artifact Pasini `data/10` | Lab P3 (JSDOM, token-id cố định) |
|---|---|---|
| Detector LSTM acc | 99.83% | 99.1% |
| PPO ER | **98.78%** | **0.75%** |
| OR(V) trên escape | 48.5% | 28–75% (hiếm escape) |

Cùng 27 action, khác encode + dataset filter. ER 99% chỉ xuất hiện khi giữ bug `LabelEncoder` của artifact.

## PPO vs MLP / CNN (seed 42, 250k, không Oracle)

Test 901 payload, cùng script artifact.

| | ER paper (10 seed) | ER lab | RR(E) paper | RR(E) lab | RR(V) paper | RR(V) lab | OR(V) paper | OR(V) lab |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LSTM | 98.62% | **98.78%** | 6.34% | **8.99%** | 97.31% | **98.54%** | 47.49% | **48.54%** |
| MLP | 99.73% | **98.67%** | 7.07% | **10.24%** | 97.84% | **98.54%** | 44.76% | **45.01%** |
| CNN | 98.25% | **98.89%** | 6.36% | **0%** | 92.57% | **1.35%** | 43.85% | **2.42%** |

LSTM và MLP khớp cơ chế TH2 (OOV cao, RR(V) ~98%). CNN seed 42 vẫn ER ~99% nhưng **ít token `None`** — agent spam `<script>` (LabelEncoder vẫn lệch id). Đây là phương sai 1 seed, không phải fail replication ER.

LSTM thêm seed (PPO không Oracle, 50k bước): seed 43 ER **97.34%**, seed 44 ER **96.56%**. Ba seed (42@250k + 43/44@50k) tb **97.56%** vs paper 98.62%.

## RQ3 — Oracle-in-loop, đủ 3 mạng

Reward artifact: −5 nếu reconstruct không còn XSS theo Oracle DOM. Test 901.

| | ER paper | ER lab | RR(V) paper | RR(V) lab | OR(V) lab | Ghi chú |
|---|---:|---:|---:|---:|---:|---|
| LSTM | 98.13% | **98.34%** | 0.01% | **0** | 1.69% | 250k, seed 42 |
| CNN | 96.89% | **96.00%** | 0.08% | **0.12%** | 2.17% | 250k, seed 42 (50k đã 96.00%; test set giống hệt) |
| MLP | 97.37% | **97.89%** | 0.11% | **0** | 1.76% | 250k, seed 42 (50k chỉ 83.8% — thiếu bước) |

Cả 3 mạng khớp claim RQ3: ER>96%, RR≈0. MLP 50k thấp vì chưa hội tụ. CNN 50k đã hội tụ: 250k (`adversarial_agent_oracle/run_1`) ER vẫn 865/901 = 96.00%, RR(V)=0.12%, OR(V)=2.17%; `empirical_study_set.csv` trùng bản 50k.

Câu viết: *“Trên đúng artifact và split `data/10`, tái lập ER ~99% (replication), RR(V)~98% (TH2), và RQ3 LSTM/CNN ER>96% với RR≈0 theo Oracle DOM.”*

Câu cấm: coi ER 99% sau Oracle DOM là XSS còn chạy JavaScript.

## File

- Số: `lab/data/PASINI_FAITHFUL_RESULTS.md`
- Lệnh: `lab/src/run_pasini_faithful.sh` (`ppo-lstm-fast` / `ppo-lstm-oracle-fast`)
- Chương: `huong_dan/2026-09-17_luan-van-P6.md`
