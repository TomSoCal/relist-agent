# Version Synchronization Checklist

**Critical: Keep License Agreement Synced with Product Version**

When rebuilding or releasing a new version of Relist Agent (or any PandaSuite app), the license agreement MUST be updated to match the new version number.

---

## Before Building a New Release

### 1. Identify New Version

Determine what version you're building:

- **v2.0.0** → Build update for v2.0.0
- **v2.0.1** → Build update for v2.0.1
- **v2.1.0** → Build update for v2.1.0

### 2. Update License Agreement

**File:** `COMMERCIAL_LICENSE.md`

**Section 1.4: Product Definition**

```markdown
**Product Version:** 2.0.1 and later
```

Change to match your new version:
```markdown
**Product Version:** 2.0.2 and later
```

**Schedule A: Product Versions**

Update current version:
```markdown
### Current Version
- **v2.0.1:** August 2026 (current)
```

Change to:
```markdown
### Current Version
- **v2.0.2:** September 2026 (current)
```

**Version History Table**

Add new row:
```markdown
| 1.1 | 2026-09-15 | Updated for v2.0.2 release |
```

### 3. Update Release Notes

**File:** `RELEASE-NOTES-v2.0.2.txt` (in updates folder)

Create new file with:
- Key changes
- Bug fixes
- Features added
- Known issues

### 4. Update Version Checker

**File:** `LATEST_VERSION.txt`

Change content to:
```
2.0.2
```

### 5. Build & Compile

```bash
python build.py
# Creates: Relist-Agent-v2.0.2.exe
# Also creates: Relist-Agent-v2.0.2.zip
```

### 6. Create MSI Installer

Edit `RELIST_AGENT_PRODUCT.wxs`:

```xml
<Product ... Version="2.0.2.0" ...>
```

Build MSI:
```bash
candle.exe Product.wxs -o obj\
light.exe obj\Product.wixobj -o Relist-Agent-v2.0.2.msi
```

### 7. Commit Changes

```bash
git add COMMERCIAL_LICENSE.md RELEASE-NOTES-v2.0.2.txt
git commit -m "Release Relist Agent v2.0.2"
```

---

## Version Synchronization Matrix

| File | Section | Old | New | Notes |
|------|---------|-----|-----|-------|
| COMMERCIAL_LICENSE.md | Section 1.4 | v2.0.1 | v2.0.2 | Main version |
| COMMERCIAL_LICENSE.md | Schedule A | v2.0.1: August | v2.0.2: September | Current version |
| COMMERCIAL_LICENSE.md | Schedule A | Version History | Add new row | Track all updates |
| RELIST_AGENT_PRODUCT.wxs | Product tag | Version="2.0.1.0" | Version="2.0.2.0" | Must match |
| build.py | (if exists) | CURRENT_VERSION = "2.0.1" | CURRENT_VERSION = "2.0.2" | Build script |
| LATEST_VERSION.txt | Content | 2.0.1 | 2.0.2 | Update checker |
| RELEASE-NOTES-v2.0.2.txt | (new file) | N/A | Create file | Key changes only |

---

## Pre-Release Verification

Before uploading to website, verify:

- [ ] License agreement updated to new version number
- [ ] Product version in Section 1.4 matches new release
- [ ] Schedule A shows new version as "Current"
- [ ] Version history table has new row
- [ ] WiX template updated with new version
- [ ] build.py references new version
- [ ] LATEST_VERSION.txt contains new version number
- [ ] Release notes file created and populated
- [ ] MSI installer built with correct version
- [ ] All files ready for upload to website

---

## Files to Upload to Website

```
https://thetrashedpanda.com/updates/Relist-Agent/

├── Relist-Agent-v2.0.2.msi        (NEW MSI installer)
├── Relist-Agent-v2.0.2.zip        (NEW release zip)
├── LATEST_VERSION.txt             (UPDATED - now "2.0.2")
└── RELEASE-NOTES-v2.0.2.txt       (NEW release notes)
```

---

## Automation Opportunity

Consider adding to your build script:

```python
# build.py

VERSION = "2.0.2"

def update_license_agreement():
    """Auto-update COMMERCIAL_LICENSE.md with new version"""
    license_file = "path/to/COMMERCIAL_LICENSE.md"
    
    # Read existing file
    with open(license_file, 'r') as f:
        content = f.read()
    
    # Replace old version with new version
    content = content.replace(
        "**Product Version:** 2.0.1 and later",
        f"**Product Version:** {VERSION} and later"
    )
    
    # Update current version in Schedule A
    today = datetime.now().strftime("%B %Y")
    content = content.replace(
        "- **v2.0.1:** August 2026 (current)",
        f"- **v{VERSION}:** {today} (current)"
    )
    
    # Write updated file
    with open(license_file, 'w') as f:
        f.write(content)
    
    print(f"✓ License agreement updated to v{VERSION}")

# Call in build.py
if __name__ == "__main__":
    update_license_agreement()
    compile_exe()
    create_zip()
    create_msi()
```

---

## Checklist Template

Create this checklist as a file for each release:

```markdown
# Release v2.0.2 Checklist

## Pre-Build
- [ ] Determine version number: v2.0.2
- [ ] Update COMMERCIAL_LICENSE.md
  - [ ] Section 1.4: Product Version
  - [ ] Schedule A: Current Version
  - [ ] Version History table
- [ ] Update LATEST_VERSION.txt
- [ ] Create RELEASE-NOTES-v2.0.2.txt

## Build
- [ ] Run build.py → generates v2.0.2.exe + v2.0.2.zip
- [ ] Update RELIST_AGENT_PRODUCT.wxs (Version="2.0.2.0")
- [ ] Build MSI → generates Relist-Agent-v2.0.2.msi

## Post-Build
- [ ] Test MSI install on clean Windows
- [ ] Verify license agreement in MSI matches v2.0.2
- [ ] Verify version checker shows v2.0.2

## Release
- [ ] Upload v2.0.2.msi to website
- [ ] Upload v2.0.2.zip to website
- [ ] Upload LATEST_VERSION.txt to website
- [ ] Upload RELEASE-NOTES-v2.0.2.txt to website
- [ ] Test update checker detects new version
- [ ] Commit all changes to git

## Post-Release
- [ ] Monitor for issues with v2.0.2
- [ ] Prepare for v2.0.3 if needed
```

---

## Why This Matters

**Consistency:** Users expect the license to match the product version they purchase.

**Legal:** License agreement should clearly state what version it covers.

**Support:** Easier to track which version a customer is using.

**Updates:** Version checker relies on LATEST_VERSION.txt staying in sync.

---

## Remember

**Every new version = Update license agreement**

Don't skip this step. It's quick (2 minutes) and critical for:
- Legal compliance
- Customer trust
- Support tracking
- Release integrity

---

**Created:** 2026-07-27  
**Status:** Active for all future releases

