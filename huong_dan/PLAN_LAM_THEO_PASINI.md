# Làm theo Pasini 2026 — plan + điểm yếu

Paper: Pasini, Maragliano, Kim, Tonella. *Cross-site scripting adversarial attacks based on deep reinforcement learning: Evaluation and extension study.* JSS 2026. arXiv:2502.19095v2.

Artifact đã clone: `artifact/Adversarial_RL_XSS` @ `a299bb6` (2025-01-08).  
FigShare: https://figshare.com/articles/dataset/Artifacts_of_XSS_adversarial_example_attacks_based_on_deep_reinforcement_learning_A_Replication_and_Extension_study_/27959817  
GitHub: https://github.com/GianlucaMaragliano/Adversarial_RL_XSS

Luận văn bám **PDF v2** (RQ1–RQ3). Đọc mục lục `huong_dan/README.md`. HTML dịch paper không dùng số RQ1–RQ4.

---

## Một câu

Chen train RL để XSS “lọt” detector, ER ~99%, **không kiểm tra payload còn chạy**. Pasini lặp lại, thêm Oracle, chứng minh phần lớn “lọt” là do preprocess/OOV. Khi nhét Oracle vào train, ER vẫn >96% trên MLP/LSTM/CNN.

**Mình bám khung đánh giá (Oracle → RR → Oracle-in-the-loop), không bám ER 99%, không bám Oracle BeautifulSoup.**

---

## Pipeline bắt buộc (đúng paper)

```
payload độc (Oracle = 1)
  → agent chọn 1/27 action Table 2
  → detector (paper: MLP/LSTM/CNN; luận văn: CRS + DOMPurify)
       lọt → tập E  → ER
  → Oracle(E)                    → RR(E)     RQ1 / TH1
  → preprocess E → V, đếm None   → OR(V)     RQ2 / TH2
  → train lại, reward âm nếu không còn XSS
                                 → ER', TASR  RQ3
```

Công thức:

- `ER = (# độc detector gọi lành) / |adversarial|`
- `O(p) = 1` nếu Oracle = Malicious
- `RR(M) = 1 − Σ O(m) / |M|`
- `OR(V) = (# token None) / |V|`

Với lab CRS:

- Escape = CRS trả 200 (phụ)
- **TASR = #BYPASS_EXEC / N** ≡ ER có Oracle
- **Δ = Escape − TASR** ≡ khoảng TH2

Câu được viết: *Khung đánh giá theo Pasini et al. (2026): mẫu đối kháng phải còn độc theo oracle thực thi.*  
Câu cấm: copy ER Chen 99%; nói replication SAC; nói đánh AWS WAF; nói LLM generator.

---

## Bảng khác biệt — Chen vs Pasini vs luận văn

| | Chen 2022 | Pasini 2026 | Luận văn |
|---|---|---|---|
| Dataset detector | XSSed+Alexa ~90k, **không public** | Mereani, Oracle-filter, undersample | Mereani (tập A) + payload context (tập B) |
| Detector | MLP/LSTM/CNN + SafeDog/XSSChop | Chỉ MLP/LSTM/CNN | Baseline DL 1 lần + **CRS PL1/PL2 + DOMPurify** |
| Agent | SAC | PPO (SB3 SAC = continuous) | PPO (replication) **và** Dueling DDQN — phải có bảng so |
| State | lịch sử action | lịch sử action (code xác nhận) | **giữ lịch sử action** như paper (chưa nhúng payload — ghi threats) |
| Reward | +10 / −1 | paper: −2 nếu vỡ; **code: −5** | `R_exec`: + lọt và execute; − vỡ; 0 bị chặn còn độc |
| Oracle | không | BS4 + zss, DOM-diff vs `"abc"` | JSDOM hook + Playwright (hold-out) |
| Metric chính | ER | ER + RR + OR | TASR + Δ; ER/OR chỉ để đối chiếu paper |
| Action | 27 (mô tả) | 27 (code: A18 no-op, A20 stub) | đủ 27 + cờ `parser_alive` / `browser_alive` |

---

## Việc theo thứ tự (đã chạy — số thật)

Chi tiết lệnh + bảng: `HUONG_DAN_CHI_TIET.md`. Dựng máy: `HUONG_DAN_BUILD_LAB.md`.

### P0 — artifact

- [x] Clone, pin `a299bb6`
- [x] Dùng CSV `data/10` sẵn trong artifact (không `prepare_dataset.py`)
- [x] CRS nằm trong `lab/docker-compose.yml` (localhost)

### P1 — Oracle execute trước mọi train

Gate: RR gốc = 0 trên tập đã lọc — **đạt**.

- [x] JSDOM hook `alert` / `eval` / `title` / `cookie` / `javascript:` / `onerror`
- [x] Playwright 4 seed, khớp JSDOM
- [x] Lọc Mereani: giữ 10824 độc execute; loại 3542 parser-only (**W1 = 23.4%**)
- [x] Split kiểu Table 3, agent chỉ Malicious

