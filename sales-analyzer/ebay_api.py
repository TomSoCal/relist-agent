import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta, timezone
import json

TRADING_API_URL = "https://api.ebay.com/ws/api.dll"
SELL_ORDERS_API_URL = "https://apiz.ebay.com/sell/fulfillment/v1"
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
        f"  <RequesterCredentials><eBayAuthToken>{token}</eBayAuthToken></RequesterCredentials>\n"
        f"{body_xml}\n"
        f"</{call_name}Request>"
    )
    headers = {
        "X-EBAY-API-CALL-NAME":           call_name,
        "X-EBAY-API-APP-NAME":            cfg["app_id"],
        "X-EBAY-API-DEV-NAME":            cfg["dev_id"],
        "X-EBAY-API-CERT-NAME":           cfg["cert_id"],
        "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
        "X-EBAY-API-SITEID":              "0",
        "Content-Type":                   "text/xml; charset=utf-8",
    }
    resp = requests.post(TRADING_API_URL, data=payload.encode("utf-8"), headers=headers, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ack = root.findtext(_t("Ack")) or ""
    if ack not in ("Success", "Warning"):
        msgs = "; ".join(el.text for el in root.findall(f".//{_t('ShortMessage')}") if el.text)
        raise RuntimeError(f"{call_name} failed: {msgs or ack}")
    return root


def fetch_sold_items_rest(cfg: dict, access_token: str) -> list[dict]:
    """Fetch sold items using REST Sell Orders API (last 90 days - eBay limitation)"""
    items = []
    offset = 0
    limit = 100

    # eBay only allows filtering last 90 days via REST API
    end_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    start_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    while True:
        # Correct filter format: creationdate:[START..END]
        filter_param = f"creationdate:[{start_date}..{end_date}]"

        # Build URL with proper encoding
        url = f"https://api.ebay.com/sell/fulfillment/v1/order"

        params = {
            "filter": filter_param,
            "limit": limit,
            "offset": offset,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        print(f"DEBUG: Fetching orders from offset {offset}...")
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"DEBUG: REST API error: {e}")
            break

        orders = data.get("orders", [])
        print(f"DEBUG: Got {len(orders)} orders in this batch")

        for order in orders:
            for line_item in order.get("lineItems", []):
                item_id = line_item.get("sku") or line_item.get("itemId", "")
                title = line_item.get("title", "")
                qty = line_item.get("quantity", 1)

                items.append({
                    "item_id": item_id,
                    "title": title[:80],
                    "sold_time": order.get("creationDate", ""),
                    "quantity_sold": str(qty),
                })

        # Check if there are more pages
        if len(orders) < limit:
            break

        offset += limit
        print(f"DEBUG: Total items so far: {len(items)}")

    print(f"DEBUG: Total REST API sold items: {len(items)}")
    return items


def fetch_sold_items(cfg: dict, token: str) -> list[dict]:
    """Fetch sold items from SoldList (last ~90 days of eBay data)"""
    items = []
    page = 1

    while True:
        body = f"""
  <SoldList>
    <Include>true</Include>
    <Pagination><EntriesPerPage>200</EntriesPerPage><PageNumber>{page}</PageNumber></Pagination>
  </SoldList>"""

        root = trading_call(cfg, token, "GetMyeBaySelling", body)
        sold_list = root.find(_t("SoldList"))

        if sold_list is None:
            print(f"DEBUG: No SoldList in response")
            break

        # SoldList contains OrderTransactionArray
        order_trans_array = sold_list.find(_t("OrderTransactionArray"))
        print(f"DEBUG: OrderTransactionArray found: {order_trans_array is not None}")

        if order_trans_array is not None:
            order_transactions = order_trans_array.findall(_t("OrderTransaction"))
            print(f"DEBUG: OrderTransactions in page {page}: {len(order_transactions)}")

            for order_trans in order_transactions:
                order = order_trans.find(_t("Order"))
                transaction = order_trans.find(_t("Transaction"))

                if transaction is None:
                    continue

                item = transaction.find(_t("Item"))
                if item is None:
                    continue

                title = item.findtext(_t("Title")) or ""
                sold_time_str = _txt(order, "CreatedTime") if order is not None else ""

                items.append({
                    "item_id": item.findtext(_t("ItemID")) or "",
                    "title": title[:80],
                    "sold_time": sold_time_str,
                    "quantity_sold": transaction.findtext(_t("QuantityPurchased")) or "1",
                })

        # Check pagination
        pagination = sold_list.find(_t("PaginationResult"))
        try:
            total_pages = int(pagination.findtext(_t("TotalNumberOfPages")) if pagination is not None else "1")
        except (ValueError, AttributeError):
            total_pages = 1

        print(f"DEBUG: Page {page}/{total_pages}, items so far: {len(items)}")
        if page >= total_pages:
            break
        page += 1

    print(f"DEBUG: Total sold items returned: {len(items)}")
    return items


def fetch_all_active_listings(cfg: dict, token: str) -> list[dict]:
    """Fetch all active listings with quantity"""
    items = []
    page = 1

    while True:
        body = f"""
  <ActiveList>
    <Include>true</Include>
    <Pagination><EntriesPerPage>200</EntriesPerPage><PageNumber>{page}</PageNumber></Pagination>
  </ActiveList>"""
        root = trading_call(cfg, token, "GetMyeBaySelling", body)
        active_list = root.find(_t("ActiveList"))
        item_array = active_list.find(_t("ItemArray")) if active_list is not None else None

        for item in (item_array.findall(_t("Item")) if item_array is not None else []):
            try:
                qty = int(item.findtext(_t("Quantity")) or "0")
            except ValueError:
                qty = 0
            title = item.findtext(_t("Title")) or ""
            items.append({
                "item_id": item.findtext(_t("ItemID")) or "",
                "title": title[:80],
                "quantity": qty,
            })

        pagination = active_list.find(_t("PaginationResult")) if active_list is not None else None
        try:
            total_pages = int(pagination.findtext(_t("TotalNumberOfPages")) if pagination is not None else "1")
        except ValueError:
            total_pages = 1

        if page >= total_pages:
            break
        page += 1

    return items
