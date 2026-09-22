# Quay video demo — shot nào, nói gì

Thời lượng cắt xong: **6–8 phút**. Một take ~12 phút nếu dừng Enter giữa shot.

**Quay:** terminal chữ lớn (font 16+), cửa sổ full. Không quay mặt, không train PPO.

```bash
cd /home/kali/Desktop/ATBMHTTT
# CRS phai Up (neu chua)
cd lab && docker compose up -d && cd ..

# Quay man hinh roi chay:
bash lab/src/demo_record.sh
# hoac mot mach, khong Enter:
bash lab/src/demo_record.sh --auto
```

Cắt shot 0 (health check) nếu muốn gọn.

---

## Có quay (live)

| Shot | Thời gian | Lệnh (script lo) | Bạn nói trên voice |
|---|---|---|---|
| **1** | 40s | JSDOM `alert(1)` vs `<div>hello</div>` | Paper gọi `<div>` là XSS vì đổi DOM. Lab chỉ tính khi JS chạy. |
| **2** | 40s | `unittest` oracle + 27 action | 27 action Table 2; A18/A21 lab làm đúng, artifact bị no-op/`(1)(1)`. |
| **3** | 20s | in `filter_report.json` | 23.4% nhãn Malicious Mereani chỉ đổi DOM — đo W1. RR gốc = 0. |
| **4** | 30s | `curl` app 200 / PL1 403 / hello 200 | Cùng payload: không WAF thì 200, CRS thì 403. Localhost, không phải AWS. |
| **5** | 40s | 1 payload → BLOCK vs BYPASS_EXEC | TASR = HTTP 200 **và** execute. 200 một mình không tính. |
| **6** | 30s | `/html` vs `/purify/html` | DOMPurify: HTTP vẫn 200, script bị tẩy, Δ = 1. |
| **7** | 45s | in ER hai nhánh | Artifact ~99% vì LabelEncoder. Lab ~0.75% khi khép encode. Cùng 27 action. |
| **8** | 30s | Playwright 2 payload | Hold-out Chromium khớp JSDOM trên seed. |

Voice kết: *Không train RL trên CRS vì TASR Table 2 = 0. Không claim bypass WAF.*

---

## Không quay (dài / không thêm thông tin)

| Việc | Lý do |
|---|---|
| `filter_mereani.py` full | 15–40 phút, số đã có shot 3 |
| `run_p3.py` / `run_p4.py` train | 10–40 phút, checkpoint sẵn |
| Lưới 10 seed 250k | nửa ngày, seed 42 đủ Table 4 |
| Oracle FastAPI `:5555` | nhánh A; video dùng JSDOM + số JSON |
| `measure_tasr.py` 84 payload | vài phút; shot 5 đủ ý TASR |
| Mở IDE scroll 200 file | rối |

Nếu GV muốn “thấy PPO chạy”: **một clip phụ** 20 giây `ls lab/runs/p3/*.zip` + mở `p3_eval.json` — không `learn()`.

---

## Cắt video (gợi ý timeline)

| Phút | Nội dung |
|---|---|
| 0:00–0:20 | Intro 2 câu (file `HUONG_DAN_DEMO_BAO_CAO.md`) |
| 0:20–1:20 | Shot 1–3 Oracle + W1 |
| 1:20–2:40 | Shot 4–6 CRS + TASR + Purify |
| 2:40–4:00 | Shot 7 hai nhánh 99% vs 1% |
| 4:00–4:40 | Shot 8 Playwright + kết luận TASR=0 |
| 4:40–6:00 | (tuỳ) chiếu slide bảng P6, không terminal |

Ghép sẵn ảnh bảng nếu terminal shot 7 chữ nhỏ.

---

## Nếu một lệnh fail khi quay

| Fail | Làm |
|---|---|
| `connection refused :13000` | `cd lab && docker compose up -d`, đợi 10s, quay lại shot 4–6 |
| Playwright `not installed` | bỏ shot 8, nói “JSDOM là oracle train, Playwright hold-out đã chạy 4 seed” |
| unittest fail | đừng improv; mở `lab/README.md` số đã đo |
