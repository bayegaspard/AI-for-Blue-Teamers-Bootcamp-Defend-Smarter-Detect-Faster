# AI Blue Team & Intro to AI Red Teaming - Bootcamp Labs

Hands-on lab package for the 5-day bootcamp delivered by **Valix AI (Dr. Gaspard Baye)**
for **Evolve Academy**. Built to run against the existing cyberlab (Ollama GPU VM +
Wazuh SIEM) **and** on any laptop with just Docker - no GPU or VPN required.

> Maps 1:1 to the signed Statement of Work. 5 days × 2 hours. Each day is a self-contained
> module with an instructor guide, a step-by-step student guide, runnable labs, and solutions.

> **New here? Open [START_HERE.md](START_HERE.md)** - it tells you exactly what to run first
> and links every lab in order. **Verifying the environment? See [TESTING.md](TESTING.md)** and
> run `bash scripts/selftest.sh`.

---

## What's in the box

| Path | What it is |
|------|-----------|
| [module1-foundations/](module1-foundations/) | Day 1 - AI in the SOC: connect to Ollama + Wazuh, first AI log triage |
| [module2-detection/](module2-detection/) | Day 2 - Traffic analysis & detection: run real attacks, catch them |
| [module3-prompt-engineering/](module3-prompt-engineering/) | Day 3 - Prompt engineering: Sigma rules, summaries, AI triage workflow |
| [module4-red-teaming/](module4-red-teaming/) | Day 4 - AI red teaming: prompt injection (direct + indirect) & defense |
| [module5-capstone/](module5-capstone/) | Day 5 - Capstone: end-to-end AI-powered incident, scored |
| [slides/](slides/) | One professional PowerPoint deck per module (graphic-first, 2-hour paced) |
| [common/](common/) | Reusable `ollama_client`, `wazuh_client`, and a tested security prompt library |
| [docker/](docker/) | The whole attackable lab: mock LLM, AI SOC assistant, victims, attacker, log generator |
| [datasets/](datasets/) | Sample auth/web logs, a poisoned log, and a threat-intel feed |
| [scripts/](scripts/) | `verify_env`, `lab_up`, `lab_down`, `teardown`, `smoke_test` |
| [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) | How to run the week, day by day |
| [SETUP.md](SETUP.md) | Full setup for both the cyberlab and the portable path |

---

## How students run the labs

Students use the two shared cyberlab boxes over the network. They do not SSH into them;
they only reach the model and the SIEM:
- Ollama `llama3.1:8b` on the GPU VM `10.50.142.235:11434`
- Wazuh 4.14 on `10.50.136.116` (dashboard 443, API 55000, indexer 9200)

The whole student path is **Python-only, no Docker**. Every AI and SIEM interaction is
selected by a single `.env` file that already points at these two IPs.

Docker is **optional**, for two extras: running your own attackable stack at home
(victims, attacker, the web assistant) and the fully offline mock. See SETUP.md.

---

## Student quickstart (the two shared boxes, no Docker)

```bash
# From the repo root
cp .env.example .env
# Set WAZUH_PASS/WAZUH_INDEXER_PASS (run scripts/get_wazuh_creds.sh on the Wazuh VM).
# OLLAMA_HOST/WAZUH_API already point at the two VMs.

python3 scripts/verify_env.py     # Ollama + Wazuh should be green
```

Then start at [START_HERE.md](START_HERE.md) and
[module1-foundations/STUDENT_GUIDE.md](module1-foundations/STUDENT_GUIDE.md).

## Optional: at-home / offline (requires Docker)

```bash
bash scripts/smoke_test.sh        # proves the AI pipeline with no GPU/VPN (4/4 PASS)
scripts/lab_up.sh core            # the local mock + web assistant
scripts/lab_up.sh core targets attack   # your own victims + attacker toolbox
```

---

## The signature lab: indirect prompt injection

Day 4 ties Blue and Red together. An attacker plants a prompt-injection payload inside a
field that ends up in a **log** (a crafted `User-Agent` or username). When an analyst asks the
AI SOC assistant to triage that alert, the payload hijacks the model - flipping a malicious
verdict to "benign," or leaking the system prompt. Students then flip the assistant to
**hardened** mode (prompt isolation + input sanitization + output validation) and watch every
attack fail - and see the Wazuh rule that flags injection payloads in logs before the AI ever
reads them. It's the most current, most memorable lesson in the week, and it's fully runnable
offline.

---

## Safety & scope

This package is for **authorized, educational** security training in an isolated lab. The
"victim" apps are intentionally vulnerable and must never be exposed to the internet or real
data. Red-team payloads are benign (verdict-flipping / prompt-leaking) and are always paired
with the detection and mitigation that stops them. See [SETUP.md](SETUP.md) for isolation notes.
