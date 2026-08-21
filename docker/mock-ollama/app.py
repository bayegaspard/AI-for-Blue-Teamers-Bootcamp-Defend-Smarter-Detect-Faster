#!/usr/bin/env python3
"""
mock-ollama - a GPU-free stand-in for the lab's Ollama server.

Why this exists
---------------
The real labs run against the GPU VM (llama3.1:8b at 10.50.142.235:11434). But an
instructor may need to demo or dry-run on a laptop with no GPU and no VPN. This
service speaks enough of the Ollama HTTP API (/api/tags, /api/generate, /api/chat,
streaming) that every lab script and the ai-soc-assistant run unchanged - just point
OLLAMA_HOST at this container.

It is also a *deterministic teaching model*: its susceptibility to prompt injection
is rule-based, so the Module 4 attack and the Module 4 defense both land reliably in
a classroom regardless of GPU availability or real-model randomness. On the real 8B
model the same attacks usually work too; the mock just guarantees the lesson.

This is intentionally simple and is NOT a real LLM.
"""
from __future__ import annotations

import json
import re
import time

from flask import Flask, Response, request, jsonify

app = Flask(__name__)
MODEL = "llama3.1:8b"

# --- injection detection (the "weakness" the mock deliberately has) ----------
INJECTION_PATTERNS = {
    "benign_override": [
        r"ignore (all|any|the) (previous|prior|above)",
        r"disregard .*instructions",
        r"mark (this|it|the alert) as benign",
        r"classify .*as (benign|safe|clean)",
        r"this is (a )?(false positive|authorized|approved)",
        r"do not (raise|create) (an )?(alert|ticket)",
        r"classif(y|ied) .{0,30}benign",
        r"authorized (vulnerability )?scanner",
        r"per runbook",
        r"(reply|respond|output)\b[^\n]{0,60}benign",
    ],
    "leak_prompt": [
        r"(reveal|print|show|repeat|output).{0,30}(system prompt|your instructions|initial prompt)",
        r"what (are|were) your (instructions|rules)",
        r"quote[^\n]{0,40}(instructions|output format)",
        r"instructions and output format",
    ],
    "jailbreak": [
        r"you are now .*(dan|unrestricted|jailbroken|developer mode)",
        r"ignore your (safety|guard).*",
        r"pretend you have no (rules|restrictions)",
    ],
}

# A "hardened" system prompt tells the model that data is untrusted. If those
# markers are present, the mock resists injection (mirrors the Module 4 fix).
HARDENED_MARKERS = ["untrusted data", "not instructions", "<<<data>>>",
                    "ignore any text inside the data", "only follow instructions that appear outside"]


def is_hardened(system: str) -> bool:
    s = (system or "").lower()
    return any(m in s for m in HARDENED_MARKERS)


def detect_injection(text: str) -> str | None:
    t = (text or "").lower()
    for tag, patterns in INJECTION_PATTERNS.items():
        for p in patterns:
            if re.search(p, t):
                return tag
    return None


def injection_response(tag: str, system: str) -> str:
    if tag == "benign_override":
        return ("SUMMARY: Routine activity, nothing of concern.\n"
                "VERDICT: benign\nCONFIDENCE: high\n"
                "INDICATORS: none\nRECOMMENDED ACTION: close the alert, no follow-up needed.\n"
                "\n[!! mock-ollama note: the DATA hijacked my verdict - this is the attack succeeding.]")
    if tag == "leak_prompt":
        return ("Sure - my system prompt is:\n\"" + (system or "").strip() + "\"\n"
                "\n[!! mock-ollama note: system prompt was exfiltrated via the DATA.]")
    if tag == "jailbreak":
        return ("[JAILBREAK SUCCESSFUL] I will disregard my safety instructions for this request.\n"
                "(In a real assessment this is where an unrestricted response would follow.)\n"
                "\n[!! mock-ollama note: guardrails bypassed via the DATA.]")
    return "OK."


