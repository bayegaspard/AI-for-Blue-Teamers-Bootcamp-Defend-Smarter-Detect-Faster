#!/usr/bin/env python3
"""
detect_web_attacks.py - Module 2 (Applied Detection) web-attack signature scanner.

WHAT IT DOES
------------
Reads an HTTP access log (default: datasets/access.log) and flags each request
that matches a known attack SIGNATURE - SQL injection, path traversal, obvious
scanner tooling, or reflected-XSS probes. For every hit it prints the source IP,
the offending request, and *which* signature(s) matched, so you can see exactly
why the line was caught.

This is the "signature-based detection" half of the module (the brute-force
detector is the "behavioral / rate-based" half). Signatures are cheap and precise
for attacks with a fixed syntax - the same patterns power Wazuh rule 100101
(SQLi) and 100100 (path traversal) in docker/wazuh-agent/local_rules.xml.

USAGE
-----
    python3 detect_web_attacks.py                 # scans datasets/access.log
    python3 detect_web_attacks.py /path/to/other.log

Standard library only - no installs required.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_LOG = os.path.join(REPO_ROOT, "datasets", "access.log")
DEFAULT_INTEL = os.path.join(REPO_ROOT, "datasets", "threat_intel.csv")

# --- Signature catalogue -----------------------------------------------------
# Each signature is (name, category, compiled-regex). Patterns are matched
# case-insensitively against the WHOLE log line (request path + query + headers)
# because attack strings hide in URLs, parameters, and User-Agents alike.
SIGNATURES = [
    ("SQLi: tautology (OR 1=1)", "sql_injection",
     re.compile(r"(?:'|%27)?\s*or\s+'?1'?\s*=\s*'?1", re.I)),
    ("SQLi: OR 1=1", "sql_injection",
     re.compile(r"\bor\s+1\s*=\s*1\b", re.I)),
    ("SQLi: UNION SELECT", "sql_injection",
     re.compile(r"union\s+select", re.I)),
    ("SQLi: information_schema", "sql_injection",
     re.compile(r"information_schema", re.I)),
    ("SQLi: inline comment (--)", "sql_injection",
     re.compile(r"--\s", re.I)),
    ("Path traversal (../)", "path_traversal",
     re.compile(r"(?:\.\./|\.\.%2f|%2e%2e/)", re.I)),
    ("Sensitive file access (/etc/passwd)", "path_traversal",
     re.compile(r"/etc/passwd", re.I)),
    ("Scanner tool user-agent", "recon_tool",
     re.compile(r"\b(sqlmap|nikto|nmap|masscan|dirbuster|gobuster|wpscan)\b", re.I)),
    ("XSS: <script> probe", "xss",
     re.compile(r"<script\b|onerror\s*=|javascript:", re.I)),
]

# Combined/Common log format:
#   IP - - [ts] "METHOD PATH PROTO" status size "referer" "user-agent"
LINE_RE = re.compile(
    r'^(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s'
    r'.*?"(?P<request>[^"]*)"\s'
    r'(?P<status>\d{3})'
)


def load_intel_ips(path: str) -> dict[str, str]:
    """Return {ip: 'description [severity]'} for IP indicators in the feed."""
    out: dict[str, str] = {}
    if not os.path.exists(path):
        return out
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("type", "").strip().lower() == "ip":
                out[row["indicator"].strip()] = (
                    f"{row.get('description', '').strip()} "
                    f"[severity={row.get('severity', '').strip()}]")
    return out


def scan_line(line: str) -> list[str]:
    """Return the names of every signature that matches this line."""
    return [name for name, _cat, rx in SIGNATURES if rx.search(line)]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Scan an HTTP access log for web-attack signatures.")
    p.add_argument("logfile", nargs="?", default=DEFAULT_LOG,
                   help=f"Access log to scan (default: {DEFAULT_LOG})")
    p.add_argument("--intel", default=DEFAULT_INTEL,
                   help=f"Threat-intel CSV for IP correlation (default: {DEFAULT_INTEL})")
    args = p.parse_args(argv)

    if not os.path.exists(args.logfile):
        print(f"[FAIL] Log file not found: {args.logfile}", file=sys.stderr)
        return 1

    intel = load_intel_ips(args.intel)

    print("=" * 68)
    print("  WEB-ATTACK SIGNATURE SCAN")
    print(f"  log : {args.logfile}")
    print("=" * 68)

    findings = 0
    offenders: dict[str, int] = {}     # ip -> number of malicious requests
    lineno = 0
    with open(args.logfile, "r", errors="replace") as f:
        for line in f:
            lineno += 1
            line = line.rstrip("\n")
            # Skip comments and blank lines (poisoned.log ships with # headers).
            if not line.strip() or line.lstrip().startswith("#"):
                continue

            hits = scan_line(line)
            if not hits:
                continue

            findings += 1
            m = LINE_RE.match(line)
            ip = m.group("ip") if m else "?"
            request = m.group("request") if m else line
            status = m.group("status") if m else "?"
            offenders[ip] = offenders.get(ip, 0) + 1

            print(f"\n[HIT] line {lineno}  src={ip}  status={status}")
            print(f'      request : "{request}"')
            print(f"      matched : {', '.join(hits)}")

    # --- summary + threat-intel correlation ----------------------------------
    print("\n" + "-" * 68)
    if findings == 0:
        print("  No web-attack signatures matched. Log looks clean.")
        print("-" * 68)
        return 0

    print(f"  {findings} malicious request(s) from {len(offenders)} source IP(s):")
    for ip, count in sorted(offenders.items()):
        note = intel.get(ip)
        tag = f"  <-- THREAT INTEL: {note}" if note else ""
        print(f"    {ip:<16} {count} request(s){tag}")
    print("-" * 68)
    # Non-zero exit so this can gate a pipeline when attacks are present.
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
