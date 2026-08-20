#!/usr/bin/env bash
# =============================================================================
#  selftest.sh - acceptance test that runs against WHATEVER your .env points at
#  (the real cyberlab GPU + Wazuh, or the local offline stack). It exercises the
#  live services and every module's lab script, then prints a PASS/WARN/FAIL tally.
#
#  Run from the repo root:
#     bash scripts/selftest.sh
#
#  Optional:
#     SELFTEST_START_CORE=1 bash scripts/selftest.sh   # also start the AI SOC
#                                                       # assistant and test its API
#
#  Legend:  PASS = works    WARN = optional/unreachable (often fine)    FAIL = broken
#  This script never changes your config. It only reads .env and calls the services.
# =============================================================================
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PASS=0; WARN=0; FAIL=0
pass(){ echo "  [PASS] $1"; PASS=$((PASS+1)); }
warn(){ echo "  [WARN] $1"; WARN=$((WARN+1)); }
fail(){ echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }
sec(){ echo; echo "== $1 =========================================================="; }

# Load .env into the environment safely (no eval; values with special chars are fine).
if [ -f .env ]; then
  while IFS='=' read -r k v; do
    case "$k" in ''|\#*) continue;; esac
    export "$k=$v"
  done < .env
else
  warn ".env not found - using built-in defaults (real VM IPs). Copy .env.example to .env."
fi
PY=python3; command -v python3 >/dev/null || PY=python

AI_SOC_PORT="$(grep -E '^AI_SOC_PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]')"; AI_SOC_PORT="${AI_SOC_PORT:-8080}"
OLLAMA_OK=0

# ---------------------------------------------------------------------------
sec "1. Prerequisites"
if command -v "$PY" >/dev/null; then pass "Python present ($($PY --version 2>&1))"; else fail "Python 3 not found"; fi
if command -v docker >/dev/null; then pass "Docker present ($(docker --version | cut -d, -f1))"; else warn "Docker not found (only needed for the offline stack and Modules 2/4/5 containers)"; fi
if $PY -c "import dotenv" 2>/dev/null; then pass "python-dotenv installed (.env auto-loaded)"; else warn "python-dotenv missing - selftest exported .env for you, but install it: pip install -r common/requirements.txt"; fi

# ---------------------------------------------------------------------------
# Optionally start the offline core stack up front, so the Ollama and assistant
# checks below can use it (mock-ollama on host port MOCK_OLLAMA_PORT, default 11435).
if [ "${SELFTEST_START_CORE:-0}" = "1" ] && command -v docker >/dev/null; then
  echo; echo "  starting core stack (SELFTEST_START_CORE=1)..."
  bash scripts/lab_up.sh core >/dev/null 2>&1
  for _ in $(seq 1 30); do curl -sf "http://localhost:${AI_SOC_PORT}/health" >/dev/null 2>&1 && break; sleep 2; done
fi

# ---------------------------------------------------------------------------
sec "2. Ollama (the LLM)"
if $PY common/ollama_client.py --health >/tmp/st_ollama 2>&1; then
  pass "Ollama reachable: $(grep -o 'reachable at .*' /tmp/st_ollama | head -1)"
  OLLAMA_OK=1
  # live generation on a brute-force log -> expect a verdict word
  OUT=$(printf 'Failed password for admin from 10.10.10.5\nFailed password for admin from 10.10.10.5\nFailed password for root from 10.10.10.5' \
        | $PY common/ollama_client.py --stdin --system "You are a SOC analyst. Give SUMMARY, VERDICT (benign/suspicious/malicious), and one action." 2>/tmp/st_gen)
  if [ -n "$OUT" ]; then
    pass "Ollama generated a response ($(printf '%s' "$OUT" | wc -c | tr -d ' ') chars)"
    if printf '%s' "$OUT" | grep -qiE 'malicious|suspicious'; then
      pass "Model flagged the brute force (verdict: malicious/suspicious)"
    else
      warn "Model responded but did not clearly flag the brute force (real-model wording varies)"
    fi
  else
    fail "Ollama returned an empty response"
  fi
else
  warn "Ollama not reachable ($(tail -1 /tmp/st_ollama)). Real path: check VPN/GPU VM. Offline: scripts/lab_up.sh core + set OLLAMA_HOST=http://localhost:11435"
fi

# ---------------------------------------------------------------------------
sec "3. Wazuh (the SIEM)"
if $PY common/wazuh_client.py --health >/tmp/st_wz 2>&1; then
  pass "Wazuh manager reachable: $(cat /tmp/st_wz)"
  AGENTS=$($PY common/wazuh_client.py --agents 2>/dev/null | wc -l | tr -d ' ')
  pass "Wazuh agents query works ($AGENTS agent line(s) returned)"
  ALERTS=$($PY common/wazuh_client.py --alerts 5 2>/dev/null | wc -l | tr -d ' ')
  if [ "$ALERTS" -gt 0 ]; then pass "Recent alerts query works ($ALERTS returned)"; else warn "No recent alerts yet (normal on a fresh SIEM; generate some in Module 2)"; fi
