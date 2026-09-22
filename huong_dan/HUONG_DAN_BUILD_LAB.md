# Hướng dẫn build lab từ máy trống

Ngày: 2026-09-17  
Repo: `/home/kali/Desktop/ATBMHTTT`  
Đọc trước: `README.md` (mục lục) → `PLAN_LAM_THEO_PASINI.md` (khung) → file này khi **cài máy**.  
Sổ tay số + câu viết: `HUONG_DAN_CHI_TIET.md`.

Mục tiêu: dựng **đúng** lab luận văn (nhánh B) và tùy chọn nhánh A (artifact Pasini). Mọi lệnh dưới đây đã chạy được trên Kali Linux, Python 3.13, Node 24, Docker 28.

Sau mỗi bước có **kỳ vọng**. Sai kỳ vọng thì dừng, đừng train PPO.

**Không** copy Escape Rate 99% của Chen. Lab bám khung Pasini: payload đối kháng phải còn độc theo oracle thực thi.

Hai nhánh **không trộn số**:

| | Nhánh B — luận văn (lab/) | Nhánh A — sát paper (artifact/) |
|---|---|---|
| Dataset | Mereani lọc JSDOM | `data/10` của Pasini |
| Encode | token-id cố định | `LabelEncoder` từng mẫu |
| Oracle | JSDOM + Playwright | FastAPI + BeautifulSoup + zss |
| ER PPO điển hình | ~0.75% | ~99% |
| CRS | có | không |

---

## 0. Máy cần gì

| Thành phần | Tối thiểu | Đã kiểm trên máy này |
|---|---|---|
| OS | Linux (Kali/Ubuntu 22.04+) | Kali |
| RAM | 8 GB (Docker + PPO) | — |
| Disk | ~8 GB (node_modules, torch, CRS image) | — |
| CPU | 4 luồng; **không cần GPU** | CPU-only |
| Python | 3.11–3.13 | 3.13 + venv |
| Node.js | ≥ 20 | v24.18.0 |
| npm | đi kèm Node | — |
| Docker | 24+ + plugin compose | 28.5.2 |
| Git | clone artifact | — |

Cổng **chỉ bind 127.0.0.1** — không mở WAN:

| Cổng | Dịch vụ |
|---:|---|
| 13000 | xss-lab-app (Express + 3 sink + DOMPurify) |
| 18080 | CRS paranoia 1 |
| 18081 | CRS paranoia 2 |
| 5555 | Oracle FastAPI Pasini (chỉ khi chạy nhánh A) |

Nếu cổng bận: `ss -ltn | grep -E '13000|18080|18081|5555'`.

---

## 1. Lấy source

```bash
# Nếu đã có repo:
cd /home/kali/Desktop/ATBMHTTT

# Cây tối thiểu
ls lab/docker-compose.yml lab/src/run_p3.py lab/data/Payloads.csv
ls artifact/Adversarial_RL_XSS/data/10/detectors/train.csv
```

Artifact Pasini (pin commit paper):

```bash
mkdir -p artifact
git clone https://github.com/GianlucaMaragliano/Adversarial_RL_XSS.git artifact/Adversarial_RL_XSS
git -C artifact/Adversarial_RL_XSS checkout a299bb6
```

Dataset Mereani đã nằm tại `lab/data/Payloads.csv` (cột `Payloads,Class`, encoding **latin-1**). Không cần tải FigShare nếu `artifact/.../data/10/` đã có 7 file CSV.

---

## 2. Python venv (root repo)

```bash
cd /home/kali/Desktop/ATBMHTTT
python3 -m venv .venv
source .venv/bin/activate   # fish: source .venv/bin/activate.fish

pip install -U pip
pip install -r lab/requirements.txt
# torch CPU đủ. Không cài CUDA.
```

`lab/requirements.txt`:

- `beautifulsoup4`, `pandas`, `lxml`
- `torch>=2.2`
- `stable-baselines3>=2.3`
- `gymnasium>=1.0`

Khuyến nghị thêm (P4/P5, Wilcoxon, artifact):

```bash
pip install scipy scikit-learn nltk validators zss fastapi uvicorn \
  jinja2 python-dotenv pydantic-settings requests markupsafe
```

Kiểm:

```bash
.venv/bin/python -c "import torch, pandas, gymnasium, stable_baselines3; print('py_ok', torch.__version__)"
```

Mọi lệnh Python trong file này dùng **`.venv/bin/python`**, không dùng `python` hệ thống.

