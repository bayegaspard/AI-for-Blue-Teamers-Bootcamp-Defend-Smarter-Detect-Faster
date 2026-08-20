# Module 2 — Applied Detection: Traffic Analysis & Threat Identification (Day 2)

**Instructor guide.** 2 hours. Blue-team, defensive, authorized training for Evolve Academy.

This day is the hands-on detection core of the bootcamp. Students *generate* real attack
telemetry against intentionally vulnerable targets, then *detect* it three ways: with a SIEM
(Wazuh), with small readable Python detectors, and finally with an AI assistant (Ollama) — the
bridge into Module 3.

> Every lab ships **two paths**:
> - **Real cyberlab** — the GPU VM + the Wazuh VM (dashboard, manager API, indexer).
> - **Portable / offline** — the self-contained Docker stack, runs on a laptop, no VPN/GPU.
>
> Teach whichever your room can reach. The learning objectives are identical.

---

## SoW mapping — what this module delivers

| SoW Module 2 bullet | Where it is taught | Student proof-of-skill |
|---|---|---|
| Traffic analysis & log monitoring | Labs 2.1–2.3 | Reads `auth.log` / `access.log`, watches live Wazuh alerts |
| Attack signatures & behavioral patterns | Lab 2.3 (signatures) + Lab 2.4 (behavioral/rate) | Explains signature vs. rate-based detection; runs both detectors |
| Correlating threat intel from multiple sources | Lab 2.4 | Matches source IPs against [`threat_intel.csv`](../datasets/threat_intel.csv) |
| Detecting common attack vectors (brute force & injection) | Labs 2.2 (SSH brute force), 2.3 (SQLi + web brute force) | Detects both from raw logs and from Wazuh rule IDs |

**Module outcome (say this out loud at the start and the end):** *by the end of Day 2 a student
can take a raw log, decide whether an attack occurred, name the attack, identify the source IP,
check that IP against a threat feed, and produce a one-paragraph triage summary — the day-to-day
job of a Tier-1 SOC analyst.*

---

## 2-hour timing (120 min)

