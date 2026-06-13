"""
Update Checker for Relist Agent
Reads versions.json from https://thetrashedpanda.com/updates/
"""

import urllib.request
import urllib.error
import json

CURRENT_VERSION = "1.0.4"
VERSIONS_JSON_URL = "https://thetrashedpanda.com/updates/versions.json"


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
        print(f"[UPDATE] Fetching from: {VERSIONS_JSON_URL}")
        req = urllib.request.Request(
            VERSIONS_JSON_URL,
            headers={'User-Agent': 'Relist-Agent/1.0.4'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            raw_data = response.read().decode('utf-8')
            print(f"[UPDATE] Raw response: {raw_data}")
            data = json.loads(raw_data)
            print(f"[UPDATE] Parsed JSON: {data}")
            versions = data.get('versions', [])
            print(f"[UPDATE] Versions list: {versions}")
            sorted_versions = sorted(versions, key=parse_version, reverse=True)
            print(f"[UPDATE] Sorted versions: {sorted_versions}")
            return sorted_versions
    except Exception as e:
        print(f"[UPDATE] Failed to fetch versions: {e}")
        import traceback
        traceback.print_exc()
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
