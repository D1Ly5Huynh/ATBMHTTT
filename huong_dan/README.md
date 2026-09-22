# Mục lục `huong_dan/` — đọc theo thứ tự này

Repo: `/home/kali/Desktop/ATBMHTTT`  
Cập nhật: 2026-09-17

Đây **không** phải nơi chứa PDF trùng hay bản nháp. Mỗi file một việc. Số thí nghiệm nằm ở `lab/data/`, không copy vào đây trừ khi cần giải thích.

## Thứ tự đọc (bắt buộc)

| # | File | Việc | Độ dài |
|---|---|---|---|
| 1 | **README.md** (file này) | Biết đọc gì, không đọc gì | ngắn |
| 2 | **PLAN_LAM_THEO_PASINI.md** | Paper nói gì, mình bám gì, hai nhánh A/B, W1–W10 | trung |
| 3 | **HUONG_DAN_CHI_TIET.md** | Sổ tay đầy đủ: công thức, 27 action, P0–P6, số đã đo, câu được/cấm, citation | **dài — đọc khi làm** |
| 4 | **HUONG_DAN_BUILD_LAB.md** | Dựng máy trống: venv, Node, Docker CRS, lệnh từng pha | dài — đọc khi cài |
| 4b | **Quy_trinh_tai_hien_day_du.docx** | Full quy trình nhánh A+B (Word, copy lệnh) | Word |
| 5 | **2026-09-17_luan-van-P6.md** | Dán vào luận văn: Related Work, Phương pháp, Kết quả, Threats | dài — đọc khi viết |
| 6 | **HUONG_DAN_DEMO_BAO_CAO.md** | Checklist demo 10 phút + slide/báo cáo | ngắn — đọc trước bảo vệ |
| 6b | **HUONG_DAN_QUAY_VIDEO.md** | Shot list quay terminal 6–8 phút | ngắn |
| 6c | **Slide_Bao_ve_ATBMHTTT.pptx** | 10 slide bảo vệ (generate: `_gen_slides.py`) | chiếu |
| 7 | **Pasini_2026_BanDich_TiengViet.html** | Dịch paper. RQ HTML cũ có thể RQ1–RQ4 — **bỏ**, bám PDF v2 RQ1–RQ3 | paper |

PDF gốc **một bản**: `../papers/core/Pasini_2026_JSS_arXiv.pdf` (arXiv:2502.19095v2).

## Số thí nghiệm (không nằm trong thư mục này)

| File | Nội dung |
|---|---|
| `../lab/data/P1_P2_RESULTS.md` | Oracle JSDOM, Mereani, 27 action |
| `../lab/data/P3_RESULTS.md` | LSTM + PPO nhánh B, ER 0.75% |
| `../lab/data/P4_RESULTS.md` | Oracle-in-loop nhánh B |
| `../lab/data/PPO_VS_DDQN.md` | Bảng PPO vs Dueling DQN |
| `../lab/data/P5_RESULTS.md` | CRS / TASR / DOMPurify |
| `../lab/data/PASINI_FAITHFUL_RESULTS.md` | Nhánh A, đúng `data/10` |

## Hai nhánh — đừng trộn

| | Nhánh A (sát paper) | Nhánh B (luận văn) |
|---|---|---|
| Thư mục | `artifact/Adversarial_RL_XSS` | `lab/` |
| Dataset | `data/10` | Mereani lọc JSDOM |
| ER PPO điển hình | ~99% | ~0.75% |
| Viết vào luận văn | “protocol lặp lại được” | “khi khép TH2, ER 99% biến mất” |

## Câu cấm (mọi file)

Không viết: replication ER Chen 99% là thành công của mình; SAC; bypass CRS; WAF cloud; LLM generator; CRS HTTP 200 = TASR.

## File đã xóa (cố ý)

PDF copy, HTML giải thích trùng, docx “dễ hiểu”, chương kết quả 16-09 (gộp vào P6), sổ tay `.txt` 1000 dòng cũ (thay bằng `HUONG_DAN_CHI_TIET.md`).
