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
        active_list = root.find(_t("ActiveList"))
        item_array = active_list.find(_t("ItemArray")) if active_list is not None else None
        for item in (item_array.findall(_t("Item")) if item_array is not None else []):
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
        pagination = active_list.find(_t("PaginationResult")) if active_list is not None else None
        try:
            total_pages = int(pagination.findtext(_t("TotalNumberOfPages")) if pagination is not None else "1")
        except ValueError:
            total_pages = 1
        if page >= total_pages:
            break
        page += 1
    return items


def get_item(cfg: dict, token: str, item_id: str) -> dict:
    if not str(item_id).isdigit():
        raise ValueError(f"item_id must be numeric, got: {item_id!r}")
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
    if not str(item_id).isdigit():
        raise ValueError(f"item_id must be numeric, got: {item_id!r}")
    body = f"""
  <ItemID>{item_id}</ItemID>
  <EndingReason>NotAvailable</EndingReason>"""
    trading_call(cfg, token, "EndItem", body)


def _subtree_xml(el: ET.Element | None) -> str:
    if el is None:
        return ""
    raw = ET.tostring(el, encoding="unicode")
    raw = re.sub(r'\s*xmlns(?::\w+)?="[^"]*"', "", raw)
    raw = re.sub(r"<(/)?([\w]+):", r"<\1", raw)
    return raw


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
