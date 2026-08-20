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

# 0) Detect this VM's private IP so the .env points at the IP, not localhost.
#    (The self-tests below run on this VM, so localhost also works here, but the
#     labs run from OTHER machines and must use the IP.)
HOST_IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)' | head -1)"
[ -z "$HOST_IP" ] && HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[ -z "$HOST_IP" ] && HOST_IP="127.0.0.1"
echo "[*] This VM's IP: $HOST_IP"

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
WZ_HOST_IP="$HOST_IP" python3 - "$PWFILE" <<'PY'
import re, sys, os
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

ip = os.environ.get("WZ_HOST_IP", "127.0.0.1")
print("\n================= paste this into your .env =================")
print(f"WAZUH_API=https://{ip}:55000")
print(f"WAZUH_INDEXER=https://{ip}:9200")
print(f"WAZUH_USER={api_user}")
print(f"WAZUH_PASS={api_pw}")
print(f"WAZUH_INDEXER_USER=admin")
print(f"WAZUH_INDEXER_PASS={admin_pw}")
print("============================================================")
print("(Use the IP above, not localhost, when the labs run from another machine.)")

# stash for the live test below
open("/tmp/wz_env", "w").write(
    f"WZ_API_USER={api_user}\nWZ_API_PASS={api_pw}\nWZ_ADMIN_PASS={admin_pw}\n")
PY

# 2) Live-test the creds on BOTH localhost and the VM IP (self-signed cert -> -k).
#    localhost proves the creds; the IP proves the API is reachable from other hosts.
if [ -f /tmp/wz_env ] && command -v curl >/dev/null; then
  # shellcheck disable=SC1091
  . /tmp/wz_env
  ip_api_ok=0; ip_idx_ok=0
  for TARGET in "localhost" "$HOST_IP"; do
    echo
    echo "[*] Testing Manager API at https://$TARGET:55000 ..."
    if curl -sk --max-time 8 -u "$WZ_API_USER:$WZ_API_PASS" -X POST \
         "https://$TARGET:55000/security/user/authenticate?raw=true" 2>/dev/null | grep -qE '^[A-Za-z0-9_-]+\.'; then
      echo "    [OK] API reachable at $TARGET"
      [ "$TARGET" = "$HOST_IP" ] && ip_api_ok=1
    else
      echo "    [WARN] API NOT reachable at $TARGET"
    fi
    echo "[*] Testing Indexer at https://$TARGET:9200 ..."
    if curl -sk --max-time 8 -u "admin:$WZ_ADMIN_PASS" "https://$TARGET:9200/_cluster/health" 2>/dev/null | grep -qi 'status'; then
      echo "    [OK] Indexer reachable at $TARGET"
      [ "$TARGET" = "$HOST_IP" ] && ip_idx_ok=1
    else
      echo "    [WARN] Indexer NOT reachable at $TARGET"
    fi
  done
  echo
  if [ "$ip_api_ok" = 1 ] && [ "$ip_idx_ok" = 1 ]; then
    echo "[OK] Both services answer on $HOST_IP, so they ARE reachable via the API from"
    echo "     other machines (as long as the security group allows it). Use the IP in .env."
  else
    echo "[!] A service answered on localhost but NOT on $HOST_IP. To fix remote access:"
    echo "    - Manager API: ensure /var/ossec/api/configuration/api.yaml has 'host: 0.0.0.0'"
    echo "      then: sudo systemctl restart wazuh-manager"
    echo "    - Indexer: ensure /etc/wazuh-indexer/opensearch.yml 'network.host' is 0.0.0.0"
    echo "      (or includes $HOST_IP) then: sudo systemctl restart wazuh-indexer"
    echo "    - Firewall/AWS: open TCP 55000 and 9200 from your VPN/student subnet only."
    echo "    Confirm what they bind to:  sudo ss -ltnp | grep -E ':55000|:9200'"
  fi
fi

rm -f "$TMP" /tmp/wz_env 2>/dev/null
echo
echo "Done. Paste the .env block above into your .env (on the machine that runs the labs),"
echo "then run: python3 scripts/verify_env.py"
