# eBay Listing Refresh Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily agent that ends the 10 oldest fixed-price eBay listings, re-creates them as fresh listings with identical details, ends any zero-quantity listings, and emails a report to tomnissley@gmail.com.

**Architecture:** Five focused modules — `auth` (OAuth), `ebay_api` (Trading API wrapper), `listing_logic` (filtering/sorting), `notifications` (email + toast), and a main orchestrator. Reuses the eBay developer app credentials pattern from `ebay_monitor`. Scheduled via Windows Task Scheduler at 12pm daily.

**Tech Stack:** Python 3.x, `requests`, `smtplib`/`ssl` (stdlib), eBay Trading API (XML/SOAP), Windows Task Scheduler, pytest

---

### Task 1: Scaffold the project

**Files:**
- Create: `C:\Users\tom\agents\ebay-relist-agent\requirements.txt`
- Create: `C:\Users\tom\agents\ebay-relist-agent\run.bat`
- Create: `C:\Users\tom\agents\ebay-relist-agent\tests\__init__.py`

- [ ] **Step 1: Create directory structure**

```powershell
New-Item -ItemType Directory -Force "C:\Users\tom\agents\ebay-relist-agent\tests"
```

- [ ] **Step 2: Create requirements.txt**

Create `C:\Users\tom\agents\ebay-relist-agent\requirements.txt`:
```
requests
pytest
```

- [ ] **Step 3: Create run.bat**

Create `C:\Users\tom\agents\ebay-relist-agent\run.bat`:
```bat
@echo off
cd /d "%~dp0"
python ebay_relist_agent.py
pause
```

- [ ] **Step 4: Create tests/__init__.py**

Create `C:\Users\tom\agents\ebay-relist-agent\tests\__init__.py` as an empty file.

- [ ] **Step 5: Install dependencies**

```
cd C:\Users\tom\agents\ebay-relist-agent
pip install -r requirements.txt
```

Expected: `requests` and `pytest` installed (or already satisfied).

- [ ] **Step 6: Commit**

```
git -C C:\Users\tom\agents init
git -C C:\Users\tom\agents add ebay-relist-agent/requirements.txt ebay-relist-agent/run.bat ebay-relist-agent/tests/
git -C C:\Users\tom\agents commit -m "feat: scaffold ebay-relist-agent project"
```

---

### Task 2: auth.py — Config and OAuth token management

**Files:**
- Create: `C:\Users\tom\agents\ebay-relist-agent\auth.py`
- Create: `C:\Users\tom\agents\ebay-relist-agent\tests\test_auth.py`

Handles reading config/tokens from disk, refreshing the OAuth access token, and running the interactive first-time OAuth flow (`--setup`). Note the new `sell.inventory` scope required for `AddItem`.

- [ ] **Step 1: Write the failing tests**

Create `C:\Users\tom\agents\ebay-relist-agent\tests\test_auth.py`:
```python
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_get_access_token_returns_cached_token():
    from auth import get_access_token
    cfg = {"app_id": "app", "cert_id": "cert", "dev_id": "dev", "ru_name": "ru"}
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    tokens = {"access_token": "cached_token", "expires_at": future, "refresh_token": "rt"}
    with patch("auth.load_tokens", return_value=tokens):
        result = get_access_token(cfg)
    assert result == "cached_token"


def test_get_access_token_refreshes_when_expired():
    from auth import get_access_token
    cfg = {"app_id": "app", "cert_id": "cert", "dev_id": "dev", "ru_name": "ru"}
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    tokens = {"access_token": "old", "expires_at": past, "refresh_token": "rt"}
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "new_token", "expires_in": 7200}
    mock_resp.raise_for_status = MagicMock()
    with patch("auth.load_tokens", return_value=tokens), \
         patch("auth.save_tokens") as mock_save, \
         patch("requests.post", return_value=mock_resp):
        result = get_access_token(cfg)
    assert result == "new_token"
    mock_save.assert_called_once()


def test_get_access_token_raises_without_refresh_token():
    from auth import get_access_token
    cfg = {"app_id": "app", "cert_id": "cert", "dev_id": "dev", "ru_name": "ru"}
    with patch("auth.load_tokens", return_value={}):
        with pytest.raises(RuntimeError, match="No refresh token"):
            get_access_token(cfg)
```

- [ ] **Step 2: Run tests to verify they fail**

