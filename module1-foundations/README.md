# Module 1 - Foundations: AI for Blue Team Operations (Day 1)

**Instructor guide** · 2 hours (live session + hands-on labs) · Beginner-friendly

> Part of the **AI Blue Team & Intro to AI Red Teaming Bootcamp** for Evolve Academy (delivered by Valix AI).
> This is authorized, defensive/educational security training.

---

## Where this fits in the Statement of Work

This module delivers **SoW Module 1**. Every SoW bullet maps to a concrete lab:

| SoW Module 1 bullet | Delivered by |
| --- | --- |
| Overview of AI tools in cybersecurity | Live intro + **Lab 1.2** (first AI conversation for security) |
| How SOC analysts leverage AI for **log analysis** | **Lab 1.3** (AI-assisted log triage of `datasets/auth.log`) |
| How SOC analysts leverage AI for **alert triage** | **Lab 1.4** (Wazuh tour + `wazuh_client --alerts`) and the triage output format in 1.3 |
| How SOC analysts leverage AI for **IR workflows** | Live discussion of the triage → ticket → response loop; sets up Modules 2 & 5 |
| AI-assisted automation | **Lab 1.3** starter script `first_ai_triage.py` (a repeatable, scriptable triage step) |

**SoW outcome for this module:** *"Participants understand how AI integrates into modern SOC environments."*
By the end of Day 1 a student can: point a script or CLI at a local LLM, get a **structured** triage verdict from raw logs, read a SIEM's alert stream, and articulate where the human stays in the loop. That is the mental model the rest of the week builds on.

---

## Learning objectives

By the end of this module, participants can:

1. **Explain the AI-in-the-SOC landscape** - what LLMs are good at (summarizing, triaging, drafting), what they are *not* (ground truth, decisions), and why we run a **local** model (`llama3.1:8b`) instead of a public chatbot for sensitive logs.
2. **Verify a working lab environment** - Ollama (LLM) and Wazuh (SIEM) reachable, using either the real cyberlab VMs or the portable Docker fallback.
3. **Prompt an LLM for a security task** using a deliberate **system persona** (the "SOC Analyst Assistant") and understand why the persona changes the output.
4. **Run an AI-assisted log-triage** pass over real SSH auth logs and read the structured verdict (SUMMARY / VERDICT / CONFIDENCE / INDICATORS / RECOMMENDED ACTION).
5. **Navigate a SIEM (Wazuh)** dashboard and pull alerts programmatically - the raw material the AI will summarize in later modules.
6. **Describe the human-in-the-loop principle** - AI drafts, the analyst decides.

---

## Prerequisites

**For students:**
- Comfort with a terminal (cd, run a command, edit a file).
- Basic idea of what an SSH login and a web request are. No ML background needed.
- Their student VM (SSH/API access to the cyberlab) **or** a laptop with Docker for the portable path.

**Already provisioned (shared infrastructure - do not rebuild):**
- **GPU VM** - Ollama serving `llama3.1:8b` at `http://10.50.142.235:11434` (Tesla T4).
- **Wazuh VM** - Wazuh 4.14 all-in-one: dashboard `https://10.50.136.116`, manager API `:55000`, indexer `:9200`.
- **Shared tooling** in the repo root: [`common/ollama_client.py`](../common/ollama_client.py), [`common/wazuh_client.py`](../common/wazuh_client.py), prompt templates in [`common/prompts/`](../common/prompts/), datasets in [`datasets/`](../datasets/), and the Docker fallback under [`docker/`](../docker/).

**Instructor pre-flight (do this before class):**
1. Confirm the `.env` at the repo root has the **real** `WAZUH_PASS` / `WAZUH_INDEXER_PASS` filled in (they ship as `CHANGE_ME`). Ollama needs no secret.
2. From the repo root, run the environment check and confirm both PASS:
   ```bash
   python3 scripts/verify_env.py
   ```
3. Bring up the portable stack once so it's warm and image-built, in case the VPN/GPU is flaky during class:
   ```bash
   scripts/lab_up.sh core
   ```
4. Skim [`common/prompts/log_triage.md`](../common/prompts/log_triage.md) and [`common/prompts/system_prompts.md`](../common/prompts/system_prompts.md) - these are the two artifacts you'll refer to on the whiteboard.

---

## Setup commands (either path works, unchanged)

**Real cyberlab (VMs + GPU):** ensure `.env` has
```
OLLAMA_HOST=http://10.50.142.235:11434
WAZUH_API=https://10.50.136.116:55000
WAZUH_INDEXER=https://10.50.136.116:9200
```
Then `python3 scripts/verify_env.py` should report two PASS lines.

**Portable / offline (any laptop, no GPU, no VPN):**
```bash
scripts/lab_up.sh core                       # starts mock-ollama + ai-soc-assistant
# then edit .env:
#   OLLAMA_HOST=http://localhost:11435
python3 common/ollama_client.py --health      # should list llama3.1:8b
```
The `mock-ollama` is a deterministic, GPU-free stand-in. It returns **malicious** for brute-force/SQLi-shaped logs and **benign** otherwise, so every AI lab behaves identically to the real GPU. Wazuh has no offline stand-in - on the portable path, do Lab 1.4's dashboard tour as an instructor-led screen-share and let students still run the CLI against the VM if they have API reachability; if not, use the sample alert output in the solutions key.

---

## 2-hour timing breakdown (approximate)

