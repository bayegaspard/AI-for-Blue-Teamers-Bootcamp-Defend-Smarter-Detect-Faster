# Module 3 - Solutions / Answer Key (Instructor)

Reference outputs and challenge solutions for [../STUDENT_GUIDE.md](../STUDENT_GUIDE.md).

> Remember: on the real `llama3.1:8b` the **wording varies every run** - grade on *structure and
> correctness*, not exact text. The offline `mock-ollama` is deterministic, so its answers match
> word-for-word. All example prompts assume the personas in
> [../../common/prompts/system_prompts.md](../../common/prompts/system_prompts.md).

---

## Lab 3.1 - vague vs. structured

**BAD prompt** → an unstructured paragraph with no verdict/severity/action; different each run;
often ends with a clarifying question. *Not* ticket-usable. (Point: vague in, vague out.)

**GOOD prompt** → the log-triage schema, e.g.:
```
SUMMARY: Repeated failed SSH logins from 10.10.10.5 culminated in a successful admin login - a brute force that succeeded.
VERDICT: malicious
CONFIDENCE: high
INDICATORS: 10.10.10.5 (source), users admin/root/oracle/postgres, ~7 failures 03:11:02-03:11:07, success 03:11:41.
RECOMMENDED ACTION: Block 10.10.10.5, force-reset the admin credential, and hunt for post-login activity on web01.
```
Grading: all five fields present, verdict `malicious`, indicators cite the real IP/users/times.

---

## Lab 3.2 - an example *good* Sigma rule

This is a solid target after the class fixes the model's first draft. Note the explicit
count-threshold + same-source correlation the LLM usually forgets on the first try.

```yaml
title: SSH Brute Force Followed by Successful Login From Same Source
id: 6f3a1c9e-2b47-4d8a-9c11-7e2f4a1b90dd   # placeholder GUID - regenerate before deploy
status: experimental
description: >
  Detects more than 10 failed SSH authentications from a single source IP within a short
  window, followed by a successful login from that same IP - a strong brute-force-success signal.
author: SOC Bootcamp (AI draft, engineer-verified)
date: 2026/08/10
references:
  - https://attack.mitre.org/techniques/T1110/
logsource:
  product: linux
  service: auth            # assumes /var/log/auth.log via the sshd decoder; fields: message, src_ip
detection:
  failed:
    message|contains: 'Failed password'
  success:
    message|contains: 'Accepted password'
  timeframe: 60s
  condition: failed | count() by src_ip > 10 and success by src_ip
fields:
  - src_ip
  - user
falsepositives:
  - Legitimate users mistyping a password several times before succeeding
  - VPN reconnect storms or monitoring bots retrying from a shared egress IP
level: high
# NOTE: Sigma's aggregation/correlation support varies by backend. Validate with
# `sigma check` and confirm the target SIEM (Wazuh/Elastic) actually supports the
# count()/timeframe correlation before relying on it. AI drafts; engineer verifies.
```

**Validation talking points**
- Valid YAML (parses), has `title`/`logsource`/`detection`/`condition`/`level`.
- The correlation the model most often botches: tying failures **and** success to the **same**
  `src_ip`, plus the `> 10` threshold and `timeframe`. Make students find/add these.
- Would it fire on [../../datasets/auth.log](../../datasets/auth.log)? The dataset shows ~7
  failures then a success from `10.10.10.5`. With a `> 10` threshold it would **not** fire on this
  short sample - a great discussion: tune the threshold to your environment and test data.

**Offline mock** returns a minimal canned rule (`title: Example Detection`, a single
`message|contains: 'Failed password'` selection, `level: medium`). That's intentionally
*incomplete* - perfect raw material for the validation exercise.

---

## Lab 3.3 - example summary + IR report

**Alert summary** ([alert_summary.md](../../common/prompts/alert_summary.md) schema):
```
TITLE: SSH brute force succeeded against web01
WHAT_HAPPENED: Repeated failed SSH logins from 10.10.10.5 were followed by a successful login as admin on web01.
SEVERITY: high
AFFECTED_ASSET: web01 / 10.20.30.5
MITRE: T1110, T1110.001
NEXT_STEP: Isolate web01, reset the admin credential, and block 10.10.10.5 at the perimeter.
```
Grading: `SEVERITY: high` (rule.level 10 → high, per the rubric), MITRE IDs copied from the alert,
asset from `agent.name`/`agent.ip`. If a student's model says "critical," check whether they
handed it the rubric - if not, that's the lesson (principle #4).

