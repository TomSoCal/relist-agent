"""
PandaSuite Shared API Configuration Module

All PandaSuite apps use this module to load/save API credentials.
Supports multiple platforms (eBay, Amazon, Etsy, etc.)

Location: C:\Users\tom\AppData\Roaming\PandaSuite\
Structure:
  - ebay/config.json + tokens.json
  - amazon/config.json + tokens.json
  - etsy/config.json + tokens.json
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import requests
import base64


class PandaSuiteAPI:
    """Centralized API credential management for all PandaSuite apps"""

    def __init__(self):
        self.suite_path = Path(os.environ['APPDATA']) / 'PandaSuite'
        self.suite_path.mkdir(parents=True, exist_ok=True)

    def get_platform_path(self, platform: str) -> Path:
        """Get path to platform folder (e.g., 'ebay', 'amazon')"""
        platform_path = self.suite_path / platform.lower()
        platform_path.mkdir(parents=True, exist_ok=True)
        return platform_path

    def load_config(self, platform: str) -> dict:
        """Load platform config (app credentials)"""
        config_file = self.get_platform_path(platform) / 'config.json'
        if not config_file.exists():
            return {}
        with open(config_file, 'r') as f:
            return json.load(f)

    def save_config(self, platform: str, config: dict) -> None:
        """Save platform config"""
        config_file = self.get_platform_path(platform) / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def load_tokens(self, platform: str) -> dict:
        """Load platform tokens (access_token, refresh_token)"""
        tokens_file = self.get_platform_path(platform) / 'tokens.json'
        if not tokens_file.exists():
            return {}
        with open(tokens_file, 'r') as f:
            return json.load(f)

    def save_tokens(self, platform: str, tokens: dict) -> None:
        """Save platform tokens"""
        tokens_file = self.get_platform_path(platform) / 'tokens.json'
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)

    def refresh_token_if_needed(self, platform: str) -> str:
        """
        Check if token is expired, refresh if needed.
        Returns access_token ready to use.
        """
        if platform.lower() != 'ebay':
            raise NotImplementedError(f"Token refresh not implemented for {platform}")

        config = self.load_config(platform)
        tokens = self.load_tokens(platform)

        now = datetime.now(timezone.utc)
        try:
            expires_at = datetime.fromisoformat(tokens.get("expires_at", "2000-01-01T00:00:00+00:00"))
        except ValueError:
            expires_at = now

        # If token still valid for 5+ minutes, use it
        if tokens.get("access_token") and expires_at > now + timedelta(minutes=5):
            return tokens["access_token"]

        # Need to refresh
        if not tokens.get("refresh_token"):
            raise RuntimeError(
                f"No refresh token for {platform}. "
                "Run setup to re-authenticate."
            )

        # Refresh via eBay OAuth
        creds = base64.b64encode(
            f"{config['app_id']}:{config['cert_id']}".encode()
        ).decode()

        SCOPES = " ".join([
            "https://api.ebay.com/oauth/api_scope",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
        ])

        resp = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
                "scope": SCOPES
            },
            timeout=30,
        )

        if not resp.ok:
            raise RuntimeError(
                f"Token refresh failed ({resp.status_code}). "
                "Run setup to re-authenticate."
            )

        data = resp.json()
        tokens["access_token"] = data["access_token"]
        tokens["expires_at"] = (
            now + timedelta(seconds=data["expires_in"])
        ).isoformat()

        if "refresh_token" in data:
            tokens["refresh_token"] = data["refresh_token"]

        self.save_tokens(platform, tokens)
        return tokens["access_token"]

    def get_access_token(self, platform: str) -> str:
        """Get valid access token (refreshes if needed)"""
        return self.refresh_token_if_needed(platform)

    def platform_configured(self, platform: str) -> bool:
        """Check if platform credentials exist"""
        config = self.load_config(platform)
        tokens = self.load_tokens(platform)
        return bool(config and tokens)

    def list_platforms(self) -> list:
        """List all configured platforms"""
        platforms = []
        for item in self.suite_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                platforms.append(item.name)
        return sorted(platforms)


# Usage example:
# suite = PandaSuiteAPI()
# token = suite.get_access_token('ebay')  # Auto-refreshes if needed
# config = suite.load_config('ebay')
