# Kết quả P1 + P2

## P1 — Oracle execute + Mereani

Oracle JSDOM (không phải BeautifulSoup). Payload độc = **có hook chạy** (`alert`, `eval`, `javascript:`, `onerror`, `document.title`, `cookie`).

| | n |
|---|---|
| Mereani gốc | 43217 (15149 độc / 28068 lành) |
| Độc còn execute, giữ | **10824** |
| Độc chỉ đổi DOM, loại (W1) | **3542 (23.4%)** |
| Độc không DOM không JS | 783 |
| Lành bị oracle gọi độc (loại) | 10 |
| **RR trên tập độc đã giữ** | **0.0** |

Pasini giữ 3542 mẫu kia vì DOM đổi. Lab loại — đó là đo W1 trên đúng dataset của họ.

Split (seed 42), cùng tỉ lệ Table 3:

- Detector train/val/test: 3463+865+1084 mỗi lớp
- Agent train/val/test: 3463 / 865 / 1084 (chỉ độc)

## P2 — 27 action, `parser_alive` vs `browser_alive`

Khi action **thật sự đổi** payload (3 seed: script, img onerror, javascript href):

Giữ execution: A1, A2, A3, A4, A8, A11, A14, A15, A17, A18, A19, A21, A22, A23, A27.

Đổi payload mà **parser còn sống, JS chết** (W8): A5, A6, A7, A12, A13, A20, A25. A9/A24/A26 chết trên một phần seed.

A10/A16 no-op trên 3 seed (không có `http://` / `data:`) — bình thường.

A18 không còn no-op (artifact Pasini `return payload`). A21 không còn `(1)(1)`.
