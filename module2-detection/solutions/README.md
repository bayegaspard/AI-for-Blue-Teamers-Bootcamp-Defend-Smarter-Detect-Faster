# Module 2 — Instructor Answer Key & Solutions

Private to instructors. Contains expected outputs, rule IDs, the hidden successful login, the
malicious IPs, sample AI summaries, and full challenge answers. All outputs below are reproduced
from the shipped sample datasets, so they are identical every run.

Quick way to regenerate everything:
```bash
cd path/to/repo
python3 module2-detection/labs/detect_bruteforce.py     # exit code 2 = something flagged
python3 module2-detection/labs/detect_web_attacks.py    # exit code 2 = something flagged
```

---

## Lab 2.1 — Expected

- **Offline:** `curl http://localhost:8081/health` → `ok`; `recon_nmap.sh victim-web` shows `8081/tcp open http`.
- **Real:** `wazuh_client.py --health` prints `[OK] Wazuh manager 4.14.x ...`; `--agents` lists at least one `active` agent.

---

## Lab 2.2 — SSH brute force: expected alerts / rule IDs

| Path | What proves detection |
|---|---|
| 🟦 Real (Wazuh) | **5710** = attempt to login using a non-existent user; **5712** = SSHD brute force (many failures fast); **5720** = multiple failed logins from same source; **100120** (custom, level 12) = *"SSH brute force burst (>=8 failures/60s) from one source"* from [`local_rules.xml`](../../docker/wazuh-agent/local_rules.xml). |
| 🟩 Offline | `docker logs soclab-victim-ssh-1` shows a wall of `Failed password for labuser from <172.x> ...` then one `Accepted password ...`. Hydra reports `password: Password1`. |

Teaching point: detection here is **behavioral** (rate of failures), not a single signature. That's
why the custom rule uses `frequency=8 timeframe=60` with `<same_source_ip/>`.

---

## Lab 2.3 — Web attacks: expected behavior / rule IDs

- **SQLi auth bypass:** baseline `admin/wrongpass` → **HTTP 401**; `password=' OR '1'='1` → **HTTP 200**
  (`Welcome, authenticated user!`). The `401 → 200` flip is the demonstrable bypass. Root cause: the app
  builds SQL with string formatting (`docker/victim-web/app.py`), so `' OR '1'='1` makes the WHERE clause always true.
- **Web brute force:** repeated `Failed password for admin from <172.x> port 0 http` in `docker logs soclab-victim-web-1`.
- 🟦 Real (Wazuh): SQLi trips custom rule **100101** (level 12) — *"SQL injection pattern in web traffic"*
  (matches `UNION SELECT | ' OR '1'='1 | OR 1=1 | information_schema | sqlmap`). Path traversal would trip **100100**.

---

## Lab 2.4 — Parse & correlate: canonical output

### `detect_bruteforce.py` (default: [`datasets/auth.log`](../../datasets/auth.log))

```
[FLAGGED] 10.10.10.5
    failures (total)     : 6
    worst burst in 120s : 6
    usernames targeted   : admin, oracle, postgres, root

  * 10.10.10.5
      THREAT INTEL MATCH  -> Known SSH brute-force source (internal threat feed) [severity=high]
      !! SUCCESSFUL LOGIN -> account 'admin' authenticated from this IP after the failures (likely compromised).

  SUMMARY: 1 IP(s) flagged, 1 confirmed by threat intel, 1 with a successful login.
```
Exit code **2** (flagged). The 6 failures are `auth.log` lines 3–8 (03:11:02–03:11:07); the success is line 9 (03:11:41).

### `detect_web_attacks.py` (default: [`datasets/access.log`](../../datasets/access.log))

```
[HIT] line 3  src=10.10.10.7  status=200  -> SQLi: tautology (OR 1=1), Scanner tool user-agent
[HIT] line 4  src=10.10.10.7  status=200  -> SQLi: UNION SELECT, SQLi: inline comment (--), Scanner tool user-agent
[HIT] line 5  src=10.10.10.7  status=404  -> Path traversal (../), Sensitive file access (/etc/passwd)

  3 malicious request(s) from 1 source IP(s):
    10.10.10.7   3 request(s)  <-- THREAT INTEL: Automated SQLi scanner (sqlmap) observed [severity=high]
```
Exit code **2**. Clean lines (1, 2, 6) are ignored.

---

