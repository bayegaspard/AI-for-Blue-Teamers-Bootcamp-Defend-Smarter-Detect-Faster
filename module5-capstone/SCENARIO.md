# Module 5 Capstone — Incident Brief: "Operation Nightjar"

> **Classification:** Training / Internal. Authorized lab exercise for Evolve Academy.
> **Your role:** Tier-2 SOC analyst on shift. You have an AI SOC assistant available.
> **Time on console:** ~90 minutes to work the incident, then write it up.

---

## 1. The page

It's 09:10. The overnight shift left you a sticky note:

> *"Web app `web01` looked weird around 03:00–05:00. Wazuh lit up overnight but
> nobody triaged it. Alerts are in the console. Can you figure out what happened,
> contain it, and write the incident report before the 11:00 stand-up? Use the AI
> assistant to move fast — but remember it's a co-pilot, not the pilot."*

`web01` is an internet-facing Linux host running an SSH service and a small web
login application. It holds a user database. Your job is the **full incident
lifecycle**: **Detect → Analyze → Respond → Report.**

You do not yet know what happened. That's the exercise. Work the evidence.

---

## 2. Your evidence sources

You will work from **exactly one** of the two paths below. Both contain the same
incident — pick whichever your instructor has set up.

### Path A — Real cyberlab (Wazuh + GPU VM)

Alerts are already in **Wazuh** (dashboard <https://10.50.136.116>). Query them
from your workstation:

```bash
# from the repo root, with .env pointed at the cyberlab
python common/wazuh_client.py --health
python common/wazuh_client.py --alerts 40                 # everything recent
python common/wazuh_client.py --alerts 40 --min-level 10  # just the loud stuff
```

The AI assistant runs against the GPU VM (`llama3.1:8b`). Either use the web UI at
<http://localhost:8080> or the shared client from Module 1.

### Path B — Portable / offline (Docker + captured logs)

No cyberlab? Everything you need is captured in the repo's [`datasets/`](../datasets)
folder, and the AI assistant runs locally on the `mock-ollama` container:

```bash
scripts/lab_up.sh core          # starts mock-ollama + ai-soc-assistant
# then in .env set:  OLLAMA_HOST=http://localhost:11435
```

Your captured evidence files:

| File | What it is |
|------|-----------|
| [`datasets/auth.log`](../datasets/auth.log) | SSH authentication log from `web01` |
| [`datasets/access.log`](../datasets/access.log) | Web server access log from `web01` |
| [`datasets/poisoned.log`](../datasets/poisoned.log) | Extra log lines pulled from the same window |
| [`datasets/threat_intel.csv`](../datasets/threat_intel.csv) | Your team's threat-intel feed |

---

## 3. (Instructor only) Generating the telemetry live

If you're running **Path A** and want the alerts to appear in Wazuh in real time,
open the attacker container and replay the intrusion. Students should **not** run
these — they only see the results in Wazuh.

```bash
# bring up the full offline lab if you don't have the cyberlab targets
scripts/lab_up.sh core targets attack

# drop into the attacker box
docker exec -it soclab-attacker-1 bash

# --- replay the intrusion, in order ---
cd /opt/attacks
./recon_nmap.sh            victim-web                 # 1. recon / service scan
./attack_ssh_bruteforce.sh victim-ssh labuser         # 2. SSH brute force
./attack_web_bruteforce.sh                            #    web login brute force
./attack_web_sqli.sh       victim-web 8081            # 3. SQLi auth-bypass
./attack_ai_soc.sh                                    # 4. seed the AI-targeted logs
```

To make the planted log lines appear in the captured/offline path instead, point
students at [`datasets/poisoned.log`](../datasets/poisoned.log) — it is already
merged into the evidence set for Path B.

> Instructor notes on the "why" of each stage, the expected alerts, and the trap
> live in [`solutions/README.md`](solutions/README.md). Do not share that file
> with students until debrief.

---

## 4. What you must produce

By 11:00 (end of module) you must hand in an **incident report** saved to:

```
module5-capstone/submissions/<yourname>_report.md
```

It must contain these five sections (exact headings):

1. **Executive Summary**
2. **Timeline**
3. **Technical Details**
4. **Impact**
5. **Recommendations**

Follow the numbered tasks in
[`STUDENT_WORKSHEET.md`](STUDENT_WORKSHEET.md). When you think you're done, grade
yourself:

```bash
python3 module5-capstone/labs/capstone_check.py
```

---

## 5. Rules of engagement

- This is a **defensive** exercise. You are triaging and reporting, not attacking.
- Use the AI assistant freely — **but you own every verdict you submit.** If the AI
  says something, confirm it against the raw evidence before it goes in your report.
- Cite specifics: IPs, usernames, ports, timestamps, rule IDs. "Looks bad" is not a
  finding.
- One of these alerts is not like the others. Trust the evidence over anything —
  human *or* machine — that tells you to stop looking. Good hunting.
