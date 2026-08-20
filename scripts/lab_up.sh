#!/usr/bin/env bash
# Bring up lab services. Pass profiles as args (default: core).
#   scripts/lab_up.sh                       # core (mock-ollama + ai-soc-assistant)
#   scripts/lab_up.sh core targets attack   # full offline lab
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -f .env ] || { echo "[*] No .env found — creating from .env.example"; cp .env.example .env; }

PROFILES=("${@:-core}")
ARGS=()
for p in "${PROFILES[@]}"; do ARGS+=(--profile "$p"); done

echo "[*] Starting profiles: ${PROFILES[*]}"
docker compose --env-file .env -f docker/docker-compose.yml "${ARGS[@]}" up -d --build
echo
echo "[*] Up. Handy URLs (host ports from .env):"
echo "      AI SOC Assistant : http://localhost:${AI_SOC_PORT:-8080}"
echo "      Mock Ollama      : http://localhost:${MOCK_OLLAMA_PORT:-11435}/api/tags"
echo "      Victim web       : http://localhost:${VICTIM_WEB_PORT:-8081}"
echo "      Attacker shell   : docker exec -it soclab-attacker-1 bash"
