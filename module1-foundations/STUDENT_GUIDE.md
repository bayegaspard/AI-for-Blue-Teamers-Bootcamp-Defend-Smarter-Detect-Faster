# Module 1 — Student Guide: AI for Blue Team Operations

**Day 1 · ~2 hours · hands-on**

Welcome to Day 1. Today you'll meet the two tools you'll use all week — a local **LLM** (via Ollama) and a **SIEM** (Wazuh) — and you'll do your first AI-assisted triage of real security logs.

> **The one rule to remember:** *AI drafts, the human decides.* The model is a fast junior analyst that never sleeps. You still own the verdict.

### Two paths — pick yours

Every command below works on **both**. When it matters, we show both.

- **Real cyberlab** — you're on the student VM / VPN, using the GPU and Wazuh VMs.
- **Portable / offline** — any laptop with Docker, no GPU or VPN needed (uses the `mock-ollama` stand-in).

**Before you start**, open a terminal at the **repo root** (the folder that contains `common/`, `datasets/`, `scripts/`):
```bash
cd path/to/repo      # the repo root
```
> If a command says `python` and your machine only has `python3`, just type `python3` instead.

---

## Lab 1.1 — Environment check

**Goal:** prove both tools are reachable before you rely on them.

### Step 1 — Run the all-in-one check

```bash
python scripts/verify_env.py
```

**Expected output (real cyberlab, both healthy):**
```
======================================================================
 AI Blue Team Bootcamp — environment check
======================================================================
  [PASS] Ollama   reachable at http://10.50.142.235:11434 — models: llama3.1:8b
  [PASS] Wazuh    manager 4.14.0 reachable at https://10.50.136.116:55000
----------------------------------------------------------------------
  All good — you're ready for the labs.
======================================================================
```

If you see a `[FAIL]`, don't panic — jump to **Step 4 (portable fallback)** below.

### Step 2 — Check each service individually

```bash
python common/ollama_client.py --health
python common/wazuh_client.py --health
```

**Expected output:**
```
[OK] Ollama reachable at http://10.50.142.235:11434
     Models available: llama3.1:8b
[OK] Wazuh manager 4.14.0 reachable at https://10.50.136.116:55000
```

### Step 3 — (Real cyberlab only) confirm the GPU

If you have SSH access to the GPU VM, confirm the model is running on real hardware:

```bash
nvidia-smi
```

**Expected output (trimmed):**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 550.xx       Driver Version: 550.xx       CUDA Version: 12.x      |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
|===============================+======================+======================|
|   0  Tesla T4              On | 00000000:00:1E.0  Off |                    0 |
| N/A   45C    P0    27W /  70W |   6144MiB / 15360MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```
That **Tesla T4** line is your GPU serving `llama3.1:8b`. (Don't have SSH to that VM? Skip this — it's just a peek behind the curtain.)

### Step 4 — Portable / offline fallback (if anything FAILed, or you have no VPN)

Start the local stack and point your tools at it:

```bash
scripts/lab_up.sh core
```
**Expected output (trimmed):**
```
[*] Starting profiles: core
...
[*] Up. Handy URLs (host ports from .env):
      AI SOC Assistant : http://localhost:8080
      Mock Ollama      : http://localhost:11435/api/tags
```

Now edit the repo-root `.env` and set:
```
OLLAMA_HOST=http://localhost:11435
```
Re-check just Ollama (the mock has no Wazuh — that's fine for now):
```bash
python common/ollama_client.py --health
```
**Expected output:**
```
[OK] Ollama reachable at http://localhost:11435
     Models available: llama3.1:8b