```
cd C:\Users\tom\agents\ebay-relist-agent
pytest tests/test_auth.py -v
```
Expected: `ImportError` or `ModuleNotFoundError` (auth.py doesn't exist yet)

- [ ] **Step 3: Create auth.py**

Create `C:\Users\tom\agents\ebay-relist-agent\auth.py`:
```python
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
    resp.raise_for_status()
    data = resp.json()
    tokens["access_token"] = data["access_token"]
    tokens["expires_at"] = (now + timedelta(seconds=data["expires_in"])).isoformat()
    if "refresh_token" in data:
        tokens["refresh_token"] = data["refresh_token"]
    save_tokens(tokens)
    return tokens["access_token"]


_auth_code_queue: queue.Queue = queue.Queue()


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params:
            _auth_code_queue.put(params["code"][0])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h1>Authorization successful! You may close this tab.</h1>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h1>Authorization failed.</h1>")

    def log_message(self, *_):
        pass


def _do_oauth(cfg: dict) -> None:
    auth_url = (
        f"{OAUTH_AUTH_URL}?client_id={urllib.parse.quote(cfg['app_id'])}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(cfg['ru_name'])}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )
    server = HTTPServer(("127.0.0.1", CALLBACK_PORT), _CallbackHandler)
    threading.Thread(target=server.handle_request, daemon=True).start()
    print("\nOpening browser for eBay authorization...")
    webbrowser.open(auth_url)
    print("Waiting for authorization (120s timeout)...")
    try:
        code = _auth_code_queue.get(timeout=120)
    except queue.Empty:
        print("ERROR: Timed out.")
        server.server_close()
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
    now = datetime.now(timezone.utc)
    save_tokens({
        "access_token":  data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
cd C:\Users\tom\agents\ebay-relist-agent
pytest tests/test_auth.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```
git -C C:\Users\tom\agents add ebay-relist-agent/auth.py ebay-relist-agent/tests/test_auth.py
git -C C:\Users\tom\agents commit -m "feat: add auth module with OAuth token management"
```

---

### Task 3: ebay_api.py — Trading API wrapper (fetch, get_item, end_item)

**Files:**
- Create: `C:\Users\tom\agents\ebay-relist-agent\ebay_api.py`
- Create: `C:\Users\tom\agents\ebay-relist-agent\tests\test_ebay_api.py`

- [ ] **Step 1: Write the failing tests**

Create `C:\Users\tom\agents\ebay-relist-agent\tests\test_ebay_api.py`:
```python
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

ACTIVE_LIST_XML = """<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingResponse xmlns="urn:ebay:apis:eBLBaseComponents">
  <Ack>Success</Ack>
  <ActiveList>
    <ItemArray>
      <Item>
        <ItemID>111</ItemID>
        <Title>Test Item A</Title>
        <ListingType>FixedPriceItem</ListingType>
        <Quantity>2</Quantity>
        <ListingDetails><StartTime>2026-01-01T00:00:00.000Z</StartTime></ListingDetails>
      </Item>
      <Item>
        <ItemID>222</ItemID>
        <Title>Test Item B</Title>
        <ListingType>Chinese</ListingType>
        <Quantity>1</Quantity>
        <ListingDetails><StartTime>2026-01-02T00:00:00.000Z</StartTime></ListingDetails>
      </Item>
      <Item>
        <ItemID>333</ItemID>
        <Title>Test Item C</Title>
        <ListingType>FixedPriceItem</ListingType>
        <Quantity>0</Quantity>
        <ListingDetails><StartTime>2026-01-03T00:00:00.000Z</StartTime></ListingDetails>
      </Item>
    </ItemArray>
    <PaginationResult>
      <TotalNumberOfPages>1</TotalNumberOfPages>
    </PaginationResult>
  </ActiveList>
</GetMyeBaySellingResponse>"""

GET_ITEM_XML = """<?xml version="1.0" encoding="utf-8"?>
<GetItemResponse xmlns="urn:ebay:apis:eBLBaseComponents">
  <Ack>Success</Ack>
  <Item>
    <ItemID>111</ItemID>
    <Title>Test Item A</Title>
    <Description>A great item</Description>
    <PrimaryCategory><CategoryID>9876</CategoryID></PrimaryCategory>
    <StartPrice currencyID="USD">19.99</StartPrice>
    <Quantity>2</Quantity>
    <ListingDuration>GTC</ListingDuration>
    <ListingType>FixedPriceItem</ListingType>
    <ConditionID>1000</ConditionID>
    <PictureDetails>
      <PictureURL>https://i.ebayimg.com/img1.jpg</PictureURL>
      <PictureURL>https://i.ebayimg.com/img2.jpg</PictureURL>
    </PictureDetails>
    <ItemSpecifics>
      <NameValueList><Name>Brand</Name><Value>Nike</Value></NameValueList>
      <NameValueList><Name>Size</Name><Value>XL</Value></NameValueList>
    </ItemSpecifics>
    <SKU>MY-SKU-001</SKU>
    <ShippingDetails><ShippingType>Free</ShippingType></ShippingDetails>
    <ShipToLocations>US</ShipToLocations>
    <ReturnPolicy><ReturnsAcceptedOption>ReturnsAccepted</ReturnsAcceptedOption></ReturnPolicy>
    <DispatchTimeMax>1</DispatchTimeMax>
  </Item>
</GetItemResponse>"""


def _mock_resp(xml_str):
    r = MagicMock()
    r.text = xml_str
    r.raise_for_status = MagicMock()
    return r


def test_fetch_all_active_listings_returns_all_items():
    from ebay_api import fetch_all_active_listings
    cfg = {"app_id": "a", "cert_id": "c", "dev_id": "d"}
    with patch("requests.post", return_value=_mock_resp(ACTIVE_LIST_XML)):
        items = fetch_all_active_listings(cfg, "tok")
    assert len(items) == 3
    assert items[0]["item_id"] == "111"
    assert items[1]["listing_type"] == "Chinese"
    assert items[2]["quantity"] == 0


def test_fetch_all_active_listings_includes_start_time():
    from ebay_api import fetch_all_active_listings
    cfg = {"app_id": "a", "cert_id": "c", "dev_id": "d"}
    with patch("requests.post", return_value=_mock_resp(ACTIVE_LIST_XML)):
        items = fetch_all_active_listings(cfg, "tok")
    assert items[0]["start_time"] == "2026-01-01T00:00:00.000Z"


def test_get_item_extracts_all_fields():
    from ebay_api import get_item
    cfg = {"app_id": "a", "cert_id": "c", "dev_id": "d"}
    with patch("requests.post", return_value=_mock_resp(GET_ITEM_XML)):
        fields = get_item(cfg, "tok", "111")
    assert fields["title"] == "Test Item A"
    assert fields["sku"] == "MY-SKU-001"
    assert fields["primary_category_id"] == "9876"
    assert fields["start_price"] == "19.99"
    assert fields["pictures"] == [
        "https://i.ebayimg.com/img1.jpg",
        "https://i.ebayimg.com/img2.jpg",
    ]
    assert fields["item_specifics"] == [("Brand", "Nike"), ("Size", "XL")]
```

- [ ] **Step 2: Run tests to verify they fail**

```
cd C:\Users\tom\agents\ebay-relist-agent
pytest tests/test_ebay_api.py -v
```
Expected: `ImportError` (ebay_api.py doesn't exist yet)

- [ ] **Step 3: Create ebay_api.py**

Create `C:\Users\tom\agents\ebay-relist-agent\ebay_api.py`:
```python
import re
import xml.etree.ElementTree as ET

import requests

TRADING_API_URL = "https://api.ebay.com/ws/api.dll"
NS = "urn:ebay:apis:eBLBaseComponents"
ET.register_namespace("", NS)


def _t(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def _txt(el: ET.Element, path: str) -> str:
    cur = el
    for part in path.split("/"):
        cur = cur.find(_t(part))
        if cur is None:
            return ""
    return cur.text or ""


def trading_call(cfg: dict, token: str, call_name: str, body_xml: str) -> ET.Element:
    payload = (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<{call_name}Request xmlns="{NS}">\n'
        f"{body_xml}\n"
        f"</{call_name}Request>"
    )
    headers = {
        "X-EBAY-API-CALL-NAME":           call_name,
        "X-EBAY-API-APP-NAME":            cfg["app_id"],
        "X-EBAY-API-DEV-NAME":            cfg["dev_id"],
        "X-EBAY-API-CERT-NAME":           cfg["cert_id"],
        "X-EBAY-API-COMPATIBILITY-LEVEL": "1225",
        "X-EBAY-API-SITEID":              "0",
        "Content-Type":                   "text/xml",
        "Authorization":                  f"Bearer {token}",
    }
    resp = requests.post(TRADING_API_URL, data=payload.encode("utf-8"), headers=headers, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    ack = root.findtext(_t("Ack")) or ""
    if ack not in ("Success", "Warning"):
        msgs = "; ".join(el.text for el in root.findall(f".//{_t('ShortMessage')}") if el.text)
        raise RuntimeError(f"{call_name} failed: {msgs or ack}")
    return root


def fetch_all_active_listings(cfg: dict, token: str) -> list[dict]:
    items = []
    page = 1
    while True:
        body = f"""
  <ActiveList>
    <Include>true</Include>
    <Pagination><EntriesPerPage>200</EntriesPerPage><PageNumber>{page}</PageNumber></Pagination>
  </ActiveList>"""
        root = trading_call(cfg, token, "GetMyeBaySelling", body)
        for item in root.findall(f".//{_t('ActiveList')}/{_t('ItemArray')}/{_t('Item')}"):
            try:
                qty = int(item.findtext(_t("Quantity")) or "0")
            except ValueError:
                qty = 0
            items.append({
                "item_id":      item.findtext(_t("ItemID")) or "",
                "title":        (item.findtext(_t("Title")) or "")[:80],
                "listing_type": item.findtext(_t("ListingType")) or "",
                "quantity":     qty,
                "start_time":   _txt(item, "ListingDetails/StartTime"),
            })
        total_pages = int(
            root.findtext(f".//{_t('ActiveList')}/{_t('PaginationResult')}/{_t('TotalNumberOfPages')}") or "1"
        )
        if page >= total_pages:
            break
        page += 1
    return items


def get_item(cfg: dict, token: str, item_id: str) -> dict:
    body = f"""
  <ItemID>{item_id}</ItemID>
  <DetailLevel>ReturnAll</DetailLevel>
  <IncludeItemSpecifics>true</IncludeItemSpecifics>"""
    root = trading_call(cfg, token, "GetItem", body)
    item = root.find(f".//{_t('Item')}")
    if item is None:
        raise RuntimeError(f"GetItem returned no Item for {item_id}")

    pictures = [el.text for el in item.findall(f"{_t('PictureDetails')}/{_t('PictureURL')}") if el.text]
    item_specifics = [
        (nvl.findtext(_t("Name")) or "", nvl.findtext(_t("Value")) or "")
        for nvl in item.findall(f"{_t('ItemSpecifics')}/{_t('NameValueList')}")
    ]
    ship_to = [el.text for el in item.findall(_t("ShipToLocations")) if el.text]

    return {
        "title":                 _txt(item, "Title"),
        "description":           _txt(item, "Description"),
        "primary_category_id":   _txt(item, "PrimaryCategory/CategoryID"),
        "secondary_category_id": _txt(item, "SecondaryCategory/CategoryID"),
        "store_category_id":     _txt(item, "Storefront/StoreCategoryID"),
        "store_category2_id":    _txt(item, "Storefront/StoreCategory2ID"),
        "start_price":           item.findtext(_t("StartPrice")) or "0.00",
        "quantity":              _txt(item, "Quantity"),
        "listing_duration":      _txt(item, "ListingDuration"),
        "listing_type":          _txt(item, "ListingType"),
        "condition_id":          _txt(item, "ConditionID"),
        "condition_description": _txt(item, "ConditionDescription"),
        "pictures":              pictures,
        "item_specifics":        item_specifics,
        "sku":                   _txt(item, "SKU"),
        "shipping_xml":          _subtree_xml(item.find(_t("ShippingDetails"))),
        "ship_to_locations":     ship_to,
        "return_policy_xml":     _subtree_xml(item.find(_t("ReturnPolicy"))),
        "dispatch_time_max":     _txt(item, "DispatchTimeMax"),
    }


def end_item(cfg: dict, token: str, item_id: str) -> None:
    body = f"""
  <ItemID>{item_id}</ItemID>
  <EndingReason>NotAvailable</EndingReason>"""
    trading_call(cfg, token, "EndItem", body)


def _subtree_xml(el: ET.Element | None) -> str:
    if el is None:
        return ""
    raw = ET.tostring(el, encoding="unicode")
    raw = re.sub(r'\s*xmlns(?::\w+)?="[^"]*"', "", raw)
    raw = re.sub(r"<ns\d+:", "<", raw)
    raw = re.sub(r"</ns\d+:", "</", raw)
    return raw
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_ebay_api.py -v
```
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```
git -C C:\Users\tom\agents add ebay-relist-agent/ebay_api.py ebay-relist-agent/tests/test_ebay_api.py
git -C C:\Users\tom\agents commit -m "feat: add ebay_api with fetch, get_item, end_item"
```

---

### Task 4: ebay_api.py — build_additem_xml and add_item

**Files:**
- Modify: `C:\Users\tom\agents\ebay-relist-agent\ebay_api.py`
- Modify: `C:\Users\tom\agents\ebay-relist-agent\tests\test_ebay_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `C:\Users\tom\agents\ebay-relist-agent\tests\test_ebay_api.py`:
```python
ADD_ITEM_RESPONSE_XML = """<?xml version="1.0" encoding="utf-8"?>
<AddItemResponse xmlns="urn:ebay:apis:eBLBaseComponents">
  <Ack>Success</Ack>
  <ItemID>999</ItemID>
</AddItemResponse>"""


SAMPLE_FIELDS = {
    "title": "Cool Shirt", "description": "Great condition",
    "primary_category_id": "123", "secondary_category_id": "",
    "store_category_id": "456", "store_category2_id": "",
    "start_price": "19.99", "quantity": "2",
    "listing_duration": "GTC", "listing_type": "FixedPriceItem",
    "condition_id": "1000", "condition_description": "",
    "pictures": ["https://i.ebayimg.com/a.jpg", "https://i.ebayimg.com/b.jpg"],
    "item_specifics": [("Brand", "Nike"), ("Size", "XL")],
    "sku": "MY-SKU-001",
    "shipping_xml": "<ShippingDetails><ShippingType>Free</ShippingType></ShippingDetails>",
    "ship_to_locations": ["US"],
    "return_policy_xml": "<ReturnPolicy><ReturnsAcceptedOption>ReturnsAccepted</ReturnsAcceptedOption></ReturnPolicy>",
    "dispatch_time_max": "1",
}


def test_build_additem_xml_includes_sku_and_pictures():
    from ebay_api import build_additem_xml
    xml = build_additem_xml(SAMPLE_FIELDS)
    assert "MY-SKU-001" in xml
    assert "https://i.ebayimg.com/a.jpg" in xml
    assert "https://i.ebayimg.com/b.jpg" in xml


def test_build_additem_xml_includes_item_specifics():
    from ebay_api import build_additem_xml
    xml = build_additem_xml(SAMPLE_FIELDS)
    assert "Nike" in xml
    assert "Brand" in xml
    assert "Size" in xml


def test_build_additem_xml_includes_store_category():
    from ebay_api import build_additem_xml
    xml = build_additem_xml(SAMPLE_FIELDS)
    assert "456" in xml


def test_add_item_returns_new_item_id():
    from ebay_api import add_item
    cfg = {"app_id": "a", "cert_id": "c", "dev_id": "d"}
    with patch("requests.post", return_value=_mock_resp(ADD_ITEM_RESPONSE_XML)):
        new_id = add_item(cfg, "tok", SAMPLE_FIELDS)
    assert new_id == "999"
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_ebay_api.py::test_build_additem_xml_includes_sku_and_pictures tests/test_ebay_api.py::test_add_item_returns_new_item_id -v
```
Expected: `ImportError` for `build_additem_xml`, `add_item`

- [ ] **Step 3: Append build_additem_xml, _esc, and add_item to ebay_api.py**

Add to the bottom of `C:\Users\tom\agents\ebay-relist-agent\ebay_api.py`:
```python
def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_additem_xml(fields: dict) -> str:
    lines = ["<Item>"]
    lines.append(f"  <Title>{_esc(fields['title'])}</Title>")
    lines.append(f"  <Description><![CDATA[{fields['description']}]]></Description>")
    lines.append("  <ListingType>FixedPriceItem</ListingType>")
    lines.append(f"  <ListingDuration>{fields.get('listing_duration') or 'GTC'}</ListingDuration>")
    lines.append(f"  <StartPrice currencyID=\"USD\">{fields['start_price']}</StartPrice>")
    lines.append(f"  <Quantity>{fields['quantity']}</Quantity>")
    lines.append(f"  <PrimaryCategory><CategoryID>{fields['primary_category_id']}</CategoryID></PrimaryCategory>")
    if fields.get("secondary_category_id"):
        lines.append(f"  <SecondaryCategory><CategoryID>{fields['secondary_category_id']}</CategoryID></SecondaryCategory>")
    if fields.get("condition_id"):
        lines.append(f"  <ConditionID>{fields['condition_id']}</ConditionID>")
    if fields.get("condition_description"):
        lines.append(f"  <ConditionDescription>{_esc(fields['condition_description'])}</ConditionDescription>")
    if fields.get("sku"):
        lines.append(f"  <SKU>{_esc(fields['sku'])}</SKU>")
    if fields.get("pictures"):
        lines.append("  <PictureDetails>")
        for url in fields["pictures"]:
            lines.append(f"    <PictureURL>{url}</PictureURL>")
        lines.append("  </PictureDetails>")
    if fields.get("item_specifics"):
        lines.append("  <ItemSpecifics>")
        for name, value in fields["item_specifics"]:
            lines.append(f"    <NameValueList><Name>{_esc(name)}</Name><Value>{_esc(value)}</Value></NameValueList>")
        lines.append("  </ItemSpecifics>")
    if fields.get("shipping_xml"):
        lines.append(f"  {fields['shipping_xml']}")
    for loc in fields.get("ship_to_locations", []):
        lines.append(f"  <ShipToLocations>{loc}</ShipToLocations>")
    if fields.get("return_policy_xml"):
        lines.append(f"  {fields['return_policy_xml']}")
    if fields.get("dispatch_time_max"):
        lines.append(f"  <DispatchTimeMax>{fields['dispatch_time_max']}</DispatchTimeMax>")
    if fields.get("store_category_id") or fields.get("store_category2_id"):
        lines.append("  <Storefront>")
        if fields.get("store_category_id"):
            lines.append(f"    <StoreCategoryID>{fields['store_category_id']}</StoreCategoryID>")
        if fields.get("store_category2_id"):
            lines.append(f"    <StoreCategory2ID>{fields['store_category2_id']}</StoreCategory2ID>")
        lines.append("  </Storefront>")
    lines.append("</Item>")
    return "\n".join(lines)


def add_item(cfg: dict, token: str, fields: dict) -> str:
    body = build_additem_xml(fields)
    root = trading_call(cfg, token, "AddItem", body)
    new_id = root.findtext(_t("ItemID")) or ""
    if not new_id:
        raise RuntimeError("AddItem succeeded but returned no ItemID")
    return new_id
```

- [ ] **Step 4: Run all API tests**

```
pytest tests/test_ebay_api.py -v
```
Expected: 9 PASSED

- [ ] **Step 5: Commit**

```
git -C C:\Users\tom\agents add ebay-relist-agent/ebay_api.py ebay-relist-agent/tests/test_ebay_api.py
git -C C:\Users\tom\agents commit -m "feat: add build_additem_xml and add_item"
```

---

### Task 5: listing_logic.py — Filter, partition, sort

**Files:**
- Create: `C:\Users\tom\agents\ebay-relist-agent\listing_logic.py`
- Create: `C:\Users\tom\agents\ebay-relist-agent\tests\test_listing_logic.py`

- [ ] **Step 1: Write the failing tests**

Create `C:\Users\tom\agents\ebay-relist-agent\tests\test_listing_logic.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

ITEMS = [
    {"item_id": "1", "title": "Old Fixed",  "listing_type": "FixedPriceItem", "quantity": 2, "start_time": "2026-01-01T00:00:00.000Z"},
    {"item_id": "2", "title": "Auction",    "listing_type": "Chinese",        "quantity": 1, "start_time": "2026-01-02T00:00:00.000Z"},
    {"item_id": "3", "title": "Zero Qty",   "listing_type": "FixedPriceItem", "quantity": 0, "start_time": "2026-01-03T00:00:00.000Z"},
    {"item_id": "4", "title": "New Fixed",  "listing_type": "FixedPriceItem", "quantity": 5, "start_time": "2026-02-01T00:00:00.000Z"},
    {"item_id": "5", "title": "Mid Fixed",  "listing_type": "FixedPriceItem", "quantity": 1, "start_time": "2026-01-15T00:00:00.000Z"},
]


def test_partition_zero_qty_items():
    from listing_logic import partition_listings
    zero_qty, eligible = partition_listings(ITEMS)
    assert [i["item_id"] for i in zero_qty] == ["3"]


def test_partition_excludes_auctions_from_both_lists():
    from listing_logic import partition_listings
    zero_qty, eligible = partition_listings(ITEMS)
    all_ids = [i["item_id"] for i in zero_qty + eligible]
    assert "2" not in all_ids


def test_partition_eligible_contains_fixed_price_with_qty():
    from listing_logic import partition_listings
    zero_qty, eligible = partition_listings(ITEMS)
    ids = [i["item_id"] for i in eligible]
    assert "1" in ids and "4" in ids and "5" in ids


def test_select_oldest_returns_n_oldest_by_start_time():
    from listing_logic import select_oldest
    items = [
        {"item_id": "A", "start_time": "2026-01-03T00:00:00.000Z"},
        {"item_id": "B", "start_time": "2026-01-01T00:00:00.000Z"},
        {"item_id": "C", "start_time": "2026-01-02T00:00:00.000Z"},
    ]
    result = select_oldest(items, n=2)
    assert [i["item_id"] for i in result] == ["B", "C"]


def test_select_oldest_returns_all_if_fewer_than_n():
    from listing_logic import select_oldest
    items = [{"item_id": "X", "start_time": "2026-01-01T00:00:00.000Z"}]
    assert len(select_oldest(items, n=10)) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_listing_logic.py -v
```
Expected: `ImportError` (listing_logic.py doesn't exist)

- [ ] **Step 3: Create listing_logic.py**

Create `C:\Users\tom\agents\ebay-relist-agent\listing_logic.py`:
```python
AUCTION_TYPES = {"Chinese", "Dutch"}


def partition_listings(items: list[dict]) -> tuple[list[dict], list[dict]]:
    zero_qty = []
    eligible = []
    for item in items:
        if item["listing_type"] in AUCTION_TYPES:
            continue
        if item["quantity"] == 0:
            zero_qty.append(item)
        else:
            eligible.append(item)
    return zero_qty, eligible


def select_oldest(items: list[dict], n: int = 10) -> list[dict]:
    return sorted(items, key=lambda i: i["start_time"])[:n]
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_listing_logic.py -v
```
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```
git -C C:\Users\tom\agents add ebay-relist-agent/listing_logic.py ebay-relist-agent/tests/test_listing_logic.py
git -C C:\Users\tom\agents commit -m "feat: add listing_logic for filter and oldest-first selection"
```

---

### Task 6: notifications.py — Email report and Windows toast

**Files:**
- Create: `C:\Users\tom\agents\ebay-relist-agent\notifications.py`
- Create: `C:\Users\tom\agents\ebay-relist-agent\tests\test_notifications.py`

- [ ] **Step 1: Write the failing tests**

Create `C:\Users\tom\agents\ebay-relist-agent\tests\test_notifications.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_format_report_includes_relisted_items():
    from notifications import format_report
    report = format_report(
        relisted=[{"old_id": "111", "new_id": "999", "title": "Cool Shirt"}],
        ended_zero_qty=[],
        failures=[],
    )
    assert "111" in report and "999" in report and "Cool Shirt" in report


def test_format_report_includes_zero_qty_items():
    from notifications import format_report
    report = format_report(
        relisted=[],
        ended_zero_qty=[{"item_id": "555", "title": "Old Hat"}],
        failures=[],
    )
    assert "555" in report and "Old Hat" in report


def test_format_report_includes_failures():
    from notifications import format_report
    report = format_report(
        relisted=[],
        ended_zero_qty=[],
        failures=[{"item_id": "777", "title": "Bad Item", "reason": "API error"}],
    )
    assert "777" in report and "API error" in report


def test_format_subject_includes_date_and_brand():
    from notifications import format_subject
    subject = format_subject("2026-05-24")
    assert "2026-05-24" in subject and "eBay" in subject
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_notifications.py -v
```
Expected: `ImportError` (notifications.py doesn't exist)

- [ ] **Step 3: Create notifications.py**

Create `C:\Users\tom\agents\ebay-relist-agent\notifications.py`:
```python
import smtplib
import ssl
import subprocess
from email.mime.text import MIMEText

SENDER = "tomnissley@gmail.com"
RECIPIENT = "tomnissley@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def format_subject(date_str: str) -> str:
    return f"eBay Relist Report — {date_str}"


def format_report(relisted: list[dict], ended_zero_qty: list[dict], failures: list[dict]) -> str:
    lines = [f"Relisted ({len(relisted)}):"]
    if relisted:
        for r in relisted:
            lines.append(f"  - [{r['old_id']} -> {r['new_id']}] {r['title']}")
    else:
        lines.append("  (none)")

    lines += ["", f"Zero-Quantity Ended ({len(ended_zero_qty)}):"]
    if ended_zero_qty:
        for r in ended_zero_qty:
            lines.append(f"  - [{r['item_id']}] {r['title']}")
    else:
        lines.append("  (none)")

    lines += ["", f"Failures ({len(failures)}):"]
    if failures:
        for r in failures:
            lines.append(f"  - [{r['item_id']}] {r['title']} -- {r['reason']}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


def send_email(gmail_app_password: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
        server.login(SENDER, gmail_app_password)
        server.sendmail(SENDER, [RECIPIENT], msg.as_string())


def notify_toast(title: str, body: str) -> None:
    title = title.replace("'", "''").replace('"', '`"')
    body = body.replace("'", "''").replace('"', '`"')
    ps = (
        "[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null;"
        "[reflection.assembly]::loadwithpartialname('System.Drawing') | Out-Null;"
        "$n = New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon = [System.Drawing.SystemIcons]::Information;"
        "$n.Visible = $true;"
        f"$n.ShowBalloonTip(8000, '{title}', '{body}', [System.Windows.Forms.ToolTipIcon]::Info);"
        "Start-Sleep -Seconds 9; $n.Dispose()"
    )
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    try:
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-NonInteractive", "-Command", ps],
            creationflags=flags,
        )
    except Exception:
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_notifications.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```
git -C C:\Users\tom\agents add ebay-relist-agent/notifications.py ebay-relist-agent/tests/test_notifications.py
git -C C:\Users\tom\agents commit -m "feat: add notifications with email and toast"
```

---

### Task 7: ebay_relist_agent.py — Main orchestrator

**Files:**
- Create: `C:\Users\tom\agents\ebay-relist-agent\ebay_relist_agent.py`
- Create: `C:\Users\tom\agents\ebay-relist-agent\tests\test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

Create `C:\Users\tom\agents\ebay-relist-agent\tests\test_orchestrator.py`:
```python
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

CFG = {"app_id": "a", "cert_id": "c", "dev_id": "d", "ru_name": "r", "gmail_app_password": "pw"}

MOCK_FIELDS = {
    "title": "Normal", "description": "", "primary_category_id": "1",
    "secondary_category_id": "", "store_category_id": "", "store_category2_id": "",
    "start_price": "9.99", "quantity": "2", "listing_duration": "GTC",
    "listing_type": "FixedPriceItem", "condition_id": "1000", "condition_description": "",
    "pictures": [], "item_specifics": [], "sku": "SKU1",
    "shipping_xml": "", "ship_to_locations": [], "return_policy_xml": "",
    "dispatch_time_max": "1",
}


def test_run_ends_zero_qty_and_relists_eligible():
    from ebay_relist_agent import run
    all_items = [
        {"item_id": "ZZ1", "title": "Zero", "listing_type": "FixedPriceItem", "quantity": 0, "start_time": "2026-01-01T00:00:00Z"},
        {"item_id": "A01", "title": "Normal", "listing_type": "FixedPriceItem", "quantity": 2, "start_time": "2026-01-02T00:00:00Z"},
    ]
    with patch("ebay_relist_agent.load_config", return_value=CFG), \
         patch("ebay_relist_agent.get_access_token", return_value="tok"), \
         patch("ebay_relist_agent.fetch_all_active_listings", return_value=all_items), \
         patch("ebay_relist_agent.get_item", return_value=MOCK_FIELDS), \
         patch("ebay_relist_agent.add_item", return_value="NEW01"), \
         patch("ebay_relist_agent.end_item") as mock_end, \
         patch("ebay_relist_agent.send_email"), \
         patch("ebay_relist_agent.notify_toast"), \
         patch("ebay_relist_agent.append_log"):
        run()
    ended_ids = [c.args[2] for c in mock_end.call_args_list]
    assert "ZZ1" in ended_ids
    assert "A01" in ended_ids


def test_run_does_not_end_item_when_add_item_fails():
    from ebay_relist_agent import run
    all_items = [
        {"item_id": "F01", "title": "Fail", "listing_type": "FixedPriceItem", "quantity": 1, "start_time": "2026-01-01T00:00:00Z"},
    ]
    with patch("ebay_relist_agent.load_config", return_value=CFG), \
         patch("ebay_relist_agent.get_access_token", return_value="tok"), \
         patch("ebay_relist_agent.fetch_all_active_listings", return_value=all_items), \
         patch("ebay_relist_agent.get_item", return_value=MOCK_FIELDS), \
         patch("ebay_relist_agent.add_item", side_effect=RuntimeError("API error")), \
         patch("ebay_relist_agent.end_item") as mock_end, \
         patch("ebay_relist_agent.send_email"), \
         patch("ebay_relist_agent.notify_toast"), \
         patch("ebay_relist_agent.append_log"):
        run()
    ended_ids = [c.args[2] for c in mock_end.call_args_list]
    assert "F01" not in ended_ids
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_orchestrator.py -v
```
Expected: `ImportError` (ebay_relist_agent.py doesn't exist)

- [ ] **Step 3: Create ebay_relist_agent.py**

Create `C:\Users\tom\agents\ebay-relist-agent\ebay_relist_agent.py`:
```python
#!/usr/bin/env python3
"""
eBay Listing Refresh Agent

Daily: ends the 10 oldest fixed-price active listings and re-creates them fresh.
Also ends any zero-quantity listings without relisting them.
Emails a report to tomnissley@gmail.com after each run.

First run:  python ebay_relist_agent.py --setup
Ongoing:    python ebay_relist_agent.py
"""

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from auth import get_access_token, interactive_setup, load_config
from ebay_api import add_item, end_item, fetch_all_active_listings, get_item
from listing_logic import partition_listings, select_oldest
from notifications import format_report, format_subject, notify_toast, send_email

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "relist_log.json"


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def append_log(entries: list[dict]) -> None:
    existing = []
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                pass
    existing.extend(entries)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def run() -> None:
    today = date.today().isoformat()
    log(f"=== eBay Relist Agent starting ({today}) ===")

    cfg = load_config()
    token = get_access_token(cfg)

    log("Fetching all active listings...")
    all_items = fetch_all_active_listings(cfg, token)
    log(f"  {len(all_items)} active listings found")

    zero_qty, eligible = partition_listings(all_items)
    to_relist = select_oldest(eligible, n=10)
    log(f"  {len(zero_qty)} zero-qty | {len(eligible)} eligible | {len(to_relist)} to relist")

    log_entries = []
    ended_zero_qty_report = []
    relisted_report = []
    failures_report = []

    for item in zero_qty:
        iid = item["item_id"]
        try:
            end_item(cfg, token, iid)
            log(f"  Ended zero-qty: {iid} — {item['title']}")
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "ended-zero-qty"})
            ended_zero_qty_report.append({"item_id": iid, "title": item["title"]})
        except Exception as e:
            log(f"  ERROR ending zero-qty {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": str(e)})
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})

    for item in to_relist:
        iid = item["item_id"]
        try:
            fields = get_item(cfg, token, iid)
        except Exception as e:
            log(f"  ERROR GetItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"GetItem failed: {e}"})
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
            continue

        try:
            new_id = add_item(cfg, token, fields)
        except Exception as e:
            log(f"  ERROR AddItem {iid}: {e}")
            failures_report.append({"item_id": iid, "title": item["title"], "reason": f"AddItem failed: {e}"})
            log_entries.append({"date": today, "item_id": iid, "title": item["title"], "status": "error", "reason": str(e)})
            continue

        try:
            end_item(cfg, token, iid)
        except Exception as e:
            log(f"  WARNING EndItem {iid} failed (new listing {new_id} is live): {e}")

        log(f"  Relisted: {iid} -> {new_id} — {item['title']}")
        relisted_report.append({"old_id": iid, "new_id": new_id, "title": item["title"]})
        log_entries.append({
            "date": today, "old_item_id": iid, "new_item_id": new_id,
            "title": item["title"], "status": "relisted",
        })

    append_log(log_entries)

    body = format_report(relisted_report, ended_zero_qty_report, failures_report)
    subject = format_subject(today)
    try:
        send_email(cfg["gmail_app_password"], subject, body)
        log("Email report sent.")
    except Exception as e:
        log(f"WARNING: Email failed: {e}")

    if failures_report:
        toast_body = f"Relisted {len(relisted_report)}/10 — {len(failures_report)} failed"
    else:
        toast_body = f"Cycled {len(relisted_report)} | Ended {len(ended_zero_qty_report)} zero-qty"
    notify_toast("eBay Relist Agent", toast_body)

    log(f"=== Done — {len(relisted_report)} relisted, {len(ended_zero_qty_report)} zero-qty ended, {len(failures_report)} errors ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eBay Listing Refresh Agent")
    parser.add_argument("--setup", action="store_true", help="Interactive first-time setup")
    args = parser.parse_args()
    if args.setup:
        interactive_setup()
    else:
        run()
```

- [ ] **Step 4: Run all tests**

```
pytest tests/ -v
```
Expected: All tests PASSED

- [ ] **Step 5: Commit**

```
git -C C:\Users\tom\agents add ebay-relist-agent/ebay_relist_agent.py ebay-relist-agent/tests/test_orchestrator.py
git -C C:\Users\tom\agents commit -m "feat: add main orchestrator with relist loop and json logging"
```

---

### Task 8: setup_task.ps1 — Windows Task Scheduler registration

**Files:**
- Create: `C:\Users\tom\agents\ebay-relist-agent\setup_task.ps1`

- [ ] **Step 1: Create setup_task.ps1**

Create `C:\Users\tom\agents\ebay-relist-agent\setup_task.ps1`:
```powershell
# Run once as Administrator to register the 12pm daily Task Scheduler job.
$taskName  = "eBayRelistAgent"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = (Get-Command python).Source
$script    = Join-Path $scriptDir "ebay_relist_agent.py"

$action   = New-ScheduledTaskAction -Execute $pythonExe -Argument $script -WorkingDirectory $scriptDir
$trigger  = New-ScheduledTaskTrigger -Daily -At "12:00PM"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
Write-Host "Task '$taskName' registered — runs daily at 12:00 PM."
```

- [ ] **Step 2: Verify the file is valid PowerShell**

```powershell
powershell -NonInteractive -Command "& { . 'C:\Users\tom\agents\ebay-relist-agent\setup_task.ps1' }" 2>&1 | Select-String "registered"
```

Note: this will actually register the task if run. To just syntax-check, use:
```powershell
powershell -NonInteractive -Command "Get-Content 'C:\Users\tom\agents\ebay-relist-agent\setup_task.ps1' | Out-Null; Write-Host 'OK'"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```
git -C C:\Users\tom\agents add ebay-relist-agent/setup_task.ps1
git -C C:\Users\tom\agents commit -m "feat: add Task Scheduler registration script for 12pm daily run"
```

---

## First-Time Setup (after all tasks complete)

Once you have your eBay developer credentials and Gmail App Password:

```
cd C:\Users\tom\agents\ebay-relist-agent
python ebay_relist_agent.py --setup
```

Then register the scheduled task (run PowerShell as Administrator):
```powershell
C:\Users\tom\agents\ebay-relist-agent\setup_task.ps1
```

**Gmail App Password:** Create one at [myaccount.google.com](https://myaccount.google.com) > Security > 2-Step Verification > App Passwords. Select "Mail" and "Windows Computer".
