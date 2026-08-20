#!/usr/bin/env python3
"""
victim-web — an INTENTIONALLY VULNERABLE login app for the detection lab (Module 2).

DO NOT deploy this anywhere real. It exists so students can generate realistic attack
telemetry (brute force + SQL injection) and then detect it.

Vulnerabilities on purpose:
  * SQL injection in /login (string-formatted query).
  * Weak/known credentials (admin/admin123) for brute-force practice.
  * Verbose auth logging to /var/log/victim-web/auth.log in a syslog-like format
    that Wazuh (or the log-generator) can ingest.
"""
from __future__ import annotations

import datetime
import os
import sqlite3

from flask import Flask, request, Response

app = Flask(__name__)
LOG_DIR = "/var/log/victim-web"
LOG_FILE = os.path.join(LOG_DIR, "auth.log")
DB = "/tmp/victim.db"


def init_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    con.execute("DELETE FROM users")
    con.executemany("INSERT INTO users VALUES (?, ?)",
                    [("admin", "admin123"), ("analyst", "Password1"), ("svc_backup", "backup2024")])
    con.commit()
    con.close()


def log_line(msg: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%b %d %H:%M:%S")
    line = f"{ts} victim-web app[1]: {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line, flush=True)


PAGE = """<!doctype html><title>Corp Portal</title>
<h2>Corporate Portal — Sign in</h2>
<form method=post action=/login>
  <input name=username placeholder=username> <input name=password type=password placeholder=password>
  <button>Login</button>
</form><p style="color:#888">Test app for the detection lab. Do not use real credentials.</p>"""


@app.get("/")
def home():
    return PAGE


@app.post("/login")
def login():
    user = request.form.get("username", "")
    pw = request.form.get("password", "")
    src = request.headers.get("X-Forwarded-For", request.remote_addr)
    con = sqlite3.connect(DB)
    # VULNERABLE ON PURPOSE: string-formatted SQL -> SQL injection.
    q = f"SELECT * FROM users WHERE username = '{user}' AND password = '{pw}'"
    try:
        row = con.execute(q).fetchone()
    except Exception as e:
        log_line(f"SQL error for user '{user}' from {src}: {e}")
        con.close()
        return Response("error", status=500)
    con.close()
    if row:
        log_line(f"Accepted password for {user} from {src} port 0 http")
        return Response("Welcome, authenticated user!", status=200)
    log_line(f"Failed password for {user} from {src} port 0 http")
    return Response("Invalid credentials", status=401)


@app.get("/products")
def products():
    ua = request.headers.get("User-Agent", "")
    src = request.headers.get("X-Forwarded-For", request.remote_addr)
    log_line(f"GET /products from {src} ua=\"{ua}\"")
    return "product catalog"


@app.get("/health")
def health():
    return "ok"


if __name__ == "__main__":
    init_db()
    log_line("victim-web started")
    app.run(host="0.0.0.0", port=8081)
