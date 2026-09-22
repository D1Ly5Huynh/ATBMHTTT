#!/usr/bin/env bash
# Quay video demo. Khong train. Can Docker CRS dang up.
#   bash lab/src/demo_record.sh          # dung Enter giua cac shot
#   bash lab/src/demo_record.sh --auto   # chay het, nghi 2s
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LAB="$ROOT/lab"
PY="$ROOT/.venv/bin/python"
export PYTHONWARNINGS=ignore
cd "$LAB"
AUTO=0
[[ "${1:-}" == "--auto" ]] && AUTO=1

pause() {
  echo
  if [[ "$AUTO" == 1 ]]; then sleep 2; else read -r -p ">> Enter de shot tiep... "; fi
}

banner() {
  echo
  echo "============================================================"
  echo "  SHOT $1 — $2"
  echo "============================================================"
}

banner 0 "Kiem tra stack (khong noi, cat bot neu muon)"
docker compose ps
curl -sS http://127.0.0.1:13000/health; echo
pause

banner 1 "Oracle JSDOM: script chay, div KHONG chay (W1)"
echo "--- <script>alert(1)</script> ---"
node oracle/jsdom_oracle.mjs --payload '<script>alert(1)</script>'
echo
echo "--- <div>hello</div>  (Pasini DOM-oracle se goi la doc) ---"
node oracle/jsdom_oracle.mjs --payload '<div>hello</div>'
pause

banner 2 "Unit test oracle + 27 action"
"$PY" -m unittest tests.test_oracle tests.test_actions -v
pause

banner 3 "W1 so loc Mereani (file da chay, khong loc lai 40 phut)"
"$PY" - <<'PY'
import json
from pathlib import Path
d=json.loads(Path("data/filter_report.json").read_text())
for k in ("malicious_in","malicious_exec","malicious_parser_only","rr_malicious_kept"):
    print(f"{k:24} {d.get(k)}")
print("W1 parser-only % =", round(100*d["malicious_parser_only"]/d["malicious_in"], 1))
PY
pause

banner 4 "CRS: app 200, PL1 chan script 403, hello 200"
set +e
curl -sS -o /dev/null -w 'app  /html?q=<script>     HTTP %{http_code}\n' \
  'http://127.0.0.1:13000/html?q=%3Cscript%3Ealert(1)%3C/script%3E'
curl -sS -o /dev/null -w 'PL1  /html?q=<script>     HTTP %{http_code}\n' \
  'http://127.0.0.1:18080/html?q=%3Cscript%3Ealert(1)%3C/script%3E'
curl -sS -o /dev/null -w 'PL1  /html?q=hello        HTTP %{http_code}\n' \
  'http://127.0.0.1:18080/html?q=hello'
curl -sS -o /dev/null -w 'PL2  /html?q=<script>     HTTP %{http_code}\n' \
  'http://127.0.0.1:18081/html?q=%3Cscript%3Ealert(1)%3C/script%3E'
set -e
pause

banner 5 "TASR 1 payload: 200 khong du, phai execute"
"$PY" - <<'PY'
import sys
sys.path.insert(0, "src")
from crs_client import APP, CRS_PL1, fetch
from oracle import evaluate_one

p = "<script>alert(1)</script>"
ex = evaluate_one(p).browser_alive
print(f"payload: {p}")
print(f"JSDOM executed: {ex}")
for name, base in (("app", APP), ("CRS_PL1", CRS_PL1)):
    h = fetch(base, "/html", p)
    if h.blocked:
        label = "BLOCK"
    elif h.ok and ex:
        label = "BYPASS_EXEC"
    elif h.ok:
        label = "BYPASS_NOEXEC"
    else:
        label = f"HTTP_{h.status}"
    print(f"  {name:8} HTTP {h.status}  -> {label}")
print("TASR = 1 chi khi HTTP 200 VA executed. PL1 o day = BLOCK, TASR=0.")
PY
pause

banner 6 "DOMPurify: HTTP 200 nhung het doc (Delta = 1)"
"$PY" - <<'PY'
import sys
sys.path.insert(0, "src")
from crs_client import APP, fetch
from oracle import evaluate_one
p="<script>alert(1)</script>"
raw=fetch(APP,"/html",p)
pur=fetch(APP,"/purify/html",p)
print("app /html        HTTP", raw.status, "JSDOM executed", evaluate_one(p).browser_alive)
print("app /purify/html HTTP", pur.status)
print("body purify (rut gon):", (pur.body or "")[:180].replace("\n"," "))
print("Delta = Escape - TASR = 1.00 tren catalog lab (HTTP lot, JS chet).")
PY
pause

banner 7 "Nhanh A vs nhanh B — so da do (khong train)"
"$PY" - <<'PY'
import json
from pathlib import Path
print("NHANH A  artifact data/10  LabelEncoder  Oracle DOM")
print("  Table 4  P/R/Acc = 99.67 / 100 / 99.83  (3 mang trung)")
a=json.loads(Path("../artifact/Adversarial_RL_XSS/runs/lstm/10/run_0/adversarial_agent/run_0/results.json").read_text())
b=json.loads(Path("../artifact/Adversarial_RL_XSS/runs/lstm/10/run_0/adversarial_agent_oracle/run_0/results.json").read_text())
print(f"  LSTM PPO ER        {a['escape_rate']*100:.2f}%   (paper 98.62%)")
print(f"  LSTM RQ3 ER        {b['escape_rate']*100:.2f}%   (paper 98.13%)")
print()
print("NHANH B  lab JSDOM  token-id co dinh")
p3=json.loads(Path("runs/p3/p3_eval.json").read_text())
print(f"  LSTM acc           {p3['lstm_test']['acc']:.3f}")
print(f"  P3 PPO ER tb 3 seed {p3['er_mean_20k_three_seeds']*100:.2f}%")
p4=json.loads(Path("runs/p4/p4_eval.json").read_text())
print("  P4 PPO TASR        0.25%  (san FN, 3 seed)")
print("  P4 Dueling DQN tb  1.08%")
print("  CRS PL1 TASR       0")
print()
print("Cung 27 action. Khac encode + oracle -> 99% vs ~1%.")
PY
pause

banner 8 "Playwright hold-out (Chromium, 2 payload)"
set +e
printf '%s\n' '{"payload":"<script>alert(1)</script>"}' '{"payload":"<div>hello</div>"}' \
  | node oracle/pw_check.mjs
pw_rc=$?
set -e
if [[ "$pw_rc" -ne 0 ]]; then
  echo "SHOT 8 skip: Chromium Playwright chua cai. JSDOM (shot 1) van la oracle train."
  echo "  cd lab && npx playwright install chromium"
  echo "  hoac: export PW_CHROME=/usr/bin/chromium"
fi
echo
echo "=== HET DEMO. Khong quay train PPO / 10 seed / filter_mereani full. ==="