---

## 3. Node — JSDOM oracle + Playwright

Oracle train **không** phải BeautifulSoup. `lab/src/oracle.py` spawn `node lab/oracle/jsdom_oracle.mjs`.

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
npm install
# playwright là devDependency
npx playwright install chromium
npx playwright install-deps chromium   # nếu thiếu lib hệ thống
```

`package.json` lab: `jsdom`, `playwright`.  
App Docker tự `npm install` `express` + `dompurify` + `jsdom` — **không** trộn với `lab/node_modules`.

Smoke oracle (phải `executed: true` / `false` đúng 4 dòng):

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
node oracle/jsdom_oracle.mjs --payload '<script>alert(1)</script>'
node oracle/jsdom_oracle.mjs --payload '<img src=x onerror=alert(1)>'
node oracle/jsdom_oracle.mjs --payload '<a href="javascript:alert(1)">x</a>'
node oracle/jsdom_oracle.mjs --payload '<div>hello</div>'
```

Kỳ vọng: 3 payload đầu `"executed":true`, `<div>` `"executed":false`.

Playwright hold-out:

```bash
printf '%s\n' \
  '{"payload":"<script>alert(1)</script>"}' \
  '{"payload":"<div>hello</div>"}' \
  | node oracle/pw_check.mjs
```

Kỳ vọng JSONL `executed: true` rồi `false`. Lỗi `playwright_not_installed` → thiếu `npm install` / chưa `npx playwright install chromium`.

---

## 4. Unit test (không cần Docker)

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
../.venv/bin/python -m unittest tests.test_oracle tests.test_actions -v
```

Phải xanh:

- `test_oracle`: script/img/`javascript:` execute; `<div>hello</div>` **parser đổi nhưng không execute** (W1).
- `test_actions`: 27 action, A18 không no-op, A21 không thành `(1)(1)`.

Fail `node: not found` → cài Node, `PATH` có `node`.  
Fail `Cannot find module 'jsdom'` → `cd lab && npm install`.

---

## 5. P1 — Lọc Mereani (gate RR = 0)

Mặc định đọc `lab/data/Payloads.csv`. Chạy **toàn bộ** ~15k độc + 28k lành qua JSDOM: **15–40 phút**.

Smoke 200 dòng trước (không ghi đè file thật nếu đổi `--output`):

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
../.venv/bin/python src/filter_mereani.py --limit 200 \
  --output /tmp/mereani_smoke.csv --report /tmp/filter_smoke.json
cat /tmp/filter_smoke.json
```

Full (đúng số luận văn):

```bash
../.venv/bin/python src/filter_mereani.py
# → data/mereani_exec_oracle.csv
# → data/filter_report.json
```

Gate: `rr_malicious_kept` **phải = 0**. Số máy này:

| | n |
|---|---:|
| Mereani gốc | 43217 (15149 độc / 28068 lành) |
| Độc execute, giữ | 10824 |
| Độc chỉ đổi DOM, loại (W1) | 3542 (23.4%) |
| RR trên tập giữ | **0.0** |

Nếu file lọc đã có và `filter_report.json` khớp, **bỏ qua** bước này.

---

## 6. Split kiểu Table 3 + P2 action

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
../.venv/bin/python src/split_table3.py
# seed 42; detector undersample Benign = số Malicious detector
# → data/splits/detectors/{train,val,test}.csv
# → data/splits/adversarial_agents/{train,val,test}.csv
# → data/splits/split_report.json

../.venv/bin/python src/action_alive.py
# → data/action_alive.csv
```

Agent split **chỉ Malicious**. Không đưa Benign vào PPO.

---

## 7. Docker — app + CRS PL1/PL2

Image: `owasp/modsecurity-crs:nginx-alpine` (kéo lần đầu ~ vài trăm MB). App build từ `lab/app/Dockerfile` (node:20-alpine).

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
docker compose up -d --build
docker compose ps
```

Health:

```bash
curl -sS http://127.0.0.1:13000/health
# {"ok":true,"service":"xss-lab-app", ...}

curl -sS -o /dev/null -w '%{http_code}\n' \
  'http://127.0.0.1:13000/html?q=%3Cscript%3Ealert(1)%3C/script%3E'
# 200 — app phản xạ, không WAF

curl -sS -o /dev/null -w '%{http_code}\n' \
  'http://127.0.0.1:18080/html?q=%3Cscript%3Ealert(1)%3C/script%3E'
# 403 — CRS PL1 chặn

curl -sS -o /dev/null -w '%{http_code}\n' \
  'http://127.0.0.1:18080/html?q=hello'
# 200

curl -sS -o /dev/null -w '%{http_code}\n' \
  'http://127.0.0.1:18081/html?q=%3Cscript%3Ealert(1)%3C/script%3E'
# 403 — CRS PL2
```

