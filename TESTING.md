# Testing and Acceptance Guide

Use this to prove the whole package works before you release it to the cohort. There
are two layers:

1. **Automated** - two scripts that check most things in one shot.
2. **Manual acceptance** - a per-module checklist, including the Wazuh dashboard steps
   a script cannot verify for you.

Run everything from the repo root: `cd /Users/drbae/BASE/evolve`.

---

## 1. Automated tests

### A. Offline pipeline proof (no GPU, no VPN) - always run this first
```bash
bash scripts/smoke_test.sh
```
**Pass criteria:** `ALL SMOKE TESTS PASSED` with 4/4 - normal brute force is flagged
malicious, prompt injection flips the verdict in vulnerable mode, and the hardened mode
holds. This uses the deterministic mock, so it must pass on any machine.

### B. Live acceptance test against your .env (real cyberlab or offline)
```bash
bash scripts/selftest.sh
# to also start and test the assistant API automatically:
SELFTEST_START_CORE=1 bash scripts/selftest.sh
```
It reads your `.env` and exercises the live Ollama, live Wazuh, every module lab script,
and the assistant API, then prints `PASS / WARN / FAIL`. **Pass criteria:** `FAIL=0`.
`WARN` is fine (it marks optional or unreachable pieces, for example Wazuh on the offline
path). It never changes your config.

---

## 2. Environment checks

| Test | Command | Pass criteria |
|------|---------|---------------|
| Config present | `test -f .env && echo ok` | prints `ok` (else `cp .env.example .env`) |
| Both services | `python3 scripts/verify_env.py` | `PASS` for Ollama and Wazuh |
| Ollama only | `python3 common/ollama_client.py --health` | lists `llama3.1:8b` |
| Ollama generate | `python3 common/ollama_client.py "Say the single word: pong"` | non-empty reply |
| Wazuh only | `python3 common/wazuh_client.py --health` | `manager 4.14.x reachable` |
| Wazuh agents | `python3 common/wazuh_client.py --agents` | lists your enrolled agents |
| Custom rules loaded | on the manager: `/var/ossec/bin/wazuh-logtest` then paste an SSH failed-password line | fires rule 5710/5716 (and 100120 after a burst) |

---

## 3. Module-by-module acceptance

### Module 1 - Foundations
| Check | Command | Expected |
|-------|---------|----------|
| Env check | `python3 scripts/verify_env.py` | both PASS |
| AI log triage | `python3 module1-foundations/labs/first_ai_triage.py` | a verdict block; a brute force reads as malicious/suspicious |
| Wazuh pull | `python3 common/wazuh_client.py --alerts 10` | recent alerts print (or none on a fresh SIEM) |

### Module 2 - Detection  (real telemetry)
```bash
scripts/lab_up.sh core targets attack        # start victims + attacker
docker exec -it soclab-attacker-1 bash        # jump into the attacker box
# inside the attacker container:
/opt/attacks/attack_ssh_bruteforce.sh victim-ssh labuser
/opt/attacks/attack_web_sqli.sh victim-web 8081
/opt/attacks/attack_web_bruteforce.sh victim-web 8081 admin
exit
```
| Check | How | Expected |
|-------|-----|----------|
| Victim web logs | `docker logs soclab-victim-web-1 \| tail` | repeated `Failed password for admin`, and the SQLi strings |
| SQLi bypass works | the sqli script output | injection returns HTTP 200 while the wrong password returns 401 |
| Detector (offline) | `python3 module2-detection/labs/detect_bruteforce.py` | flags 10.10.10.5, threat-intel match, and the hidden successful login |
| Web detector | `python3 module2-detection/labs/detect_web_attacks.py` | flags SQLi and traversal from 10.10.10.7 |
| **Wazuh (real path)** | Wazuh dashboard -> Security events, filter last 15 min | SSH brute-force alerts (5710/5712), burst rule 100120, SQLi rule 100101 |
| Wazuh via API | `python3 common/wazuh_client.py --alerts 20 --min-level 5` | the attack alerts appear |

### Module 3 - Prompt Engineering
| Check | Command | Expected |
|-------|---------|----------|
| Sigma generation | `python3 module3-prompt-engineering/labs/gen_sigma.py "10+ failed SSH logins from one IP in 60s then a success"` | valid-looking Sigma YAML |
| Triage workflow | `python3 module3-prompt-engineering/labs/triage_workflow.py` | a ranked table (TITLE / SEVERITY / VERDICT / NEXT_STEP); falls back to sample alerts if Wazuh is down |

### Module 4 - AI Red Teaming
```bash
scripts/lab_up.sh core        # assistant at http://localhost:8080
```
| Check | Command | Expected |
|-------|---------|----------|
| List payloads | `python3 module4-red-teaming/labs/inject.py --list` | 8 teaching payloads |
| Direct injection (attack works) | `python3 module4-red-teaming/labs/inject.py --payload verdict-flip --mode vulnerable` | `ATTACK SUCCEEDED` |
| Same, hardened (defense holds) | `python3 module4-red-teaming/labs/inject.py --payload verdict-flip --mode hardened` | `ATTACK STOPPED` |
| Indirect injection | `python3 module4-red-teaming/labs/inject.py --payload indirect-ua --mode vulnerable` | `ATTACK SUCCEEDED` |
| Control (no injection) | `python3 module4-red-teaming/labs/inject.py --payload benign --mode vulnerable` | stays malicious, `No hijack detected` |
| Browser view | open http://localhost:8080, toggle vulnerable/hardened, triage the poisoned alerts | the exact prompt sent is shown; verdict flips in vulnerable, holds in hardened |
| Blue-team detection | on the manager: `wazuh-logtest`, paste a line containing `IGNORE ALL PREVIOUS INSTRUCTIONS` | fires rule 100110 |

### Module 5 - Capstone
| Check | Command | Expected |
|-------|---------|----------|
| Auto-grader (passing) | write a report to `module5-capstone/submissions/test.md` with all 5 sections + IPs 10.10.10.5/10.10.10.7 + a prompt-injection mention, then `python3 module5-capstone/labs/capstone_check.py` | `RESULT: PASS`, 100/100 |
| Auto-grader (adversarial gate) | grade a report that omits the injection mention | score capped, `ADVERSARIAL MISS` |
| Scenario replay | follow [module5-capstone/SCENARIO.md](module5-capstone/SCENARIO.md) | telemetry generated for students to investigate |

---

## 4. Slides
```bash
python3 -c "from pptx import Presentation; import glob; [print(f, len(Presentation(f).slides._sldIdLst)) for f in sorted(glob.glob('slides/*.pptx'))]"
```
**Pass criteria:** all five decks open and report 12-14 slides each.

---

## 5. Cleanup after testing
```bash
scripts/lab_down.sh     # stop containers
scripts/teardown.sh     # stop + remove images, volumes, and generated logs
```

---

## Results log (fill in during your run)

| Area | Result (PASS/FAIL) | Notes |
|------|--------------------|-------|
| smoke_test.sh (offline) | | |
| selftest.sh (live) | | |
| Ollama live generate | | |
| Wazuh reachable + rules loaded | | |
| Module 1 triage | | |
| Module 2 attacks -> Wazuh alerts | | |
| Module 3 Sigma + workflow | | |
| Module 4 attack + defense + rule 100110 | | |
| Module 5 grader + adversarial gate | | |
| Slides open | | |
