# eBay Listing Refresh Agent — Design Spec

**Date:** 2026-05-24  
**Status:** Approved

## Overview

A daily Python automation agent that keeps eBay listings fresh by cycling the 10 oldest active fixed-price listings each day. It ends the old listings and creates brand-new ones with identical details ("sell similar" via API). With ~600 active listings, the full inventory rotates approximately every 60 days.

## Goals

- End the 10 oldest fixed-price active listings daily at 12pm
- Re-create each as a fresh listing with all details preserved exactly
- Preserve: title, description, categories (eBay + store), item specifics, SKU, price, quantity, condition, pictures (in order), shipping, return policy
- Skip any auction-format listings (never end them)
- End any zero-quantity listings without relisting them (do not count toward the 10-item limit)
- Log all activity for review

## Non-Goals

- Deleting inactive/unsold listings (eBay Trading API does not support this; ended listings auto-expire after 90 days)
- Price adjustments or optimization
- Supporting auction-format listings

## Architecture

### Location

`C:\Users\tom\agents\ebay-relist-agent\`

### Shared Infrastructure

Reuses credentials and token management from `C:\Users\tom\agents\ebay_monitor\`:
- `config.json` — App ID, Cert ID, Dev ID, RuName
- `tokens.json` — OAuth access + refresh tokens
- Requires one re-authentication to add `sell.inventory` OAuth scope

### API

eBay Trading API (XML/SOAP) at `https://api.ebay.com/ws/api.dll`

### OAuth Scopes Required

- `https://api.ebay.com/oauth/api_scope`
- `https://api.ebay.com/oauth/api_scope/sell.fulfillment`
- `https://api.ebay.com/oauth/api_scope/sell.inventory` ← new, needed for AddItem

## Data Flow

```
GetMyeBaySelling (ActiveList, paginated — up to 3 pages for ~600 listings)
  → filter: fixed-price only (skip ListingType == Chinese/Auction)
  → partition:
      zero_qty  = items where Quantity == 0
      eligible  = remaining items, sorted by ListingDetails/StartTime ascending

For each item in zero_qty:
  1. EndItem (reason=NotAvailable)
  2. Log: {date, item_id, title, status="ended-zero-qty"}
  (does NOT count toward the 10-item limit)

For each of the 10 oldest in eligible:
  1. GetItem (DetailLevel=ReturnAll)
       → capture all fields listed below
  2. AddItem (new listing with copied fields)
       → on AddItem failure: log error, skip — do NOT end the original
  3. EndItem (reason=NotAvailable)
       → on EndItem failure: log warning (both old+new briefly active, old expires naturally)
  4. Log: {date, old_item_id, new_item_id, title, status="relisted"}
```

## Fields Copied Exactly

| Field | API Element |
|-------|-------------|
| Title | `Title` |
| Description | `Description` |
| eBay Category | `PrimaryCategory/CategoryID` |
| eBay Secondary Category | `SecondaryCategory/CategoryID` |
| Store Category | `Storefront/StoreCategoryID` |
| Store Category 2 | `Storefront/StoreCategory2ID` |
| Item Specifics | `ItemSpecifics/NameValueList[]` (all pairs) |
| Custom SKU | `SKU` |
| Price | `StartPrice` |
| Quantity | `Quantity` |
| Condition | `ConditionID`, `ConditionDescription` |
| Pictures | `PictureDetails/PictureURL[]` (all, in order) |
| Shipping | `ShippingDetails` (full subtree) |
| Ship-To Locations | `ShipToLocations` |
| Return Policy | `ReturnPolicy` (full subtree) |
| Listing Duration | `ListingDuration` (preserves GTC) |
| Dispatch Time | `DispatchTimeMax` |

## Error Handling

- **GetItem fails:** Log error, skip that item entirely.
- **AddItem fails:** Log error, do NOT end the original listing. Original stays active.
- **EndItem fails after successful AddItem:** Log warning — both old and new listing are briefly active. Old will expire naturally.
- **Auth failure:** Log error, exit, send Windows toast notification.
- **Zero-quantity item EndItem fails:** Log error, continue — no relist attempted.
- **Fewer than 10 eligible listings:** Process however many exist (no minimum required).

## Pagination

`GetMyeBaySelling` returns up to 200 items per page. With ~600 listings, the agent paginates through all pages, collects the full active listing set, then sorts by `ListingDetails/StartTime` and selects the 10 oldest.

## File Structure

```
C:\Users\tom\agents\ebay-relist-agent\
  ebay_relist_agent.py   — main script (--setup flag for first-time auth)
  setup_task.ps1         — registers 12pm daily Windows Task Scheduler job
  run.bat                — manual one-click trigger
  relist_log.json        — running log of all cycles
  config.json            — copied from ebay_monitor on first --setup
  tokens.json            — written by --setup OAuth flow
```

## Scheduling

- **Trigger:** Windows Task Scheduler, daily at 12:00pm
- **Script:** `setup_task.ps1` registers the job (run once as admin)
- **Manual run:** `run.bat` or `python ebay_relist_agent.py`

## Notifications

**Windows toast** (same PowerShell method as `ebay_monitor.py`) on:
- Successful completion: "eBay Relist: Cycled 10 listings"
- Partial success: "eBay Relist: X/10 succeeded — Y failed"
- Fatal auth error: "eBay Relist Agent failed: auth error"

**Daily email** sent to `tomnissley@gmail.com` via Gmail SMTP after each run:
- Subject: `eBay Relist Report — 2026-05-24`
- Body (plain text):

```
Relisted (10):
  - [old ID → new ID] Title
  - ...

Zero-Quantity Ended (N):
  - [item ID] Title
  - ...

Failures (N):
  - [item ID] Title — reason
```

- Gmail app password stored in `config.json` as `gmail_app_password`
- Sender: `tomnissley@gmail.com`, uses `smtplib` + `ssl` (stdlib, no new deps)

## Dependencies

- Python 3.x
- `requests` (already installed via ebay_monitor)
- No new packages required
