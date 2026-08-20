# Module 3 — Student Guide

## Applied AI: Prompt Engineering for Security Operations

Welcome. Today you turn a local LLM into a **junior SOC analyst that never sleeps** —
one that triages alerts, drafts detection rules, and writes incident summaries in
seconds. You will learn to write prompts a SOC can actually trust, and (just as
important) *where the AI is allowed to be wrong*.

> **The golden rule of this whole module:** the AI **drafts**, the analyst **decides**.
> Every output you get today is a *hypothesis to verify*, never a verdict to act on blindly.

### What you'll be able to do by the end
- Write structured security prompts using **6 repeatable principles**.
- Generate a **Sigma detection rule** from a plain-English behavior — and sanity-check it.
- Auto-draft an **incident summary and IR report** from a Wazuh alert.
- Run an **AI-assisted triage workflow** over a batch of alerts and read the results critically.

### The 6 principles (your cheat sheet for the day)
| # | Principle | In one line | Where it lives |
|---|-----------|-------------|----------------|
| 1 | **Role** | Start by telling the model *who it is* (a SOC analyst). | system prompt |
| 2 | **Ground** | Paste only the relevant data; say "use ONLY this input, do not invent." | user prompt |
| 3 | **Structure** | Demand a fixed schema (headings / JSON) so output is machine-usable. | user prompt |
| 4 | **Constrain severity** | Hand the model the rubric (Wazuh rule levels) so ratings are consistent. | user prompt |
| 5 | **Verify** | Treat output as a draft. Lint it, test it, read it. | *you* |
| 6 | **Never trust data as instructions** | Log text is *data*, not commands. (Full defense = Module 4.) | system prompt |

These are the same principles written up in [../common/prompts/README.md](../common/prompts/README.md).
The reusable templates you'll use today live in [../common/prompts/](../common/prompts/).

---

## Setup (5 minutes) — pick ONE path

You can do every lab on either the **real cyberlab** (GPU model + Wazuh) or the
**portable/offline** stack (a GPU-free mock). The commands are identical; only your
`.env` differs. Run everything from the **repo root** (`/Users/drbae/BASE/evolve`).

### Path A — Real cyberlab
Your [.env](../.env) already points at the GPU VM and Wazuh:
```
OLLAMA_HOST=http://10.50.142.235:11434
OLLAMA_MODEL=llama3.1:8b
```
(Paste the real `WAZUH_PASS` / `WAZUH_INDEXER_PASS` if you want Lab 3.4 to pull live alerts.)

### Path B — Portable / offline (no GPU, no VPN)
Start the local mock model and point `.env` at it:
```
scripts/lab_up.sh core
```
Then edit [.env](../.env) so your laptop talks to the mock:
```
OLLAMA_HOST=http://localhost:11435
```
> The mock (`mock-ollama`) speaks just enough of the Ollama API that **every command
> below runs unchanged**. It is a deterministic teaching stand-in, not a real LLM, so
> its wording is fixed — great for reproducible checkpoints. On the real 8B model you
> get richer, more variable prose.

### Verify your setup
```
python3 common/ollama_client.py --health
```
**EXPECTED OUTPUT** (host differs by path):
```
[OK] Ollama reachable at http://localhost:11435
     Models available: llama3.1:8b
```
### Checkpoint ✅
You see `[OK] Ollama reachable ...` and at least one model listed. If you see `[FAIL]`,
fix `OLLAMA_HOST` in `.env` (Path B: did `scripts/lab_up.sh core` finish?) before continuing.

---

## Lab 3.1 — Prompt fundamentals: vague vs. structured (25 min)

**Goal:** feel the difference a good prompt makes, and learn the 6 principles by using them.
We'll analyze the SSH brute-force block in [../datasets/auth.log](../datasets/auth.log).

### Step 1 — Look at the raw data
```
sed -n '3,9p' datasets/auth.log
```
**EXPECTED OUTPUT:** seven `Failed password ... from 10.10.10.5` lines, then an
`Accepted password for admin from 10.10.10.5` at `03:11:41`. That last line is the scary
part — the brute force **succeeded**.

