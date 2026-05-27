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
    r.content = xml_str.encode("utf-8")
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


def test_fetch_all_active_listings_paginates_multiple_pages():
    from ebay_api import fetch_all_active_listings

    PAGE1_XML = """<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingResponse xmlns="urn:ebay:apis:eBLBaseComponents">
  <Ack>Success</Ack>
  <ActiveList>
    <ItemArray>
      <Item>
        <ItemID>001</ItemID>
        <Title>Page1 Item</Title>
        <ListingType>FixedPriceItem</ListingType>
        <Quantity>1</Quantity>
        <ListingDetails><StartTime>2026-01-01T00:00:00.000Z</StartTime></ListingDetails>
      </Item>
    </ItemArray>
    <PaginationResult><TotalNumberOfPages>2</TotalNumberOfPages></PaginationResult>
  </ActiveList>
</GetMyeBaySellingResponse>"""

    PAGE2_XML = """<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingResponse xmlns="urn:ebay:apis:eBLBaseComponents">
  <Ack>Success</Ack>
  <ActiveList>
    <ItemArray>
      <Item>
        <ItemID>002</ItemID>
        <Title>Page2 Item</Title>
        <ListingType>FixedPriceItem</ListingType>
        <Quantity>2</Quantity>
        <ListingDetails><StartTime>2026-01-02T00:00:00.000Z</StartTime></ListingDetails>
      </Item>
    </ItemArray>
    <PaginationResult><TotalNumberOfPages>2</TotalNumberOfPages></PaginationResult>
  </ActiveList>
</GetMyeBaySellingResponse>"""

    cfg = {"app_id": "a", "cert_id": "c", "dev_id": "d"}
    responses = [_mock_resp(PAGE1_XML), _mock_resp(PAGE2_XML)]
    with patch("requests.post", side_effect=responses):
        items = fetch_all_active_listings(cfg, "tok")
    assert len(items) == 2
    assert items[0]["item_id"] == "001"
    assert items[1]["item_id"] == "002"


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
    assert "<StoreCategoryID>456</StoreCategoryID>" in xml


def test_add_item_returns_new_item_id():
    from ebay_api import add_item
    cfg = {"app_id": "a", "cert_id": "c", "dev_id": "d"}
    with patch("requests.post", return_value=_mock_resp(ADD_ITEM_RESPONSE_XML)):
        new_id = add_item(cfg, "tok", SAMPLE_FIELDS)
    assert new_id == "999"


def test_build_additem_xml_escapes_special_chars_in_title():
    from ebay_api import build_additem_xml
    fields = {**SAMPLE_FIELDS, "title": "Shirt & Tie <New>"}
    xml = build_additem_xml(fields)
    assert "<Title>Shirt &amp; Tie &lt;New&gt;</Title>" in xml


def test_add_item_raises_when_no_item_id_returned():
    import pytest
    from ebay_api import add_item
    NO_ID_XML = """<?xml version="1.0" encoding="utf-8"?>
<AddItemResponse xmlns="urn:ebay:apis:eBLBaseComponents">
  <Ack>Success</Ack>
</AddItemResponse>"""
    cfg = {"app_id": "a", "cert_id": "c", "dev_id": "d"}
    with patch("requests.post", return_value=_mock_resp(NO_ID_XML)):
        with pytest.raises(RuntimeError, match="no ItemID"):
            add_item(cfg, "tok", SAMPLE_FIELDS)
