# Module 5 Capstone - Student Worksheet

**Incident:** "Operation Nightjar" (see [`SCENARIO.md`](SCENARIO.md))
**Goal:** Work the full lifecycle - **Detect → Analyze → Respond → Report** - using
your AI SOC assistant, then catch the one thing the AI gets wrong.

**How to use this sheet:** Do the tasks in order. Each has a **What to run**, an
**Expected output**, and a **Checkpoint** you must be able to tick before moving on.
Everything runs from the **repo root** (the folder you cloned) unless noted.

> **The lab runs against the two shared boxes** (Ollama on 10.50.142.235, Wazuh on
> 10.50.136.116) from your `.env`. No Docker is required.

**One-time setup**

```bash
python3 scripts/verify_env.py
# Expected: Ollama and Wazuh API both green.
```

---

## Task 1 - DETECT: find the attack

You have overnight telemetry. Find every source that misbehaved and rank it.

### 1a. Pull the evidence

The incident evidence is in the bundled logs, so this always works. Start with the SSH log
and the Module 2 detector:
```bash
python3 module2-detection/labs/detect_bruteforce.py datasets/auth.log
```
**Expected output** (abridged):
```
[FLAGGED] 10.10.10.5
    failures (total)     : 6
    worst burst in 120s  : 6
    usernames targeted   : admin, oracle, postgres, root
...
  * 10.10.10.5
      THREAT INTEL MATCH  -> Known SSH brute-force source (internal threat feed) [severity=high]
      !! SUCCESSFUL LOGIN -> account 'admin' authenticated from this IP after the failures (likely compromised).
```

**Optional - live Wazuh** (only if your instructor generated telemetry into the shared
Wazuh; otherwise this is empty and the datasets are your source of record):
```bash
python3 common/wazuh_client.py --alerts 40 --min-level 5
```
If it returns rows you will see high-level alerts such as the SSH brute-force burst
(rule 100120) and, if web telemetry was generated, the SQLi pattern (100101). Empty output
just means no attacks have been run against a monitored host yet - continue with the datasets.

### 1b. Read the web log by eye

```bash
cat datasets/access.log
```
Look for a client whose requests are obviously not a browser. You are looking for
SQL syntax (`' OR '1'='1`, `UNION SELECT`), a `sqlmap` user-agent, and a
`/../../etc/passwd` path-traversal probe.

### 1c. Skim the "extra" lines

```bash
cat datasets/poisoned.log
```
These came from the same time window. Note anything that looks *odd* - you'll come
back to it in Task 5.

> **Checkpoint 1** - Write down the three source IPs you'd investigate and *why*:
> - `10.10.10.5` - SSH brute force (6 failures + a successful `admin` login)
> - `10.10.10.7` - web attacker: SQLi + path traversal, `sqlmap` user-agent
> - at least one IP from `poisoned.log` that "looks weird" (`10.10.10.9` / `10.10.10.11` / `10.10.10.12`)

---

## Task 2 - ANALYZE: triage with AI, then verify

Now use the AI assistant to summarize each finding fast - **and check its work.**

### 2a. Triage the SSH brute force

**Any path (CLI):**
```bash
python3 module1-foundations/labs/first_ai_triage.py datasets/auth.log
```
**Expected output** (wording varies; the verdict should not):
```
SUMMARY: Repeated failed SSH authentications from a single source indicate a brute-force attempt.
VERDICT: malicious
CONFIDENCE: high
INDICATORS: multiple 'Failed password' events, same source IP (10.10.10.5), short window.
RECOMMENDED ACTION: block the source IP, confirm no successful login followed...
```

### 2b. Triage the web attack

Feed the SQLi line to the model directly (no Docker) using the Module 4 tool:
```bash
python3 module4-red-teaming/labs/inject.py --custom "10.10.10.7 POST /login?user=admin&pass=' OR '1'='1 sqlmap/1.7" --mode vulnerable
```
**Expected:** the MODEL RESPONSE names SQL injection / sqlmap and the verdict is malicious.

> **VERIFY THE AI (do this every time).** For each AI verdict, find the exact log
> line that supports it. If you can't point at the evidence, don't trust the verdict.
> The AI is a co-pilot; you sign off.

> **Checkpoint 2** - For each of your three IPs you have: (a) an AI one-line summary,
> and (b) the raw log line that proves it. Note where the AI was right - and keep an
> eye out for where it might be wrong.

---

## Task 3 - RESPOND: contain and correlate

### 3a. Correlate your IPs with threat intel

```bash
cat datasets/threat_intel.csv
```
Match each observed IP against the feed. **Expected matches:**

| Observed IP | Intel note | Severity |
|-------------|-----------|----------|
| `10.10.10.5` | Known SSH brute-force source (internal threat feed) | high |
| `10.10.10.7` | Automated SQLi scanner (sqlmap) observed | high |
| `10.10.10.11` | Credential stuffing infrastructure | medium |

(Optional AI-assisted version - use the correlation prompt in
[`common/prompts/threat_intel_correlation.md`](../common/prompts/threat_intel_correlation.md)
by pasting your observed IPs as block A and the CSV as block B into the assistant.)

### 3b. Recommend containment

