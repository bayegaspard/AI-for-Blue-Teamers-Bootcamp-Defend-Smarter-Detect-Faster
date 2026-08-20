#!/usr/bin/env python3
"""
triage_workflow.py - Module 3, Lab 3.4: an AI-assisted SOC triage workflow.

What it does
------------
1. Pulls recent alerts from Wazuh (WazuhClient.recent_alerts()).
   If Wazuh is unreachable (wrong password, VM down, no VPN), it falls back to a
   local JSON file (labs/sample_alerts.json) so the lab ALWAYS runs.
2. For each alert it builds the `alert_summary` prompt (see
   common/prompts/alert_summary.md), augmented with a one-line VERDICT so the
   triage table has a verdict column.
3. Sends each prompt to the local/GPU model via OllamaClient and parses the
   answer into four columns:  TITLE | SEVERITY | VERDICT | NEXT_STEP
4. Prints a clean triage table.

It is deliberately dependency-light (Python standard library only) and fails
loudly-but-clearly when Ollama or Wazuh is down, so students always know what to fix.

Run it
------
    # real cyberlab (Wazuh + GPU Ollama, from your .env):
    python3 labs/triage_workflow.py

    # portable / offline (local file + mock-ollama):
    #   1) scripts/lab_up.sh core        # starts mock-ollama on host port 11435
    #   2) set OLLAMA_HOST=http://localhost:11435 in .env
    python3 labs/triage_workflow.py --source file --limit 5

    # force the local file even if Wazuh is up (deterministic for class):
    python3 labs/triage_workflow.py --source file
"""
from __future__ import annotations

# --- shared-tooling import boilerplate (see SHARED CONTEXT) -----------------
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import argparse
import json
import re
import textwrap

from common.ollama_client import OllamaClient, OllamaError

# WazuhClient is optional at import time: the offline path must work even if the
# module or its config is missing, so we import defensively.
try:
    from common.wazuh_client import WazuhClient, WazuhError
    _WAZUH_AVAILABLE = True
except Exception:  # pragma: no cover - defensive
    WazuhClient = None  # type: ignore
    WazuhError = Exception  # type: ignore
    _WAZUH_AVAILABLE = False

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ALERTS_FILE = os.path.join(HERE, "sample_alerts.json")

# The SOC-analyst persona from common/prompts/system_prompts.md.
SOC_SYSTEM_PROMPT = (
    "You are a senior SOC analyst assistant. You help human analysts triage alerts, "
    "summarize logs, and explain attacker behavior clearly and concisely. Be precise, "
    "cite the specific fields that justify each conclusion, and never invent details "
    "that are not present in the input. When you are uncertain, say so."
)

# The alert_summary template (common/prompts/alert_summary.md), plus a VERDICT line
# so the triage table can show a benign/suspicious/malicious call per alert.
ALERT_SUMMARY_PROMPT = """\
Summarize this Wazuh alert for an incident ticket. Use ONLY the alert JSON.

Output exactly these fields, one per line, each label in CAPS followed by a colon:
- TITLE: short, ticket-ready (max 12 words)
- WHAT_HAPPENED: 1-2 sentences in plain language
- SEVERITY: map from rule.level (0-3 low, 4-7 medium, 8-11 high, 12-15 critical)
- VERDICT: benign | suspicious | malicious
- AFFECTED_ASSET: agent.name / agent.ip
- MITRE: list any rule.mitre.id present, else "none listed"
- NEXT_STEP: one concrete action

ALERT JSON:
{alert_json}
"""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def severity_from_level(level) -> str:
    """Wazuh rule-level rubric -> severity word (matches the prompt rubric)."""
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        return "unknown"
    if lvl <= 3:
        return "low"
    if lvl <= 7:
        return "medium"
    if lvl <= 11:
        return "high"
    return "critical"


def verdict_from_severity(sev: str) -> str:
    """Reasonable fallback when the model omits an explicit VERDICT line."""
    return {
        "low": "benign",
        "medium": "suspicious",
        "high": "malicious",
        "critical": "malicious",
    }.get(sev, "review")


