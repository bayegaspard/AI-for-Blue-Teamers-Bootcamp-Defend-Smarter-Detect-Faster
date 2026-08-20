#!/usr/bin/env python3
"""
detect_bruteforce.py - Module 2 (Applied Detection) brute-force detector.

WHAT IT DOES
------------
1. Reads a log file (default: datasets/auth.log) line by line.
2. Finds every "Failed password ... from <IP>" event and buckets it by source IP.
3. Uses a SLIDING TIME WINDOW to count how many failures each IP produced in the
   busiest <window> seconds, and FLAGS any IP whose burst is >= <threshold>.
4. Cross-references each flagged IP against a threat-intel feed
   (default: datasets/threat_intel.csv) and prints any match.
5. As a bonus (this is the key teaching point of Lab 2.4), it also reports any
   "Accepted password" that came from a flagged IP - i.e. the SUCCESSFUL login
   hiding inside the brute-force noise.

WHY A SLIDING WINDOW?
---------------------
A total count alone is misleading: 20 failures spread over a week is probably a
forgetful user, but 20 failures in 30 seconds is an automated attack. Wazuh's
built-in SSH rules (5710/5712) and our custom burst rule (100120) work the same
way - "N events from one source inside T seconds". This script is a tiny,
readable version of that same idea so you can see the logic end to end.

USAGE
-----
    # default: analyze datasets/auth.log with threshold=5 failures / 120s window
    python3 detect_bruteforce.py

    # analyze a captured log (e.g. saved from `docker logs soclab-victim-web-1`)
    python3 detect_bruteforce.py /path/to/captured.log

    # tune the sensitivity
    python3 detect_bruteforce.py --threshold 10 --window 60

This script uses only the Python standard library - no pip installs needed.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

# --- Where the shared datasets live -----------------------------------------
# This file is at:  <repo>/module2-detection/labs/detect_bruteforce.py
# so the repo root is two directories up. We build absolute default paths from
# it so the script works no matter which directory you run it from.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_LOG = os.path.join(REPO_ROOT, "datasets", "auth.log")
DEFAULT_INTEL = os.path.join(REPO_ROOT, "datasets", "threat_intel.csv")

# --- Line patterns -----------------------------------------------------------
# Syslog-style timestamp at the start of a line, e.g. "Aug 10 03:11:02".
TS_RE = re.compile(r"^([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})")

# A failed auth event. Matches BOTH the SSH format:
#   "Failed password for invalid user admin from 10.10.10.5 port 51122 ssh2"
# and the victim-web format:
#   "Failed password for admin from 10.10.10.7 port 0 http"
FAIL_RE = re.compile(
    r"Failed password for (?:invalid user )?(?P<user>\S+) "
    r"from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
)

# A successful auth event, same two formats ("Accepted password for ...").
OK_RE = re.compile(
    r"Accepted password for (?P<user>\S+) "
    r"from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
)

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def line_seconds(line: str, fallback: float) -> float:
    """
    Convert a log line's syslog timestamp into an absolute number of seconds so we
    can measure gaps between events. We don't need a real calendar date - we only
    need a consistent, monotonic number to subtract. If a line has no parseable
    timestamp we reuse the previous value (`fallback`) so it still counts.
    """
    m = TS_RE.match(line)
    if not m:
        return fallback
    mon, day, hh, mm, ss = m.groups()
    month = MONTHS.get(mon, 1)
    # (month * 31 + day) is a rough day ordinal - good enough to order events and
    # measure second-level gaps within the same log. Then add the time-of-day.
    day_ordinal = month * 31 + int(day)
    return day_ordinal * 86400 + int(hh) * 3600 + int(mm) * 60 + int(ss)


def max_events_in_window(times: list[float], window: float) -> int:
    """
    Given the sorted timestamps (in seconds) of one IP's failures, return the most
    events that fall inside any single <window>-second span. Classic two-pointer
    sliding window: slide `left` forward until the span [left, right] fits.
    """
    times.sort()
    left = 0
    best = 0
    for right in range(len(times)):
        while times[right] - times[left] > window:
            left += 1
        best = max(best, right - left + 1)
    return best


def load_threat_intel(path: str) -> dict[str, dict[str, str]]:
    """Return {ip: {"description": ..., "severity": ...}} for IP indicators."""
    intel: dict[str, dict[str, str]] = {}
    if not os.path.exists(path):
        return intel
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("type", "").strip().lower() == "ip":
                intel[row["indicator"].strip()] = {
                    "description": row.get("description", "").strip(),
                    "severity": row.get("severity", "").strip(),
                }
    return intel


def analyze(log_path: str, threshold: int, window: float):
    """Walk the log and build per-IP failure/success records."""
    # For each IP we track: list of failure timestamps, usernames tried, and any
    # successful ("Accepted") logins (username + timestamp seconds).
    failures: dict[str, list[float]] = {}
    users_tried: dict[str, set[str]] = {}
    successes: dict[str, list[str]] = {}

    last_seconds = 0.0
    with open(log_path, "r", errors="replace") as f:
        for line in f:
            last_seconds = line_seconds(line, last_seconds)

            fail = FAIL_RE.search(line)
            if fail:
                ip = fail.group("ip")
                failures.setdefault(ip, []).append(last_seconds)
                users_tried.setdefault(ip, set()).add(fail.group("user"))
                continue

            ok = OK_RE.search(line)
            if ok:
                ip = ok.group("ip")
                successes.setdefault(ip, []).append(ok.group("user"))

    return failures, users_tried, successes


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Detect SSH/web brute-force bursts and correlate source IPs "
                    "with a threat-intel feed.")
    p.add_argument("logfile", nargs="?", default=DEFAULT_LOG,
                   help=f"Log file to analyze (default: {DEFAULT_LOG})")
    p.add_argument("--threshold", type=int, default=5,
                   help="Failures within the window that mark an IP as brute force "
                        "(default: 5)")
    p.add_argument("--window", type=float, default=120,
                   help="Sliding window in seconds (default: 120)")
    p.add_argument("--intel", default=DEFAULT_INTEL,
                   help=f"Threat-intel CSV (default: {DEFAULT_INTEL})")
    args = p.parse_args(argv)

    if not os.path.exists(args.logfile):
        print(f"[FAIL] Log file not found: {args.logfile}", file=sys.stderr)
        return 1

    failures, users_tried, successes = analyze(args.logfile, args.threshold, args.window)
    intel = load_threat_intel(args.intel)

    print("=" * 68)
    print("  BRUTE-FORCE DETECTION REPORT")
    print(f"  log       : {args.logfile}")
    print(f"  rule      : >= {args.threshold} failed logins from one IP within "
          f"{int(args.window)}s")
    print(f"  intel feed: {args.intel}")
    print("=" * 68)

    if not failures:
        print("\nNo 'Failed password' events found. Nothing to flag.")
        return 0

    # Rank every source IP by its worst burst so the report is deterministic.
    flagged = []
    for ip, times in sorted(failures.items()):
        burst = max_events_in_window(list(times), args.window)
        total = len(times)
        marker = "FLAGGED" if burst >= args.threshold else "ok"
        print(f"\n[{marker}] {ip}")
        print(f"    failures (total)     : {total}")
        print(f"    worst burst in {int(args.window)}s : {burst}")
        print(f"    usernames targeted   : "
              f"{', '.join(sorted(users_tried.get(ip, [])))}")
        if burst >= args.threshold:
            flagged.append(ip)

    # --- Correlate flagged IPs with threat intel + surface hidden successes ---
    print("\n" + "-" * 68)
    print("  CORRELATION: flagged IPs vs threat intel + successful logins")
    print("-" * 68)
    if not flagged:
        print("  No IP exceeded the threshold.")
    for ip in flagged:
        print(f"\n  * {ip}")
        hit = intel.get(ip)
        if hit:
            print(f"      THREAT INTEL MATCH  -> {hit['description']} "
                  f"[severity={hit['severity']}]")
        else:
            print("      threat intel        -> no match in feed")
        if ip in successes:
            # This is the alarming part: the attacker eventually guessed right.
            who = ", ".join(sorted(set(successes[ip])))
            print(f"      !! SUCCESSFUL LOGIN -> account '{who}' authenticated "
                  f"from this IP after the failures (likely compromised).")
        else:
            print("      successful login    -> none observed (attack unsuccessful)")

    print("\n" + "=" * 68)
    print(f"  SUMMARY: {len(flagged)} IP(s) flagged, "
          f"{sum(1 for ip in flagged if ip in intel)} confirmed by threat intel, "
          f"{sum(1 for ip in flagged if ip in successes)} with a successful login.")
    print("=" * 68)
    # Exit non-zero when something was flagged so this can gate a script/pipeline.
    return 2 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
