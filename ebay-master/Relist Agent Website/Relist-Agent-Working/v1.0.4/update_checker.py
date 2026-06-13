"""
Update Checker for Relist Agent
Reads versions.json from https://thetrashedpanda.com/updates/
"""

import urllib.request
import urllib.error
import json
import sys
import os
from pathlib import Path

CURRENT_VERSION = "1.0.4"
VERSIONS_JSON_URL = "https://thetrashedpanda.com/updates/versions.json"

# Get log file path (same as EXE location)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
else:
    BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "update_checker_debug.log"

def log_debug(msg):
    """Write debug message to file and console"""
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass


def parse_version(version_string):
    """Parse version string like 'v1.0.5' to tuple (1, 0, 5)"""
    try:
        version_string = str(version_string).lstrip('v')
        return tuple(map(int, version_string.split('.')))
    except:
        return (0, 0, 0)


def get_available_versions():
    """Fetch available versions from versions.json"""
    try:
        log_debug(f"[UPDATE] Fetching from: {VERSIONS_JSON_URL}")
        req = urllib.request.Request(
            VERSIONS_JSON_URL,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'close'
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            raw_data = response.read().decode('utf-8')
            log_debug(f"[UPDATE] Raw response: {raw_data}")
            data = json.loads(raw_data)
            log_debug(f"[UPDATE] Parsed JSON: {data}")
            versions = data.get('versions', [])
            log_debug(f"[UPDATE] Versions list: {versions}")
            sorted_versions = sorted(versions, key=parse_version, reverse=True)
            log_debug(f"[UPDATE] Sorted versions: {sorted_versions}")
            return sorted_versions
    except Exception as e:
        log_debug(f"[UPDATE] Failed to fetch versions: {e}")
        import traceback
        log_debug(traceback.format_exc())
        return []


def check_for_updates():
    """
    Check if a newer version is available
    Returns: (has_update, latest_version)
    """
    versions = get_available_versions()
    
    if not versions:
        return False, None

    latest = versions[0]
    current = parse_version(CURRENT_VERSION)
    remote = parse_version(latest)

    log_debug(f"[UPDATE] Current: {current}, Latest: {remote}")
    if remote > current:
        log_debug(f"[UPDATE] New version available: {latest}")
        return True, latest

    log_debug(f"[UPDATE] No update available (latest: {latest})")
    return False, None
