#!/usr/bin/env bash
# =============================================================================
#  get_wazuh_creds.sh - recover the Wazuh credentials and print .env lines.
#
#  RUN THIS ON THE WAZUH MANAGER VM (10.50.136.116), with sudo:
#      sudo bash scripts/get_wazuh_creds.sh
#
#  Why you need it
#  ---------------
#  Wazuh has THREE credential sets, and they are NOT the same:
#    1. Dashboard / Indexer login  -> user 'admin'      (port 443 / 9200)
#    2. Manager API                -> user 'wazuh-wui'  (port 55000)  <-- verify_env uses this
#    3. Internal indexer service   -> 'kibanaserver' etc.
#  Logging into the web dashboard uses set (1). The API in set (2) has a DIFFERENT
#  password, so pasting the dashboard password as WAZUH_PASS returns HTTP 401.
#  This script prints all of them and the exact .env block to paste.
# =============================================================================
set -uo pipefail

echo "=================================================================="
echo " Wazuh credential recovery"
echo "=================================================================="

# 1) Locate the install bundle created by 'wazuh-install.sh -a'
TAR=""
for c in ./wazuh-install-files.tar /root/wazuh-install-files.tar \
         /home/*/wazuh-install-files.tar "$HOME/wazuh-install-files.tar"; do
  [ -f "$c" ] && { TAR="$c"; break; }
done
[ -z "$TAR" ] && TAR="$(find /root /home /opt -maxdepth 3 -name 'wazuh-install-files.tar' 2>/dev/null | head -1)"

PWFILE=""
TMP="$(mktemp)"
if [ -n "$TAR" ] && [ -f "$TAR" ]; then
  echo "[*] Found install bundle: $TAR"
  if tar -O -xf "$TAR" wazuh-install-files/wazuh-passwords.txt >"$TMP" 2>/dev/null; then
    PWFILE="$TMP"
  fi
fi
# Fallback: a loose wazuh-passwords.txt
if [ -z "$PWFILE" ]; then
  for c in ./wazuh-passwords.txt /root/wazuh-passwords.txt "$HOME/wazuh-passwords.txt"; do
    [ -f "$c" ] && { PWFILE="$c"; break; }
  done
fi

if [ -z "$PWFILE" ]; then
  echo
  echo "[FAIL] Could not find wazuh-install-files.tar or wazuh-passwords.txt."
  echo "       They are created in the directory where you ran wazuh-install.sh (usually /root)."
  echo
  echo "  If the file was deleted, reset the API user password with the bundled tool"
  echo "  (it sits next to wazuh-install.sh):"
  echo "      sudo bash wazuh-passwords-tool.sh -u wazuh-wui -p 'NewStrongPassw0rd!'"
  echo "  and reset the dashboard/indexer admin the same way:"
  echo "      sudo bash wazuh-passwords-tool.sh -u admin -p 'NewStrongAdminPass!'"
  echo "  Then re-run this script or paste those into .env."
  rm -f "$TMP"
  exit 1
fi

echo "[*] Parsing credentials..."
python3 - "$PWFILE" <<'PY'
import re, sys
txt = open(sys.argv[1]).read()

def pairs(kind):
    us = re.findall(rf"{kind}_username:\s*'([^']+)'", txt)
    ps = re.findall(rf"{kind}_password:\s*'([^']+)'", txt)
    d = {}
    for u, p in zip(us, ps):
        d.setdefault(u, p)
    return d

idx = pairs("indexer")
api = pairs("api")

print("\n--- Dashboard / Indexer users  (port 443 / 9200) ---")
for u, p in idx.items():
    print(f"  {u:16} {p}")
print("\n--- Manager API users  (port 55000) ---")
for u, p in api.items():
    print(f"  {u:16} {p}")

admin_pw = idx.get("admin", "<PASTE_admin_password>")
api_user = "wazuh-wui" if "wazuh-wui" in api else (next(iter(api), "wazuh-wui"))
api_pw = api.get(api_user, "<PASTE_api_password>")

print("\n================= paste this into your .env =================")
print(f"WAZUH_USER={api_user}")
print(f"WAZUH_PASS={api_pw}")
print(f"WAZUH_INDEXER_USER=admin")
print(f"WAZUH_INDEXER_PASS={admin_pw}")
print("============================================================")

# stash for the live test below
open("/tmp/wz_env", "w").write(
    f"WZ_API_USER={api_user}\nWZ_API_PASS={api_pw}\nWZ_ADMIN_PASS={admin_pw}\n")
PY

# 2) Live-test the recovered creds locally (self-signed cert -> -k)
if [ -f /tmp/wz_env ] && command -v curl >/dev/null; then
  # shellcheck disable=SC1091
  . /tmp/wz_env
  echo
  echo "[*] Testing Manager API (https://localhost:55000)..."
  if curl -sk -u "$WZ_API_USER:$WZ_API_PASS" -X POST \
       "https://localhost:55000/security/user/authenticate?raw=true" | grep -qE '^[A-Za-z0-9_-]+\.'; then
    echo "    [OK] API auth works with $WZ_API_USER"
  else
    echo "    [WARN] API auth did not return a token - check the password above or the API port."
  fi
  echo "[*] Testing Indexer (https://localhost:9200)..."
  if curl -sk -u "admin:$WZ_ADMIN_PASS" "https://localhost:9200/_cluster/health" | grep -qi 'status'; then
    echo "    [OK] Indexer auth works with admin"
  else
    echo "    [WARN] Indexer auth failed - check the admin password above."
  fi
fi

rm -f "$TMP" /tmp/wz_env 2>/dev/null
echo
echo "Done. Paste the .env block above into your .env, then run: python3 scripts/verify_env.py"