def _field(text: str, *labels: str) -> str | None:
    """Pull the value after the first matching 'LABEL:' line (case-insensitive)."""
    for label in labels:
        m = re.search(rf"^\s*[-*]?\s*{re.escape(label)}\s*:\s*(.+)$",
                      text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def parse_triage(model_text: str, alert: dict) -> dict:
    """Turn the model's free-text answer into the 4 table columns.

    Robust to two output shapes we see in this bootcamp:
      * the alert_summary schema (TITLE/SEVERITY/VERDICT/NEXT_STEP) from the real model
      * the log_triage schema (SUMMARY/VERDICT/RECOMMENDED ACTION) from mock-ollama
    Missing fields fall back to values derived from the alert JSON itself.
    """
    rule = alert.get("rule", {}) or {}
    level = rule.get("level")

    title = _field(model_text, "TITLE", "SUMMARY") or rule.get("description") or "(no title)"
    severity = _field(model_text, "SEVERITY") or severity_from_level(level)
    verdict = _field(model_text, "VERDICT") or verdict_from_severity(severity_from_level(level))
    next_step = _field(model_text, "NEXT_STEP", "RECOMMENDED ACTION", "RECOMMENDED_ACTION") \
        or "Analyst review required"

    # Normalize a couple of noisy values.
    severity = severity.split()[0].lower().strip(".") if severity else severity
    verdict = verdict.split()[0].lower().strip(".") if verdict else verdict
    return {
        "title": title,
        "severity": severity,
        "verdict": verdict,
        "next_step": next_step,
    }


def build_prompt(alert: dict) -> str:
    return ALERT_SUMMARY_PROMPT.format(alert_json=json.dumps(alert, indent=2))


# --------------------------------------------------------------------------- #
# Alert sources
# --------------------------------------------------------------------------- #
def load_alerts_from_file(path: str, limit: int) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Alert file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    alerts = data if isinstance(data, list) else [data]
    return alerts[:limit]


def load_alerts_from_wazuh(limit: int, min_level: int) -> list[dict]:
    if not _WAZUH_AVAILABLE or WazuhClient is None:
        raise WazuhError("wazuh_client is not importable")
    wz = WazuhClient()
    return wz.recent_alerts(limit=limit, min_level=min_level)


def get_alerts(source: str, path: str, limit: int, min_level: int) -> tuple[list[dict], str]:
    """Return (alerts, human-readable-source-label)."""
    if source == "file":
        return load_alerts_from_file(path, limit), f"local file ({os.path.basename(path)})"

    # source == "auto" or "wazuh": try Wazuh first, fall back to file on any failure.
    try:
        alerts = load_alerts_from_wazuh(limit, min_level)
        if alerts:
            return alerts, "Wazuh indexer"
        # Reachable but empty -> use the file so the lab still demonstrates output.
        print("[i] Wazuh returned 0 alerts; using the local sample file instead.")
    except Exception as e:  # WazuhError, auth failure, network, missing config...
        if source == "wazuh":
            raise
        print(f"[i] Wazuh unavailable ({e.__class__.__name__}); "
              f"falling back to the local sample file.")
    return load_alerts_from_file(path, limit), f"local file ({os.path.basename(path)})"


# --------------------------------------------------------------------------- #
# Table rendering
# --------------------------------------------------------------------------- #
COLS = [("TITLE", 40), ("SEVERITY", 9), ("VERDICT", 11), ("NEXT_STEP", 44)]


def _cell(value: str, width: int) -> list[str]:
    value = (value or "-").replace("\n", " ").strip()
    return textwrap.wrap(value, width) or [""]


def print_table(rows: list[dict]) -> None:
    header = " | ".join(name.ljust(w) for name, w in COLS)
    sep = "-+-".join("-" * w for _, w in COLS)
    print(header)
    print(sep)
    for r in rows:
        cells = [
            _cell(r["title"], COLS[0][1]),
            _cell(r["severity"], COLS[1][1]),
            _cell(r["verdict"], COLS[2][1]),
            _cell(r["next_step"], COLS[3][1]),
        ]
        for i in range(max(len(c) for c in cells)):
            line = " | ".join(
                (cells[j][i] if i < len(cells[j]) else "").ljust(COLS[j][1])
                for j in range(len(COLS))
            )
            print(line)
        print(sep)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run(args: argparse.Namespace) -> int:
    # 1) Get alerts (Wazuh or file).
    try:
        alerts, source_label = get_alerts(args.source, args.file, args.limit, args.min_level)
    except FileNotFoundError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        print("       Create labs/sample_alerts.json or pass --file <path>.", file=sys.stderr)
        return 2
    except WazuhError as e:
        print(f"[FAIL] Wazuh source requested but unavailable: {e}", file=sys.stderr)
        print("       Check WAZUH_* in .env, or run with --source file.", file=sys.stderr)
        return 2

    if not alerts:
        print("[i] No alerts to triage.")
        return 0

    # 2) Confirm the model is reachable BEFORE looping (one clean message).
    ai = OllamaClient(model=args.model) if args.model else OllamaClient()
    try:
        tags = ai.health()
        models = ", ".join(m.get("name", "?") for m in tags.get("models", [])) or "(none)"
    except OllamaError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        print("       Fixes: check OLLAMA_HOST in .env, run "
              "`python3 common/ollama_client.py --health`,", file=sys.stderr)
        print("       or start the offline mock: `scripts/lab_up.sh core` then set "
              "OLLAMA_HOST=http://localhost:11435", file=sys.stderr)
        return 3

    print(f"[*] Source : {source_label}  ({len(alerts)} alert(s))")
    print(f"[*] Model  : {ai.model} @ {ai.host}   (available: {models})")
    print(f"[*] Prompt : alert_summary + VERDICT   temp={args.temp}")
    print()

    # 3) Triage each alert.
    rows: list[dict] = []
    for idx, alert in enumerate(alerts, 1):
        prompt = build_prompt(alert)
        desc = (alert.get("rule", {}) or {}).get("description", "(no description)")
        print(f"[{idx}/{len(alerts)}] Triaging: {desc[:70]}")
        try:
            answer = ai.generate(prompt, system=SOC_SYSTEM_PROMPT, temperature=args.temp)
        except OllamaError as e:
            print(f"    [!] Model call failed for this alert: {e}", file=sys.stderr)
            rows.append({"title": desc, "severity": "error",
                         "verdict": "error", "next_step": "model call failed"})
            continue
        row = parse_triage(answer, alert)
        rows.append(row)
        if args.show_raw:
            print(textwrap.indent(answer.strip(), "    | "))
            print()

    # 4) Table.
    print()
    print("=" * 80)
    print("AI-ASSISTED TRIAGE TABLE")
    print("=" * 80)
    print_table(rows)
    print("\nReminder: the AI drafts, the analyst decides. Verify before you act.")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="AI-assisted SOC triage workflow (Module 3, Lab 3.4).")
    p.add_argument("--source", choices=["auto", "wazuh", "file"], default="auto",
                   help="Where to read alerts from (default: auto = Wazuh, then file).")
    p.add_argument("--file", default=DEFAULT_ALERTS_FILE,
                   help="Local alerts JSON (used by --source file or as the fallback).")
    p.add_argument("--limit", type=int, default=10, help="Max alerts to triage.")
    p.add_argument("--min-level", type=int, default=7,
                   help="Minimum Wazuh rule.level when pulling from Wazuh.")
    p.add_argument("--temp", type=float, default=0.2, help="Model temperature.")
    p.add_argument("--model", default=None, help="Override OLLAMA_MODEL.")
    p.add_argument("--show-raw", action="store_true",
                   help="Also print the model's raw answer per alert.")
    args = p.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
