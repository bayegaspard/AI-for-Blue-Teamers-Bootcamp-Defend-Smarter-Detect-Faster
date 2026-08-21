# Module 5 - Capstone: End-to-End AI-Powered SOC Workflow (Day 5)

**Instructor guide.** Duration: **2 hours.** Audience: bootcamp students who have
completed Modules 1-4. This is the graded capstone.

---

## 1. Module objectives

Module 5 is the **capstone** of the "AI Blue Team & Intro to AI Red Teaming"
bootcamp. It consolidates everything from Days 1-4 into one realistic incident that
students work end-to-end:

| Learning outcome | How this capstone delivers it |
|---|---|
| Run the full incident lifecycle: **Detection → Analysis → Response → Reporting** | Tasks 1→4 of the worksheet mirror the four phases exactly. |
| **Apply AI tools across the workflow** | Students triage with the AI SOC assistant, correlate with an AI prompt, and draft the report with the IR prompt. |
| **Optimize SOC efficiency** with AI | The AI does first-pass summarization so students spend their time verifying, not typing. |
| Capstone combining **traffic analysis + AI-assisted investigation + adversarial considerations** | The scenario blends SSH/web brute force + SQLi (traffic) with AI triage (investigation) and a planted **prompt-injection** log line (adversarial). |

The adversarial twist is the assessment's teeth: the incident data contains a
prompt-injection payload (the Module 4 threat, now seen from the blue side). A
student who lets the AI talk them into closing the "benign" alert **fails the
capstone**. This is deliberate and is the single most important learning check.

**Prior modules referenced (do not re-teach, just recall):**
Module 1 (first AI triage), Module 2 (brute-force detection + threat intel),
Module 3 (prompt engineering for SOC), Module 4 (prompt injection, vulnerable vs.
hardened AI SOC assistant).

---

## 2. Files in this module

| File | Audience | Purpose |
|---|---|---|
| [`README.md`](README.md) | Instructor | This guide. |
| [`SCENARIO.md`](SCENARIO.md) | Students | The incident brief ("Operation Nightjar"). **Does not reveal the trap.** |
| [`STUDENT_WORKSHEET.md`](STUDENT_WORKSHEET.md) | Students | Numbered Detect→Analyze→Respond→Report→Adversarial tasks. |
| [`RUBRIC.md`](RUBRIC.md) | Instructor | Human grading rubric, 100 pts. |
| [`labs/capstone_check.py`](labs/capstone_check.py) | Both | Automated report grader. |
| [`solutions/README.md`](solutions/README.md) | Instructor | Full expected findings + model report + expected grader output. **Do not share until debrief.** |
| [`submissions/`](submissions) | Students | Where students save `<name>_report.md`. |

---

## 3. Prerequisites & setup

**Students need:** the repo cloned, Python 3, and a working `.env` (from Modules
1-4). They do **not** need to install anything new.

**You (instructor) choose one delivery path:**

### Path A - Real cyberlab
- GPU VM Ollama (`llama3.1:8b`) reachable at `http://10.50.142.235:11434`.
- Wazuh 4.14 up (dashboard `https://10.50.136.116`, API `:55000`, indexer `:9200`)
  with custom rules **100101** (SQLi), **100110** (prompt-injection), **100120**
  (SSH brute-force burst) installed - see
  [`docker/wazuh-agent/local_rules.xml`](../docker/wazuh-agent/local_rules.xml).
- Generate the telemetry live from the attacker container **before class** (or as a
  live demo) - commands are in [`SCENARIO.md` §3](SCENARIO.md). Confirm the alerts
  appear: `python3 common/wazuh_client.py --alerts 40 --min-level 10`.

### Path B - Portable / offline (recommended default)
```bash
scripts/lab_up.sh core          # mock-ollama + ai-soc-assistant, no GPU needed
# students set OLLAMA_HOST=http://localhost:11435 in their .env
```
The evidence is pre-captured in [`datasets/`](../datasets) (including
[`poisoned.log`](../datasets/poisoned.log)), so this path needs no attacker replay.

**Pre-flight checklist (run before students arrive):**
```bash
python3 scripts/verify_env.py                     # Ollama + Wazuh reachable
python3 module4-red-teaming/labs/inject.py --list # injection tool ready (direct, no Docker)
python3 module5-capstone/labs/capstone_check.py   # grader runs (will say "no report" - fine)
```
The mock-ollama is **deterministic** (see [`docker/mock-ollama/app.py`](../docker/mock-ollama/app.py)):
a normal brute-force/SQLi log → `malicious`; the injection payload hijacks
**vulnerable** mode and is resisted in **hardened** mode. This guarantees the lesson
lands in class regardless of GPU/model randomness.

