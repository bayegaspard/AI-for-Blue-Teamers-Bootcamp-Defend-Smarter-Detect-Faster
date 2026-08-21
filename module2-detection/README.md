# Module 2 - Applied Detection: Traffic Analysis and Threat Identification (Day 2)

**Instructor guide.** 2 hours. Blue-team, defensive, authorized training.

This is the hands-on detection core. Because students have no SSH to the boxes, they do
not run attacks - **you generate the telemetry once into the shared Wazuh**, and students
detect it three ways: with the SIEM (Wazuh dashboard + API), with small readable Python
detectors over the bundled datasets, and with the AI model (the bridge into Module 3). No
Docker on student machines.

---

## Module objectives - what this module delivers

| Objective | Where it is taught | Student proof-of-skill |
|---|---|---|
| Traffic analysis & log monitoring | Labs 2.1-2.3 | Reads Wazuh alerts and `auth.log` / `access.log` |
| Attack signatures & behavioral patterns | Lab 2.3 (signatures) + Lab 2.2 (behavioral/rate) | Explains signature vs. rate-based detection; runs both detectors |
| Correlating threat intel from multiple sources | Lab 2.4 | Matches source IPs against [`threat_intel.csv`](../datasets/threat_intel.csv) |
| Detecting common attack vectors (brute force & injection) | Labs 2.2, 2.3 | Detects both from raw logs and by Wazuh rule IDs |

**Module outcome:** by the end of Day 2 a student can take a log, decide whether an attack
occurred, name it, identify the source IP, check that IP against a threat feed, and produce
a one-paragraph triage - the day-to-day job of a Tier-1 SOC analyst.

---

## 2-hour timing (120 min)

