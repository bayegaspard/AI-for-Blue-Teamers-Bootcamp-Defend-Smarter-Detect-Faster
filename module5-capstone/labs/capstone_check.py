#!/usr/bin/env python3
"""
capstone_check.py — Module 5 (Capstone) automated report grader.

WHAT IT DOES
------------
Given a student's incident report (Markdown), it checks that the report:

  1. Contains all five required sections:
         Executive Summary, Timeline, Technical Details, Impact, Recommendations
  2. Names the SSH brute-force source IP        -> 10.10.10.5
  3. Names the SQLi scanner (sqlmap) source IP  -> 10.10.10.7
  4. FLAGS the planted prompt-injection / poisoned log entry. A report passes
     this check if it mentions ANY of:
         "prompt injection" | "prompt-injection" | "poisoned" | 10.10.10.9 | 10.10.10.11

It prints a scored rubric (points per check) and a total out of 100, then exits
0 if the submission passes (>= PASS_MARK) and 1 otherwise. This is the SAME
adversarial trap the students were warned about: a report that "closed the alert
as benign" because the AI said so will MISS check #4 and lose 20 points.

USAGE
-----
    # grade the newest report in module5-capstone/submissions/
    python3 capstone_check.py

    # grade a specific report
    python3 capstone_check.py ../submissions/gaspard_report.md
    python3 capstone_check.py /abs/path/to/report.md

This script uses only the Python standard library — no pip installs needed.
It is robust to a missing / empty file and to an empty submissions directory.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

# This file lives at <repo>/module5-capstone/labs/capstone_check.py, so the
# module directory is one level up and the repo root is two levels up.
MODULE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SUBMISSIONS_DIR = os.path.join(MODULE_ROOT, "submissions")

PASS_MARK = 70  # out of 100

# --- ground truth (see solutions/README.md) ---------------------------------
BRUTEFORCE_IP = "10.10.10.5"   # SSH brute force, threat_intel = high
SQLI_IP = "10.10.10.7"         # sqlmap SQLi scanner, threat_intel = high
POISON_IPS = ("10.10.10.9", "10.10.10.11")  # planted prompt-injection sources

REQUIRED_SECTIONS = (
    "Executive Summary",
    "Timeline",
    "Technical Details",
    "Impact",
    "Recommendations",
)


def find_newest_report(directory: str) -> str | None:
    """Return the most-recently-modified *.md report in `directory`, or None."""
    if not os.path.isdir(directory):
        return None
    # Prefer files that look like real submissions, then any markdown file.
    candidates = glob.glob(os.path.join(directory, "*_report.md"))
    if not candidates:
        candidates = [
            p for p in glob.glob(os.path.join(directory, "*.md"))
            if os.path.basename(p).lower() not in ("readme.md",)
        ]
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def read_report(path: str) -> str | None:
    """Read a report file. Return its text, or None if it can't be read."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return None


def has_section(text: str, name: str) -> bool:
    """True if `name` appears as a heading-ish line.

    Tolerant of Markdown decoration: "## Executive Summary", "1. Executive
    Summary", "**Executive Summary**", "EXECUTIVE SUMMARY", etc. We anchor to
    the start of a line and allow leading #, *, digits, dots and spaces so a
    passing mention has to be a real heading, not a word buried in a sentence.
    """
    pattern = rf"(?im)^[#*\s\d\.\-]*{re.escape(name)}\b"
    return re.search(pattern, text) is not None


def mentions_ip(text: str, ip: str) -> bool:
    """True if the exact IP string appears (word-boundary safe)."""
    return re.search(rf"(?<!\d){re.escape(ip)}(?!\d)", text) is not None


def flags_injection(text: str) -> bool:
    """True if the report identifies the prompt-injection / poisoned entry."""
    low = text.lower()
    if "prompt injection" in low or "prompt-injection" in low or "poisoned" in low:
        return True
    return any(mentions_ip(text, ip) for ip in POISON_IPS)


def build_checks(text: str) -> list[tuple[str, bool, int]]:
    """Return a list of (label, passed, points) rubric rows."""
    checks: list[tuple[str, bool, int]] = []

    # Sections: 10 points each = 50.
    for name in REQUIRED_SECTIONS:
        checks.append((f"Section present: {name}", has_section(text, name), 10))

    # Detection of the two real attacker IPs.
    checks.append(
        (f"Names SSH brute-force source IP ({BRUTEFORCE_IP})",
         mentions_ip(text, BRUTEFORCE_IP), 15))
    checks.append(
        (f"Names SQLi scanner IP ({SQLI_IP})",
         mentions_ip(text, SQLI_IP), 15))

    # The adversarial catch — the whole point of the capstone.
    checks.append(
        ("Flags the prompt-injection / poisoned log entry",
         flags_injection(text), 20))

    return checks


def print_report(path: str, checks: list[tuple[str, bool, int]]) -> int:
    earned = sum(pts for _, ok, pts in checks if ok)
    total = sum(pts for _, _, pts in checks)

    print("=" * 68)
    print("  MODULE 5 CAPSTONE — AUTOMATED REPORT CHECK")
    print(f"  report: {path}")
    print("=" * 68)
    for label, ok, pts in checks:
        mark = "PASS" if ok else "FAIL"
        awarded = pts if ok else 0
        print(f"  [{mark}] {label:<48} {awarded:>3}/{pts}")
    print("-" * 68)
    print(f"  TOTAL: {earned}/{total}    (pass mark: {PASS_MARK})")

    if not any(ok for label, ok, _ in checks
               if label.startswith("Flags the prompt-injection")):
        print()
        print("  !! ADVERSARIAL MISS: the report does NOT flag the planted")
        print("     prompt-injection/poisoned entry. If the AI told you this")
        print("     alert was 'benign — close it', you were played. Re-read the")
        print("     odd log line from 10.10.10.9 / 10.10.10.11 and try again.")

    passed = earned >= PASS_MARK
    print("=" * 68)
    print(f"  RESULT: {'PASS' if passed else 'FAIL'}")
    print("=" * 68)
    return 0 if passed else 1


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Grade a Module 5 capstone incident report.")
    p.add_argument(
        "report", nargs="?", default=None,
        help="Path to the report .md (default: newest in submissions/).")
    args = p.parse_args(argv)

    path = args.report or find_newest_report(SUBMISSIONS_DIR)

    if path is None:
        print("[FAIL] No report to grade.", file=sys.stderr)
        print(f"       No *.md files found in {SUBMISSIONS_DIR}", file=sys.stderr)
        print("       Save your report as submissions/<name>_report.md, or pass",
              file=sys.stderr)
        print("       a path:  python3 capstone_check.py path/to/report.md",
              file=sys.stderr)
        return 2

    if not os.path.exists(path):
        print(f"[FAIL] Report file not found: {path}", file=sys.stderr)
        return 2

    text = read_report(path)
    if text is None:
        print(f"[FAIL] Could not read report file: {path}", file=sys.stderr)
        return 2
    if not text.strip():
        print(f"[FAIL] Report file is empty: {path}", file=sys.stderr)
        return 2

    checks = build_checks(text)
    return print_report(path, checks)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