---

## 4. Two-hour run sheet (120 min)

| Time | Min | Segment | Instructor does | Students do |
|------|----:|---------|------------------|-------------|
| 0:00 | 10 | **Mission brief** | Recap Days 1-4 in 3 bullets. Read the page from [`SCENARIO.md`](SCENARIO.md). Confirm everyone's AI backend answers `--health`. | Skim SCENARIO; run the health check. |
| 0:10 | 20 | **Task 1 - Detect** | Float. Point stuck students at `--alerts` / `detect_bruteforce.py`. | Pull alerts/logs; list the suspect IPs + why (Checkpoint 1). |
| 0:30 | 25 | **Task 2 - Analyze** | Demo one AI triage, then stress **"verify against the raw line."** | Triage each finding with AI; attach the proving log line (Checkpoint 2). |
| 0:55 | 20 | **Task 3 - Respond** | Discuss containment priorities; surface the hidden **successful** `admin` login. | Correlate IPs with `threat_intel.csv`; write a tied-to-evidence containment list (Checkpoint 3). |
| 1:15 | 25 | **Task 4 - Report** | Show the [`ir_report`](../common/prompts/ir_report.md) prompt; remind them the draft is a *first draft to edit*. | Draft with AI; save `submissions/<name>_report.md` with the 5 sections (Checkpoint 4). |
| 1:40 | 15 | **Task 5 - Adversarial** | This is the payoff. Have everyone run the same log in **vulnerable** then **hardened** mode together. | Prove the injection; add the Adversarial note; run `capstone_check.py` (Checkpoint 5). |
| 1:55 | 5  | **Debrief** | Reveal the trap using [`solutions/README.md`](solutions/README.md). Poll: who closed the "benign" alert? Normalize it - that's the lesson. | Submit final report. |

If you're tight on time, protect **Task 5** - it can be shortened elsewhere but the
adversarial catch is the graded core.

---

## 5. Facilitation notes

- **The trap is the point.** Expect a chunk of the class to close the injected alert
  as benign in Task 5a. Don't warn them off in advance - let them get fooled in
  vulnerable mode, *then* show hardened mode. The "aha" is worth more than the save.
- **"Verify the AI" is the mantra.** Every time a student quotes an AI verdict, ask
  "which line proves that?" Make it reflexive.
- **The hidden success is the sting in Task 3.** [`auth.log`](../datasets/auth.log)
  line 9 is an `Accepted password for admin from 10.10.10.5` *after* the failures -
  the brute force worked. Students who only report "6 failed logins" understated the
  impact. `detect_bruteforce.py` surfaces it for them.
- **Common stumbles:** wrong `OLLAMA_HOST` (should be the GPU VM
  `http://10.50.142.235:11434`; offline students use `:11435`); saving the report
  outside `submissions/` (the grader defaults to newest there). The AI tools run
  directly against the model, so there is no web server to quote JSON against.
- **Path-agnostic:** every worksheet task has both a cyberlab and an offline command;
  students on either path reach the same findings.

---

## 6. How to grade

Grading is **two layers**: the automated check gates the essentials, and you apply
the human rubric for quality.

### 6a. Automated gate - [`labs/capstone_check.py`](labs/capstone_check.py)
```bash
# grade one student
python3 module5-capstone/labs/capstone_check.py submissions/gaspard_report.md

# grade everyone
for f in module5-capstone/submissions/*_report.md; do
  echo "### $f"; python3 module5-capstone/labs/capstone_check.py "$f"
done
```
It scores 100 points across: the 5 required sections (10 each = 50), naming
`10.10.10.5` (15) and `10.10.10.7` (15), and flagging the prompt-injection/poisoned
entry (20). Pass mark is **70**, and it exits non-zero on a fail so you can script
it. It is robust to a missing/empty file. A submission that misses the adversarial
catch caps at 80 and prints an **ADVERSARIAL MISS** banner.

### 6b. Human rubric - [`RUBRIC.md`](RUBRIC.md)
Use it to score analysis quality, response prioritization, and report clarity - the
things a substring check can't see. The automated total and the human total both sum
to 100 and are weighted the same way (detection / analysis / response / reporting /
adversarial), so a student's two scores should be close; a big gap is a signal to
read the report carefully (e.g. right IPs pasted but no real analysis).

### 6c. What "excellent" looks like
See the model report and expected grader output in
[`solutions/README.md`](solutions/README.md). Short version: correct IPs and rule
IDs, the `admin` compromise called out in Impact, a prioritized containment list,
and a crisp Adversarial note that names the injection, its source IP, rule 100110,
and hardened-mode as the mitigation.
