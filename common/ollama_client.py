#!/usr/bin/env python3
"""
ollama_client.py - thin, dependency-light client for the lab's Ollama server.

Used by every AI-assisted lab (Modules 1, 3, 4, 5). It talks to whatever
OLLAMA_HOST points at in your .env: the real GPU VM (10.50.142.235:11434) or
the local `mock-ollama` container (no GPU required).

Quick use (library):
    from common.ollama_client import OllamaClient
    ai = OllamaClient()
    print(ai.generate("Summarize this SSH log line: <line>"))

Quick use (CLI):
    python3 common/ollama_client.py "Explain what a brute-force attack looks like in auth.log"
    echo "<log line>" | python3 common/ollama_client.py --stdin --system "You are a SOC analyst."
    python3 common/ollama_client.py --health
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error

# --- optional niceties (never required) -------------------------------------
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

DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://10.50.142.235:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

# A sensible default persona for defensive security work. Labs override this.
SOC_SYSTEM_PROMPT = (
    "You are a senior SOC (Security Operations Center) analyst assistant. "
    "You help human analysts triage alerts, summarize logs, and explain attacker "
    "behavior clearly and concisely. Be precise, cite the specific fields/lines that "
    "justify your conclusion, and never invent details that are not in the input."
)


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    """Minimal Ollama client using only the Python standard library."""

    def __init__(self, host: str | None = None, model: str | None = None, timeout: int = 300):
        self.host = (host or DEFAULT_HOST).rstrip("/")
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout

    # ---- low level ---------------------------------------------------------
    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.host}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except TimeoutError as e:
            raise OllamaError(
                f"Ollama at {self.host} did not answer within {self.timeout}s. On first use "
                "the model loads into memory - retry once (it stays warm for a few minutes). "
                "If it keeps timing out, the GPU VM may be running on CPU: check `ollama ps` "
                "(PROCESSOR should say GPU) and `nvidia-smi` on the GPU VM."
            ) from e
        except urllib.error.URLError as e:  # connection refused, DNS, etc.
            reason = getattr(e, "reason", e)
            if isinstance(reason, TimeoutError):
                raise OllamaError(
                    f"Ollama at {self.host} timed out after {self.timeout}s (model loading on "
                    "first use, or the GPU VM is on CPU). Retry once; if it persists check "
                    "`ollama ps` and `nvidia-smi` on the GPU VM."
                ) from e
            raise OllamaError(
                f"Could not reach Ollama at {self.host}. "
                f"Is OLLAMA_HOST correct and reachable? Underlying error: {e}"
            ) from e

    # ---- public API --------------------------------------------------------
    def health(self) -> dict:
        """Return the list of models the server has, or raise OllamaError."""
        url = f"{self.host}/api/tags"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as e:
            raise OllamaError(f"Ollama not reachable at {self.host}: {e}") from e

    def generate(self, prompt: str, system: str | None = SOC_SYSTEM_PROMPT,
                 temperature: float = 0.2, num_predict: int = 512) -> str:
        """Single-shot completion. Low temperature by default for analytic tasks."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict},
        }
        out = self._post("/api/generate", payload)
        return out.get("response", "")

    def chat(self, messages: list[dict], temperature: float = 0.2,
             num_predict: int = 512) -> str:
        """Multi-turn chat. `messages` = [{"role": "system"|"user"|"assistant", "content": ...}]."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict},
        }
        out = self._post("/api/chat", payload)
        return out.get("message", {}).get("content", "")

    def stream(self, prompt: str, system: str | None = SOC_SYSTEM_PROMPT,
               temperature: float = 0.2):
        """Yield response chunks as they arrive (nice for live demos)."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model, "prompt": prompt, "system": system,
            "stream": True, "options": {"temperature": temperature},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                for raw in resp:
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if obj.get("response"):
                        yield obj["response"]
                    if obj.get("done"):
                        break
        except (urllib.error.URLError, TimeoutError) as e:
            raise OllamaError(f"Stream failed against {self.host}: {e}") from e


# ---- CLI -------------------------------------------------------------------
def _cli(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Talk to the lab's Ollama server.")
    p.add_argument("prompt", nargs="?", help="Prompt text (omit with --stdin).")
    p.add_argument("--stdin", action="store_true", help="Read the prompt from stdin.")
    p.add_argument("--system", default=SOC_SYSTEM_PROMPT, help="System prompt.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--temp", type=float, default=0.2)
    p.add_argument("--timeout", type=int, default=300, help="Request timeout in seconds.")
    p.add_argument("--stream", action="store_true", help="Stream the output.")
    p.add_argument("--health", action="store_true", help="Check server + list models.")
    args = p.parse_args(argv)

    client = OllamaClient(host=args.host, model=args.model, timeout=args.timeout)

    if args.health:
        try:
            tags = client.health()
            models = [m.get("name") for m in tags.get("models", [])]
            print(f"[OK] Ollama reachable at {client.host}")
            print(f"     Models available: {', '.join(models) if models else '(none pulled)'}")
            return 0
        except OllamaError as e:
            print(f"[FAIL] {e}", file=sys.stderr)
            return 1

    prompt = sys.stdin.read() if args.stdin else args.prompt
    if not prompt:
        p.error("Provide a prompt argument or use --stdin.")

    try:
        if args.stream:
            for chunk in client.stream(prompt, system=args.system, temperature=args.temp):
                print(chunk, end="", flush=True)
            print()
        else:
            print(client.generate(prompt, system=args.system, temperature=args.temp))
        return 0
    except OllamaError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