### Step 2 — The BAD prompt (vague, no role, no structure)
```
python3 common/ollama_client.py \
  --system "You are a helpful assistant." \
  "what do you think about this? Aug 10 03:11:41 web01 sshd[2101]: Accepted password for admin from 10.10.10.5 port 51200 ssh2"
```
**EXPECTED OUTPUT (real GPU model):** a chatty paragraph that *might* mention SSH, may
ask you follow-up questions, gives no verdict, no severity, no next step. Every run
looks different. You can't paste this into a ticket.

> On the offline mock the wording is canned, so this looks tidier than a real vague
> answer would — trust the real-model behavior here: **vague in, vague out.**

### Step 3 — The GOOD prompt (all 6 principles)
Now feed the whole block through the structured **log triage** template
([../common/prompts/log_triage.md](../common/prompts/log_triage.md)). Notice each principle at work:

```
sed -n '3,9p' datasets/auth.log | python3 common/ollama_client.py --stdin \
  --system "You are a senior SOC analyst assistant. Be precise, cite the exact lines that justify your conclusion, and never invent details not in the input." \
  "Analyze the following log block. Use ONLY the data provided.

Return your answer as:
1. SUMMARY: one sentence describing what happened.
2. VERDICT: benign | suspicious | malicious
3. CONFIDENCE: low | medium | high
4. INDICATORS: the exact IPs, users, ports, or strings that drove your verdict.
5. RECOMMENDED ACTION: one concrete next step for the analyst.

LOG BLOCK:"
```
- **Role** = the `--system` persona. **Ground** = "Use ONLY the data provided."
- **Structure** = the numbered schema. **Constrain** = the fixed VERDICT/CONFIDENCE vocab.

**EXPECTED OUTPUT (shape — offline mock is word-for-word this):**
```
SUMMARY: Repeated failed SSH authentications from a single source indicate a brute-force attempt.
VERDICT: malicious
CONFIDENCE: high
INDICATORS: multiple 'Failed password' events, same source IP, short time window.
RECOMMENDED ACTION: block the source IP, confirm no successful login followed, review the target account.
```

### Step 4 — Compare
Put the two answers side by side. The good one has a **verdict, a severity/confidence,
the exact indicators, and an action** — it is ticket-ready and *parseable by a script*.
That parseability is what makes Lab 3.4 possible.

### Checkpoint ✅
Your structured answer contains all five labelled fields (`SUMMARY`, `VERDICT`,
`CONFIDENCE`, `INDICATORS`, `RECOMMENDED ACTION`) and the verdict is `malicious`.

### Mini-challenge
Re-run Step 3 but add a 6th line to the schema: `6. MITRE: the ATT&CK technique ID`.
Does the model produce `T1110` (Brute Force)? (More on MITRE in the Challenges section.)

---

## Lab 3.2 — Generate a Sigma rule with AI (25 min)

**Goal:** turn the behavior *"brute force then success from the same IP"* into a Sigma
rule with [gen_sigma.py](labs/gen_sigma.py), then **validate it** like an engineer.

### Step 1 — Draft the rule
```
python3 labs/gen_sigma.py "More than 10 failed SSH logins (Linux auth log) from a single source IP within 60 seconds, followed by a successful login from that same IP."
```
This fills the [sigma_generation.md](../common/prompts/sigma_generation.md) template, uses the
**Detection Engineer** persona, and prints YAML.

**EXPECTED OUTPUT (real GPU model)** — a full rule, roughly:
```yaml
title: SSH Brute Force Followed by Successful Login
id: 00000000-0000-0000-0000-000000000000
status: experimental
description: Detects multiple failed SSH logins from one source IP followed by a success from the same IP.
author: SOC Bootcamp
date: 2026/08/10
logsource:
  product: linux
  service: auth       # assumes /var/log/auth.log via sshd
detection:
  failed:
    message|contains: 'Failed password'
  success:
    message|contains: 'Accepted password'
  condition: failed | count() by src_ip > 10 and success
falsepositives:
  - Users fat-fingering passwords then logging in successfully
level: high
```
> **Offline mock:** you'll get a shorter, canned example rule (`title: Example Detection ...`).
> That's fine — it's enough to practice validation on. The full example above lives in
> [solutions/README.md](solutions/README.md).