| Time | Min | Segment | Instructor focus |
|---|---|---|---|
| 0:00–0:10 | 10 | **Intro & recap** | Recap Module 1 (AI + SOC basics). State objectives + SoW outcome. Signature vs. behavioral detection in one slide. |
| 0:10–0:25 | 15 | **Lab 2.1 — Stand up the range** | `scripts/lab_up.sh targets attack`; confirm services with `recon_nmap.sh`. Fix Docker/VPN issues here so later labs flow. |
| 0:25–0:45 | 20 | **Lab 2.2 — SSH brute force** | Run the attack; watch Wazuh rules 5710/5712/**100120** (real) or `docker logs` (offline). Emphasize "many failures/short window". |
| 0:45–1:05 | 20 | **Lab 2.3 — Web attacks** | SQLi auth-bypass (200 vs 401) + web brute force. Wazuh rule **100101**. Show the injection string *in the log*. |
| 1:05–1:10 | 5 | **Break** | — |
| 1:10–1:35 | 25 | **Lab 2.4 — Parse & correlate** | Students run [`detect_bruteforce.py`](labs/detect_bruteforce.py) + [`detect_web_attacks.py`](labs/detect_web_attacks.py); correlate IPs with the threat feed. Peak teaching moment: the *hidden successful login*. |
| 1:35–1:55 | 20 | **Lab 2.5 — AI-assisted detection** | Feed captured logs to Ollama with the [log-triage prompt](../common/prompts/log_triage.md). Compare AI output to their own findings. Bridge to Module 3. |
| 1:55–2:00 | 5 | **Wrap-up** | Review the 3 challenges, restate SoW outcome, preview Module 3 (prompt engineering for defense). |

---

## Prerequisites

**For students**
- Completed Module 1 (knows what Ollama/Wazuh are, has the repo cloned, `.env` in place).
- Comfortable in a terminal (cd, run a command, read output). No Python experience required —
  the detectors are copy-paste.

**Instructor pre-flight (do this BEFORE class — ~15 min)**
1. From the repo root, confirm the shared tooling is healthy:
   ```bash
   python3 common/ollama_client.py --health     # real GPU VM or mock
   python3 common/wazuh_client.py --health       # real path only
   ```
2. **Real cyberlab:** confirm the custom rules from [`docker/wazuh-agent/local_rules.xml`](../docker/wazuh-agent/local_rules.xml)
   are installed on the Wazuh manager (`100101` SQLi, `100120` SSH burst) and the agent on the
   target host is reporting. Verify with `/var/ossec/bin/wazuh-logtest` (paste a `Failed password` line).
3. **Portable/offline:** pre-build the stack so class time isn't spent on image pulls:
   ```bash
   scripts/lab_up.sh targets attack
   docker exec -it soclab-attacker-1 bash -lc 'ls /opt/attacks'
   ```
4. Dry-run both detectors against the shipped datasets (they must exit cleanly):
   ```bash
   python3 module2-detection/labs/detect_bruteforce.py
   python3 module2-detection/labs/detect_web_attacks.py
   ```
   Answer key with the exact expected output: [`solutions/README.md`](solutions/README.md).

---

## Setup summary (student-facing, one screen)

| | Real cyberlab | Portable / offline |
|---|---|---|
| Targets | Wazuh-monitored host on the range | `victim-web` (:8081), `victim-ssh` (:2222) |
| Attacker | Your kali/jump box | `soclab-attacker-1` container |
| SIEM | Wazuh dashboard `https://10.50.136.116` | `docker logs` + the Python detectors |
| Bring up | (already running) | `scripts/lab_up.sh targets attack` |
| AI model | GPU VM `llama3.1:8b` @ `10.50.142.235:11434` | `mock-ollama` container (deterministic) |

Full student walkthrough: **[`STUDENT_GUIDE.md`](STUDENT_GUIDE.md)**.

---

## Teaching notes (the points worth pausing on)

- **Signature vs. behavioral — the core mental model of the day.**
  - *Signature* detection (Lab 2.3, [`detect_web_attacks.py`](labs/detect_web_attacks.py) and Wazuh rule 100101) catches a *fixed string* — `UNION SELECT`, `../`. Cheap, precise, but blind to anything it hasn't seen.
  - *Behavioral / rate* detection (Lab 2.2/2.4, [`detect_bruteforce.py`](labs/detect_bruteforce.py) and Wazuh rule 100120) catches a *pattern of activity* — "8 failures in 60 seconds" — regardless of the exact password tried. Draw both on the board; every later module leans on this split.
- **The sliding window is the whole trick.** 20 failures over a week = a forgetful user; 20 in
  30 seconds = an attack. Wazuh's `frequency=8 timeframe=60` on rule 100120 and the `--window`/`--threshold`
  flags in `detect_bruteforce.py` are the *same idea*. Have students change `--threshold` and watch the verdict flip.
- **The "money" moment — the hidden success.** In [`auth.log`](../datasets/auth.log) the brute force
  from `10.10.10.5` ends with `Accepted password for admin`. Most students miss it. The detector calls it out
  explicitly (`!! SUCCESSFUL LOGIN`). This is *the* teaching beat: detection isn't done at "attack seen" —
  it's done at "did it work?". Ties directly to Challenge 1.
- **Threat intel turns "an IP" into "a known-bad IP".** Correlating against [`threat_intel.csv`](../datasets/threat_intel.csv)
  is what lets a Tier-1 analyst prioritize. Two of the attack IPs (`10.10.10.5`, `10.10.10.7`) are in the feed; make them find it (Challenge 2).
- **AI is an accelerant, not an oracle.** In Lab 2.5 the AI summary should *agree with* the evidence students
  already gathered by hand. Frame it as "the analyst is still accountable." On the mock model the verdict is
  deterministic (`malicious` for brute force/SQLi); on the real 8B model expect richer prose but the same verdict.
  This is the on-ramp to Module 3 (making the AI reliable) and Module 4 (when logs try to trick the AI).

---

## Common pitfalls & fixes

| Symptom | Cause | Fix |
|---|---|---|
| `lab_up.sh` hangs / image build slow | First-run image pulls | Pre-build in pre-flight; on the day, start it during the 0:00 intro. |
| Attacker script "command not found" | Not inside the container | `docker exec -it soclab-attacker-1 bash`, then `cd /opt/attacks`. |
| No Wazuh alerts appear | Agent not installed / rules not merged / wrong VM | Fall back to the **offline path** (`docker logs …` + detectors). Verify rules with `wazuh-logtest`. Don't lose the room debugging the SIEM — the objective is met either way. |
| Detector flags a `172.x` IP on live captures | `victim-web` logs the *attacker container's* internal IP, not a public one | Expected. Correlation against the curated feed is demonstrated on [`auth.log`](../datasets/auth.log); note the difference out loud. |
| `10.10.10.5` not flagged | `--threshold` set too high for the sample (only 6 failures) | Default threshold is 5. If a student raised it, reset: `--threshold 5 --window 120`. |
| `ollama_client.py` FAIL/timeout | GPU VM unreachable | Point `OLLAMA_HOST` at the mock in `.env` (`http://mock-ollama:11434` inside Docker, or `http://localhost:11434` from the host). |
| Python "file not found" for a log | Ran from the wrong dir | The detectors default to absolute repo paths; a custom path arg is resolved from the current directory. |

---

## Files in this module

- [`README.md`](README.md) — this instructor guide.
- [`STUDENT_GUIDE.md`](STUDENT_GUIDE.md) — the copy-paste student walkthrough (Labs 2.1–2.5 + challenges).
- [`labs/detect_bruteforce.py`](labs/detect_bruteforce.py) — rate/behavioral brute-force detector + threat-intel correlation.
- [`labs/detect_web_attacks.py`](labs/detect_web_attacks.py) — signature-based web-attack scanner.
- [`solutions/README.md`](solutions/README.md) — instructor answer key (expected alerts, rule IDs, the hidden login, malicious IPs, sample AI summaries, challenge answers).

**Shared assets referenced (do not edit from this module):**
[`common/ollama_client.py`](../common/ollama_client.py), [`common/wazuh_client.py`](../common/wazuh_client.py),
[`common/prompts/log_triage.md`](../common/prompts/log_triage.md),
[`common/prompts/threat_intel_correlation.md`](../common/prompts/threat_intel_correlation.md),
[`datasets/auth.log`](../datasets/auth.log), [`datasets/access.log`](../datasets/access.log),
[`datasets/threat_intel.csv`](../datasets/threat_intel.csv), [`scripts/lab_up.sh`](../scripts/lab_up.sh),
[`docker/wazuh-agent/local_rules.xml`](../docker/wazuh-agent/local_rules.xml).