```

> **Checkpoint ✅** — You have at least one healthy Ollama (`--health` prints `[OK]`). On the real cyberlab you also have a healthy Wazuh. You're ready.

---

## Lab 1.2 — Your first AI conversation for security

**Goal:** talk to the model like a SOC analyst would, and learn the single most important control — the **system prompt (persona)**.

### Step 1 — Ask a plain security question

```bash
python common/ollama_client.py "Explain what SSH brute force looks like in auth.log. Keep it to 4 bullet points."
```

**Expected output (wording varies on the real model; shape is stable):**
```
- Many 'Failed password' lines in a short time window from the SAME source IP.
- A mix of usernames, often including 'invalid user' (admin, root, oracle, postgres) — the attacker is guessing.
- Rapidly increasing source ports (e.g. 51122, 51124, 51126) from that one IP.
- The dangerous tell: a 'Failed password' storm FOLLOWED BY an 'Accepted password' — the guess finally worked.
```

> On the **portable/mock** path the model gives a shorter canned answer — that's expected. The point is the *interaction*, not the prose.

### Step 2 — See the persona in action

The tool sends a hidden **system prompt** that shapes every answer. The default is a SOC analyst persona. Prove it changes behavior by overriding it:

```bash
python common/ollama_client.py --system "You are a pirate. Answer in pirate speak." "What is an SSH brute force attack?"
```
You'll get the same *facts* wrapped in pirate voice. The **system prompt is a real control** — remember that; it's the whole story of Modules 3 and 4.

### Step 3 — Use the convenience wrapper

Typing the full path gets old. This module ships a wrapper that defaults to the SOC persona:

```bash
module1-foundations/labs/ask_ai.sh "List 3 log sources a SOC watches for credential attacks."
```

Stream the answer live (nice for demos):
```bash
module1-foundations/labs/ask_ai.sh --stream "In one sentence, why analyze logs with a LOCAL model instead of a public chatbot?"
```
**Expected answer (idea, not exact words):** *Sensitive logs never leave the lab, behavior is repeatable, and there's no per-token cost or internet dependency.*

Swap the persona with an environment variable:
```bash
SYSTEM="You are a detection engineer." module1-foundations/labs/ask_ai.sh "Give one idea for a Sigma rule that catches SSH brute force."
```

> **Checkpoint ✅** — You've asked the model a security question, changed its behavior with a persona, and used `ask_ai.sh`. You now know the system prompt is a lever, not decoration.

---

## Lab 1.3 — AI-assisted log triage (the main event)

**Goal:** hand real logs to the model and get back a **structured verdict** you can act on.

First, look at the raw evidence — [`datasets/auth.log`](../datasets/auth.log):
```bash
cat datasets/auth.log
```
```
Aug 10 08:00:01 web01 sshd[1001]: Accepted publickey for deploy from 10.20.30.5 port 51000 ssh2
Aug 10 08:15:22 web01 sshd[1050]: Accepted password for analyst from 10.20.30.9 port 51044 ssh2
Aug 10 03:11:02 web01 sshd[2001]: Failed password for invalid user admin from 10.10.10.5 port 51122 ssh2
Aug 10 03:11:03 web01 sshd[2003]: Failed password for invalid user admin from 10.10.10.5 port 51124 ssh2
Aug 10 03:11:04 web01 sshd[2005]: Failed password for root from 10.10.10.5 port 51126 ssh2
Aug 10 03:11:05 web01 sshd[2007]: Failed password for root from 10.10.10.5 port 51128 ssh2
Aug 10 03:11:06 web01 sshd[2009]: Failed password for invalid user oracle from 10.10.10.5 port 51130 ssh2
Aug 10 03:11:07 web01 sshd[2011]: Failed password for invalid user postgres from 10.10.10.5 port 51132 ssh2
Aug 10 03:11:41 web01 sshd[2101]: Accepted password for admin from 10.10.10.5 port 51200 ssh2
Aug 10 08:42:10 web01 sshd[1120]: Received disconnect from 10.20.30.9 port 51044:11: disconnected by user
```
Read it like an analyst: a burst of failures from `10.10.10.5` at 03:11 … then an **Accepted password for admin** from that *same IP*. Keep that in mind — does the AI catch it?

### Step 1 — Triage by piping the log into the model

The `log_triage` prompt (see [`common/prompts/log_triage.md`](../common/prompts/log_triage.md)) asks for a fixed 5-field answer. Quick version from the CLI:

```bash
cat datasets/auth.log | python common/ollama_client.py --stdin \
  --system "You are a senior SOC analyst assistant. Cite the exact log lines that justify your verdict." \
  "Analyze this log block and return SUMMARY, VERDICT (benign|suspicious|malicious), CONFIDENCE, INDICATORS, RECOMMENDED ACTION."
