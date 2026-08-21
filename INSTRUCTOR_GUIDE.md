# Instructor Guide - Running the Week

Facilitator playbook for the 5-day bootcamp. Each day is 2 hours: a short concept
segment, guided hands-on labs, then debrief and Q&A. Read [SETUP.md](SETUP.md) first.

Students use the two shared boxes over the VPN and run everything in Python - no Docker
on student machines. You (instructor) have SSH to the boxes and generate the Module 2
telemetry. Docker is optional, only for an offline demo or building an at-home lab.

## Before Day 1 - one-time prep

1. Each student VM has this repo, Python 3, and a `.env` pointing at the two boxes. Recover
   the Wazuh credentials once on the Wazuh VM with `sudo bash scripts/get_wazuh_creds.sh`
   and share the four `WAZUH_*` lines; `OLLAMA_HOST`/`WAZUH_API` already point at the VMs.
2. On the Wazuh manager, load [docker/wazuh-agent/local_rules.xml](docker/wazuh-agent/local_rules.xml)
   (adds rules 100101 SQLi, 100110 prompt-injection, 100120 SSH-burst) and restart the manager.
3. Confirm the model answers: `python3 common/ollama_client.py --health`.
4. Have every student run `python3 scripts/verify_env.py` (Ollama + Wazuh should be green).

## Daily rhythm (2 hours)

| Time | Segment |
|------|---------|
| 0:00-0:20 | Concept intro + live demo (instructor drives) |
| 0:20-1:40 | Guided labs (students follow the STUDENT_GUIDE; you float) |
| 1:40-2:00 | Debrief, challenge review, Q&A, preview tomorrow |

---

## Day 1 - Foundations ([module1-foundations/](module1-foundations/))
- **Goal:** connect to the AI (Ollama) and the SIEM (Wazuh) and run the first AI log triage.
- **Prep:** none beyond the pre-flight. Project the Wazuh dashboard for the tour.
- **Watch for:** `.env` / VPN issues - budget time for `verify_env.py`. This is the day to fix
  everyone's environment.
- **Debrief:** where AI helps vs. where the analyst must stay in the loop.

## Day 2 - Applied Detection ([module2-detection/](module2-detection/))
- **Goal:** detect real attacks (SSH/web brute force, SQLi) in the shared Wazuh and the datasets.
- **Prep:** generate the telemetry into the shared Wazuh before class (students do not attack):
  `bash scripts/generate_wazuh_telemetry.sh 10.50.136.116` (needs `sshpass`). Confirm with
  `python3 common/wazuh_client.py --alerts 30 --min-level 5`.
- **Watch for:** students trying to run attacks - they only analyze. Point them at the dashboard,
  `wazuh_client.py --alerts`, and the detectors.
- **Debrief:** signature vs. behavioral detection; how correlation cuts false positives.

## Day 3 - Prompt Engineering ([module3-prompt-engineering/](module3-prompt-engineering/))
- **Goal:** Sigma rules, incident summaries, and an AI-assisted triage workflow.
- **Prep:** none. Have [common/prompts/](common/prompts/) open.
- **Watch for:** over-trusting AI output. Reinforce "AI drafts, analyst verifies," especially for
  generated detection rules.
- **Debrief:** which tasks are worth automating; good vs. bad prompts.

## Day 4 - AI Red Teaming ([module4-red-teaming/](module4-red-teaming/))
- **Goal:** attack the AI directly (direct + indirect prompt injection) with `inject.py`, then defend it.
- **Prep:** none - `inject.py` runs against the shared model. Confirm with `inject.py --list`.
- **Safety framing (say it out loud):** defensive education; every attack is paired with its
  detection and mitigation; payloads are benign.
- **The money moment:** `inject.py --payload verdict-flip --mode vulnerable` (ATTACK SUCCEEDED)
  then `--mode hardened` (ATTACK STOPPED). Tie it back to Wazuh rule 100110.
- **Debrief:** why "never treat data as instructions" is the core lesson of LLM security.

## Day 5 - Capstone ([module5-capstone/](module5-capstone/))
- **Goal:** run the full lifecycle (Detect to Report) with AI, and catch the adversarial
  prompt-injection trap rather than trust the AI blindly.
- **Prep:** generate the incident telemetry as in Day 2 (or point students at the datasets).
- **Grading:** students submit to `module5-capstone/submissions/`. Run
  `python3 module5-capstone/labs/capstone_check.py` and combine with
  [module5-capstone/RUBRIC.md](module5-capstone/RUBRIC.md).

---

## Grading at a glance
- Days 1-4: completion + challenge answers (each module's `solutions/README.md` has the key).
- Day 5: capstone rubric (100 pts) + auto-grader. The single most important criterion is whether
  the student **identified and resisted the prompt-injection attempt**.

## Common failure modes (and fixes)
| Symptom | Fix |
|---------|-----|
| Ollama `--health` FAIL | VPN down or wrong `OLLAMA_HOST`. Run `python3 scripts/verify_env.py`. |
| Ollama first call is slow / times out | The model loads on first use (30-60s), then stays warm. The client waits up to 300s. Check the GPU with `ollama ps` on the GPU VM. |
| Wazuh 401 | Using the dashboard password for the API. Use the `wazuh-wui` API password from `get_wazuh_creds.sh`. |
| No Module 2 alerts | Re-run `generate_wazuh_telemetry.sh` against a monitored target; confirm the custom rules loaded (`wazuh-logtest`). |
| Injection "doesn't work" on the real model | The 8B model is usually injectable but nondeterministic; retry, or use the optional deterministic mock for the canonical walk-through. |

## Optional Docker (offline demo / at-home lab)
```bash
bash scripts/smoke_test.sh                  # deterministic offline proof (4/4)
scripts/lab_up.sh core targets attack       # your own victims + attacker
scripts/teardown.sh                         # reset
```