Unit stack:

```bash
../.venv/bin/python -m unittest tests.test_crs_stack -v
```

`SkipTest: CRS stack down` → `docker compose logs crs-pl1 --tail 50`. Thường do image chưa kéo xong hoặc `app` chưa healthy.

Tắt:

```bash
docker compose down
```

**Không** publish `0.0.0.0`. Compose đã ghim `127.0.0.1`.

Ba sink app: `/html?q=`, `/attr?q=`, `/js?q=`. Bản purify: `/purify/html`, `/purify/attr`, `/purify/js`.

---

## 8. P5 — đo TASR (cần Docker đang lên)

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
../.venv/bin/python src/measure_tasr.py --sink /html
# 3 seed × 27 action = 84 payload × 4 target (pl1, pl2, app, purify)

../.venv/bin/python src/measure_tasr.py --sink /html --pairs --only pl1
# chuỗi 2 action, chỉ PL1

../.venv/bin/python src/complete_p5.py --bases 40 --transfer-n 80
# bộ ba + Mereani decode + transfer PPO (cần checkpoint P3/P4 nếu đo transfer)
```

Nhãn: `BLOCK` (403) | `BYPASS_NOEXEC` (200, JS chết) | `BYPASS_EXEC` (200 **và** execute).

**TASR = #BYPASS_EXEC / N.** HTTP 200 một mình **không** phải thành công.

Kỳ vọng lab này: CRS PL1/PL2 TASR = **0** trên Table 2. App TASR ~0.845. DOMPurify TASR = 0, Δ = 1.

Gate `BYPASS_EXEC` trên PL1 **không đạt** → **cấm train RL trên CRS**, cấm LLM sinh payload.

---

## 9. P3 — LSTM + PPO (nhánh B, chưa Oracle trong reward)

Cần `data/splits/` từ bước 6.

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
../.venv/bin/python src/run_p3.py --phase vocab
../.venv/bin/python src/run_p3.py --phase detector
../.venv/bin/python src/run_p3.py --phase ppo --timesteps 20000 --ppo-seeds 42,43,44
../.venv/bin/python src/run_p3.py --phase eval --ppo-seeds 42,43,44 --max-eval 400
```

Hoặc một phát: `--phase all`.

Checkpoint: `lab/runs/p3/lstm.pt`, `vocab.json`, `ppo_seed*.zip`.  
Số máy này: LSTM acc **0.991**; PPO ER tb **0.75%** (không phải 99%).

Lệch paper đã ghi: **Adam** (SGD kẹt 50% trên split JSDOM), pad 40.

---

## 10. P4 — Oracle-in-loop + Dueling DQN

Cần `runs/p3/lstm.pt`.

```bash
cd /home/kali/Desktop/ATBMHTTT/lab
../.venv/bin/python src/run_p4.py --phase all --algo ppo --seeds 42,43,44 --timesteps 20000 --max-eval 400
../.venv/bin/python src/run_p4.py --phase train --algo dqn --seeds 42 --timesteps 20000
../.venv/bin/python src/run_p4.py --phase eval --algo ppo,dqn --seeds 42,43,44 --max-eval 400
../.venv/bin/python src/train_ddqn.py --phase all --seeds 42,43,44 --timesteps 20000 --max-eval 400
```

Reward `R_exec`: −2 hết độc; +10 **chỉ** khi detector lọt **và** JSDOM execute.

Kỳ vọng: PPO ER = TASR = **0.25%** (sàn FN); Dueling DQN tb **1.08%**; RR(E)=0.  
Bảng: `lab/data/PPO_VS_DDQN.md`.

---

## 11. Nhánh A — sát artifact Pasini (tùy chọn)

Chỉ khi muốn tái lập ER ~99% trên **đúng** `data/10`. Không thay số nhánh B.

### 11.1 Dependency thêm + Oracle FastAPI

