# Kết quả P4 — Oracle-in-the-loop trên LSTM

Đối tượng: detector LSTM P3 (không phải CRS — gate PL1 chưa có BYPASS_EXEC).

## Reward `R_exec`

| Tình huống | Reward | `success` |
|---|---:|---|
| Mutation hết độc (JSDOM không execute) | **−2** (paper; artifact dùng −5) | không |
| Còn độc, detector vẫn bắt | −1 | không |
| Còn độc **và** detector gọi lành | **+10** | có |

Khác artifact Pasini: họ vẫn `done=True` khi detector lọt dù Oracle fail — chỉ đổi reward. Lab **không** tính success nếu không execute.

## Số (400 mẫu agent-test, 20k bước)

FN không đột biến: **1/400 = 0.25%**.

| Agent | ER (detector lọt) | TASR (lọt **và** execute) | RR(E) |
|---|---:|---:|---:|
| P3 PPO, không Oracle, tb 3 seed | **0.75%** | ~0.58% | 0–0.33 |
| P4 PPO + Oracle, 3 seed | **0.25%** | **0.25%** | **0** |
| P4 DQN SB3, seed 42 | **0.25%** | **0.25%** | **0** |
| **P4 Dueling DQN, 3 seed** | **1.08%** | **1.08%** | **0** |
| Sàn FN detector | 0.25% | 0.25% | 0 |

Dueling DQN seed 42/43/44: ER = TASR = 1.75% / 0.75% / 0.75%. RR(E)=0 trên mọi seed (Oracle-in-loop giữ payload còn chạy). Vẫn cách xa Pasini >96%.

Bảng chính thức PPO vs DDQN (mọi seed, OR(V), câu được/cấm): `lab/data/PPO_VS_DDQN.md`. Chương luận văn: `huong_dan/2026-09-17_luan-van-P6.md` §3.5.

P4 ER = TASR = sàn FN. Oracle-in-loop **cắt** các escape P3 không còn chạy (và không tìm thêm tấn công thật).

Histogram action trên 1 episode thành công không đủ để kết luận policy dùng A1/A6–A13.

## Đọc so với paper

Pasini RQ3: nhét Oracle, ER vẫn **>96%**, RR(V) ~0. Họ đánh detector dính OOV-`None`.

Lab: cùng protocol, detector encode ổn định + action giữ XSS → Oracle-in-loop **không** cho ER cao. Đúng hệ quả khi khép TH2.

Câu viết: *“Trên LSTM đã khép lối OOV, R_exec kéo ER về sàn false-negative (0.25%), RR(E)=0. Không tái lập ER>96% của Pasini khi Oracle vào train.”*

Câu cấm: PPO/DQN “thành công hơn Chen”.

## Lệnh

```bash
cd lab
../.venv/bin/python src/run_p4.py --phase train --algo ppo --seeds 42,43,44 --timesteps 20000
../.venv/bin/python src/run_p4.py --phase train --algo dqn --seeds 42 --timesteps 20000
../.venv/bin/python src/run_p4.py --phase eval --algo ppo,dqn --seeds 42,43,44 --max-eval 400
```

Checkpoint: `lab/runs/p4/*_oracle_seed*.zip`
