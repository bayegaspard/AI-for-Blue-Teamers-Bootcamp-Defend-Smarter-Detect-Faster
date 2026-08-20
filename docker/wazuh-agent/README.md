# Wiring endpoints into the real Wazuh manager (10.50.136.116)

Use this when you want **real** SIEM telemetry (the cyberlab path) instead of the
synthetic log-generator. Two things: (1) enroll an agent on each endpoint, (2) load
the custom bootcamp rules on the manager.

## 1. Install the Wazuh agent on a Linux endpoint

```bash
# On the endpoint (e.g., the victim VM / a student endpoint)
WAZUH_MANAGER="10.50.136.116" apt-get install -y curl gnupg
curl -sO https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.14.0-1_amd64.deb
sudo WAZUH_MANAGER="10.50.136.116" dpkg -i ./wazuh-agent_4.14.0-1_amd64.deb
sudo systemctl enable --now wazuh-agent
```

Verify on the manager: the agent shows up in **Dashboard → Agents**, or:
```bash
python3 common/wazuh_client.py --agents
```

## 2. Tell the agent which extra logs to read

Add to `/var/ossec/etc/ossec.conf` on the endpoint (inside `<ossec_config>`), then
`sudo systemctl restart wazuh-agent`:

```xml
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/auth.log</location>
</localfile>
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/victim-web/auth.log</location>
</localfile>
```

## 3. Load the custom bootcamp rules on the MANAGER

```bash
# On 10.50.136.116
sudo cp local_rules.xml /var/ossec/etc/rules/local_rules.xml   # merge if one already exists
sudo systemctl restart wazuh-manager
# Test a sample line:
sudo /var/ossec/bin/wazuh-logtest
#   paste:  Aug 10 03:11:02 web01 sshd[2001]: Failed password for invalid user admin from 10.10.10.5 port 51122 ssh2
```

## 4. Dockerized endpoint (optional)

The Docker `victim-web` writes to `/var/log/victim-web/auth.log`. To ship those to
Wazuh, either bind-mount that path onto a host that runs a Wazuh agent, or run a
Wazuh agent container that shares the volume. For most cohorts the simplest reliable
path is: **real VMs with agents** for live Wazuh, **Docker + log-generator** for the
portable/offline path. Both are supported by the labs.