| Time | Segment | Format | Notes |
| ---: | --- | --- | --- |
| 0:00-0:15 | **Welcome + the big picture** | Live | Why AI in the SOC now; the "AI drafts, human decides" rule; tour the repo (`common/`, `datasets/`, `scripts/`). Set expectations: local model, not ChatGPT. |
| 0:15-0:30 | **Lab 1.1 - Environment check** | Hands-on | Everyone gets two PASS lines. Triage stragglers to the portable path early - this is the #1 time sink. |
| 0:30-0:50 | **Lab 1.2 - First AI conversation for security** | Hands-on | Ask the model security questions. Introduce the **system persona** and show how it changes answers. |
| 0:50-0:55 | **Break / buffer** | - | Also a catch-up window for anyone still on Lab 1.1. |
| 0:55-1:25 | **Lab 1.3 - AI-assisted log triage** | Hands-on | The centerpiece. Pipe `auth.log` through the model; read the structured verdict; run the starter script. |
| 1:25-1:50 | **Lab 1.4 - Meet the SIEM** | Hands-on + demo | Guided Wazuh dashboard tour; pull alerts with the CLI. Connect "logs → alerts → AI summary." |
| 1:50-2:00 | **Wrap-up + mini-challenges + preview** | Live | Debrief the 3 challenges, restate the SoW outcome, tease Module 2 (detection engineering). |

Timeboxing tip: Labs 1.2 and 1.3 are where the learning is. If you're behind, compress the Wazuh tour (1.4) to a demo and assign the challenges as homework - do **not** cut Lab 1.3.

---

## Teaching notes

- **Lead with "why local."** The first question is always "why not just use ChatGPT?" Answer on the board: sensitive logs never leave the lab, deterministic/repeatable behavior, no per-token cost, works air-gapped. This framing justifies the whole toolchain.
- **Make the persona tangible (Lab 1.2).** Run the *same* question twice - once with the default persona, once with `--system "You are a pirate."` The content changes dramatically. Students remember that the system prompt is a real control, not decoration. This is the seed for Module 3 (prompt engineering) and Module 4 (prompt injection).
- **Read the triage output as a template, not prose (Lab 1.3).** Point at each of the five fields. Emphasize **INDICATORS** - "the model must cite the exact lines; if it can't, don't trust the verdict." That habit is the whole point.
- **The brute-force story in `auth.log` is deliberate.** Walk the timeline out loud: many `Failed password` from `10.10.10.5` at 03:11 … then `Accepted password for admin from 10.10.10.5` at 03:11:41. The attacker **succeeded**. A good analyst (and a good model) flags the successful login as the scary part, not just the failures. See the solutions key.
- **On the real 8B model, wording varies run-to-run.** The *verdict* (malicious) should be stable; the exact sentences will not be. Tell students up front so they don't think their run is "wrong." The mock is word-for-word deterministic, which is great for demos.
- **Keep Wazuh light (Lab 1.4).** Day 1 is orientation. You're planting the map (agents, alerts, rule levels, MITRE), not doing detection engineering - that's Module 2.
- **Close every lab by restating the loop:** raw logs → SIEM alert → AI triage/summary → human decision → IR action. That loop is the through-line for the entire week.

---

## Common pitfalls (and fixes)

| Symptom | Cause | Fix |
| --- | --- | --- |
| `verify_env.py` Ollama = FAIL | Not on VPN / wrong `OLLAMA_HOST` | Switch to portable path: `scripts/lab_up.sh core`, set `OLLAMA_HOST=http://localhost:11435`. |
| `verify_env.py` Wazuh = FAIL, "auth failed" | `WAZUH_PASS` still `CHANGE_ME` | Paste the real install-time password into `.env`. |
| Wazuh FAIL, "unreachable" | No route to `10.50.136.116` | Confirm VPN/student-VM networking; Wazuh has no local mock - use instructor screen-share for the tour. |
| `ModuleNotFoundError: common` | Ran a lab script from inside `labs/` without the boilerplate, or copied a snippet wrong | The provided scripts add the repo root to `sys.path`; run them as-is, e.g. `python3 module1-foundations/labs/first_ai_triage.py`. |
| First model call "hangs" ~10-30s | Cold GPU load of the 8B model | Normal on the first request. It warms up; subsequent calls are fast. |
| `python: command not found` | System only has `python3` | Use `python3` (the repo targets 3.10+; it's tested on 3.13). |
| Model output "looks different from the slides" | Real 8B is non-deterministic | Expected - compare **verdicts**, not wording. Use the mock for a byte-identical demo. |
| Dashboard shows a cert warning | Wazuh uses self-signed TLS | Expected in the lab; click through. `VERIFY_TLS=0` in `.env` already handles this for the CLI. Never do this in prod. |

---

## Files in this module

- [`README.md`](./README.md) - this instructor guide.
- [`STUDENT_GUIDE.md`](./STUDENT_GUIDE.md) - the hands-on walk-through (Labs 1.1-1.4, checkpoints, challenges).
- [`labs/first_ai_triage.py`](./labs/first_ai_triage.py) - starter script for Lab 1.3 (reads `auth.log`, calls the LLM, prints the verdict).
- [`labs/ask_ai.sh`](./labs/ask_ai.sh) - convenience wrapper around the Ollama CLI for Lab 1.2.
- [`solutions/README.md`](./solutions/README.md) - instructor answer key: expected verdicts, talking points, challenge answers.

---

## What "done" looks like

A student finishing Module 1 can, unprompted:
- get two PASS lines from `verify_env.py` on their chosen path,
- ask the local model a security question and change its behavior with a persona,
- run `first_ai_triage.py` and correctly read the 5-field verdict - including spotting the **successful** login after the brute force,
- open Wazuh (or view the CLI alert stream) and name what an agent, an alert, and a rule level are,
- and say, in one sentence, **where the human stays in the loop.**

That is the SoW outcome: *participants understand how AI integrates into modern SOC environments.*
