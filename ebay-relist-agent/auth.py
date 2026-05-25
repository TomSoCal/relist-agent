import base64
import json
import queue
import threading
import urllib.parse
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
TOKEN_FILE = BASE_DIR / "tokens.json"

OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
OAUTH_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"
CALLBACK_PORT = 8080

SCOPES = " ".join([
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
])


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"No config at {CONFIG_FILE}. Run: python ebay_relist_agent.py --setup")
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def load_tokens() -> dict:
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_tokens(tokens: dict) -> None:
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)


def get_access_token(cfg: dict) -> str:
    tokens = load_tokens()
    now = datetime.now(timezone.utc)
    try:
        expires_at = datetime.fromisoformat(tokens.get("expires_at", "2000-01-01T00:00:00+00:00"))
    except ValueError:
        expires_at = now

    if tokens.get("access_token") and expires_at > now + timedelta(minutes=5):
        return tokens["access_token"]

    if not tokens.get("refresh_token"):
        raise RuntimeError("No refresh token found — run with --setup to authenticate.")

    creds = base64.b64encode(f"{cfg['app_id']}:{cfg['cert_id']}".encode()).decode()
    resp = requests.post(
        OAUTH_TOKEN_URL,
        headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"], "scope": SCOPES},
        timeout=30,
    )
    try:
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Token refresh failed ({resp.status_code}) — re-run --setup if credentials changed") from e
    data = resp.json()
    tokens["access_token"] = data["access_token"]
    tokens["expires_at"] = (now + timedelta(seconds=data["expires_in"])).isoformat()
    if "refresh_token" in data:
        tokens["refresh_token"] = data["refresh_token"]
    save_tokens(tokens)
    return tokens["access_token"]


def _serve_until_code(server: HTTPServer, code_queue: queue.Queue) -> None:
    while code_queue.empty():
        server.handle_request()


def _do_oauth(cfg: dict) -> None:
    auth_url = (
        f"{OAUTH_AUTH_URL}?client_id={urllib.parse.quote(cfg['app_id'])}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(cfg['ru_name'])}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )
    auth_code_queue: queue.Queue = queue.Queue()

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in params:
                auth_code_queue.put(params["code"][0])
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h1>Authorization successful! You may close this tab.</h1>")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h1>Waiting...</h1>")

        def log_message(self, *_):
            pass

    server = HTTPServer(("127.0.0.1", CALLBACK_PORT), _Handler)
    threading.Thread(target=_serve_until_code, args=(server, auth_code_queue), daemon=True).start()
    print("\nOpening browser for eBay authorization...")
    webbrowser.open(auth_url)
    print("Waiting for authorization (120s timeout)...")
    try:
        code = auth_code_queue.get(timeout=120)
    except queue.Empty:
        print("ERROR: Timed out.")
        raise SystemExit(1)
    finally:
        server.server_close()

    creds = base64.b64encode(f"{cfg['app_id']}:{cfg['cert_id']}".encode()).decode()
    resp = requests.post(
        OAUTH_TOKEN_URL,
        headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": cfg["ru_name"]},
        timeout=30,
    )
    if not resp.ok:
        print(f"ERROR: {resp.status_code}\n{resp.text}")
        raise SystemExit(1)
    data = resp.json()
    if not data.get("refresh_token"):
        raise RuntimeError("eBay did not return a refresh token. Check your app credentials and scopes.")
    now = datetime.now(timezone.utc)
    save_tokens({
        "access_token":  data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at":    (now + timedelta(seconds=data["expires_in"])).isoformat(),
    })
    print("Tokens saved.")


def interactive_setup() -> None:
    print("=" * 60)
    print("eBay Relist Agent Setup")
    print("=" * 60)
    print("""
You need a free eBay developer account:
  1. Go to https://developer.ebay.com and sign in
  2. Create a new application keyset (Production environment)
  3. Under "User Tokens", add a redirect URI: http://localhost:8080/callback
  4. Note the RuName shown next to that redirect URI
  5. Copy your App ID, Cert ID, and Dev ID from the keyset
  6. For Gmail: create an App Password at myaccount.google.com > Security > App Passwords
""")
    cfg = {
        "app_id":             input("App ID (Client ID):      ").strip(),
        "cert_id":            input("Cert ID (Client Secret): ").strip(),
        "dev_id":             input("Dev ID:                  ").strip(),
        "ru_name":            input("RuName:                  ").strip(),
        "gmail_app_password": input("Gmail App Password:      ").strip(),
    }
    save_config(cfg)
    print(f"\nConfig saved to {CONFIG_FILE}")
    _do_oauth(cfg)
    print("\nSetup complete! Run setup_task.ps1 (as admin) to schedule daily runs.")
