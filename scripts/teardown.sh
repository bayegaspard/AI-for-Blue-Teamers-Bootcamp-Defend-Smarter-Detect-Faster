#!/usr/bin/env bash
# Full cleanup: stop containers, remove locally-built images and volumes.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
docker compose --env-file .env -f docker/docker-compose.yml \
  --profile core --profile targets --profile attack --profile logs down -v --rmi local
rm -rf datasets/generated
echo "[*] Teardown complete."