**IR report** ([ir_report.md](../../common/prompts/ir_report.md) schema), abbreviated:
```
EXECUTIVE SUMMARY: On 2026-08-10 an external source (10.10.10.5) conducted a password-guessing
attack against the web01 server and obtained access to the "admin" account. The activity was
detected by Wazuh rule 5720. There is no evidence yet of follow-on data access; investigation
is ongoing.

TIMELINE:
- 03:11:02-03:11:07 UTC - Multiple failed SSH logins from 10.10.10.5 (users admin, root, oracle, postgres).
- 03:11:41 UTC - Successful SSH login as "admin" from 10.10.10.5.

TECHNICAL DETAILS: Wazuh rule 5720 (level 10) fired on web01 (10.20.30.5) after correlating
repeated authentication failures with a subsequent success from the same source IP. Mapped to
MITRE ATT&CK T1110 (Brute Force) / T1110.001 (Password Guessing).

IMPACT: A successful interactive login to the admin account occurred. No evidence of privilege
escalation, lateral movement, or data exfiltration is present in the provided evidence.

RECOMMENDATIONS:
1. Contain: isolate web01 and invalidate the admin session/credential.
2. Block 10.10.10.5 and check other hosts for the same source.
3. Enforce key-based SSH auth + fail2ban/rate limiting; disable password auth where possible.
4. Hunt for post-login persistence on web01 (cron, authorized_keys, new users).
```
Grading: **IMPACT must stay conservative** - the evidence proves a login only. Any claim of data
theft/exfiltration is an over-claim and fails the checkpoint (principle #2 / #5).

---

## Lab 3.4 - workflow output shape
```
[*] Source : local file (sample_alerts.json)  (2 alert(s))
[*] Model  : llama3.1:8b @ <host>   (available: llama3.1:8b)
[*] Prompt : alert_summary + VERDICT   temp=0.2

AI-ASSISTED TRIAGE TABLE
TITLE                                    | SEVERITY  | VERDICT     | NEXT_STEP
-----------------------------------------+-----------+-------------+------------------------
SSH brute force succeeded on web01       | high      | malicious   | Block 10.10.10.5, reset admin cred
SQL injection attempt against shop-nginx | critical  | malicious   | Block 10.10.10.7, review DB logs
```
Key facts to verify with the class: SQLi = level 12 → **critical**, brute force = level 10 →
**high**; both `malicious`; `NEXT_STEP` names the correct attacker IP. The columns are always
populated because [triage_workflow.py](../labs/triage_workflow.py) derives SEVERITY from
`rule.level` and falls back when the model omits a field (`parse_triage`).

---

## Challenge solutions

### Challenge 1 - JSON-only output
A prompt that reliably yields parseable JSON on the 8B model:
```
You are a SOC analyst assistant. Use ONLY the alert JSON below.
Output ONLY a single JSON object and nothing else - no markdown, no code fences, no commentary.
Use exactly these keys and value types:
{"title": string, "severity": "low"|"medium"|"high"|"critical", "verdict": "benign"|"suspicious"|"malicious", "mitre": [string], "next_step": string}
Map severity from rule.level (0-3 low, 4-7 medium, 8-11 high, 12-15 critical).

ALERT JSON:
<paste sample_alert.json>
```
Expected (parses with `json.loads` with zero edits):
```json
{"title": "SSH brute force succeeded on web01", "severity": "high", "verdict": "malicious", "mitre": ["T1110", "T1110.001"], "next_step": "Block 10.10.10.5 and reset the admin credential."}
```
Teaching points: (1) set temperature low; (2) forbid markdown/fences explicitly - the model's
favourite mistake is ```` ```json ````; (3) **always** wrap in `try/except json.JSONDecodeError`
in real code and re-prompt or strip fences on failure (see the fence-stripping in
[gen_sigma.py](../labs/gen_sigma.py) for the same defensive idea). Validate:
```
python3 -c "import json,sys; print(json.loads(sys.stdin.read()))"   # paste the model answer
```

### Challenge 2 - Add a MITRE field
Two implementations, and the point is *which to trust*:

1. **Deterministic (recommended)** - read it straight from the alert, model can't be wrong:
   ```python
   mitre = (alert.get("rule", {}).get("mitre", {}) or {}).get("id", []) or ["none listed"]
   ```
   Add `("MITRE", 18)` to `COLS` in [triage_workflow.py](../labs/triage_workflow.py) and populate
   the cell from that value.
2. **Model-driven** - add `- MITRE: list any rule.mitre.id present, else "none listed"` to the
   prompt and parse a `MITRE:` line with the existing `_field()` helper.

**Answer to "which do you trust more":** the deterministic read - the ground truth is *already in
the data* (principle #2, Ground). Use the model for the *narrative*, use the structured field
for facts the data already contains. Expected values: SSH alert → `T1110, T1110.001`; SQLi → `T1190`.

### Challenge 3 - Reduce false positives in the Sigma rule
Tightened `detection:` (the fix the class should arrive at):
```yaml
detection:
  failed:
    message|contains: 'Failed password'
  success:
    message|contains: 'Accepted password'
  timeframe: 60s
  condition: failed | count() by src_ip > 10 and success by src_ip
falsepositives:
  - User mistypes a password a few times, then logs in (below the >10 threshold)
  - VPN reconnect storms / monitoring bots retrying from a shared egress IP
  - Password-manager auto-fill retries after a rotation
level: high
```
What was traded away: a higher threshold + same-IP + time-window cuts false positives **but
raises false negatives** - a slow, distributed, or low-and-slow brute force (few attempts per IP,
spread over hours, or across many IPs) can now evade it. That trade-off (precision vs. recall) is
a *human* risk decision - exactly why principle #5 (Verify) and a tuning/test cycle exist. Good
answers also mention testing the tuned rule against both the attack sample and a benign baseline
before deploying.
