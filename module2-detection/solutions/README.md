# Module 2 - Instructor Answer Key and Solutions

Private to instructors. Expected outputs are reproduced from the shipped datasets, so
they are identical every run.

## Key facts

- Brute-force source: 10.10.10.5 (Wazuh rules 5710 / 5712, burst rule 100120). A
  successful `admin` login follows the failures at 03:11:41 in datasets/auth.log
  (line 9) - treat that account as compromised.
- Web attack source: 10.10.10.7 - SQL injection and path traversal (custom rule 100101),
  scanner user-agent sqlmap.
- Threat feed matches (datasets/threat_intel.csv): 10.10.10.5 (high), 10.10.10.7 (high),
  10.10.10.11 (medium).

## Expected detector output

```bash
python3 module2-detection/labs/detect_bruteforce.py    # flags 10.10.10.5, threat-intel match, hidden success
python3 module2-detection/labs/detect_web_attacks.py   # flags SQLi + traversal from 10.10.10.7
```

## Challenge answers

1. `Aug 10 03:11:41 web01 sshd[2101]: Accepted password for admin from 10.10.10.5 ...`
2. 10.10.10.5 (high) and 10.10.10.7 (high); 10.10.10.11 is medium.
3. Any accurate one-paragraph summary; the teaching point is that the student catches an
   AI overstatement or missing detail on review.

## Instructor: how to generate the telemetry students analyze

Students have no SSH to the boxes, so you populate the shared Wazuh. Two simple options:

1. Self-monitored manager (simplest, no Docker): the Wazuh all-in-one monitors its own
   host, so an SSH brute force against the Wazuh VM's own sshd raises 5710 / 5712 and,
   past the threshold, 100120. Use the bundled helper from any Linux box that can reach
   the target:
   ```bash
   sudo apt-get install -y sshpass                      # one-time
   bash scripts/generate_wazuh_telemetry.sh 10.50.136.116
   python3 common/wazuh_client.py --alerts 30 --min-level 5   # confirm they landed
   ```
2. Enrolled endpoint: enroll a Wazuh agent on a disposable Linux endpoint (or the GPU
   VM), point it at 10.50.136.116 (see docker/wazuh-agent/README.md), then run the same
   helper with a web port to also send SQLi/traversal:
   `bash scripts/generate_wazuh_telemetry.sh <endpoint-ip> 8081`.

Load the custom rules on the manager first (SETUP.md): local_rules.xml adds 100101,
100110, 100120. After generating attacks, students will see them in Lab 2.1.
