# ⚠️ CRITICAL RULES - eBay Relist Agent

These are non-negotiable rules for ALL versions and implementations of the eBay Relist Agent.

## Rule 1: NEVER Create Duplicate Listings

**⛔ VIOLATION PENALTY:** eBay will reject or flag the seller account

**Implementation Requirements:**
- Any relist/refresh operation MUST delist the old listing BEFORE creating the new one
- This applies to:
  - Manual relist button in Inventory
  - Automatic relist agent
  - Any future relist features
  
**Code Pattern:**
```python
# ✅ CORRECT
1. Get item details
2. Delist old item (end_item)
3. Create new listing (add_item)

# ❌ WRONG
1. Create new listing (add_item)
2. Delist old item (end_item)

# ❌ WRONG
1. Create new listing (add_item)
# (forget to delist old one)
```

**Why This Matters:**
- eBay's API has limitations that prevent truly identical listings
- Duplicate listings violate eBay's Terms of Service
- Account flags can lead to suspension or permanent banning
- This is a business-critical constraint

---

## Rule 2: Always Verify Operations Before Execution

All user-initiated actions that modify listings must:
1. Show confirmation dialog with item details
2. Allow user to cancel
3. Verify success/failure
4. Show user the result (success or error)

---

## Implementation Checklist

Before deploying ANY version (backup, master, advanced):
- [ ] Verify relist operation: delist THEN create new (never both active)
- [ ] Verify no orphaned delists (if add fails, old listing not deleted)
- [ ] Verify no duplicate creation paths
- [ ] Add tests to prevent regressions

---

**Last Updated:** 2026-06-02  
**Applies To:** All versions (backup, master, advanced)  
**Status:** Non-negotiable