else
  warn "Wazuh not reachable ($(tail -1 /tmp/st_wz)). Set WAZUH_PASS in .env, or use the offline dataset path (labs support it)."
fi

# ---------------------------------------------------------------------------
sec "4. Module lab scripts (offline-deterministic)"
# Note: these detectors exit non-zero when they FIND threats, so we check their
# output, not their exit code.
$PY module2-detection/labs/detect_bruteforce.py >/tmp/st_m2a 2>&1
if grep -q "10.10.10.5" /tmp/st_m2a && grep -qi "threat intel" /tmp/st_m2a; then
  pass "M2 detect_bruteforce.py flags 10.10.10.5 and correlates threat intel"
else
  fail "M2 detect_bruteforce.py did not produce the expected finding (see /tmp/st_m2a)"
fi
$PY module2-detection/labs/detect_web_attacks.py >/tmp/st_m2b 2>&1
if grep -q "10.10.10.7" /tmp/st_m2b; then
  pass "M2 detect_web_attacks.py flags the SQLi scanner 10.10.10.7"
else
  fail "M2 detect_web_attacks.py did not flag 10.10.10.7 (see /tmp/st_m2b)"
fi
# Capstone auto-grader on a temporary passing report
TMPR="$(mktemp -t capstone_report.XXXXXX).md"
cat > "$TMPR" <<'RPT'
# Incident Report
## Executive Summary
Multi-stage intrusion: brute force from 10.10.10.5 and SQL injection from 10.10.10.7.
A prompt injection / poisoned log entry was identified and not acted on.
## Timeline
03:11 brute force 10.10.10.5 (successful admin login). 03:20 SQLi 10.10.10.7.
## Technical Details
Sources 10.10.10.5 and 10.10.10.7; poisoned entry attempted prompt injection.
## Impact
The admin account from 10.10.10.5 is compromised.
## Recommendations
Block 10.10.10.5 and 10.10.10.7; treat AI output as untrusted when logs carry a prompt injection.
RPT
if $PY module5-capstone/labs/capstone_check.py "$TMPR" 2>/tmp/st_m5 | grep -q "RESULT: PASS"; then
  pass "M5 capstone_check.py scores a model report as PASS"
else
  fail "M5 capstone_check.py did not pass a model report (see /tmp/st_m5)"
fi
rm -f "$TMPR"

# ---------------------------------------------------------------------------
sec "5. Module lab scripts (need Ollama)"
if [ "$OLLAMA_OK" = "1" ]; then
  $PY module1-foundations/labs/first_ai_triage.py >/tmp/st_m1 2>&1
  if grep -qiE 'verdict|malicious|suspicious|benign' /tmp/st_m1; then
    pass "M1 first_ai_triage.py produced an AI verdict on auth.log"
  else
    fail "M1 first_ai_triage.py did not produce a verdict (see /tmp/st_m1)"
  fi
  $PY module3-prompt-engineering/labs/triage_workflow.py >/tmp/st_m3 2>&1
  if grep -qiE 'TRIAGE|VERDICT|SEVERITY' /tmp/st_m3; then
    pass "M3 triage_workflow.py produced a triage table"
  else
    warn "M3 triage_workflow.py did not render a table (see /tmp/st_m3)"
  fi
else
  warn "Skipped M1/M3 AI labs because Ollama was not reachable above"
fi

# ---------------------------------------------------------------------------
sec "6. AI SOC assistant API (Module 4 target)"
if curl -sf "http://localhost:${AI_SOC_PORT}/health" >/tmp/st_soc 2>&1; then
  pass "Assistant reachable at http://localhost:${AI_SOC_PORT} ($(cat /tmp/st_soc))"
  R=$(curl -sf -X POST "http://localhost:${AI_SOC_PORT}/api/triage" -H 'Content-Type: application/json' \
        -d '{"mode":"vulnerable","log":"Failed password for admin from 10.10.10.5\nFailed password for admin\nFailed password for root"}')
  if printf '%s' "$R" | grep -qiE 'malicious|suspicious|benign'; then
    pass "Assistant /api/triage returned a verdict"
  else
    fail "Assistant /api/triage did not return a verdict"
  fi
  echo "  note: for the deterministic prompt-injection attack/defense proof, run: bash scripts/smoke_test.sh"
else
  warn "Assistant not running. Start it with: scripts/lab_up.sh core   (or re-run: SELFTEST_START_CORE=1 bash scripts/selftest.sh)"
fi

# ---------------------------------------------------------------------------
echo
echo "============================================================"
echo "  SELFTEST SUMMARY:  PASS=$PASS  WARN=$WARN  FAIL=$FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo "  RESULT: OK - everything reachable passed. WARN items are optional."
else
  echo "  RESULT: $FAIL check(s) failed - see the /tmp/st_* files noted above."
fi
echo "============================================================"
[ "$FAIL" -eq 0 ]
