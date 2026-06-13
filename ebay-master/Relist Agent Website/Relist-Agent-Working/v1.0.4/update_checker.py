"""
Update Checker for Relist Agent
Checks https://thetrashpanda/updates/ for newer versions
"""

import urllib.request
import urllib.error
import re
from pathlib import Path

CURRENT_VERSION = "1.0.4"
UPDATES_URL = "https://thetrashpanda/updates/"


def parse_version(version_string):
    """Parse version string like 'v1.0.5' to tuple (1, 0, 5)"""
    try:
        # Extract numbers from version string like 'v1.0.4'
        match = re.search(r'v?(\d+)\.(\d+)\.(\d+)', version_string)
        if match:
            return tuple(map(int, match.groups()))
    except:
        pass
    return (0, 0, 0)


def get_available_versions():
    """Fetch list of available versions from updates directory"""
    try:
        req = urllib.request.Request(
            UPDATES_URL,
            headers={'User-Agent': 'Relist-Agent/1.0.4'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')
            # Extract version folders (v1.0.4, v1.0.5, etc)
            versions = re.findall(r'v\d+\.\d+\.\d+', html)
            return sorted(set(versions), key=parse_version, reverse=True)
    except Exception as e:
        print(f"[UPDATE] Failed to fetch versions: {e}")
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

    if remote > current:
        print(f"[UPDATE] New version available: {latest}")
        return True, latest

    print(f"[UPDATE] No update available (latest: {latest})")
    return False, None
