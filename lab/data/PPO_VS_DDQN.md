# Bảng PPO vs Dueling DQN (lab P4, bắt buộc)

Đối tượng: LSTM P3 (vocab cố định, pad 40, Adam). Tập đánh giá: 400 mẫu đầu `splits/adversarial_agents/test.csv`. Sàn FN không đột biến: **1/400 = 0.25%**.

Reward `R_exec` (P4): −2 hết độc JSDOM; −1 còn độc nhưng detector bắt; **+10 chỉ khi lọt và còn execute**. Success chỉ khi execute.

Không so với ER 99% Chen/Pasini artifact. Không viết “DQN mạnh hơn Chen”.

## Bảng chính

| Agent | Oracle trong train | Seed | Bước | ER | TASR | RR(E) | OR(V) trên E |
|---|---|---|---:|---:|---:|---:|---:|
| P3 PPO (baseline, không Oracle) | không | 42, 43, 44 | 20k | 0.25 / 0.50 / 1.50% | ~0.25 / 0.50 / 1.00% | 0 / 0 / 0.33 | 0.75 / 0.28 / 0.40 |
| P3 PPO trung bình 3 seed | không | — | 20k | **0.75%** | **~0.58%** | 0–0.33 | — |
| P3 PPO | không | 45 | 80k | 2.00% | — | 0.12 | 0.43 |
| P4 PPO + `R_exec` | có | 42, 43, 44 | 20k | 0.25 / 0.25 / 0.25% | 0.25 / 0.25 / 0.25% | **0** | 0.75 |
| P4 PPO trung bình 3 seed | có | — | 20k | **0.25%** | **0.25%** | **0** | — |
| P4 DQN SB3 `MlpPolicy` | có | 42 | 20k | 0.25% | 0.25% | 0 | 0.62 |
| P4 Dueling DQN | có | 42 | 20k | 1.75% | 1.75% | 0 | 0.38 |
| P4 Dueling DQN | có | 43 | 20k | 0.75% | 0.75% | 0 | 0.35 |
| P4 Dueling DQN | có | 44 | 20k | 0.75% | 0.75% | 0 | 0.50 |
| P4 Dueling DQN trung bình 3 seed | có | — | 20k | **1.08%** | **1.08%** | **0** | — |
| Sàn FN detector (không đột biến) | — | — | — | 0.25% | 0.25% | 0 | — |

Nguồn: `lab/runs/p3/p3_eval.json`, `lab/runs/p4/p4_eval.json`, `lab/runs/p4/ddqn_eval.json`.

## Đọc bảng

1. Mọi agent lab **sát sàn FN**. Không có ER >96%.
2. Oracle-in-loop **kéo PPO về đúng sàn** (0.25%) và **RR(E)=0**.
3. Dueling DQN trung bình **1.08% > PPO 0.25%** nhưng vẫn cùng bậc 1%, RR=0. Không đủ để kết luận thuật toán “thắng” detector.
4. Wilcoxon P3 vs P4 PPO (cặp 3 seed): n hiệu = 2, p two-sided exact **0.5**. Chỉ mô tả: P4 ≤ P3 mọi seed. Không tuyên bố ý nghĩa thống kê.

## Câu được / cấm

Được: *Trên LSTM đã khép OOV, PPO và Dueling DQN với `R_exec` cho ER = TASR ∈ [0.25%, 1.08%], RR(E)=0.*

Cấm: “DDQN thành công hơn Chen”; “PPO replication SAC”; dùng Wilcoxon p=0.5 như bằng chứng.
