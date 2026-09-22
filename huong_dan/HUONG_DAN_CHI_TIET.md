# Sổ tay làm luận văn — bám Pasini 2026

Cập nhật: 2026-09-17  
Repo: `/home/kali/Desktop/ATBMHTTT`  
Mục lục: `README.md` · Dựng máy: `HUONG_DAN_BUILD_LAB.md` · Dán luận văn: `2026-09-17_luan-van-P6.md`

---

## 0. Bạn đang ở đâu

Đây là luận văn ATBMHTTT. Bài gốc:

Pasini, Maragliano, Kim, Tonella. *Cross-site scripting adversarial attacks based on deep reinforcement learning: Evaluation and extension study.* **JSS 2026**. arXiv:2502.19095**v2**. Artifact GitHub `GianlucaMaragliano/Adversarial_RL_XSS` commit **`a299bb6`**.

**Mục tiêu không phải** copy Escape Rate ~99% của Chen.  
**Mục tiêu là** bám **khung đánh giá**: payload đối kháng phải còn độc theo oracle.

Hai nhánh đã chạy **xong thí nghiệm**. Việc còn lại của người viết: dán `2026-09-17_luan-van-P6.md` vào Word/LaTeX.

| Pha | Trạng thái | Số chốt |
|---|---|---|
| P0 Artifact pin | xong | `a299bb6` |
| P1 Oracle JSDOM + Mereani | xong | RR gốc = 0; W1 = 23.4% |
| P2 27 action | xong | `lab/src/actions.py` |
| P3 LSTM+PPO nhánh B | xong | acc 0.991; ER tb **0.75%** |
| P4 Oracle-in-loop nhánh B | xong | PPO TASR **0.25%**; DDQN **1.08%** |
| P5 CRS + DOMPurify | xong | TASR PL1 = **0** |
| P6 Chương | xong bản markdown | file P6 |
| Nhánh A `data/10` | xong seed 42 (+ 43/44 LSTM) | Table 4 trùng; LSTM ER **98.78%**; RQ3 LSTM **98.34%** |

Gate **treo đúng**: chưa có payload Table 2 vừa execute vừa lọt CRS PL1 → **không** train RL trên CRS.

---

## 1. Paper nói gì (PDF v2, không HTML)

HTML `Pasini_2026_BanDich_TiengViet.html` có thể đánh RQ1–RQ4. **Bỏ.** PDF v2 chỉ **RQ1–RQ3**.

| RQ | Câu hỏi | Metric |
|---|---|---|
| Replication | PPO có lọt detector DL ~99% như Chen? | ER |
| RQ1 / TH1 | Mutation có phá XSS không? | `RR(E)` trên tập lọt |
| RQ2 / TH2 | Preprocess/OOV có phá XSS không? | `RR(V)`, `OR(V)` |
| RQ3 | Nhét Oracle vào reward thì ER còn cao? | ER', RR sau train |

Pasini kết luận: TH1 nhẹ (~6–7%); TH2 là thủ phạm (`RR(V)` ~93–98%, gần nửa token là `None`); khi Oracle DOM vào train, ER vẫn **>96%** và RR ~0.

Luận văn: **bám khung**, **không bám ER 99%**, **không bám Oracle BeautifulSoup**.

---

## 2. Công thức (viết đúng, dùng đúng)

\[
ER = \frac{\text{số payload độc mà detector gọi lành}}{\text{số payload adversarial}}
\]

\[
O(p) = 1 \text{ nếu Oracle = Malicious},\quad
RR(M) = 1 - \frac{1}{|M|}\sum_{m \in M} O(m)
\]

\[
OR(V) = \frac{\text{số token } None}{|V|}
\]

`E` = tập lọt detector. `V` = E sau preprocess (token, pad, thay OOV bằng `None`).

**Lab CRS** (paper không có):

| Tên | Nghĩa | Dùng |
|---|---|---|
| Escape | HTTP 200 | phụ, **không** phải thành công |
| **TASR** | `#BYPASS_EXEC / N` | chính = ER có oracle thực thi |
| **Δ** | Escape − TASR | khoảng TH2 (lọt HTTP nhưng hết độc) |

