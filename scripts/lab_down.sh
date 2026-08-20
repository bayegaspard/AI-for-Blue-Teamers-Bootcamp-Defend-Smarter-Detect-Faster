#!/usr/bin/env bash
# Stop lab services (keeps images/volumes).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
docker compose --env-file .env -f docker/docker-compose.yml \
  --profile core --profile targets --profile attack --profile logs down
echo "[*] Stopped. Use scripts/teardown.sh to also remove images/volumes."
