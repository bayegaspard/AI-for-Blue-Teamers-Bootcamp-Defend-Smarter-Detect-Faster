#!/usr/bin/env python3
"""
verify_env.py - pre-flight check students run on Day 1.

Confirms the two core services from your .env are reachable and prints a clean,
color-coded result (green tick = pass, red cross = fail). Safe to run repeatedly.

    python3 scripts/verify_env.py

Colors auto-disable when the output is not a terminal or when NO_COLOR is set.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.ollama_client import OllamaClient, OllamaError  # noqa: E402
from common.wazuh_client import WazuhClient, WazuhError      # noqa: E402
from common import wazuh_client as _wz                       # noqa: E402

_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def green(s): return _c("32", s)
def red(s): return _c("31", s)
def dim(s): return _c("2", s)
def bold(s): return _c("1", s)


TICK = green("✓")   # check mark
CROSS = red("✗")    # cross mark


def check_ollama():
    cl = OllamaClient()
    try:
        tags = cl.health()
        models = ", ".join(m.get("name", "?") for m in tags.get("models", [])) or "(none pulled)"
        return True, f"reachable at {cl.host}  ({models})", None
    except OllamaError as e:
        return False, "not reachable", str(e).split(". ")[0]


def check_wazuh():
    w = WazuhClient(timeout=8)
    try:
        data = w.health().get("data", {})
        ver = data.get("version") or data.get("api_version") or ""
        return True, f"authenticated at {w.api}" + (f"  ({ver})" if ver else ""), None
    except WazuhError as e:
        hint = None
        if _wz.WAZUH_PASS == "CHANGE_ME":
            hint = "WAZUH_PASS is still 'CHANGE_ME' - run scripts/get_wazuh_creds.sh and paste it into .env"
        elif "401" in str(e):
            hint = (f"user '{_wz.WAZUH_USER}' rejected - use the wazuh-wui API password "
                    "(not the dashboard admin password)")
        return False, str(e).split(". Check")[0], hint


def check_indexer():
    w = WazuhClient(timeout=8)
    try:
        h = w.indexer_health()
        return True, f"reachable at {w.indexer}  (status: {h.get('status', '?')})", None
    except WazuhError as e:
        if _wz.WAZUH_INDEXER_PASS == "CHANGE_ME":
            hint = "WAZUH_INDEXER_PASS is 'CHANGE_ME' - paste the admin password into .env"
        else:
            hint = ("port 9200 not reachable - open it in the security group like 55000, "
                    "or run Modules 3 and 5 from the Wazuh VM")
        return False, str(e).split(": <")[0], hint


def main() -> int:
    print()
    print(bold("  AI Blue Team Bootcamp - environment check"))
    print()

    # (name, required, ok, detail, hint). The indexer is advisory: Day 1 does not need it.
    rows = [
        ("Ollama", True) + check_ollama(),
        ("Wazuh API", True) + check_wazuh(),
        ("Indexer", False) + check_indexer(),
    ]
    req_total = req_pass = 0
    for name, required, ok, detail, hint in rows:
        mark = TICK if ok else CROSS
        tag = "" if required else dim("  (advisory: Modules 3 & 5)")
        print(f"  {mark} {bold(name.ljust(10))} {dim(detail)}{tag}")
        if hint:
            print(f"      {dim('-> ' + hint)}")
        if required:
            req_total += 1
            req_pass += 1 if ok else 0

    print()
    if req_pass == req_total:
        print("  " + green("All required checks passed. You are ready for the labs."))
        rc = 0
    else:
        print("  " + red(f"{req_pass} of {req_total} required checks passed."))
        print(dim("  Offline fallback: scripts/lab_up.sh core, then set "
                  "OLLAMA_HOST=http://localhost:11435 in .env"))
        rc = 1
    print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
