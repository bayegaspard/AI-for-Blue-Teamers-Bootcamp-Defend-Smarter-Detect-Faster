# Start Here

New to this package? You are in the right place. This page tells you exactly what to
run first and links every lab in order. Total course: 5 days, 2 hours per day.

---

## Step 1 - Get the code and open a terminal in it

Clone the repository (or unzip the archive your instructor shared), then move into the
folder it creates. The repo root is the folder that contains `common/`, `datasets/`,
`scripts/`, and the `module1..5` folders.

```bash
git clone <REPO_URL>
cd <the-folder-that-was-created>    # then run everything from here
```

## Step 2 - Create your config file (once)

```bash
cp .env.example .env
```

- On the **real cyberlab**, open `.env` and set `WAZUH_PASS` to the Wazuh password
  (the VM IP addresses are already filled in).
- On **any laptop / offline**, you do not need to edit anything yet. See Step 3b.

## Step 3 - Check your environment

```bash
python3 scripts/verify_env.py
```

- If both checks say `PASS`, you are ready. Go to Step 4.
- If you see `FAIL` (no VPN, or you are on a laptop), use the offline path in Step 3b.

### Step 3b - Offline path (no GPU, no VPN)

Bring up the local stand-in stack, then point your config at it:

```bash
scripts/lab_up.sh core
```
Then edit `.env` and set these two lines (the defaults point at the cyberlab GPU VM,
so offline you switch both to the local mock):
```
OLLAMA_HOST=http://localhost:11435
AI_SOC_OLLAMA_HOST=http://mock-ollama:11434
```
Now `python3 scripts/verify_env.py` will pass for Ollama, and the AI SOC assistant is
live at http://localhost:8080. (Wazuh stays offline on this path; the labs give you a
dataset-based way to do everything that would use Wazuh.)

> Want to run your own real Ollama (not the mock) and reach it over your network or
> VPN in your own time? See [SELF_HOSTING_OLLAMA.md](SELF_HOSTING_OLLAMA.md).

## Step 4 - Start Lab 1

Open the Day 1 student guide and follow it top to bottom:

**[module1-foundations/STUDENT_GUIDE.md](module1-foundations/STUDENT_GUIDE.md)**  <-- begin here

That guide starts at Lab 1.1 (environment check) and walks you through your first
AI-assisted log triage. Each later day works the same way: open that module's
`STUDENT_GUIDE.md` and follow it.

---

## The whole course at a glance

Work through the days in order. For each module, students use the `STUDENT_GUIDE`;
instructors use the `README`.

### Day 1 - Foundations  ([guide](module1-foundations/STUDENT_GUIDE.md) · [instructor](module1-foundations/README.md) · [slides](slides/Module1_Foundations.pptx))
| Lab | What you do |
|-----|-------------|
| 1.1 | Environment check: confirm Ollama, Wazuh, and the GPU are reachable |
| 1.2 | Your first AI conversation for security |
| 1.3 | AI-assisted log triage of `datasets/auth.log` |
| 1.4 | Tour the Wazuh SIEM and pull alerts from the API |

### Day 2 - Applied Detection  ([guide](module2-detection/STUDENT_GUIDE.md) · [instructor](module2-detection/README.md) · [slides](slides/Module2_Detection.pptx))
| Lab | What you do |
|-----|-------------|
| 2.1 | Bring up the victim targets and the attacker toolbox |
| 2.2 | Run an SSH brute force and see the Wazuh alerts it raises |
| 2.3 | Run web SQL injection and a login brute force |
| 2.4 | Parse the logs and correlate attacking IPs with threat intel |
| 2.5 | Hand the attack logs to AI for a fast summary |

### Day 3 - Prompt Engineering  ([guide](module3-prompt-engineering/STUDENT_GUIDE.md) · [instructor](module3-prompt-engineering/README.md) · [slides](slides/Module3_Prompt_Engineering.pptx))
| Lab | What you do |
|-----|-------------|
| 3.1 | Prompt fundamentals: the six principles |
| 3.2 | Generate a Sigma detection rule with AI |
| 3.3 | Automate an incident summary and a report |
| 3.4 | Build an AI-assisted triage workflow |

### Day 4 - AI Red Teaming  ([guide](module4-red-teaming/STUDENT_GUIDE.md) · [instructor](module4-red-teaming/README.md) · [slides](slides/Module4_Red_Teaming.pptx))
| Lab | What you do |
|-----|-------------|
| 4.1 | Direct prompt injection: flip an AI verdict |
| 4.2 | Extract the system prompt and try a jailbreak |
| 4.3 | Indirect injection through a poisoned log (the headline lab) |
| 4.4 | Defense in depth, plus detecting injection with Wazuh |
| 4.5 | The mitigation checklist |

### Day 5 - Capstone  ([scenario](module5-capstone/SCENARIO.md) · [worksheet](module5-capstone/STUDENT_WORKSHEET.md) · [instructor](module5-capstone/README.md) · [slides](slides/Module5_Capstone.pptx))
| Stage | What you do |
|-------|-------------|
| Detect | Find the multi-stage attack in Wazuh or the datasets |
| Analyze | Triage with AI, and verify what it tells you |
| Respond | Contain the attack and correlate with threat intel |
| Report | Draft the incident report with AI |
| Adversarial | Catch and resist the prompt-injection trap |

---

## If something breaks

- Re-run `python3 scripts/verify_env.py` to see what is unreachable.
- Full setup, both paths, and a troubleshooting table: **[SETUP.md](SETUP.md)**.
- Running the whole week as an instructor: **[INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md)**.
- Stop the lab: `scripts/lab_down.sh`   ·   Reset everything: `scripts/teardown.sh`

## Handy commands (the student path, no Docker)

| Do this | Command |
|---------|---------|
| Check the two shared boxes | `python3 scripts/verify_env.py` |
| First AI log triage (Module 1) | `python3 module1-foundations/labs/first_ai_triage.py datasets/auth.log` |
| Pull live Wazuh alerts (Module 2) | `python3 common/wazuh_client.py --alerts 20 --min-level 5` |
| Run a prompt-injection test (Module 4) | `python3 module4-red-teaming/labs/inject.py --payload verdict-flip --mode vulnerable` |

Optional at-home extras (require Docker): `bash scripts/smoke_test.sh` (offline proof),
`scripts/lab_up.sh core targets attack` (your own victims + attacker), and the web
assistant at http://localhost:8080.
