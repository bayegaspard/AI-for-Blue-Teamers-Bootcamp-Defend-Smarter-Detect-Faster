#!/usr/bin/env python3
"""
wazuh_client.py - thin client for the Wazuh 4.14 manager API + indexer.

Used by Modules 2, 3, and 5 to pull agents and alerts programmatically so the AI
labs can feed real SIEM data into Ollama.

The Wazuh manager API (port 55000) handles auth/agents. Stored alerts live in the
Wazuh indexer (OpenSearch, port 9200), so alert queries go there.

Quick use (library):
    from common.wazuh_client import WazuhClient
    wz = WazuhClient()
    print(wz.list_agents())
    for a in wz.recent_alerts(limit=10):
        print(a["rule"]["description"])

Quick use (CLI):
    python3 common/wazuh_client.py --health
    python3 common/wazuh_client.py --agents
    python3 common/wazuh_client.py --alerts 20
    python3 common/wazuh_client.py --alerts 20 --min-level 7
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import urllib.request
import urllib.error

def _load_env() -> None:
    """Load the repo-root .env into os.environ. Uses python-dotenv if present, and
    otherwise falls back to a tiny built-in parser so the labs work on a bare VM
    with no pip installs. Existing environment variables always win."""
    envpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(envpath)
        return
    except Exception:  # dotenv not installed: parse .env ourselves
        pass
    try:
        lines = open(envpath, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return
    preexisting = set(os.environ)  # real environment variables win over .env
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k in preexisting:
            continue
        os.environ[k] = v  # within the file, a later line overrides an earlier duplicate


_load_env()

WAZUH_API = os.environ.get("WAZUH_API", "https://10.50.136.116:55000")
WAZUH_INDEXER = os.environ.get("WAZUH_INDEXER", "https://10.50.136.116:9200")
WAZUH_USER = os.environ.get("WAZUH_USER", "wazuh-wui")
WAZUH_PASS = os.environ.get("WAZUH_PASS", "CHANGE_ME")
WAZUH_INDEXER_USER = os.environ.get("WAZUH_INDEXER_USER", "admin")
WAZUH_INDEXER_PASS = os.environ.get("WAZUH_INDEXER_PASS", "CHANGE_ME")
VERIFY_TLS = os.environ.get("VERIFY_TLS", "0") not in ("0", "false", "False", "")


class WazuhError(RuntimeError):
    pass


def _ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not VERIFY_TLS:
        # Lab Wazuh uses self-signed certs. Do NOT disable verification in prod.
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


class WazuhClient:
    def __init__(self, api: str | None = None, indexer: str | None = None,
                 user: str | None = None, password: str | None = None,
                 timeout: int = 30):
        self.api = (api or WAZUH_API).rstrip("/")
        self.indexer = (indexer or WAZUH_INDEXER).rstrip("/")
        self.user = user or WAZUH_USER
        self.password = password or WAZUH_PASS
        self.timeout = timeout
        self._token: str | None = None

    # ---- manager API -------------------------------------------------------
    def _authenticate(self) -> str:
        url = f"{self.api}/security/user/authenticate"
        basic = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
        req = urllib.request.Request(url, method="POST",
                                     headers={"Authorization": f"Basic {basic}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ctx()) as resp:
                body = json.loads(resp.read().decode())
                self._token = body["data"]["token"]
                return self._token
        except urllib.error.HTTPError as e:
            raise WazuhError(f"Wazuh auth failed ({e.code}). Check WAZUH_USER/WAZUH_PASS.") from e
        except urllib.error.URLError as e:
            raise WazuhError(f"Wazuh API unreachable at {self.api}: {e}") from e

    def _api_get(self, path: str) -> dict:
        if not self._token:
            self._authenticate()
        url = f"{self.api}{path}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self._token}"})
        with urllib.request.urlopen(req, timeout=self.timeout, context=_ctx()) as resp:
            return json.loads(resp.read().decode())

    def health(self) -> dict:
        """Return manager info (also proves auth works)."""
        return self._api_get("/manager/info")

    def list_agents(self) -> list[dict]:
        data = self._api_get("/agents")
        return data.get("data", {}).get("affected_items", [])

    # ---- indexer (alerts) --------------------------------------------------
    def _indexer_post(self, path: str, body: dict) -> dict:
        url = f"{self.indexer}{path}"
        basic = base64.b64encode(
            f"{WAZUH_INDEXER_USER}:{WAZUH_INDEXER_PASS}".encode()).decode()
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data, method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Basic {basic}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ctx()) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            raise WazuhError(f"Wazuh indexer unreachable at {self.indexer}: {e}") from e

    def recent_alerts(self, limit: int = 20, min_level: int = 0) -> list[dict]:
        """Return the most recent alerts (optionally filtered by rule level)."""
        query: dict = {
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"range": {"rule.level": {"gte": min_level}}},
        }
        res = self._indexer_post("/wazuh-alerts-*/_search", query)
        hits = res.get("hits", {}).get("hits", [])
        return [h.get("_source", {}) for h in hits]

    def indexer_health(self) -> dict:
        """GET the indexer cluster health (proves 9200 is reachable + creds work).

        Used by verify_env. The indexer (port 9200) is only needed for pulling stored
        alerts (Modules 3 and 5), not for Day 1.
        """
        url = f"{self.indexer}/_cluster/health"
        basic = base64.b64encode(
            f"{WAZUH_INDEXER_USER}:{WAZUH_INDEXER_PASS}".encode()).decode()
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {basic}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ctx()) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            raise WazuhError(f"Wazuh indexer unreachable at {self.indexer}: {e}") from e


# ---- CLI -------------------------------------------------------------------
def _cli(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Query the lab's Wazuh manager/indexer.")
    p.add_argument("--health", action="store_true")
    p.add_argument("--agents", action="store_true")
    p.add_argument("--alerts", type=int, metavar="N", help="Fetch N recent alerts.")
    p.add_argument("--min-level", type=int, default=0)
    args = p.parse_args(argv)

    wz = WazuhClient()
    try:
        if args.health:
            info = wz.health().get("data", {})
            print(f"[OK] Wazuh manager {info.get('version', '?')} reachable at {wz.api}")
            return 0
        if args.agents:
            for a in wz.list_agents():
                print(f"{a.get('id'):>4}  {a.get('name'):<20} {a.get('ip','-'):<16} {a.get('status')}")
            return 0
        if args.alerts is not None:
            for a in wz.recent_alerts(limit=args.alerts, min_level=args.min_level):
                rule = a.get("rule", {})
                print(f"[L{rule.get('level','?'):>2}] {a.get('timestamp','')[:19]}  "
                      f"{rule.get('description','(no desc)')}")
            return 0
        p.print_help()
        return 0
    except WazuhError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