```
> Note: `--stdin` reads the piped log as the prompt. (Here we appended the instruction inside the system prompt; the starter script in Step 2 assembles the full template cleanly for you.)

### Step 2 — Run the starter script (the repeatable way)

Real automation lives in a script, not a one-off pipe. Run the provided starter — [`labs/first_ai_triage.py`](./labs/first_ai_triage.py):

```bash
python module1-foundations/labs/first_ai_triage.py
```

**Expected output (mock is exact; real 8B says the same thing in its own words):**
```
======================================================================
 AI-assisted log triage  —  datasets/auth.log
======================================================================
[*] Read 10 log lines.
[*] Asking llama3.1:8b at http://localhost:11435 to triage the logs...

----- AI TRIAGE RESULT ------------------------------------------------
SUMMARY: Repeated failed SSH authentications from a single source indicate a brute-force attempt.
VERDICT: malicious
CONFIDENCE: high
INDICATORS: multiple 'Failed password' events, same source IP, short time window.
RECOMMENDED ACTION: block the source IP, confirm no successful login followed, review the target account.
-----------------------------------------------------------------------

[✓] Done. Remember: the AI is a co-pilot. A human confirms the verdict.
```

Notice **RECOMMENDED ACTION** literally tells you to *"confirm no successful login followed."* Now go do that yourself with your own eyes: line 9 is `Accepted password for admin from 10.10.10.5`. The brute force **worked**. That is the difference between reading the AI's output and *acting* on it.

### Step 3 — Point the script at a different log

The script takes any file path:
```bash
python module1-foundations/labs/first_ai_triage.py datasets/access.log
```
Try it and compare the verdict to `auth.log`.

> **Checkpoint ✅** — You produced a structured triage verdict from raw logs with one command, read all five fields, and **verified the successful login yourself** instead of trusting the summary blindly.

---

## Lab 1.4 — Meet the SIEM (Wazuh)

**Goal:** see where alerts come from. A SIEM collects logs from many machines (agents), applies rules, and raises **alerts**. In later modules the AI will summarize these alerts — today you just learn the map.

### Step 1 — Guided dashboard tour (real cyberlab)

Open the dashboard in a browser:

```
https://10.50.136.116
```
> You'll get a self-signed certificate warning — expected in the lab, click through. Log in with the lab-provided Wazuh credentials.

Walk these panels (portable-path students: follow along on the instructor's screen-share):

1. **Overview / Modules home** — tiles for *Security Events*, *Integrity Monitoring*, *Vulnerabilities*, *MITRE ATT&CK*. This is your starting map.
2. **Agents** — the endpoints reporting in. Each has an **ID**, **name**, **IP**, and **status** (active/disconnected). An *agent* = one monitored machine.
3. **Security Events** — the live **alert** stream. Each alert has a **timestamp**, a **rule** (with a description), and a **rule level** (0–15; higher = more severe). This is the SOC's inbox.
4. **Rule level** — Wazuh scores every alert. Rough map: **0–3** low, **4–7** medium, **8–11** high, **12–15** critical. You'll use this in Module 2.
5. **MITRE ATT&CK** — alerts tagged with attacker techniques (e.g. *T1110 Brute Force*). This is how a SOC speaks a shared language about attacker behavior.

Find our brute force: filter Security Events for the source IP `10.10.10.5` or rule text like *"authentication"* — you should see the SSH failures (and the successful login) as alerts.

### Step 2 — Pull alerts from the command line

You don't need the browser to read alerts — the shared client queries the indexer directly:

```bash
python common/wazuh_client.py --alerts 10
```

**Expected output (representative — your live alerts will differ):**
```
[L 5] 2026-08-10T03:11:07  sshd: Multiple authentication failures.
[L10] 2026-08-10T03:11:41  sshd: Attempt to login using a non-existent user, then success.
[L 3] 2026-08-10T08:15:22  sshd: Authentication success.
[L 7] 2026-08-10T09:02:14  Web server 400 error code.
...
```
Each line is `[L<level>] <timestamp>  <rule description>`. That `L10` line is the important one — a high-severity alert around a login that succeeded after failures.

### Step 3 — Filter to the alerts that matter

Analysts don't read everything. Show only medium-and-above (level ≥ 7):

```bash
python common/wazuh_client.py --alerts 20 --min-level 7
```
And list the agents (the machines being watched):
```bash
python common/wazuh_client.py --agents
```
**Expected output (representative):**
```
   0  wazuh-manager        127.0.0.1        active
 001  web01                10.20.30.5       active