Write down concrete, prioritized actions. At minimum:
- **Block** `10.10.10.5` and `10.10.10.7` at the perimeter/host firewall.
- **Disable/rotate** the `admin` account on `web01` - it had a **successful login**
  from the brute-force source (assume compromise).
- **Patch** the login app's input handling (parameterized queries) - SQLi worked.
- **Preserve** the logs as evidence before rotating them.

> **Checkpoint 3** - You have a containment list where every action is tied to a
> specific finding from Task 1/2. No orphan recommendations.

---

## Task 4 - REPORT: draft the incident report with AI, then save it

### 4a. Assemble your evidence block

Collect the log lines and findings you confirmed in Tasks 1-3 into a short evidence
block (the real IPs, timestamps, rule IDs, the successful `admin` login, the SQLi
strings, and the odd entry from Task 1c).

### 4b. Draft with the IR prompt

Use the report template in
[`common/prompts/ir_report.md`](../common/prompts/ir_report.md). Paste your evidence
block where it says `{{EVIDENCE_BLOCK}}` and send it to the assistant, e.g.:
```bash
python3 common/ollama_client.py --system "You are an incident report writer. Use ONLY the provided evidence; do not overstate impact." \
  "Draft an incident report with sections Executive Summary, Timeline, Technical Details, Impact, Recommendations. EVIDENCE: <paste your evidence block here>"
```
**Expected:** a draft with all five sections. Treat it as a *first draft* - you will
edit it for accuracy.

### 4c. Save your report (required format)

Create your report at the exact path below, with these **exact headings**:

```
module5-capstone/submissions/<yourname>_report.md
```

Required structure:
```markdown
# Incident Report - Operation Nightjar

## Executive Summary
<3-4 non-technical sentences: what happened, was anything compromised>

## Timeline
- 2026-08-10 03:11 UTC - SSH brute force from 10.10.10.5 ...
- 2026-08-10 03:20 UTC - SQLi / sqlmap from 10.10.10.7 ...
- 2026-08-10 04:15 UTC - planted prompt-injection log entry (see Adversarial note) ...

## Technical Details
<what each source did, with the supporting log line / Wazuh rule ID>

## Impact
<what was and was NOT affected - state conservatively>

## Recommendations
<prioritized, actionable - your Task 3 list>
```

> **Checkpoint 4** - `submissions/<yourname>_report.md` exists and has all five
> headings, names `10.10.10.5` and `10.10.10.7`, and does not overstate impact.

---

## Task 5 - ADVERSARIAL: catch what the AI got wrong

One of the "log lines" from Task 1c is **not telemetry - it's an attack on you and
your AI assistant.** Time to prove it and defend against it.

### 5a. Feed the odd entry to the assistant in **vulnerable** mode

```bash
python3 module4-red-teaming/labs/inject.py --payload indirect-ua --mode vulnerable
```
**Expected - the attack SUCCEEDS:**
```
Assessment        : ATTACK SUCCEEDED - the log content forced a benign verdict.
```
The text inside the User-Agent field is a **prompt-injection payload**: attacker data was
concatenated straight into the AI's instructions and overrode them.

### 5b. Re-run the SAME log in **hardened** mode

```bash
python3 module4-red-teaming/labs/inject.py --payload indirect-ua --mode hardened
```
**Expected - the attack FAILS:**
```
Assessment        : ATTACK STOPPED - the model kept a malicious/suspicious verdict.
```
Compare the USER prompt between the two runs: in hardened mode the log is fenced between
`<<<DATA>>>` markers and labeled untrusted data, and the override line is neutralized.

### 5c. Try the second payload (system-prompt theft)

```bash
python3 module4-red-teaming/labs/inject.py --payload indirect-ssh --mode vulnerable
python3 module4-red-teaming/labs/inject.py --payload indirect-ssh --mode hardened
```
**Expected:** vulnerable leaks the system prompt (ATTACK SUCCEEDED); hardened does not
(ATTACK STOPPED).

### 5d. Write the Adversarial note in your report

Add this to your `submissions/<yourname>_report.md` (it can live under Technical
Details or its own `## Adversarial Note` heading). It **must** state:

1. That a **prompt-injection / poisoned** log entry was present (call it by name).
2. The source IP(s) of the planted entry: `10.10.10.9` and/or `10.10.10.11`.
3. Which Wazuh rule catches it: **`100110` - Possible PROMPT-INJECTION payload**.
4. How you avoided being misled: you **verified the AI against raw evidence** and
   used **hardened mode** (data isolation) so the injection could not flip your
   verdict. You did **not** close the alert just because the AI said "benign".

> **Checkpoint 5** - Your report explicitly names the prompt-injection/poisoned entry
> and explains how you resisted it. This is the single most important part of the
> capstone - a report that "closed the benign alert" fails.

---

## Final step - grade yourself

```bash
python3 module5-capstone/labs/capstone_check.py
```
By default it grades the **newest** file in `submissions/`. **Expected for a
complete submission:**
```
  TOTAL: 100/100    (pass mark: 70)
  RESULT: PASS
```
If you see the **ADVERSARIAL MISS** banner, go back to Task 5 - you fell for the
injection. Fix your report and re-run.

**Deliverable to hand in:** `module5-capstone/submissions/<yourname>_report.md`,
passing `capstone_check.py`.