Ba nhãn P5: `BLOCK` (403) | `BYPASS_NOEXEC` (200, JS không chạy) | `BYPASS_EXEC` (200 **và** execute).

---

## 3. Hai nhánh — bắt buộc hiểu trước khi viết số

```
Nhánh A  artifact/ + data/10 + LabelEncoder từng mẫu + Oracle DOM
         → ER ~99%   (tái lập hiện tượng paper)

Nhánh B  lab/ + Mereani JSDOM + token-id cố định + Oracle execute
         → ER ~1%    (khép TH2 thì 99% biến mất)
```

Cùng 27 mô tả Table 2. Khác encode + oracle + (nhánh B) action làm đủ.

**Cấm** lấy ER 98.78% nhánh A viết thành “PPO luận văn đạt 99%”.  
**Cấm** lấy ER 0.75% nhánh B viết thành “replication paper thất bại vì train hỏng”.

---

## 4. Pipeline (đúng paper)

```
payload độc (Oracle = 1, RR gốc = 0)
  → agent chọn 1/27 action, tối đa 15 bước
  → detector (A: MLP/LSTM/CNN; B: LSTM; P5: CRS)
       lọt → tập E → ER
  → Oracle(E)                 → RR(E)     RQ1
  → preprocess E → V, đếm None → OR(V)    RQ2
  → train lại, reward âm nếu hết độc
                              → ER', TASR RQ3
```

---

## 5. Chen vs Pasini vs luận văn

| | Chen 2022 | Pasini 2026 | Luận văn |
|---|---|---|---|
| Dataset | XSSed+Alexa ~90k, **không public** | Mereani + Oracle DOM, undersample | A: đúng `data/10`. B: Mereani JSDOM |
| Detector | MLP LSTM CNN + SafeDog/XSSChop | MLP LSTM CNN | A: 3 mạng. B: LSTM + **CRS PL1/PL2 + DOMPurify** |
| Agent | SAC | PPO (SB3 SAC = continuous) | PPO **và** Dueling DQN — bảng bắt buộc |
| State | lịch sử action | lịch sử action (code) | **Giữ như paper** (chưa nhúng payload) |
| Reward | +10 / −1 | PDF −2 nếu vỡ; **code −5** | A: đúng code −5. B: `R_exec` (−2 hết độc; +10 chỉ lọt **và** execute) |
| Oracle | không | BS4 + zss vs `"abc"` | A: như paper. B: JSDOM; Playwright 4 seed |
| Metric | ER | ER + RR + OR | A: ER/RR/OR. B: **TASR + Δ** |
| Action | 27 mô tả | 27, A18/A20/A21 lỗi | B: đủ 27 + `parser_alive` / `browser_alive` |

Lệch nhánh B đã ghi: Adam (SGD kẹt 50%); pad 40 (artifact `MAX_LENGTH=30`, paper viết 200); 3 seed (paper 10); eval 400/1084.

---

## 6. Điểm yếu artifact (W1–W10) — đo được

Mở code `artifact/Adversarial_RL_XSS` @ `a299bb6`.

### W1 — Oracle không chạy JavaScript (nặng nhất)

FastAPI nhét payload vào Jinja `|safe` → BeautifulSoup → `zss` so với trang `"abc"`. DummyDetector **luôn True**.

- `<script>alert(1)</script>` = độc vì **thêm node**, không vì script chạy.
- `<div>hello</div>` = độc (đổi cây). Lab đo: `is_same_dom(div, abc) = False`.
- 3542/15149 (23.4%) nhãn Malicious Mereani chỉ đổi DOM, **không** execute JSDOM.

Paper mục 8 tự nhận Oracle “may be subject to misclassification”.

**Lab:** Oracle = JSDOM hook (`alert`, `eval`, `title`, `cookie`, `javascript:`, `onerror`). DOM-diff chỉ phụ.

### W2 — RR(V) gần tautology

Họ reconstruct token (`" ".join`) rồi mới Oracle. Chuỗi toàn `None` không còn HTML → RR(V) ~98% một phần **đúng vì định nghĩa**. Claim TH2 dùng **OR(V)** và Oracle trên **payload thật**, không chỉ chuỗi `None`.

### W3 — Không phải replication trung thành Chen

