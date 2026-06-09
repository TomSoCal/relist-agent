import base64
import json
import urllib.parse
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import requests

# Handle PyInstaller bundled paths
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
TOKEN_FILE = BASE_DIR / "tokens.json"

OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
OAUTH_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"

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
        raise RuntimeError(
            "No refresh token — token expired. "
            "Go to developer.ebay.com > User Tokens > Sign in to Production, "
            "copy the new token, and re-run: python ebay_relist_agent.py --setup"
        )

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


def _do_oauth(cfg: dict) -> None:
    auth_url = (
        f"{OAUTH_AUTH_URL}?client_id={urllib.parse.quote(cfg['app_id'])}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(cfg['ru_name'])}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )
    print("\nOpening browser for eBay authorization...")
    webbrowser.open(auth_url)
    print("\nAfter you approve, your browser will redirect to a URL that fails to load.")
    print("Copy the full URL from your browser's address bar and paste it below.\n")

    raw = input("Paste the redirect URL here: ").strip()
    params = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
    if "code" not in params:
        print("ERROR: No 'code' found in the URL. Make sure you copied the full URL.")
        raise SystemExit(1)
    code = params["code"][0]

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


def _paste_portal_token() -> None:
    print("\nPaste the token from the developer portal (User Tokens > Sign in to Production):")
    token = input("Token: ").strip()
    if not token:
        print("ERROR: No token entered.")
        raise SystemExit(1)
    print("Expiry date shown on portal (e.g. 'Thu, 18 Nov 2027 18:33:06 GMT').")
    expiry_raw = input("Expiry (leave blank to default to 18 months from now): ").strip()
    now = datetime.now(timezone.utc)
    if expiry_raw:
        import email.utils
        try:
            expires_at = email.utils.parsedate_to_datetime(expiry_raw)
        except Exception:
            print(f"Could not parse '{expiry_raw}', defaulting to 18 months from now.")
            expires_at = now + timedelta(days=548)
    else:
        expires_at = now + timedelta(days=548)
    save_tokens({
        "access_token": token,
        "refresh_token": "",
        "expires_at": expires_at.isoformat(),
    })
    print("Tokens saved.")


def interactive_setup() -> None:
    print("=" * 60)
    print("eBay Relist Agent Setup")
    print("=" * 60)
    print("""
You need from developer.ebay.com > My Account > Application Keys:
  - App ID (Client ID), Cert ID (Client Secret), Dev ID, RuName
And a Gmail App Password from myaccount.google.com > Security > App Passwords.
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
    print("\nHow would you like to authenticate?")
    print("  1) Paste token from developer portal (recommended)")
    print("  2) OAuth redirect flow (browser-based)")
    choice = input("Choice [1/2]: ").strip()
    if choice == "2":
        _do_oauth(cfg)
    else:
        _paste_portal_token()
    print("\nSetup complete! Run setup_task.ps1 (as admin) to schedule daily runs.")