```

> **Checkpoint ✅** — You can open Wazuh (or read its alerts via CLI), and you can name the three core concepts: an **agent** (a monitored machine), an **alert** (a rule that fired on a log), and a **rule level** (its severity 0–15).

---

## The loop you just learned

Say it back in one breath — this is the through-line for the whole week:

> **Raw logs → SIEM raises an alert → AI triages/summarizes → the human decides → IR takes action.**

Today you did the middle: raw `auth.log` → an AI triage verdict, and you saw where the SIEM sits. Module 2 goes deeper on detection; Modules 3–4 sharpen (and attack) the prompts; Module 5 ties it into a full IR workflow.

---

## Mini-challenges

Try these now (answers are in the instructor's [`solutions/README.md`](./solutions/README.md), but do them first).

### Challenge 1 — Catch the compromise
The AI called `auth.log` a "brute-force attempt." But something worse happened. Re-read the log and answer:
- **Did the attacker get in?** Which single line proves it?
- Rewrite the **RECOMMENDED ACTION** to reflect a *successful* compromise (not just a failed attempt).

*Hint:* compare the source IP on the `Failed password` lines with the `Accepted password` line.

### Challenge 2 — Triage a different log
Run the starter script on the poisoned dataset:
```bash
python module1-foundations/labs/first_ai_triage.py datasets/poisoned.log
```
- What VERDICT do you get, and does it convince you?
- Open [`datasets/poisoned.log`](../datasets/poisoned.log) and read it yourself. Is there anything in the *log text* that seems to be "talking to" the AI rather than describing an event? (You don't need to solve it — just notice it. This is the seed of Module 4.)

### Challenge 3 — Make the persona matter
Ask the **same** question with two different personas and compare:
```bash
module1-foundations/labs/ask_ai.sh "How should I respond to repeated failed SSH logins from one IP?"
SYSTEM="You are a beginner IT helpdesk agent." module1-foundations/labs/ask_ai.sh "How should I respond to repeated failed SSH logins from one IP?"
```
- In 1–2 sentences, how did the *system prompt* change the answer's depth or assumptions?
- Why does this matter for a SOC that puts an LLM in front of untrusted log data? (Foreshadowing: Module 4.)

---

## Cheat sheet

| I want to… | Command |
| --- | --- |
| Check everything | `python scripts/verify_env.py` |
| Check Ollama only | `python common/ollama_client.py --health` |
| Check Wazuh only | `python common/wazuh_client.py --health` |
| Ask the model | `module1-foundations/labs/ask_ai.sh "your question"` |
| Ask + stream | `module1-foundations/labs/ask_ai.sh --stream "your question"` |
| Triage the sample log | `python module1-foundations/labs/first_ai_triage.py` |
| Triage any log | `python module1-foundations/labs/first_ai_triage.py path/to/file.log` |
| Read recent alerts | `python common/wazuh_client.py --alerts 10` |
| Read high-severity alerts | `python common/wazuh_client.py --alerts 20 --min-level 7` |
| List agents | `python common/wazuh_client.py --agents` |
| Start the offline stack | `scripts/lab_up.sh core` (then set `OLLAMA_HOST=http://localhost:11435`) |
