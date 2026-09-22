# P5 hoàn chỉnh — CRS / DOMPurify / TASR / transfer / Playwright

P5 là **đánh giá** lab WAF, không phải bắt buộc TASR>0. Gate `BYPASS_EXEC` trên CRS PL1 **không đạt** sau khi quét đủ catalog Table 2. Không train RL lên CRS.

Stack (localhost, đang sống): app `:13000`, CRS PL1 `:18080`, PL2 `:18081`.

## Gate

Cần ≥1 payload **HTTP 200 và JS vẫn chạy** trên CRS PL1.

**Không đạt.** Không bịa payload ngoài Table 2, không LLM.

## A. Catalog 3 seed × 27 action (84), `/html`

| Target | n | BLOCK | NOEXEC | EXEC | Escape | TASR | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| CRS PL1 | 84 | 84 | 0 | 0 | 0 | **0** | 0 |
| CRS PL2 | 84 | 84 | 0 | 0 | 0 | **0** | 0 |
| App | 84 | 0 | 13 | 71 | 1.00 | **0.845** | 0.155 |
| DOMPurify | 84 | 0 | 84 | 0 | 1.00 | **0** | **1.00** |

## B. Mở rộng catalog (P5 hoàn thiện)

| Thí nghiệm | n | PL1 BLOCK | TASR PL1 |
|---|---:|---:|---:|
| Mereani đã decode × (gốc+27 action) | 1120 | 1120 | **0** |
| Chuỗi 3 action (7 keeper × 2 seed) | 686 | 686 | **0** |
| Cặp 2 action (trước đó) | 672 | 672 | **0** |
| `/attr` và `/js` 84 payload | 168 | 168 | **0** |

## C. Transfer LSTM-agent → CRS (hạng mục P5 còn thiếu, đã chạy)

80 payload agent-test, PPO P3 seed42 và PPO P4 seed42, sink `/html`.

| Agent | PL1 TASR | PL2 TASR | App TASR | App Δ |
|---|---:|---:|---:|---:|
| P3 PPO | **0** | **0** | 0 | 0.99 |
| P4 PPO-oracle | **0** | **0** | 0.0125 | 0.99 |

Agent train trên LSTM **không** chuyển thành lọt CRS. App TASR thấp vì Mereani phản xạ cả URL, khác seed `<script>`.

## D. Playwright hold-out (Chromium)

Cùng hook `alert` trên 4 mẫu:

| Payload | JSDOM | Chromium |
|---|---|---|
| `<script>alert(1)</script>` | execute | execute |
| `<img src=x onerror=alert(1)>` | execute | execute |
| `javascript:` href | execute | execute |
| `<div>hello</div>` | không | không |

Hold-out khớp JSDOM trên seed. Không có BYPASS_EXEC CRS nên không có mẫu Chromium-qua-WAF.

## E. Mereani 400 raw URL qua PL1 (trước đó)

483 BLOCK, 1 NOEXEC (encode nhiều lớp), 0 EXEC. Escape ≠ TASR.

## Kết luận P5 (đóng)

1. CRS 4 paranoia 1 **chặn hết** Table 2 (1, 2, 3 action) và agent LSTM transfer.
2. DOMPurify: Escape 100%, TASR 0 — Δ=1, bệnh “lọt HTTP nhưng hết độc”.
3. Không train RL trên CRS: catalog chưa có primitive `BYPASS_EXEC`.
4. Paper không đụng WAF; đây là phần luận văn **vượt** Pasini bằng kết quả âm.

Câu viết: *“Trên lab CRS 4 PL1, catalog Chen/Pasini và PPO train LSTM có TASR=0. WAF không dính OOV-None.”*

Câu cấm: “bypass CRS”, “TASR>0”, train RL rồi đổ lỗi thuật toán.

## Lệnh

```bash
cd lab
../.venv/bin/python src/measure_tasr.py --sink /html
../.venv/bin/python src/complete_p5.py --bases 40 --transfer-n 80 --skip-playwright
node oracle/pw_check.mjs   # JSONL stdin
```

File số: `data/tasr_report.json`, `data/p5_complete.json`, `data/p5_complete_rows.csv`.