Khác: Mereani vs 90k; PPO vs SAC; embed 8 vs Word2Vec 32; sigmoid vs softmax; bỏ SafeDog; detector và agent **cùng distribution**. Viết “protocol replication”. Không viết “reproduced Chen’s numbers”.

### W4 — Table 4 trùng tuyệt đối

MLP = LSTM = CNN = P 99.67 / R 100 / Acc 99.83. Lab **tái lập đúng bộ số đó** trên `data/10`. Ba mạng một số = detector quá dễ + encode lỗi, không phải copy bảng.

### W5 — MDP không nhìn payload

`Box(shape=(max_steps,))` = lịch sử action. Policy dễ học chuỗi tạo OOV. Plan từng muốn embed payload — **chưa làm**; viết trung thực.

### W6 — Paper ≠ code (reward)

PDF RQ3: −2. Code: **−5**. Nhánh A bám code. Nhánh B `R_exec` −2 (bám PDF) và **không** `success` nếu không execute (khác artifact: họ vẫn `done=True` khi detector lọt dù Oracle fail).

### W7 — Mereani 2018

Toàn `alert` / `<script>`. TAP-B 30 vector: LSTM FN=0 trên 17 mẫu chạy. Tập B không làm detector “vỡ”.

### W8 — Action liệt kê, code không làm đủ

| Mã | Paper | Artifact `mutators.py` | Lab `actions.py` |
|---|---|---|---|
| A1 | `&#14` trước `javascript` | `re.sub` **thay cả match** | chèn, giữ word |
| A18 | Unicode-encode JS | `return payload` no-op | có thật |
| A20 | `>` thẻ đơn → `<` | stub `&gt;&lt;` | có thật |
| A21 | thay `alert` | `alert(1)` → `(1)(1)` | không nhân `(1)` |
| A2/A4 | mixed case | preprocess `.lower()` hủy | giữ XSS; detector B vẫn lower — ghi threats |
| A8/A11/A19 | entity | `html.unescape` hủy | tương tự |
| A25 | `vbscript` | chết Chromium | cờ `browser_alive=False` |

Bảng đủ 27 (paper Table 2 → `ACTION_META` trong `lab/src/actions.py`):

| | Paper | Nhóm |
|---|---|---|
| A1 | Thêm `&#14` trước `javascript` | entity |
| A2 | Mixed-case tên thuộc tính HTML | html-case |
| A3 | Space → `/` hoặc `%0A`/`%0D` | whitespace |
| A4 | Mixed-case tên thẻ | html-case |
| A5 | Bỏ `>` thẻ rỗng | html-tag |
| A6 | Thêm `&NewLine;` vào `javascript` | entity |
| A7 | Thêm `&#x09` vào `javascript` | entity |
| A8 | HTML entity hex cho mã JS | js-encode |
| A9 | Nhân đôi thẻ HTML | html-tag |
| A10 | `http://` → `//` | url |
| A11 | HTML entity thập phân cho JS | js-encode |
| A12 | Thêm `&colon;` vào `javascript` | entity |
| A13 | Thêm `&Tab;` vào `javascript` | entity |
| A14 | Thêm `/drfv/` sau `<script` | html-tag |
| A15 | `()` → backtick | js-syntax |
| A16 | Base64 `data:` | url |
| A17 | Bỏ dấu nháy | html-tag |
| A18 | Unicode-encode JS (artifact **no-op**) | js-encode |
| A19 | HTML entity cho chữ `javascript` | entity |
| A20 | `>` thẻ đơn → `<` (artifact **stub**) | html-tag |
| A21 | `alert` qua nối chuỗi (artifact `(1)(1)`) | alert |
| A22 | `alert` qua `toString(30)` | alert |
| A23 | Chuỗi nhiễu trước payload | noise |
| A24 | Comment trong thẻ | html-tag |
| A25 | `javascript` → `vbscript` (chết Chromium) | legacy |
| A26 | `%00` trong thẻ | legacy |
| A27 | `alert` qua `/al/.source` | alert |

Khi action **đổi** payload (3 seed script/img/`javascript:`):

- Giữ JS: A1 A2 A3 A4 A8 A11 A14 A15 A17 A18 A19 A21 A22 A23 A27
- Parser sống, JS chết (W8): A5 A6 A7 A12 A13 A20 A25
- A10/A16 no-op nếu không có `http`/`data:`

