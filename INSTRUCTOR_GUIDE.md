# Instructor Guide - Running the Week

This is the facilitator's playbook for the 5-day bootcamp. Each day is 2 hours: a short
concept segment, then guided hands-on labs, then debrief/Q&A. Read [SETUP.md](SETUP.md) first
and dry-run the whole week once on the portable path (`bash scripts/smoke_test.sh`).

## Before Day 1 - one-time prep

1. Decide the delivery path per the cohort:
   - **Cyberlab** (recommended for the real experience): each student VM has this repo + Python,
     `.env` points at the GPU VM and Wazuh, and the Wazuh custom rules are loaded.
   - **Portable**: students run the Docker stack locally. Works with zero infra.
2. On the Wazuh manager, load [docker/wazuh-agent/local_rules.xml](docker/wazuh-agent/local_rules.xml)
   and restart the manager. Enroll at least one endpoint (see
   [docker/wazuh-agent/README.md](docker/wazuh-agent/README.md)).
3. Confirm the GPU VM serves the model: `python3 common/ollama_client.py --health`.
4. Distribute the repo (git clone or zip) and have each student run `python3 scripts/verify_env.py`.

## Daily rhythm (2 hours)

| Time | Segment |
|------|---------|
| 0:00-0:20 | Concept intro + live demo (instructor drives) |
| 0:20-1:40 | Guided labs (students follow the STUDENT_GUIDE; you float) |
| 1:40-2:00 | Debrief, challenge review, Q&A, preview tomorrow |

---

## Day 1 - Foundations ([module1-foundations/](module1-foundations/))
- **Goal:** students connect to the AI (Ollama) and the SIEM (Wazuh), and run their first
  AI-assisted log triage.
- **Prep:** `scripts/lab_up.sh core` if portable. Have the Wazuh dashboard open to project.
- **Watch for:** `.env` / connectivity issues - budget time for `verify_env.py`. This is the
  day to fix everyone's environment.
- **Debrief:** where does AI help vs. where must the analyst stay in the loop?

## Day 2 - Applied Detection ([module2-detection/](module2-detection/))
- **Goal:** run real attacks (SSH/web brute force, SQLi), see the telemetry, and detect it.
- **Prep:** `scripts/lab_up.sh core targets attack`. Pre-build the attacker image so class
  time isn't spent on the first `apt` build.
- **Watch for:** students attacking the wrong host - inside the attacker container the targets
  are `victim-web` and `victim-ssh` (service names), not `localhost`.
- **Debrief:** signature vs. behavioral detection; how correlation cuts false positives.

## Day 3 - Prompt Engineering ([module3-prompt-engineering/](module3-prompt-engineering/))
- **Goal:** turn prompting into a repeatable SOC skill - Sigma rules, incident summaries, and
  an AI-assisted triage workflow.
- **Prep:** `scripts/lab_up.sh core`. Have [common/prompts/](common/prompts/) open.
- **Watch for:** over-trusting AI output. Reinforce "AI drafts, analyst verifies," especially
  for generated detection rules.
- **Debrief:** which tasks are worth automating; what a good vs. bad prompt looks like.

## Day 4 - AI Red Teaming ([module4-red-teaming/](module4-red-teaming/))
- **Goal:** attack the AI SOC assistant (direct + **indirect** prompt injection), then defend it.
- **Prep:** `scripts/lab_up.sh core targets attack`. Start the assistant in **vulnerable** mode.
- **Safety framing (say this out loud):** this is defensive education; every attack is paired
  with its detection and mitigation; payloads are benign.
- **The money moment:** triage a poisoned log, watch the verdict flip, then flip to **hardened**
  mode and watch it hold. Tie it back to Wazuh rule 100110.
- **Debrief:** why "never treat data as instructions" is the core lesson of LLM security.

## Day 5 - Capstone ([module5-capstone/](module5-capstone/))
- **Goal:** students run the full lifecycle (Detect → Analyze → Respond → Report) with AI,
  and must catch the adversarial prompt-injection trap rather than trust the AI blindly.
- **Prep:** `scripts/lab_up.sh core targets attack`; optionally generate telemetry with the
  attacker scripts before class (see the scenario).
- **Grading:** students submit a report to `module5-capstone/submissions/`. Run the auto-grader
  `python3 module5-capstone/labs/capstone_check.py` and combine with
  [module5-capstone/RUBRIC.md](module5-capstone/RUBRIC.md).

---

## Grading at a glance
- Days 1-4: completion + challenge answers (each module's `solutions/README.md` has the key).
- Day 5: capstone rubric (100 pts) + auto-grader. The single most important criterion is
  whether the student **identified and resisted the prompt-injection attempt**.

## Common failure modes (and fixes)
| Symptom | Fix |
|---------|-----|
| Whole class can't reach Ollama | Fall back to portable: `scripts/lab_up.sh core` + `OLLAMA_HOST=http://localhost:11435`. |
| No Wazuh alerts after an attack | Confirm the agent reads the right log path and the custom rules loaded; use `wazuh-logtest`. |
| Injection "doesn't work" on the real model | The 8B model is usually injectable, but nondeterministic; the mock guarantees the demo - use it for the canonical walk-through. |
| Attacker build is slow | Pre-build once: `docker compose --env-file .env -f docker/docker-compose.yml --profile attack build`. |

## Reset between cohorts
```bash
scripts/teardown.sh
```