```bash
cd /home/kali/Desktop/ATBMHTTT
.venv/bin/pip install nltk scikit-learn validators zss fastapi uvicorn \
  jinja2 python-dotenv pydantic-settings requests

# Oracle DOM (cổng 5555)
cd artifact/Adversarial_RL_XSS
../../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 5555
```

Để chạy nền: thêm `&` hoặc dùng `bash lab/src/run_pasini_faithful.sh oracle-up`.

**Không** `--reload` (sinh process con). Tắt: `pkill -f 'uvicorn app.main'`.

Smoke (cần Oracle sống):

```bash
cd /home/kali/Desktop/ATBMHTTT/artifact/Adversarial_RL_XSS
../../.venv/bin/python - <<'PY'
import sys
sys.path.insert(0, "src")
from utils.request_tools import do_xss_post_request
from utils.html_tools import is_same_dom
ep = "http://127.0.0.1:5555/vuln_backend/1.0/endpoint/"
abc = do_xss_post_request(ep, "abc")
print("div_malicious", not is_same_dom(do_xss_post_request(ep, "<div>hello</div>"), abc))
print("script_malicious", not is_same_dom(do_xss_post_request(ep, "<script>alert(1)</script>"), abc))
PY
```

Cả hai phải `True` (`<div>` là “độc” theo Oracle DOM — đúng paper, khác JSDOM).

### 11.2 Detector 3 mạng (nhanh, ~3 phút)

```bash
cd /home/kali/Desktop/ATBMHTTT
bash lab/src/run_pasini_faithful.sh detectors
```

Kỳ vọng test_results: P 99.67 / R 100 / Acc 99.83 — trùng Table 4, cả 3 mạng một bộ số.

### 11.3 PPO — **đừng** 250k + eval 721 lần đầu

Paper mặc định 250000 bước và `n_eval_episodes = len(val) = 721` → ~25 phút/mạng, RQ3 Oracle ~70 phút (HTTP mỗi bước).

Val reward đã plateau từ **50k**. Dùng fast:

```bash
bash lab/src/run_pasini_faithful.sh ppo-lstm-fast          # ~3–6 phút
bash lab/src/run_pasini_faithful.sh eval-lstm \
  artifact/Adversarial_RL_XSS/runs/lstm/10/run_0/adversarial_agent_fast/run_0/best_model.zip

bash lab/src/run_pasini_faithful.sh ppo-lstm-oracle-fast   # RQ3, Oracle phải sống
```

Số đã chạy **y chang 250k** (seed 42) nằm ở `lab/data/PASINI_FAITHFUL_RESULTS.md`: LSTM ER 98.78%, RQ3 98.34%, RR=0.

Chạy từ thư mục artifact nếu gọi `python src/...` trực tiếp: `mutators.py` đọc `data/10/detectors/train.csv` **theo CWD**.

---

## 12. Checklist “lab sống”

Chạy lần lượt; ô nào fail thì dừng, đừng train PPO.

```text
[ ] .venv import torch, pandas, gymnasium
[ ] node oracle: script execute, div không
[ ] unittest test_oracle + test_actions xanh
[ ] filter_report.json rr_malicious_kept = 0  (hoặc file lọc đã có)
[ ] data/splits/detectors/train.csv tồn tại
[ ] docker compose ps: app, crs-pl1, crs-pl2 Up
[ ] curl app script → 200; curl PL1 script → 403; curl PL1 hello → 200
[ ] unittest test_crs_stack xanh
[ ] (nhánh B) runs/p3/lstm.pt
[ ] (nhánh A, tùy chọn) uvicorn :5555 + Table 4
```

---

## 13. Cây thư mục sau khi build

```
ATBMHTTT/
  .venv/
  lab/
    app/                 # Express 3 sink + DOMPurify (Docker)
    docker-compose.yml
    oracle/              # jsdom_oracle.mjs, eval_xss.mjs, pw_check.mjs
    src/                 # filter, split, actions, run_p3, run_p4, tasr
    tests/
    data/
      Payloads.csv
      mereani_exec_oracle.csv
      splits/
      P1_P2_RESULTS.md … P5_RESULTS.md
    runs/p3/  runs/p4/
    node_modules/        # jsdom + playwright
  artifact/Adversarial_RL_XSS/   # pin a299bb6
    data/10/             # split paper
    runs/{lstm,mlp,cnn}/
  huong_dan/
    HUONG_DAN_BUILD_LAB.md   ← file này
    2026-09-17_luan-van-P6.md
```

---

## 14. Lỗi thường gặp

