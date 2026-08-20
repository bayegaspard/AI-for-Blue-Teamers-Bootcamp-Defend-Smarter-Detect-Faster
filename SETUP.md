# Setup Guide

This lab package runs in two environments from the same code. Pick the one you need;
both are supported by every module.

---

## Prerequisites

| | Cyberlab path | Portable path |
|---|---|---|
| Docker + Docker Compose v2 | on student/attacker hosts (optional) | **required** |
| Python 3.9+ | required (for the CLI helpers) | required |
| Network | VPN into the cyberlab subnet | none |
| GPU | provided (Tesla T4 on the GPU VM) | not needed (mock LLM) |

Install the (light) Python deps once:
```bash
python3 -m pip install -r common/requirements.txt
```
> The `ollama_client` and `wazuh_client` use only the Python standard library, so they work
> even without the pip install. `python-dotenv`, `rich`, and `tabulate` just make output nicer.

---

## 1. Configure `.env`

```bash
cp .env.example .env
```

Then edit the values. The important ones:

| Variable | Cyberlab value | Portable value |
|----------|----------------|----------------|
| `OLLAMA_HOST` | `http://10.50.142.235:11434` | `http://localhost:11435` (after `lab_up.sh core`) |
| `OLLAMA_MODEL` | `llama3.1:8b` | `llama3.1:8b` |
| `WAZUH_API` | `https://10.50.136.116:55000` | (leave as-is; unused offline) |
| `WAZUH_USER` / `WAZUH_PASS` | real creds from install | (unused offline) |
| `WAZUH_INDEXER` | `https://10.50.136.116:9200` | (unused offline) |
| `AI_SOC_MODE` | `vulnerable` | `vulnerable` |

`VERIFY_TLS=0` is set because the lab Wazuh uses self-signed certs. **Never** disable TLS
verification in production.

---

## 2A. Cyberlab path — verify the real services

```bash
python3 scripts/verify_env.py
```
Expected:
```
[PASS] Ollama   reachable at http://10.50.142.235:11434 — models: llama3.1:8b
[PASS] Wazuh    manager 4.14.x reachable at https://10.50.136.116:55000
```

If Ollama fails: on the GPU VM confirm `nvidia-smi` shows the Tesla T4 and
`systemctl status ollama` is active and listening on `0.0.0.0:11434`.

If Wazuh fails: confirm `WAZUH_PASS` is the password saved at install time and that
`https://10.50.136.116` loads the dashboard.

### Load the custom detection rules (recommended)
On the Wazuh manager (`10.50.136.116`):
```bash
sudo cp docker/wazuh-agent/local_rules.xml /var/ossec/etc/rules/local_rules.xml   # merge if present
sudo systemctl restart wazuh-manager
```
These add SQLi detection (100101), an SSH brute-force burst rule (100120), and a
**prompt-injection-in-logs** rule (100110) used in Module 4. See
[docker/wazuh-agent/README.md](docker/wazuh-agent/README.md) for enrolling endpoints.

---

## 2B. Portable path — bring up the Docker lab

```bash
# Smoke-test the AI pipeline end to end (no GPU/VPN):
bash scripts/smoke_test.sh          # expect 4/4 PASS

# Start what a module needs (profiles):
scripts/lab_up.sh core              # mock-ollama + ai-soc-assistant   (Modules 1,3,4,5)
scripts/lab_up.sh core targets attack   # + victims + attacker         (Modules 2,5)
scripts/lab_up.sh logs              # synthetic log generator -> datasets/generated/
```

To point the CLI helpers at the local mock, set in `.env`:
```
OLLAMA_HOST=http://localhost:11435
```
Then `python3 common/ollama_client.py --health` should list `llama3.1:8b` (served by the mock).

Service map (host ports default from `.env`):

| Service | URL / access | Profile |
|---------|--------------|---------|
| AI SOC assistant | http://localhost:8080 | core |
| Mock Ollama | http://localhost:11435/api/tags | core |
| Victim web (vulnerable) | http://localhost:8081 | targets |
| Victim SSH | `ssh labuser@localhost -p 2222` (pass `Password1`) | targets |
| Attacker shell | `docker exec -it soclab-attacker-1 bash` | attack |

---

## 3. Teardown

```bash
scripts/lab_down.sh     # stop containers (keep images/volumes)
scripts/teardown.sh     # stop + remove locally-built images, volumes, generated logs
```

---

## Isolation & safety

- The `victim-web` and `victim-ssh` containers are **intentionally vulnerable**. Keep them on
  the internal lab network only. Never bind them to a public interface or feed real data.
- Red-team payloads in Module 4 are benign (they flip verdicts or leak the assistant's own
  system prompt). No payload here provides real-world offensive capability.
- The Docker network `soclab` is bridged and local to the host; the attacker container reaches
  the victims by service name, not your real network.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `port is already allocated` on 11434 | A real Ollama is running locally. The mock uses host port **11435** by default; change `MOCK_OLLAMA_PORT` in `.env` if needed. |
| `verify_env.py` Wazuh FAIL | Check VPN, `WAZUH_PASS`, and that port 55000 is reachable. |
| Assistant shows `[ERROR] Could not reach Ollama` | `OLLAMA_HOST` is wrong for your path (see the table in §1). |
| `docker compose` not found | Install Docker Desktop / the Compose v2 plugin. |
| Attacker `hydra`/`nmap` slow first run | The attacker image builds from Debian + apt on first `up`; subsequent runs are cached. |
