#!/usr/bin/env python3
"""
gen_sigma.py - Module 3, Lab 3.2: draft a Sigma rule from a behavior description.

Fills the `sigma_generation` prompt (common/prompts/sigma_generation.md) with a
plain-English behavior description, sends it to the model via OllamaClient using the
"Detection Engineer" persona, and prints the YAML the model produced.

IMPORTANT: the AI DRAFTS the rule; a detection engineer VERIFIES it. Always lint
(`sigma check rule.yml`) and test against real data before deploying. See the
"Validate it" section of STUDENT_GUIDE.md.

Run it
------
    # behavior as an argument:
    python3 labs/gen_sigma.py "More than 10 failed SSH logins from one source IP in 60s, then a success from that IP."

    # behavior from stdin:
    echo "SQL injection UNION SELECT in an nginx access log URL" | python3 labs/gen_sigma.py --stdin

    # save the draft to a file to lint it:
    python3 labs/gen_sigma.py "..." > /tmp/draft.yml
"""
from __future__ import annotations

# --- shared-tooling import boilerplate (see SHARED CONTEXT) -----------------
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import argparse

from common.ollama_client import OllamaClient, OllamaError

# The "Detection Engineer" persona from common/prompts/system_prompts.md.
DETECTION_ENGINEER_SYSTEM = (
    "You are a detection engineer. You convert attacker behavior into precise, "
    "testable detection logic (Sigma rules, Wazuh rules, KQL). Prefer low "
    "false-positive logic. Always state the assumptions and the data source your "
    "rule requires."
)

# The sigma_generation template (common/prompts/sigma_generation.md).
SIGMA_PROMPT = """\
Write a valid Sigma rule that detects the behavior described below.
Requirements:
- Output ONLY valid YAML (a single Sigma rule), no prose.
- Include: title, id (leave as a placeholder GUID), status: experimental, description,
  author, date, logsource, detection (with a selection + condition), falsepositives,
  level.
- Keep the logic tight to minimize false positives.
- Add a comment line explaining which log source/fields it assumes.

BEHAVIOR TO DETECT:
{behavior}
"""


def build_prompt(behavior: str) -> str:
    return SIGMA_PROMPT.format(behavior=behavior.strip())


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Draft a Sigma rule from a behavior description (Module 3, Lab 3.2).")
    p.add_argument("behavior", nargs="?", help="Behavior to detect (omit when using --stdin).")
    p.add_argument("--stdin", action="store_true", help="Read the behavior from stdin.")
    p.add_argument("--temp", type=float, default=0.1,
                   help="Model temperature (low = more deterministic YAML).")
    p.add_argument("--model", default=None, help="Override OLLAMA_MODEL.")
    args = p.parse_args(argv)

    behavior = sys.stdin.read() if args.stdin else args.behavior
    if not behavior or not behavior.strip():
        p.error("Provide a behavior description as an argument or via --stdin.")

    ai = OllamaClient(model=args.model) if args.model else OllamaClient()
    prompt = build_prompt(behavior)

    # Fast reachability check so we fail in seconds (not the 120s generate timeout).
    try:
        ai.health()
    except OllamaError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        print("       Fixes: check OLLAMA_HOST in .env, run "
              "`python3 common/ollama_client.py --health`,", file=sys.stderr)
        print("       or start the offline mock: `scripts/lab_up.sh core` then set "
              "OLLAMA_HOST=http://localhost:11435", file=sys.stderr)
        return 1

    try:
        yaml_text = ai.generate(prompt, system=DETECTION_ENGINEER_SYSTEM,
                                temperature=args.temp)
    except OllamaError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    # Strip accidental ```yaml fences if the model added them, so the output lints cleanly.
    text = yaml_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines and lines[0].startswith("```") else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    print(text)
    print("\n# --- Reminder: AI drafts, engineer verifies. Lint with "
          "`sigma check` and test on real data before deploying. ---",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
