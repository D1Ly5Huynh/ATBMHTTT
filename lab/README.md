# Lab bám Pasini 2026

**Build từ máy trống (chi tiết):** [`../huong_dan/HUONG_DAN_BUILD_LAB.md`](../huong_dan/HUONG_DAN_BUILD_LAB.md)

Khung đánh giá: Oracle **thực thi** → Ruin Rate → 27 action. Không copy ER 99%.

## Trạng thái P1 / P2

| Hạng mục | Kết quả |
|---|---|
| Oracle JSDOM | `oracle/eval_xss.mjs` — hook `alert` / `eval` / `title` / `cookie` / `javascript:` / `img.onerror` |
| Oracle parser (Pasini) | `parser_changed()` — DOM-diff vs `"abc"` |
| Mereani raw | `data/Payloads.csv` — 43217 dòng (15149 độc / 28068 lành) |
| Lọc execution | `data/mereani_exec_oracle.csv` |
| RR gốc sau lọc | **0.0** (gate P1 đạt) |
| W1 đo được | **23.4%** nhãn Malicious chỉ đổi DOM, **không** chạy JS (3542/15149) |
| Split kiểu Table 3 | `data/splits/` |
| 27 action | `src/actions.py` — A18 và A20 có thật (artifact Pasini để trống) |

Playwright hold-out trên 4 seed (khớp JSDOM). Chương P6: `../huong_dan/2026-09-17_luan-van-P6.md`.

## Số lọc (P1)

```
malicious_in              15149
malicious_exec (kept)     10824
malicious_parser_only      3542   ← W1
malicious_neither           783
benign_exec_false_positive   10
benign_kept               28058
rr_malicious_kept           0.0
```

Pasini giữ mọi payload **đổi cây DOM**. Lab chỉ giữ payload **chạy được**. Đó là chỗ luận văn mạnh hơn paper.

## Lệnh

```bash
cd lab
# unit tests
../.venv/bin/python -m unittest tests.test_oracle tests.test_actions -v

# lọc Mereani (RR=0)
../.venv/bin/python src/filter_mereani.py

# split detector / agent
../.venv/bin/python src/split_table3.py

# bảng parser_alive vs browser_alive
../.venv/bin/python src/action_alive.py
```

## P5 — CRS (đã đo)

Stack localhost: app `:13000`, CRS PL1 `:18080`, CRS PL2 `:18081`.
Compose: `docker-compose.yml`.

```bash
../.venv/bin/python -m unittest tests.test_crs_stack -v
../.venv/bin/python src/measure_tasr.py --sink /html
../.venv/bin/python src/measure_tasr.py --sink /html --pairs --only pl1
```

P5 **đánh giá đã đóng**. Table 2 + chuỗi 2/3 action + 1120 Mereani decode + transfer PPO: CRS PL1/PL2 **TASR = 0**. Gate `BYPASS_EXEC` không đạt → không train RL lên CRS.
App TASR 0.845; DOMPurify Δ=1.0. Playwright Chromium khớp JSDOM trên seed.
Chi tiết: `data/P5_RESULTS.md` · `data/p5_complete.json`

## P3 — LSTM + PPO (đã chạy)

Detector test: acc 0.991. PPO 3 seed × 20k: **ER trung bình 0.75%** (không phải 99%). 80k bước: ER 2%.
Chi tiết: `data/P3_RESULTS.md` · checkpoint `runs/p3/`

```bash
../.venv/bin/python src/run_p3.py --phase all --timesteps 20000 --ppo-seeds 42,43,44 --max-eval 400
```

## P4 — Oracle-in-loop (đã chạy)

`R_exec`: −2 nếu hết độc, +10 chỉ khi detector lọt **và** JSDOM execute.
PPO 3 seed: ER = TASR = **0.25%** (sàn FN). RR(E)=0. Không còn ER 0.75% kiểu P3.
DQN seed 42: cùng 0.25%. Chi tiết: `data/P4_RESULTS.md` · `runs/p4/`

```bash
../.venv/bin/python src/run_p4.py --phase all --algo ppo --seeds 42,43,44 --timesteps 20000
```

## Việc còn lại đã chạy thêm

- Catalog mở rộng TAP-B + E1–E10 vs CRS PL1: **60/60 BLOCK**, TASR=0.
- Dueling DQN 3 seed, Oracle-in-loop: ER=TASR tb **1.08%**, RR=0.
- Wilcoxon P3 vs P4: p=0.5 (n=2), chỉ mô tả.
- Tập B → LSTM: FN=0 trên 17 payload chạy được.
- Chương luận văn: `../huong_dan/2026-09-17_luan-van-P6.md`

Không train RL trên CRS (vẫn không có BYPASS_EXEC).

Artifact gốc chỉ đọc: `../artifact/Adversarial_RL_XSS` @ `a299bb6`.
Plan: `../huong_dan/PLAN_LAM_THEO_PASINI.md`