## Lab 2.5 — Sample AI summaries

The offline **mock-ollama** is deterministic (rule-based), so these are exact. The real `llama3.1:8b`
gives richer prose but the **same verdicts**.

**auth.log → brute force:**
```
SUMMARY: Repeated failed SSH authentications from a single source indicate a brute-force attempt.
VERDICT: malicious
CONFIDENCE: high
INDICATORS: multiple 'Failed password' events, same source IP, short time window.
RECOMMENDED ACTION: block the source IP, confirm no successful login followed, review the target account.
```

**access.log → SQL injection:**
```
SUMMARY: Web request contains SQL injection syntax targeting the login/query path.
VERDICT: malicious
CONFIDENCE: high
INDICATORS: SQL meta-characters / UNION SELECT / tautology in request parameters.
RECOMMENDED ACTION: block the source, check DB logs for data access, patch input validation.
```

Discussion beat: the mock's brute-force action even says *"confirm no successful login followed"* —
which is exactly the thing students found in Lab 2.4 that the AI **did not** surface on its own. Use
this to reinforce: **AI accelerates triage; the analyst confirms against the evidence.**

---

## Challenge answers

### Challenge 1 — The hidden successful login
**Answer:** [`datasets/auth.log`](../../datasets/auth.log) **line 9**:
```
Aug 10 03:11:41 web01 sshd[2101]: Accepted password for admin from 10.10.10.5 port 51200 ssh2
```
Account **`admin`**, at **03:11:41**, from **10.10.10.5** — the *same IP* that produced the 6 failures
at 03:11:02–03:11:07. It's more urgent than the failures because a failed brute force is a *nuisance*;
a **successful** one is a **compromise** — the attacker now has valid credentials.

Watch for the trap: `grep "Accepted password"` returns **two** lines. Line 2 (`analyst` from
`10.20.30.9`) is a *legitimate* internal login — that source never brute-forced anything and isn't in
the threat feed. The compromise is only line 9, because its source IP is the attacking IP. Correlating
"who succeeded" with "who was attacking" is the whole point.

### Challenge 2 — Attacking IPs vs. the threat feed
| Source IP | Seen in | In [`threat_intel.csv`](../../datasets/threat_intel.csv)? | Feed says |
|---|---|---|---|
| **10.10.10.5** | SSH brute force (auth.log) | ✅ yes | Known SSH brute-force source (internal threat feed) — **high** |
| **10.10.10.7** | Web SQLi + traversal (access.log) | ✅ yes | Automated SQLi scanner (sqlmap) observed — **high** |

Both attacking IPs are confirmed known-bad by the feed. (The feed also lists `10.10.10.11`
credential-stuffing, `198.51.100.23` C2, `evil-update[.]com`, and a sample hash — not seen in *these*
logs, but they're the "multiple sources" the students correlate against, and `10.10.10.11` returns in Module 4.)

### Challenge 3 — Tuning the detector
The sample has **6 failures within ~5 seconds** from `10.10.10.5`.

- **Misses it:** `--threshold 7` (or any threshold > 6). Verified output:
  ```
  [ok] 10.10.10.5   ...   No IP exceeded the threshold.
  SUMMARY: 0 IP(s) flagged, ...
  ```
- **Catches it:** `--threshold 5` (the default) or anything ≤ 6:
  ```
  [FLAGGED] 10.10.10.5   ...   SUMMARY: 1 IP(s) flagged, 1 confirmed by threat intel, 1 with a successful login.
  ```

One-sentence risk: **too high** a threshold ⇒ real attacks slip past undetected (false negatives);
**too low** ⇒ ordinary fat-finger logins page the analyst at 3 a.m. (false-positive fatigue). Real
tuning (e.g. Wazuh rule `100120`'s `8 / 60s`) is the deliberate middle ground.

---

## Grading rubric (quick)

A student has met the **SoW Module 2 outcome** if they can, unaided:
1. Point to evidence of the SSH brute force **and** the web SQLi (SIEM alert or log lines). *(traffic analysis / attack vectors)*
2. Explain signature vs. behavioral detection with one example of each from today. *(signatures & behavioral patterns)*
3. Name both attacking IPs and confirm them against the threat feed. *(threat-intel correlation)*
4. Identify the hidden successful login and say why it's the top priority. *(judgment)*
5. Produce an AI triage summary and state whether they trust it and why. *(AI-assisted detection → Module 3)*
