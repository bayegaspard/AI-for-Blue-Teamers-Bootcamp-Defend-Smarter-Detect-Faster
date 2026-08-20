#!/usr/bin/env bash
# Bring up lab services. Pass profiles as args (default: core).
#   scripts/lab_up.sh                       # core (mock-ollama + ai-soc-assistant)
#   scripts/lab_up.sh core targets attack   # full offline lab
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -f .env ] || { echo "[*] No .env found - creating from .env.example"; cp .env.example .env; }

if ! command -v docker >/dev/null 2>&1; then
  echo "[!] Docker is not installed on this machine."
  echo "    Day 1 / Module 1 does NOT need Docker (it uses the real Ollama + Wazuh)."
  echo "    Docker is required for Module 2 (targets/attacker), Module 4 (assistant),"
  echo "    and the offline smoke test. Install it on Ubuntu with:"
  echo "      curl -fsSL https://get.docker.com | sudo sh"
  echo "      sudo usermod -aG docker \$USER && newgrp docker"
  exit 1
fi

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
