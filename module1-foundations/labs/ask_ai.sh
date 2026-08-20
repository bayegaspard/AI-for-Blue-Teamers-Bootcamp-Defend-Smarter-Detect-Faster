#!/usr/bin/env bash
# ask_ai.sh - tiny convenience wrapper around the shared Ollama CLI.
#
# Module 1 exercises ask you to "chat" with the model a lot. Typing the full
# `python common/ollama_client.py ...` each time gets old, so this wrapper:
#   * finds the repo root no matter where you call it from,
#   * defaults to the SOC-analyst persona (override with SYSTEM=...),
#   * lets you stream, pipe files in, or just pass a question.
#
# It reads OLLAMA_HOST/OLLAMA_MODEL from .env exactly like every other tool, so
# it works against the real GPU VM or the local mock with no changes.
#
# Usage:
#   labs/ask_ai.sh "Explain what SSH brute force looks like in auth.log"
#   labs/ask_ai.sh --stream "Summarize the MITRE ATT&CK tactic 'Credential Access'"
#   cat datasets/auth.log | labs/ask_ai.sh --stdin
#   SYSTEM="You are a detection engineer." labs/ask_ai.sh "Draft a Sigma rule idea for SSH brute force"
#
# Health check:
#   labs/ask_ai.sh --health
set -euo pipefail

# Repo root = two levels up from this script (module1-foundations/labs/ -> repo).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Default persona; override by exporting SYSTEM before the call.
SYSTEM="${SYSTEM:-You are a senior SOC analyst assistant. Be precise, cite the specific log lines that justify each conclusion, and never invent details.}"

# Pass everything straight through to the shared client, injecting --system.
exec python "$ROOT/common/ollama_client.py" --system "$SYSTEM" "$@"
