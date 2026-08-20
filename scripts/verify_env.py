#!/usr/bin/env python3
"""
verify_env.py — pre-flight check students run on Day 1.

Checks that the two core services in your .env are reachable and prints a clear
pass/fail table. Safe to run repeatedly.

    python scripts/verify_env.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ollama_client import OllamaClient, OllamaError  # noqa: E402
from common.wazuh_client import WazuhClient, WazuhError      # noqa: E402


def check_ollama() -> tuple[bool, str]:
    c = OllamaClient()
    try:
        tags = c.health()
        models = ", ".join(m.get("name", "?") for m in tags.get("models", [])) or "(none)"
        return True, f"reachable at {c.host} — models: {models}"
    except OllamaError as e:
        return False, str(e)


def check_wazuh() -> tuple[bool, str]:
    w = WazuhClient()
    try:
        info = w.health().get("data", {})
        return True, f"manager {info.get('version', '?')} reachable at {w.api}"
    except WazuhError as e:
        return False, str(e)


def main() -> int:
    print("=" * 70)
    print(" AI Blue Team Bootcamp — environment check")
    print("=" * 70)
    results = [("Ollama", *check_ollama()), ("Wazuh", *check_wazuh())]
    all_ok = True
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name:<8} {detail}")
        all_ok = all_ok and ok
    print("-" * 70)
    if all_ok:
        print("  All good — you're ready for the labs.")
    else:
        print("  One or more checks failed. Fix .env, or use the local Docker fallback:")
        print("     docker compose --env-file .env -f docker/docker-compose.yml --profile core up -d")
        print("     (and set OLLAMA_HOST=http://localhost:11435 in .env)")
    print("=" * 70)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