### W9 — Thiếu thí nghiệm reviewer

Không transfer LSTM→CNN. Không adversarial training detector. 10 seed paper vs lab 1–3 seed. Wilcoxon n=2 vô nghĩa. Histogram P4: 1 escape = sàn FN.

### W10 — Presentation artifact

README còn “submitted to COSE”. FastAPI title `"StreetView"`. Intro hứa nhầm số mục. `bs4 = "^0.0.2"` là metapackage.

---

## 7. P0–P6 — lệnh và số đã đo

Mọi lệnh Python: `/home/kali/Desktop/ATBMHTTT/.venv/bin/python`. Chi tiết cài máy: `HUONG_DAN_BUILD_LAB.md`.

### P0

```bash
git -C artifact/Adversarial_RL_XSS rev-parse --short HEAD
# a299bb6
```

Không `import mutators.py` vào train nhánh B. Không chạy `prepare_dataset.py` (mất split paper).

### P1

```bash
cd lab
../.venv/bin/python -m unittest tests.test_oracle tests.test_actions -v
../.venv/bin/python src/filter_mereani.py
```

| | n |
|---|---:|
| Mereani gốc | 43217 (15149 độc / 28068 lành) |
| Độc execute, giữ | **10824** |
| Độc chỉ DOM, loại (W1) | **3542 (23.4%)** |
| RR trên tập giữ | **0.0** |

File: `lab/data/filter_report.json`, `mereani_exec_oracle.csv`.

### P2

```bash
../.venv/bin/python src/split_table3.py
../.venv/bin/python src/action_alive.py
```

Split seed 42, tỉ lệ Table 3: detector 3463/865/1084 mỗi lớp; agent chỉ độc 3463/865/1084.

### P3 (nhánh B)

```bash
../.venv/bin/python src/run_p3.py --phase all --timesteps 20000 --ppo-seeds 42,43,44 --max-eval 400
```

LSTM test n=2168: acc **0.991**. FN sàn 400 mẫu: 0.25%.  
PPO 20k × 3 seed ER: 0.25 / 0.50 / 1.50% → tb **0.75%**. 80k: 2%.  
Pasini artifact: **>96%**.

Escape còn lại OR(V) 28–75% → TH2 còn nhưng hiếm.

### P4 (nhánh B)

```bash
../.venv/bin/python src/run_p4.py --phase all --algo ppo --seeds 42,43,44 --timesteps 20000
../.venv/bin/python src/train_ddqn.py --phase all --seeds 42,43,44 --timesteps 20000
```

| Agent | ER | TASR | RR(E) |
|---|---:|---:|---:|
| P3 PPO 3 seed | 0.75% | ~0.58% | 0–0.33 |
| P4 PPO `R_exec` | **0.25%** | **0.25%** | **0** |
| P4 Dueling DQN 3 seed | **1.08%** | **1.08%** | **0** |

Chi tiết từng seed: `lab/data/PPO_VS_DDQN.md`. Wilcoxon p=0.5, n=2 — chỉ mô tả.

### P5

```bash
cd lab && docker compose up -d --build
../.venv/bin/python -m unittest tests.test_crs_stack -v
../.venv/bin/python src/measure_tasr.py --sink /html
```

Cổng: app `127.0.0.1:13000`, CRS PL1 `:18080`, PL2 `:18081`.

| Thí nghiệm | TASR CRS PL1 |
|---|---|
| 84 seed×Table2 | **0** |
| 672 cặp / 686 bộ ba / 1120 Mereani | **0** |
| Transfer PPO P3/P4 | **0** |
| TAP-B + E1–E10 | **0** |

App không WAF TASR **0.845**. DOMPurify TASR **0**, Δ=**1**.  
Playwright 4 seed khớp JSDOM. Gate BYPASS_EXEC **không đạt**.

### Nhánh A (sát paper)

```bash
bash lab/src/run_pasini_faithful.sh oracle-up     # :5555
bash lab/src/run_pasini_faithful.sh detectors     # ~3 phút, Table 4
bash lab/src/run_pasini_faithful.sh ppo-lstm-fast # 50k; đừng 250k lần đầu
```