| Time | Min | Segment | Instructor focus |
|---|---|---|---|
| 0:00-0:10 | 10 | **Intro & recap** | Recap Module 1. Signature vs. behavioral detection in one slide. |
| 0:10-0:25 | 15 | **Lab 2.1 - See the telemetry** | Students pull the alerts you generated: dashboard + `wazuh_client.py --alerts`. |
| 0:25-0:45 | 20 | **Lab 2.2 - Brute force** | `detect_bruteforce.py`; the hidden successful login; Wazuh 5710/5712/**100120**. |
| 0:45-1:05 | 20 | **Lab 2.3 - Web attacks** | `detect_web_attacks.py`; SQLi/traversal from 10.10.10.7; Wazuh rule **100101**. |
| 1:05-1:10 | 5 | **Break** | - |
| 1:10-1:35 | 25 | **Lab 2.4 - Correlate** | Match IPs against the threat feed; prioritize. |
| 1:35-1:55 | 20 | **Lab 2.5 - AI-assisted detection** | Feed the logs to the model; verify the AI. Bridge to Module 3. |
| 1:55-2:00 | 5 | **Wrap-up** | Review the 3 challenges, restate the outcome, preview Module 3. |

---

## Instructor pre-flight (before class)

1. Confirm the shared tooling is healthy from any student VM:
   ```bash
   python3 scripts/verify_env.py        # Ollama + Wazuh green
   ```
2. Confirm the custom rules are loaded on the Wazuh manager (`100101` SQLi, `100120` SSH
   burst) - see [`docker/wazuh-agent/local_rules.xml`](../docker/wazuh-agent/local_rules.xml)
   and SETUP.md. Test with `/var/ossec/bin/wazuh-logtest`.
3. **Generate the telemetry** so students have live alerts to find (no Docker):
   ```bash
   sudo apt-get install -y sshpass
   bash scripts/generate_wazuh_telemetry.sh 10.50.136.116      # brute-forces the self-monitored Wazuh sshd
   python3 common/wazuh_client.py --alerts 30 --min-level 5    # confirm they landed
   ```
   (The Wazuh all-in-one self-monitors, so attacking its own sshd raises 5710/5712/100120.
   For a monitored web endpoint, add a web port to also send SQLi: see the script header.)
4. Dry-run both detectors against the datasets (they must exit cleanly):
   ```bash
   python3 module2-detection/labs/detect_bruteforce.py
   python3 module2-detection/labs/detect_web_attacks.py
   ```
   Answer key: [`solutions/README.md`](solutions/README.md).

---

## What students touch (no Docker)

| | Shared boxes (over the VPN) |
|---|---|
| SIEM | Wazuh dashboard `https://10.50.136.116` + `wazuh_client.py --alerts` |
| Evidence | the bundled [`datasets/`](../datasets/) (auth.log, access.log, threat_intel.csv) |
| Detectors | `detect_bruteforce.py`, `detect_web_attacks.py` |
| AI model | GPU VM `llama3.1:8b` @ `10.50.142.235:11434` |

Full student walkthrough: **[`STUDENT_GUIDE.md`](STUDENT_GUIDE.md)**.

---

## Teaching notes (the points worth pausing on)

- **Signature vs. behavioral - the core mental model of the day.** Signature detection
  (`detect_web_attacks.py`, Wazuh 100101) catches a fixed string (`UNION SELECT`, `../`):
  cheap, precise, blind to the new. Behavioral/rate detection (`detect_bruteforce.py`,
  Wazuh 100120) catches a pattern ("8 failures in 60 seconds") regardless of the exact
  password. Draw both; every later module leans on this split.
- **The sliding window is the whole trick.** 20 failures over a week is a forgetful user;
  20 in 30 seconds is an attack. Wazuh `frequency=8 timeframe=60` on 100120 and the
  `--window`/`--threshold` flags in `detect_bruteforce.py` are the same idea.
- **The "money" moment - the hidden success.** In [`auth.log`](../datasets/auth.log) the
  brute force from `10.10.10.5` ends with `Accepted password for admin`. Most students miss
  it; the detector calls it out (`!! SUCCESSFUL LOGIN`). Detection isn't done at "attack
  seen", it's done at "did it work?". Ties to Challenge 1.
- **Threat intel turns "an IP" into "a known-bad IP".** Two attack IPs (`10.10.10.5`,
  `10.10.10.7`) are in [`threat_intel.csv`](../datasets/threat_intel.csv); make them find it.
- **AI is an accelerant, not an oracle.** In Lab 2.5 the AI summary should agree with what
  students already found by hand. The analyst is still accountable. On-ramp to Module 3
  (making the AI reliable) and Module 4 (when logs try to trick the AI).

---

## Common pitfalls & fixes

| Symptom | Fix |
|---|---|
| No alerts in Lab 2.1 | Re-run `generate_wazuh_telemetry.sh` against a monitored target; confirm the custom rules loaded (`wazuh-logtest`). Students can still do 2.2-2.5 from the datasets. |
| `wazuh_client.py --alerts` empty but `--health` OK | The indexer (9200) is not reachable; open it to the student subnet (SETUP.md). Not required - the datasets cover the same findings. |
| `10.10.10.5` not flagged by the detector | `--threshold` set too high. Default is 5: `--threshold 5 --window 120`. |
| `ollama_client.py` slow on first call | The model loads on first use, then stays warm; the client waits up to 300s. |
| Python "file not found" for a log | Run from the repo root; the detectors default to the bundled datasets. |

---

## Files in this module

- [`README.md`](README.md) - this instructor guide.
- [`STUDENT_GUIDE.md`](STUDENT_GUIDE.md) - the student walkthrough (Labs 2.1-2.5 + challenges).
- [`labs/detect_bruteforce.py`](labs/detect_bruteforce.py) - rate/behavioral brute-force detector + threat-intel correlation.
- [`labs/detect_web_attacks.py`](labs/detect_web_attacks.py) - signature-based web-attack scanner.
- [`solutions/README.md`](solutions/README.md) - answer key + how to generate the telemetry.

**Shared assets (do not edit from this module):**
[`common/wazuh_client.py`](../common/wazuh_client.py),
[`common/prompts/log_triage.md`](../common/prompts/log_triage.md),
[`datasets/auth.log`](../datasets/auth.log), [`datasets/access.log`](../datasets/access.log),
[`datasets/threat_intel.csv`](../datasets/threat_intel.csv),
[`scripts/generate_wazuh_telemetry.sh`](../scripts/generate_wazuh_telemetry.sh),
[`docker/wazuh-agent/local_rules.xml`](../docker/wazuh-agent/local_rules.xml).
