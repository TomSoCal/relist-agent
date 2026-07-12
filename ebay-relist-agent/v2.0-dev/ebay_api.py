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
        f"  <RequesterCredentials><eBayAuthToken>{token}</eBayAuthToken></RequesterCredentials>\n"
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
            sku = item.findtext(_t("SKU")) or ""
            custom_label = item.findtext(_t("CustomLabel")) or ""
            items.append({
                "item_id":      item.findtext(_t("ItemID")) or "",
                "title":        (item.findtext(_t("Title")) or "")[:80],
                "listing_type": item.findtext(_t("ListingType")) or "",
                "quantity":     qty,
                "start_time":   _txt(item, "ListingDetails/StartTime"),
                "sku":          sku or custom_label,  # Use custom_label as fallback
                "custom_label": custom_label,
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
    shipping_profile_id = item.findtext(f".//{_t('ShippingProfileID')}", "") or ""
    return_profile_id = item.findtext(f".//{_t('ReturnProfileID')}", "") or ""
    payment_profile_id = item.findtext(f".//{_t('PaymentProfileID')}", "") or ""

    # Extract shipping cost from ShippingDetails/ShippingServiceOptions/ShippingServiceCost
    shipping_cost = ""
    shipping_details = item.find(_t("ShippingDetails"))
    if shipping_details is not None:
        options_container = shipping_details.find(_t("ShippingServiceOptions"))
        if options_container is not None:
            cost_el = options_container.findtext(_t("ShippingServiceCost"))
            if cost_el:
                try:
                    cost_float = float(cost_el)
                    shipping_cost = f"${cost_float:.2f}" if cost_float > 0 else "FREE"
                except:
                    pass

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
        "sku":                   _txt(item, "SKU") or _txt(item, "CustomLabel"),
        "custom_label":          _txt(item, "CustomLabel"),
        "currency":              _txt(item, "Currency") or "USD",
        "country":               _txt(item, "Country") or "US",
        "location":              _txt(item, "Location"),
        "postal_code":           _txt(item, "PostalCode"),
        "shipping_cost":         shipping_cost,
        "shipping_profile_id":   shipping_profile_id,
        "return_profile_id":     return_profile_id,
        "payment_profile_id":    payment_profile_id,
        "ship_to_locations":     ship_to,
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
    currency = _esc(fields.get("currency") or "USD")
    country = _esc(fields.get("country") or "US")
    lines = ["<Item>"]
    lines.append(f"  <Title>{_esc(fields['title'])}</Title>")
    lines.append(f"  <Description><![CDATA[{fields['description']}]]></Description>")
    lines.append("  <ListingType>FixedPriceItem</ListingType>")
    lines.append(f"  <ListingDuration>{_esc(fields.get('listing_duration') or 'GTC')}</ListingDuration>")
    lines.append(f"  <StartPrice currencyID=\"{currency}\">{fields['start_price']}</StartPrice>")
    lines.append(f"  <Currency>{currency}</Currency>")
    lines.append(f"  <Country>{country}</Country>")
    if fields.get("location"):
        lines.append(f"  <Location>{_esc(fields['location'])}</Location>")
    if fields.get("postal_code"):
        lines.append(f"  <PostalCode>{_esc(fields['postal_code'])}</PostalCode>")
    lines.append(f"  <Quantity>{fields['quantity']}</Quantity>")
    lines.append(f"  <PrimaryCategory><CategoryID>{fields['primary_category_id']}</CategoryID></PrimaryCategory>")
    if fields.get("secondary_category_id"):
        lines.append(f"  <SecondaryCategory><CategoryID>{fields['secondary_category_id']}</CategoryID></SecondaryCategory>")
    if fields.get("condition_id"):
        lines.append(f"  <ConditionID>{_esc(fields['condition_id'])}</ConditionID>")
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
    if fields.get("shipping_profile_id") or fields.get("return_profile_id") or fields.get("payment_profile_id"):
        lines.append("  <SellerProfiles>")
        if fields.get("shipping_profile_id"):
            lines.append(f"    <SellerShippingProfile><ShippingProfileID>{fields['shipping_profile_id']}</ShippingProfileID></SellerShippingProfile>")
        if fields.get("return_profile_id"):
            lines.append(f"    <SellerReturnProfile><ReturnProfileID>{fields['return_profile_id']}</ReturnProfileID></SellerReturnProfile>")
        if fields.get("payment_profile_id"):
            lines.append(f"    <SellerPaymentProfile><PaymentProfileID>{fields['payment_profile_id']}</PaymentProfileID></SellerPaymentProfile>")
        lines.append("  </SellerProfiles>")
    for loc in fields.get("ship_to_locations", []):
        lines.append(f"  <ShipToLocations>{_esc(loc)}</ShipToLocations>")
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


def fetch_inventory_with_categories(cfg: dict, token: str) -> list[dict]:
    """Fetch inventory with categories using Sell Inventory API (fast, ~6 calls for 600 items)."""
    items = []
    offset = 0
    limit = 100

    while True:
        url = "https://api.ebay.com/sell/inventory/v1/inventory"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        params = {"limit": limit, "offset": offset}

        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        inventory = data.get("inventories", [])
        if not inventory:
            break

        for inv in inventory:
            sku = inv.get("sku", "")
            category_id = inv.get("categoryId", "")
            items.append({
                "sku": sku,
                "category_id": category_id,
                "title": inv.get("title", "")
            })

        total = data.get("total", 0)
        if offset + limit >= total:
            break
        offset += limit

    return items


def get_store_categories(cfg: dict, token: str) -> tuple[list[str], dict]:
    """Fetch seller's store categories using Trading API GetStore call.
    Returns: (category_names, category_id_to_name_mapping)"""
    body = """
  <CategoryStructureOnly>true</CategoryStructureOnly>"""
    try:
        root = trading_call(cfg, token, "GetStore", body)

        categories = []
        category_mapping = {}  # category_id -> name
        store = root.find(_t("Store"))
        if store is None:
            return [], {}

        cat_array = store.find(_t("CustomCategories"))
        if cat_array is None:
            return [], {}

        # Parse category hierarchy (3 levels deep)
        for cat in cat_array.findall(_t("CustomCategory")):
            cat_id = cat.findtext(_t("CategoryID"))
            name = cat.findtext(_t("Name"))
            if name:
                categories.append(name)
                if cat_id:
                    category_mapping[cat_id] = name

            # Level 2 categories
            for cat2 in cat.findall(_t("CustomCategories")):
                for subcat in cat2.findall(_t("CustomCategory")):
                    sub_id = subcat.findtext(_t("CategoryID"))
                    sub_name = subcat.findtext(_t("Name"))
                    if sub_name:
                        categories.append(sub_name)
                        if sub_id:
                            category_mapping[sub_id] = sub_name

                    # Level 3 categories
                    for cat3 in subcat.findall(_t("CustomCategories")):
                        for subcat2 in cat3.findall(_t("CustomCategory")):
                            sub_id2 = subcat2.findtext(_t("CategoryID"))
                            sub_name2 = subcat2.findtext(_t("Name"))
                            if sub_name2:
                                categories.append(sub_name2)
                                if sub_id2:
                                    category_mapping[sub_id2] = sub_name2

        return sorted(categories), category_mapping
    except Exception as e:
        print(f"[GetStore] Error: {e}")
        return [], {}
