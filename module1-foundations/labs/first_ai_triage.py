#!/usr/bin/env python3
"""
first_ai_triage.py - Module 1, Lab 1.3 starter script.

Your first AI-assisted SOC task: hand a block of SSH auth logs to a local LLM
and get back a structured triage verdict (summary / verdict / confidence /
indicators / recommended action).

Nothing here is magic. The script:
  1. reads a log file (default: datasets/auth.log),
  2. wraps it in the shared "log triage" prompt template,
  3. sends it to the Ollama server pointed at by OLLAMA_HOST in your .env,
  4. prints whatever the model says.

Because the OLLAMA_HOST/OLLAMA_MODEL values come from .env (loaded by the shared
client), this SAME script runs unchanged against either backend:
  * Real cyberlab  -> OLLAMA_HOST=http://10.50.142.235:11434  (Tesla T4 GPU VM)
  * Portable/offline-> OLLAMA_HOST=http://localhost:11435       (mock-ollama container)

Run it:
    python module1-foundations/labs/first_ai_triage.py
    python module1-foundations/labs/first_ai_triage.py datasets/poisoned.log
"""
from __future__ import annotations

# --- import boilerplate: make the repo-root packages importable --------------
# This file lives at <repo>/module1-foundations/labs/, so two levels up is the
# repo root, which is where the `common` package lives.
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from common.ollama_client import OllamaClient, OllamaError  # noqa: E402

# Absolute path to the repo root, reused to locate datasets regardless of the
# directory you launch the script from.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# The default log to triage. Any file path passed on the command line wins.
DEFAULT_LOG = os.path.join(REPO_ROOT, "datasets", "auth.log")

# ---------------------------------------------------------------------------
# Prompts. These mirror the shared templates so you can see exactly what the
# model receives. In later modules you'll load these from common/prompts/*.md.
# ---------------------------------------------------------------------------

# The persona (system prompt). See common/prompts/system_prompts.md.
SOC_SYSTEM_PROMPT = (
    "You are a senior SOC analyst assistant. You help human analysts triage "
    "alerts, summarize logs, and explain attacker behavior clearly and "
    "concisely. Be precise, cite the specific fields or log lines that justify "
    "each conclusion, and never invent details that are not present in the "
    "input. When you are uncertain, say so."
)

# The task template. See common/prompts/log_triage.md. {LOG_BLOCK} is filled in.
LOG_TRIAGE_TEMPLATE = """Analyze the following log block. Use ONLY the data provided.

Return your answer as:
1. SUMMARY: one sentence describing what happened.
2. VERDICT: benign | suspicious | malicious
3. CONFIDENCE: low | medium | high
4. INDICATORS: the exact IPs, users, ports, or strings that drove your verdict.
5. RECOMMENDED ACTION: one concrete next step for the analyst.

LOG BLOCK:
{LOG_BLOCK}
"""


def read_log(path: str) -> str:
    """Read a log file and return its contents, or exit with a helpful error."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except FileNotFoundError:
        print(f"[FAIL] Log file not found: {path}", file=sys.stderr)
        print("       Pass a path, or run from the repo root so datasets/ resolves.",
              file=sys.stderr)
        raise SystemExit(2)


def build_prompt(log_block: str) -> str:
    """Fill the triage template with the raw log lines."""
    return LOG_TRIAGE_TEMPLATE.format(LOG_BLOCK=log_block)


def main(argv: list[str]) -> int:
    log_path = argv[0] if argv else DEFAULT_LOG
    log_block = read_log(log_path)

    print("=" * 70)
    print(f" AI-assisted log triage  -  {log_path}")
    print("=" * 70)
    print(f"[*] Read {len(log_block.splitlines())} log lines.")

    # The client reads OLLAMA_HOST / OLLAMA_MODEL from .env for us.
    ai = OllamaClient()
    print(f"[*] Asking {ai.model} at {ai.host} to triage the logs...\n")

    prompt = build_prompt(log_block)

    try:
        # temperature is low on purpose: triage should be steady, not creative.
        verdict = ai.generate(prompt, system=SOC_SYSTEM_PROMPT, temperature=0.1)
    except OllamaError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        print("       Check OLLAMA_HOST in .env, or start the mock:", file=sys.stderr)
        print("         scripts/lab_up.sh core", file=sys.stderr)
        print("         then set OLLAMA_HOST=http://localhost:11435 in .env", file=sys.stderr)
        return 1

    print("----- AI TRIAGE RESULT ------------------------------------------------")
    print(verdict.strip())
    print("-----------------------------------------------------------------------")
    print("\n[✓] Done. Remember: the AI is a co-pilot. A human confirms the verdict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