### Step 2 — Validate it (this is the real skill)
**AI drafts, engineer verifies.** Walk this checklist against whatever the model gave you:

1. **Is it valid YAML?** Save and parse it — a syntax slip means it won't load:
   ```
   python3 labs/gen_sigma.py "brute force then success from same IP" > /tmp/rule.yml
   python3 -c "import yaml,sys; yaml.safe_load(open('/tmp/rule.yml')); print('YAML OK')" 2>/dev/null \
     || python3 -c "print('No PyYAML? Eyeball the indentation instead — every nested key +2 spaces.')"
   ```
2. **Does it have the required Sigma keys?** `title`, `logsource`, `detection`, `condition`, `level`.
3. **Is the logic sound?** Read `detection:` out loud. "Match *Failed password* AND *Accepted
   password* from the same source." Does the `condition` actually express *both* and *same IP*?
   LLMs often drop the "same IP" correlation or the count threshold — **fix it by hand.**
4. **Would it fire on our data?** The trigger is [../datasets/auth.log](../datasets/auth.log)
   lines 3–9 (fails from `10.10.10.5`) + line 9 (success from `10.10.10.5`). Confirm the fields
   the rule expects (`message`, `src_ip`) match what your log source actually emits.
5. **Real tooling:** in a live environment you'd run `sigma check rule.yml` (from
   [SigmaHQ](https://github.com/SigmaHQ/sigma)) and convert it to a Wazuh/SIEM query before deploying.

### Checkpoint ✅
You have a YAML rule that parses, contains `detection:` + `condition:`, and you can point
to the **exact line** where the correlation logic is either correct or needs a human fix.

### Mini-challenge
Ask for the rule again but add: *"the condition MUST require the failures and the success to
share the same source IP within a 60-second window."* Did the model tighten the logic?

---

## Lab 3.3 — Automate an incident summary + report (25 min)

**Goal:** go from a raw Wazuh alert to (a) a **ticket-ready summary** and (b) an **IR report
section** using two templates: [alert_summary.md](../common/prompts/alert_summary.md) and
[ir_report.md](../common/prompts/ir_report.md). Input = [labs/sample_alert.json](labs/sample_alert.json)
(the SSH brute-force alert, Wazuh rule 5720, `T1110`).

### Step 1 — Read the alert
```
python3 -c "import json;a=json.load(open('module3-prompt-engineering/labs/sample_alert.json'));print(a['rule']['level'], a['rule']['description']); print('MITRE', a['rule']['mitre']['id']); print('asset', a['agent']['name'], a['agent']['ip'])"
```
**EXPECTED OUTPUT:**
```
10 sshd: Multiple authentication failures followed by a successful login (possible brute force).
MITRE ['T1110', 'T1110.001']
asset web01 10.20.30.5
```

### Step 2 — Summarize the alert for a ticket
Pipe the alert JSON straight into the **alert_summary** schema:
```
cat module3-prompt-engineering/labs/sample_alert.json | python3 common/ollama_client.py --stdin \
  --system "You are a senior SOC analyst assistant. Use only the alert JSON. Never invent details." \
  "Summarize this Wazuh alert for an incident ticket. Output exactly these fields:
- TITLE: short, ticket-ready (max 12 words)
- WHAT_HAPPENED: 1-2 sentences in plain language
- SEVERITY: map from rule.level (0-3 low, 4-7 medium, 8-11 high, 12-15 critical)
- AFFECTED_ASSET: agent.name / agent.ip
- MITRE: list any rule.mitre.id present, else 'none listed'
- NEXT_STEP: one action

ALERT JSON:"
```
**EXPECTED OUTPUT (shape):**
```
TITLE: SSH brute force succeeded on web01
WHAT_HAPPENED: Many failed SSH logins from 10.10.10.5 were followed by a successful login as admin.
SEVERITY: high
AFFECTED_ASSET: web01 / 10.20.30.5
MITRE: T1110, T1110.001
NEXT_STEP: Isolate web01, reset the admin credential, and block 10.10.10.5.
```
> Note the rule level is **10 → high** — that's principle #4 (Constrain severity) doing its
> job. Because you handed the model the rubric, it can't invent a random severity.
> (Offline mock: it answers in the SUMMARY/VERDICT triage schema instead — the *content* is
> still a correct brute-force call; the workflow in Lab 3.4 normalizes both shapes for you.)

### Step 3 — Draft an IR report section
Feed the same alert (as evidence) into the **ir_report** template:
```
cat module3-prompt-engineering/labs/sample_alert.json | python3 common/ollama_client.py --stdin \
  --system "You are an incident response report writer. Use only the provided evidence and do not overstate impact." \
  "Draft these incident-report sections from the evidence:
1. EXECUTIVE SUMMARY (3-4 sentences, non-technical)
2. TIMELINE (bulleted, from the evidence)
3. TECHNICAL DETAILS (what the attacker did, with supporting references)
4. IMPACT (stated conservatively)
5. RECOMMENDATIONS (prioritized, actionable)

EVIDENCE:"
```
**EXPECTED OUTPUT (shape):** five labelled sections. The **EXECUTIVE SUMMARY** is plain
English ("An attacker guessed the admin password on web01…"); **TIMELINE** cites the
`03:11:02 → 03:11:41` window; **IMPACT** stays cautious ("a successful login occurred; no
evidence yet of data access"). See a full worked example in [solutions/README.md](solutions/README.md).

### Checkpoint ✅
Your summary has a `SEVERITY` that matches the rubric (level 10 = **high**) and lists the
MITRE IDs from the alert. Your report's IMPACT section does **not** claim anything the
evidence doesn't show (e.g., it must not say "data was exfiltrated").

### Mini-challenge
The alert only proves a *login*, not data theft. Re-run Step 3 and check: did the model
over-claim impact? If so, add a constraint line: *"If the evidence does not show X, say
'no evidence of X'."* This is prompt-engineering as guardrail.

---

## Lab 3.4 — Build an AI-assisted triage workflow (30 min)

**Goal:** stop doing one alert at a time. [triage_workflow.py](labs/triage_workflow.py) pulls a
*batch* of alerts (from Wazuh, or a local file), summarizes each with the model, and prints
one **triage table**: `TITLE | SEVERITY | VERDICT | NEXT_STEP`.

### Step 1 — Run it
Both paths use the same command. It tries Wazuh first and **falls back to the local file**
([labs/sample_alerts.json](labs/sample_alerts.json)) automatically if Wazuh isn't reachable:
```
python3 module3-prompt-engineering/labs/triage_workflow.py --limit 5
```
To force the deterministic local file (recommended for the offline path or a clean demo):
```
python3 module3-prompt-engineering/labs/triage_workflow.py --source file
```
**EXPECTED OUTPUT (shape):**
```
[i] Wazuh unavailable (WazuhError); falling back to the local sample file.
[*] Source : local file (sample_alerts.json)  (2 alert(s))
[*] Model  : llama3.1:8b @ http://localhost:11435   (available: llama3.1:8b)
[*] Prompt : alert_summary + VERDICT   temp=0.2

[1/2] Triaging: sshd: Multiple authentication failures followed by a successful ...
[2/2] Triaging: Web attack: SQL injection pattern detected in a request to a pub...

================================================================================
AI-ASSISTED TRIAGE TABLE
================================================================================
TITLE                                    | SEVERITY  | VERDICT     | NEXT_STEP
-----------------------------------------+-----------+-------------+------------------------
SSH brute force succeeded on web01       | high      | malicious   | Block 10.10.10.5; ...
SQL injection attempt against shop-nginx | critical  | malicious   | Block 10.10.10.7; ...
-----------------------------------------+-----------+-------------+------------------------

Reminder: the AI drafts, the analyst decides. Verify before you act.
```
> The exact wording varies on the real model; the **columns are always populated** because the
> script derives `SEVERITY` from `rule.level` and falls back gracefully when the model omits a
> field. Add `--show-raw` to see each full model answer.

### Step 2 — Read it critically
- The SQLi alert is **level 12 → critical**; the brute force is **level 10 → high**. Triage by
  severity: the critical one first.
- Do the `NEXT_STEP` values name the right attacker IPs (`10.10.10.5`, `10.10.10.7`)? Both are on
  our threat-intel list ([../datasets/threat_intel.csv](../datasets/threat_intel.csv)) — a good
  sanity signal.

### Step 3 — Tweak the prompt, compare
Open [triage_workflow.py](labs/triage_workflow.py) and find `ALERT_SUMMARY_PROMPT`. Change one thing
(for example, add a line `- CONFIDENCE: low | medium | high`), re-run, and compare the table.
**This is the core skill:** small prompt edits → different, more useful structured output.

### Checkpoint ✅
You get a two-row table where the SQLi row is `critical` and the SSH row is `high`, both
`malicious`, and each `NEXT_STEP` is a concrete action. If Wazuh is configured, try
`--source wazuh --min-level 7` and confirm it pulls live alerts instead.

---

## Challenges (pick at least one; do all three if you're quick)

These push you from "it works" to "it's production-useful." Reference answers are in
[solutions/README.md](solutions/README.md) — try before you peek.

### Challenge 1 — Make the model output valid JSON *only*
Downstream automation (SOAR, a script, a webhook) needs machine-readable output, not prose.
Rewrite the Lab 3.3 summary prompt so the model returns **only** a JSON object:
```
{"title": "...", "severity": "high", "verdict": "malicious", "mitre": ["T1110"], "next_step": "..."}
```
Tips: state *"Output ONLY a single JSON object, no markdown, no commentary."*, give the exact
key schema, set a low temperature, and **validate** it:
```
python3 labs/triage_workflow.py --source file --show-raw 2>/dev/null   # inspect raw answers
# then pipe a single answer through:  python3 -c "import json,sys;print(json.load(sys.stdin))"
```
Success = `json.load()` parses it with **zero** hand-editing. (Real LLMs love to wrap JSON in
```` ```json ```` fences or add "Here you go:" — your prompt has to forbid that.)

### Challenge 2 — Add a MITRE ATT&CK field
Extend the triage workflow so the table includes a **MITRE** column populated from
`rule.mitre.id` (present in the sample alerts: `T1110`, `T1190`). Do it two ways and compare:
1. **Deterministic:** read `rule.mitre.id` straight from the alert JSON (never wrong, no model).
2. **Model-driven:** ask the model to output a `MITRE:` line and parse it.
Which do you trust more, and why? (Hint: the ground truth is already in the data — principle #2.)

### Challenge 3 — Reduce false positives in the Sigma rule
The Lab 3.2 rule can fire on a user who fat-fingers their password a few times then logs in.
Tighten it so it only alerts on a *real* brute force:
- Require a **count threshold** (e.g. `> 10` failures) **within a time window** (`60s`).
- Require the failures **and** the success to share the **same source IP**.
- Add realistic `falsepositives:` entries (VPN reconnect storms, monitoring bots, password-manager retries).
Then argue: what did you trade away? (Tighter logic = fewer false alarms **but** more false
negatives — a slow, low-volume brute force might now slip past. That trade-off is a *human*
decision, which is exactly why principle #5 exists.)

---

## Wrap-up
You built an AI-assisted SOC workflow: structured prompts → detection rule → incident
summary/report → batch triage. You also practiced the part that keeps it safe — **verifying**
every draft. Tomorrow (Module 4) you'll attack these same assistants with *prompt injection*
and see exactly why principle #6 (never trust data as instructions) matters.