### P2 — 27 action

- [x] `lab/src/actions.py` đủ 27; A18/A20/A21 **không** copy bug artifact
- [x] `parser_alive` / `browser_alive` (`lab/data/action_alive.csv`)
- Gate BYPASS_EXEC CRS PL1: **không đạt** sau Table 2 + mở rộng. Đúng → không train RL CRS.

### P3 — Replication DL nhánh B (khép encode)

Mục đích: protocol lặp lại được **khi khép TH2**, không khoe ER.

- [x] Vocab 10%, pad 40, Adam, LSTM acc 0.991
- [x] PPO 3 seed × 20k: ER tb **0.75%** (80k → 2%). Paper artifact >96%
- Escape còn lại OR(V) 28–75% → TH2 còn nhưng hiếm

### P4 — Oracle-in-the-loop nhánh B

- [x] `R_exec`: +10 chỉ khi lọt **và** execute
- [x] PPO 3 seed: ER=TASR=**0.25%**, RR=0
- [x] Dueling DQN 3 seed: **1.08%**, RR=0 — `lab/data/PPO_VS_DDQN.md`
- Histogram 1 escape = sàn FN: không kết luận A1/A6–A13

### P5 — CRS / DOMPurify (vượt paper)

- [x] PL1 `:18080` PL2 `:18081` app `:13000`
- [x] TASR PL1 = **0** trên 84+672+686+1120+transfer+TAP-B
- [x] App TASR 0.845; DOMPurify Δ=1.0
- Không claim WAF cloud

### P6 — Claim luận văn

- [x] `2026-09-17_luan-van-P6.md`
- [x] Nhánh A `PASINI_FAITHFUL_RESULTS.md` (Table 4 trùng, LSTM ER 98.78%, RQ3 98.34%)
- [ ] Dán Word/LaTeX nhà trường

### Nhánh A — sát paper (thêm, không thay P3)

- [x] Table 4 MLP=LSTM=CNN = 99.67/100/99.83
- [x] PPO không Oracle 3 mạng ER ~99%; LSTM 3 seed tb 97.56%
- [x] RQ3 LSTM 98.34% / CNN 96.00% / MLP **97.89%** (cả ba 250k), RR≈0

---

## Ưu tiên (đã làm theo thứ tự này)

1. P1 + P2 — không có thì train vô nghĩa → **xong**  
2. P5 TASR/Δ trên CRS → **xong, TASR=0**  
3. P4 Oracle-in-loop → **xong**  
4. P3 một detector × 3 seed → **xong**  
5. PPO vs DDQN → **xong** (`PPO_VS_DDQN.md`)  

Không cắt thêm. Việc người viết: dán P6.  

---

# Điểm yếu Pasini (đo được trong artifact)

Pasini sửa Chen đúng hướng. Các điểm dưới là chỗ luận văn được phép mạnh hơn. Mục **code** đã mở `artifact/Adversarial_RL_XSS` @ `a299bb6`.

## W1 — Oracle không chạy JavaScript (nặng nhất)

Oracle: FastAPI nhét payload vào Jinja `|safe` → BeautifulSoup parse → `zss.simple_distance` so với trang có payload `"abc"`.

```17:29:artifact/Adversarial_RL_XSS/src/utils/html_tools.py
def is_same_dom(html_1, html_2):
    distance = get_distance_between_htmls(html_1, html_2)
    return True if distance == 0 else False
```

```5:9:artifact/Adversarial_RL_XSS/src/utils/dataset_utils.py
def check_column_validity_with_oracle(df, column, endpoint):
    basic_payload = "abc"
    basic_html = do_xss_post_request(endpoint, basic_payload)
    return df[column].apply(lambda x: is_same_dom(do_xss_post_request(endpoint, x), basic_html))
```

Hệ quả:

- `<script>alert(1)</script>` = Malicious vì **thêm node**, không vì script chạy.
- `<div>hello</div>` cũng = Malicious (đổi cây).
- `fetch('//evil')` không đổi cây có thể = Benign.
- Validator trên server là DummyDetector **luôn True** — không sanitize.

Paper mục 8 tự nhận Oracle “may be subject to misclassification and depend on the specific templates”.

**Làm:** Oracle = JS runtime. DOM-diff chỉ tín hiệu phụ.

## W2 — RR(V) gần tautology

Code reconstruct token rồi mới gọi Oracle:

```115:126:artifact/Adversarial_RL_XSS/src/envs/detector_env.py
xss_df["tokenized"] = process_payloads(xss_df, self.common_tokens)[1]
xss_df['reconstructed'] = xss_df['tokenized'].map(lambda x: ' '.join(x))
valid = (check_column_validity_with_oracle(xss_df, 'reconstructed', self.endpoint))...
```

`None` join bằng space không còn HTML. RR(V) 93–98% một phần **đúng vì định nghĩa**. OR(V) mới sạch. Báo cáo Oracle trên **chuỗi thật** trước tokenize.

