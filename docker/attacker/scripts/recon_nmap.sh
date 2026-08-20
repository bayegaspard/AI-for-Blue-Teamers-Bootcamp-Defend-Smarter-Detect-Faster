#!/usr/bin/env bash
# Light recon scan across the lab network — generates scan telemetry.
# Usage: ./recon_nmap.sh [target]
set -euo pipefail
TARGET="${1:-victim-web}"
echo "[*] Service scan of $TARGET"
nmap -sV -T4 --top-ports 50 "$TARGET" || true
echo "[*] Done."
