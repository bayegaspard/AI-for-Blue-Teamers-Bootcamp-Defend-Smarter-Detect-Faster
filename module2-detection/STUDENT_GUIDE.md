# Module 2 - Applied Detection (Student Guide)

Day 2, 2 hours. You detect real attacks three ways: in the Wazuh SIEM, with Python, and
with AI. You do not run the attacks yourself (you have no SSH to the boxes); your
instructor generates the telemetry, and you analyze it in the shared Wazuh
(https://10.50.136.116) and in the bundled datasets.

Two ideas for the day:
- Signature detection matches known-bad patterns (a SQL keyword, a scanner name). Fast
  and precise, blind to anything new.
- Behavior detection watches patterns over time (many failed logins from one host).
  Catches bursts that no single line reveals.

Common vectors you will see: brute force, SQL injection, path traversal, scanning.

Everything runs against the two shared boxes from `.env`. Confirm first:
```bash
python3 scripts/verify_env.py        # Wazuh API and Indexer should be green
```

---

## Lab 2.1 - See the telemetry

Open the Wazuh dashboard at https://10.50.136.116, go to Security events, and filter to
the last hour. Then pull the same alerts from the API:
```bash
python3 common/wazuh_client.py --alerts 30 --min-level 5
```
Expected: recent alerts print, most-severe first, for example SSH failed-password events
and, after a burst, the brute-force rule. If nothing appears yet, ask your instructor to
generate the telemetry (or use the datasets below, which mirror it).

Checkpoint: you can list real SIEM alerts from both the dashboard and the API.

---

## Lab 2.2 - Brute force up close

Analyze the bundled auth log:
```bash
python3 module2-detection/labs/detect_bruteforce.py
```
Expected output (abridged):
```
[FLAGGED] 10.10.10.5   failures: 6   usernames: admin, oracle, postgres, root
  * 10.10.10.5  THREAT INTEL MATCH -> Known SSH brute-force source [severity=high]
                !! SUCCESSFUL LOGIN -> account 'admin' authenticated after the failures (likely compromised)
```
The dangerous event is the one success hidden inside the failures. In the Wazuh
dashboard, the matching alerts are rules 5710 / 5712 (failed logins) and 100120 (the burst).

Checkpoint: you found the brute-force source and the login that succeeded.

---

## Lab 2.3 - Web attacks

Scan the bundled web access log:
```bash
python3 module2-detection/labs/detect_web_attacks.py
```
Expected: SQL injection and path traversal flagged from 10.10.10.7 (a scanner user-agent),
correlated to the threat feed. In Wazuh, the SQLi pattern is custom rule 100101.

Checkpoint: you identified the injection source and the signatures that caught it.

---

## Lab 2.4 - Correlate with threat intelligence

The detectors already cross-check flagged IPs against
[datasets/threat_intel.csv](../datasets/threat_intel.csv). Open it and confirm which
attackers are known-bad, and decide which to investigate first:
```bash
cat datasets/threat_intel.csv
```
Checkpoint: you can turn a list of IPs into a prioritized worklist using intel.

---

## Lab 2.5 - AI-assisted detection

Hand the attack logs to the shared GPU model for a fast summary:
```bash
python3 module1-foundations/labs/first_ai_triage.py datasets/auth.log
bash    module1-foundations/labs/ask_ai.sh "Summarize the web attacks in this log and name the source IP: $(cat datasets/access.log)"
```
Expected: a plain-language summary and a verdict. Always verify the AI against the raw
data; it is a co-pilot, not the decision-maker.

Checkpoint: you produced an AI summary and checked it against the evidence.

---

## Challenges

1. Find the exact line where the brute-force source logged in successfully.
2. Which two IPs in the logs appear in the threat feed, and at what severity?
3. Ask the AI for a one-paragraph incident summary, then correct one thing it got wrong
   or overstated.

---

## Optional: build your own attack lab at home (requires Docker)

If you want to generate the attacks yourself on your own machine, bring up the dockerized
targets and attacker, then run the attacks and re-analyze the logs:
```bash
scripts/lab_up.sh core targets attack        # needs Docker
docker exec -it soclab-attacker-1 bash
#   inside: /opt/attacks/attack_web_sqli.sh victim-web 8081
#           /opt/attacks/attack_ssh_bruteforce.sh victim-ssh labuser
```
At-home AI can point at the shared GPU (default) or the local mock. This is optional and
not required for the class.