## W3 — Không phải replication trung thành

Khác Chen: Mereani vs 90k; PPO vs SAC; embedding 8 vs Word2Vec 32; sigmoid vs softmax; bỏ SafeDog/XSSChop; detector và agent **cùng dataset**.

Họ tuyên bố tái lập vì ER ~99% — đó là artifact TH2. LSTM hơn Chen 6.58 điểm bị bỏ qua.

Viết “conceptual / protocol replication”, có bảng khác biệt. Không viết “reproduced Chen’s numbers”.

## W4 — Table 4 trùng tuyệt đối

MLP = LSTM = CNN: Precision 99.67%, Recall 100%, Acc/F1 99.83%. Detector quá dễ hoặc lỗi báo cáo. ER cao không chứng minh tấn công mạnh. Đối tượng chính phải là CRS/DOMPurify (không dính OOV-`None`).

## W5 — MDP không nhìn payload

```45:45:artifact/Adversarial_RL_XSS/src/envs/detector_env.py
self.observation_space = Box(low=0, high=self.num_actions , shape=(self.max_steps,), dtype=np.int32)
```

State = lịch sử action, max 15 bước. Policy dễ học chuỗi tạo OOV. State luận văn phải có payload + sink.

## W6 — Paper ≠ code (reward) + leakage

Paper RQ3: reward **−2** nếu Oracle không còn XSS.  
Code: **−5**.

Cùng Oracle pre-filter data, tính RR, và làm reward. Dùng JSDOM cho train, Playwright cho test cuối.

## W7 — Dataset 2018

Mereani: `alert` / `<script>`. Không mXSS, DOM clobbering, SVG, framework sink. Undersample Benign → phân bố giả. Cùng distribution detector/agent → không transfer.

Mereani = tập A so paper. Tập B = context hiện đại. Đo A→B.

## W8 — Action paper liệt kê, code không làm đủ

| Mã | Paper | Code `mutators.py` |
|---|---|---|
| A1 | Add `&#14` *trước* `javascript` | `re.sub(..., ' &#14javascript')` — **thay cả match**, phá chuỗi |
| A18 | Unicode-encode JS | `return payload` — **no-op**, comment `TO REMOVE ?` |
| A20 | Replace `>` thẻ đơn bằng `<` | Chỉ thay `&gt;&lt;` → `&lt;` — **stub** |
| A21/A22/A27 | thay `alert` bằng biểu thức | `re.sub(r'alert', '...(1)')` trên `alert(1)` → `...(1)(1)` — **JS vỡ** |
| A2/A4 | mixed case | preprocess **`.lower()`** trước detector → mutation bị hủy |
| A8/A11/A19 | HTML entity | preprocess **`html.unescape`** → mutation bị hủy |
| A3/A26 | `%0A` `%00` | preprocess **`unquote_plus`** |
| A25 | `vbscript` | chết trên Chromium |

Nhiều action “giữ ngữ nghĩa XSS” **không bao giờ tới detector**. Agent thắng chủ yếu nhờ token sống sót thành OOV. Oracle BS4 vẫn cho Malicious vì còn thẻ.

Bảng `parser_alive` (BS4) vs `browser_alive` (Chrome) = evidence W1+W8.

## W9 — Thiếu thí nghiệm reviewer hỏi

Không transfer LSTM→CNN. Không adversarial training detector. Không so Fang/Wang/Zhang. 10 seed, không CI/Wilcoxon. Không histogram action. Bỏ detector thương mại.

Mục 9 tự mâu thuẫn: “preprocess phá payload vẫn là tấn công thành công” — nếu vậy TH2 không invalid Chen, chỉ đổi *loại* thành công.

## W10 — Presentation

Intro hứa section 7/8/10, có cả 6 và 9. Trang 29 gọi OOV là “TH3”. FastAPI title còn `"StreetView - API backend"`. README vẫn ghi “submitted to COSE” dù bài ra JSS. `bs4 = "^0.0.2"` là metapackage PyPI, không phải phiên bản BeautifulSoup — vẫn cẩu thả.

---

## Definition of done

- Artifact pin + bảng Chen/Pasini/mình
- Oracle execute lọc Mereani, RR gốc = 0
- 27/27 action có test + `parser_alive` / `browser_alive`
- Replication DL: ER, RR(E), OR(V), ≥3 seed
- Oracle-in-loop: TASR, Δ, histogram action
- Lab CRS: BLOCK / BYPASS_NOEXEC / BYPASS_EXEC
- Không dùng ER Chen 99% làm thành công của mình
- W1, W3, W4, W8 có số lab, không chỉ lập luận

Citation:

```
Pasini S., Maragliano G., Kim J., Tonella P. (2026).
Cross-site scripting adversarial attacks based on deep reinforcement learning:
Evaluation and extension study. Journal of Systems and Software.
DOI: 10.1016/j.jss.2026.112856. arXiv:2502.19095.
```