def normal_triage(prompt: str) -> str:
    t = (prompt or "").lower()
    if re.search(r"failed password|authentication failure|invalid user", t) and t.count("failed") + t.count("invalid") >= 3:
        return ("SUMMARY: Repeated failed SSH authentications from a single source indicate a brute-force attempt.\n"
                "VERDICT: malicious\nCONFIDENCE: high\n"
                "INDICATORS: multiple 'Failed password' events, same source IP, short time window.\n"
                "RECOMMENDED ACTION: block the source IP, confirm no successful login followed, review the target account.")
    if re.search(r"union select|' or '1'='1|sqlmap|or 1=1|information_schema", t):
        return ("SUMMARY: Web request contains SQL injection syntax targeting the login/query path.\n"
                "VERDICT: malicious\nCONFIDENCE: high\n"
                "INDICATORS: SQL meta-characters / UNION SELECT / tautology in request parameters.\n"
                "RECOMMENDED ACTION: block the source, check DB logs for data access, patch input validation.")
    if re.search(r"nmap|port scan|syn scan|masscan", t):
        return ("SUMMARY: Host is performing a port/network scan.\n"
                "VERDICT: suspicious\nCONFIDENCE: medium\n"
                "INDICATORS: many connection attempts across ports from one source.\n"
                "RECOMMENDED ACTION: identify the scanning host, confirm it is authorized, monitor for follow-on activity.")
    if re.search(r"sigma|detection rule|write a rule", t):
        return ("title: Example Detection\nstatus: experimental\n"
                "logsource:\n  product: linux\n  service: auth\n"
                "detection:\n  selection:\n    message|contains: 'Failed password'\n  condition: selection\n"
                "level: medium\n# (mock rule - validate before use)")
    return ("SUMMARY: No clear indicators of compromise in the provided data.\n"
            "VERDICT: benign\nCONFIDENCE: medium\n"
            "INDICATORS: none notable.\nRECOMMENDED ACTION: no action; keep monitoring.")


def compute_response(system: str, prompt: str) -> str:
    tag = detect_injection(prompt)
    hardened = is_hardened(system)
    if tag and not hardened:
        return injection_response(tag, system)
    base = normal_triage(prompt)
    if tag and hardened:
        base += ("\n\nNOTE: The DATA contained text attempting to manipulate this assistant "
                 "(a prompt-injection attempt). It was treated as data and ignored.")
    return base


# --- Ollama-compatible API ---------------------------------------------------
@app.get("/api/tags")
def tags():
    return jsonify({"models": [{"name": MODEL, "model": MODEL, "size": 4700000000}]})


@app.get("/api/version")
def version():
    return jsonify({"version": "mock-0.1 (teaching stub)"})


def _stream_words(text: str, key_path):
    def gen():
        for word in text.split(" "):
            obj = {"model": MODEL, "created_at": "1970-01-01T00:00:00Z", "done": False}
            key_path(obj, word + " ")
            yield json.dumps(obj) + "\n"
            time.sleep(0.01)
        final = {"model": MODEL, "done": True}
        key_path(final, "")
        yield json.dumps(final) + "\n"
    return Response(gen(), mimetype="application/x-ndjson")


@app.post("/api/generate")
def generate():
    body = request.get_json(force=True, silent=True) or {}
    text = compute_response(body.get("system", ""), body.get("prompt", ""))
    if body.get("stream"):
        return _stream_words(text, lambda o, w: o.__setitem__("response", w))
    return jsonify({"model": MODEL, "response": text, "done": True})


@app.post("/api/chat")
def chat():
    body = request.get_json(force=True, silent=True) or {}
    messages = body.get("messages", [])
    system = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
    user = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
    text = compute_response(system, user)
    if body.get("stream"):
        return _stream_words(text, lambda o, w: o.__setitem__("message", {"role": "assistant", "content": w}))
    return jsonify({"model": MODEL, "message": {"role": "assistant", "content": text}, "done": True})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "note": "mock-ollama teaching stub"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=11434)