Table 4: P 99.67 R 100 Acc 99.83 — **trùng paper**, cả 3 mạng.

| | ER paper | ER lab | RR(V) lab |
|---|---:|---:|---:|
| LSTM không Oracle 250k | 98.62% | **98.78%** | 98.54% |
| MLP không Oracle | 99.73% | **98.67%** | 98.54% |
| CNN không Oracle | 98.25% | **98.89%** | 1.35% (1 seed, ít OOV) |
| LSTM RQ3 250k | 98.13% | **98.34%** | **0** |
| CNN RQ3 250k | 96.89% | **96.00%** | 0.12% |
| MLP RQ3 250k | 97.37% | **97.89%** | **0** (50k chỉ 83.8% vì thiếu bước) |

LSTM 3 seed không Oracle: 98.78 / 97.34 / 96.56% → tb 97.56%.

---

## 8. Câu được viết / câu cấm

**Được**

- Khung đánh giá theo Pasini et al. (2026): mẫu đối kháng phải còn độc theo oracle thực thi.
- 23.4% nhãn Malicious Mereani chỉ đổi DOM — Oracle BeautifulSoup không tương đương XSS.
- Trên artifact `data/10`, PPO tái lập ER ~99% và RQ3 LSTM/CNN ER>96% với RR≈0 **theo Oracle DOM**.
- Khi khép token-id, PPO Table 2 không còn ER ~99%; escape còn lại mang OOV cao.
- Trên LSTM đã khép OOV, PPO ER=TASR=0.25%, Dueling DQN 1.08%, RR(E)=0.
- Trên lab CRS 4 PL1, catalog Chen/Pasini có TASR=0.

**Cấm**

- Replication thành công ER Chen 99% như thành công luận văn.
- “Reproduced Chen’s numbers”; replication SAC.
- PPO/DQN mạnh hơn Chen.
- Bypass CRS; đánh WAF cloud.
- CRS 200 = TASR; LLM sinh payload.
- Wilcoxon p=0.5 như khác biệt có ý nghĩa.
- RQ1–RQ4 theo HTML cũ.

---

## 9. Citation

```
Pasini S., Maragliano G., Kim J., Tonella P. (2026).
Cross-site scripting adversarial attacks based on deep reinforcement
learning: Evaluation and extension study. Journal of Systems and Software.
DOI: 10.1016/j.jss.2026.112856. arXiv:2502.19095.

Chen L., Tang C., He J., Zhao H., Lan X., Li T. (2022).
XSS adversarial example attacks based on deep reinforcement learning.
Computers & Security 120:102831.

Mereani F.A., Howe J.M. (2018). Detecting cross-site scripting attacks
using machine learning. AMLTA 2018.

Fang Y. et al. (2018). DeepXSS / Dueling DQN. ER < 10%.
Wang Y. et al. (2022). Soft Q-learning. Computers & Security 113. ER ~85%.
Zhang et al. (2020). MCTS. IEEE Access.
Schulman et al. (2017). PPO. arXiv:1707.06347.
Haarnoja et al. (2018). SAC. arXiv:1801.01290.
OWASP ModSecurity Core Rule Set 4 (lab paranoia 1–2, không phải WAF vendor).
Cure53 DOMPurify 3.2.4 (lab).
```

---

## 10. Definition of done

- [x] Artifact pin + bảng Chen/Pasini/mình
- [x] Oracle execute, RR gốc = 0
- [x] 27/27 action + `parser_alive` / `browser_alive`
- [x] Replication DL nhánh B: ER, RR, OR, 3 seed
- [x] Oracle-in-loop nhánh B: TASR, bảng PPO vs DDQN
- [x] Lab CRS: BLOCK / NOEXEC / EXEC; TASR=0
- [x] Nhánh A Table 4 + ER ~99% + RQ3 LSTM
- [x] Không dùng ER Chen 99% làm thành công của mình
- [x] W1, W3, W4, W8 có số lab
- [ ] Dán P6 vào Word nhà trường
- [x] MLP RQ3 250k ER **97.89%**, RR=0
- [ ] Gate BYPASS_EXEC — **không đạt, đúng, dừng**