| Triệu chứng | Nguyên nhân | Sửa |
|---|---|---|
| `jsdom` missing | quên `npm install` trong `lab/` | `cd lab && npm install` |
| Oracle timeout / stderr đầy | process JSDOM treo | `JsdomOracle` tự recycle 800 lời gọi; xem `data/jsdom_oracle.stderr.log` |
| `latin-1` UnicodeDecodeError | đọc Payloads bằng utf-8 | script đã `encoding="latin-1"` |
| CRS `SkipTest` | compose chưa healthy | `docker compose logs -f app` |
| PL1 trả 200 cho `<script>` | sai cổng / backend không qua CRS | đúng `18080`, không gọi `13000` khi đo WAF |
| PPO ER ~99% trên lab JSDOM | nhầm nhánh A encode | nhánh B phải `runs/p3/vocab.json` id cố định |
| PPO ER ~1% rồi viết “replication 99%” | trộn hai nhánh | xem P6 |
| `nn.Embedding(..., 8.0)` TypeError | PyTorch 2.14 | artifact đã `int(embedding_dim)` |
| FastAPI 500 TemplateResponse | Starlette 1.x | `payload_service.py` đã shim |
| `mutators` FileNotFoundError | CWD không phải artifact root | `cd artifact/Adversarial_RL_XSS` |
| PPO “lâu quá” | 250k + eval 721 | dùng `ppo-lstm-fast` |
| GPU OOM | không dùng GPU | PPO `device="cpu"` |

---

## 15. Cấm

- Bind CRS/app ra ngoài localhost.
- Train RL trên CRS khi TASR PL1 = 0.
- LLM generator payload.
- Gọi HTTP 200 là TASR.
- Đánh AWS WAF / WAF cloud.
- Import `artifact/.../mutators.py` vào train nhánh B.
- Đổi `data/10` bằng `prepare_dataset.py` (mất split paper).

---

## 16. Thời gian tham chiếu (máy CPU)

| Bước | Thời gian |
|---|---|
| venv + pip + npm + playwright | 10–20 phút (mạng) |
| unittest oracle/actions | < 1 phút |
| `filter_mereani.py` full | 15–40 phút |
| `docker compose up --build` lần đầu | 5–15 phút (kéo image) |
| P3 detector | ~2 phút |
| P3 PPO 3 seed × 20k | ~10–20 phút |
| P4 PPO 3 seed | ~10–20 phút |
| P5 `measure_tasr` 84 payload | vài phút |
| Nhánh A 3 detector | ~3 phút |
| Nhánh A PPO fast 50k | ~5 phút; Oracle fast ~8–15 phút |
| Nhánh A PPO **paper** 250k | **đừng**, trừ khi cần số y chang |

---

## 16b. Kỳ vọng số — nếu lab đã build đúng

Đừng panic nếu khác 1–2 mẫu; panic nếu ER nhánh B ~99% hoặc CRS PL1 TASR > 0 trên Table 2 mà không ghi nhận.

| Sau bước | Kỳ vọng |
|---|---|
| unittest oracle | `<div>hello</div>` **không** execute; `<script>alert(1)` execute |
| `filter_report.json` | `rr_malicious_kept = 0`, W1 ≈ 23% |
| curl PL1 `<script>` | **403** |
| curl app `<script>` | **200** |
| P3 PPO 3×20k | ER tb **< 5%** (máy này 0.75%) |
| P4 PPO Oracle | ER ≈ sàn FN (máy này 0.25%) |
| P5 PL1 Table 2 | TASR **0** |
| Nhánh A Table 4 | P 99.67 R 100 Acc 99.83 |
| Nhánh A LSTM PPO | ER **~99%** |

## 17. Tài liệu đi kèm

| File | Nội dung |
|---|---|
| `lab/README.md` | Lệnh ngắn + số đã đo |
| `lab/data/P1_P2_RESULTS.md` … `P5_RESULTS.md` | Số từng pha |
| `lab/data/PASINI_FAITHFUL_RESULTS.md` | Nhánh A Table 4 / ER / RQ3 |
| `lab/data/PPO_VS_DDQN.md` | PPO vs Dueling DQN |
| `huong_dan/README.md` | Mục lục 4 file — đọc cái này trước |
| `huong_dan/2026-09-17_luan-van-P6.md` | Chương luận văn |
| `huong_dan/PLAN_LAM_THEO_PASINI.md` | Plan + câu được/cấm |
