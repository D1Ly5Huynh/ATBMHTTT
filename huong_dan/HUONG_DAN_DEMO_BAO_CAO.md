# Demo + báo cáo — việc của bạn

Cập nhật: 2026-09-17  
**Không đợi 10 seed.** Số seed 42 + nhánh B đã đủ bảo vệ.

Câu 20 giây (học thuộc):

> Chen báo Escape Rate ~99% mà không kiểm tra payload còn là XSS. Pasini thêm Oracle DOM. Em bám khung đó, siết Oracle thành thực thi JavaScript, và đo CRS. Khi giữ bug encode của artifact thì ER ~99% lặp lại được; khi khép bug thì ER rơi còn ~1%. Trên CRS lab, catalog Table 2 có TASR = 0.

---

## A. Trước demo (tối hôm trước, 20 phút)

1. Máy có Docker + `.venv` + `lab/node_modules`.
2. Bật stack CRS (giữ chạy):

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
docker compose up -d
curl -sS http://127.0.0.1:13000/health
```

3. Chạy sẵn 4 lệnh dưới, **chụp terminal** (backup nếu wifi/Docker hỏng).
4. Mở sẵn 3 file: P6, `PASINI_FAITHFUL_RESULTS.md`, `PPO_VS_DDQN.md`.
5. **Không** train PPO live. **Không** bật lưới 10 seed trên máy demo (CPU đầy).

---

## B. Demo sống (~10–12 phút)

Thứ tự nói = thứ tự lệnh. Mỗi lệnh < 30 giây.

### 1. Oracle: `<div>` không phải XSS (W1) — 2 phút

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
node oracle/jsdom_oracle.mjs --payload '<script>alert(1)</script>'
node oracle/jsdom_oracle.mjs --payload '<div>hello</div>'
../.venv/bin/python -m unittest tests.test_oracle -v
```

Nói: paper gọi `<div>hello</div>` là độc vì đổi DOM. Lab chỉ tính độc khi JS chạy. 23.4% nhãn Mereani là parser-only.

### 2. Hai nhánh, hai ER — 3 phút (slide, không train)

Mở bảng:

| Nhánh | Encode | Oracle | ER PPO |
|---|---|---|---|
| A artifact `data/10` | LabelEncoder từng mẫu | DOM vs `abc` | **~99%** |
| B lab | id cố định | JSDOM execute | **0.75%** |

Nói: cùng 27 action. Khác encode. 99% là TH2 (OOV/`None`), không phải XSS mạnh.

Chỉ file, không chạy 250k:

- `lab/data/PASINI_FAITHFUL_RESULTS.md` — Table 4 trùng, LSTM 98.78%, RQ3 98.34%
- `lab/data/P3_RESULTS.md` — ER 0.75%
- `lab/runs/p3/lstm.pt` — checkpoint có thật

### 3. CRS: 200 ≠ thành công (TASR) — 3 phút

```bash
# App không WAF: 200
curl -sS -o /dev/null -w 'app %{http_code}\n' \
  'http://127.0.0.1:13000/html?q=%3Cscript%3Ealert(1)%3C/script%3E'

# CRS PL1: 403
curl -sS -o /dev/null -w 'pl1 %{http_code}\n' \
  'http://127.0.0.1:18080/html?q=%3Cscript%3Ealert(1)%3C/script%3E'

# Chuỗi lành: 200
curl -sS -o /dev/null -w 'pl1 hello %{http_code}\n' \
  'http://127.0.0.1:18080/html?q=hello'
```

Nói: TASR = `#BYPASS_EXEC / N` (200 **và** JS chạy). Table 2 trên PL1: TASR = 0. DOMPurify: HTTP lọt nhưng hết độc, Δ = 1. Không train RL lên CRS vì chưa có primitive.

### 4. PPO vs DDQN (nhánh B) — 1 phút

Slide: PPO P4 = 0.25% = sàn FN; Dueling DQN = 1.08%; RR = 0. Không nói “DQN mạnh hơn Chen”.

### 5. Câu hỏi trước — 2 phút

| Họ hỏi | Trả lời |
|---|---|
| Sao không 99%? | Nhánh B khép LabelEncoder. Nhánh A vẫn 99%. |
| Replication Chen? | Protocol replication, PPO không SAC, Mereani không 90k. |
| Bypass CRS? | Không. TASR = 0. |
| 10 seed? | Paper 10; em seed 42 đủ Table 4 + RQ3 3 mạng. Đang/đã chạy thêm nếu xong. |
| Wilcoxon? | n=2, p=0.5 — không pretent ý nghĩa. |

**Dự phòng:** Docker chết → chỉ chiếu ảnh `curl` + JSON `lab/data/p5_complete.json`.

---

## C. Báo cáo / luận văn (việc viết)

Không viết lại thí nghiệm. **Dán** `huong_dan/2026-09-17_luan-van-P6.md` vào Word nhà trường.

| Chương | Lấy từ P6 mục | Bảng số |
|---|---|---|
| Mở đầu / mục tiêu | đoạn “Một câu” | — |
| Related Work | §1 | Chen, Fang, Wang, Pasini |
| Phương pháp | §2 | bảng Chen / Pasini / mình |
| Kết quả | §3 | hai nhánh + PPO vs DDQN + CRS |
| Thảo luận | §4 | TH2 |
| Hạn chế | §5 | JSDOM, 1–3 seed, Mereani 2018 |
| Kết luận | §6 | 5 gạch |
| Tài liệu | §8 | citation sẵn |

Slide (8–10 trang, **không** 30):

1. Vấn đề: ER không kiểm tra XSS còn chạy  
2. Pasini RQ1–RQ3  
3. Đóng góp: Oracle execute + CRS TASR  
4. Bảng Chen / Pasini / mình  
5. Nhánh A: Table 4 + ER 99%  
6. Nhánh B: ER 0.75% → 0.25%  
7. CRS TASR = 0, Δ Purify = 1  
8. Hạn chế + kết luận  

File số khi hội đồng đòi xem:

- `lab/data/P1_P2_RESULTS.md` … `P5_RESULTS.md`
- `lab/data/PASINI_FAITHFUL_RESULTS.md`
- `lab/data/PPO_VS_DDQN.md`

---

## D. Câu được / cấm trên slide và miệng

**Được:** khung Pasini; 23.4% Mereani chỉ đổi DOM; artifact tái lập ER ~99%; khép encode thì ER ~1%; CRS lab TASR=0.

**Cấm:** “em reproduce Chen 99%”; SAC; “PPO mạnh hơn Chen”; “bypass CRS / AWS WAF”; “HTTP 200 = thành công”; LLM generator.

---

## E. Không cần làm trước bảo vệ

- Đợi xong 10 seed (seed 42 đã khớp bảng chính)
- Train lại PPO live
- Mở LabelEncoder trên nhánh B
- Đánh WAF cloud
