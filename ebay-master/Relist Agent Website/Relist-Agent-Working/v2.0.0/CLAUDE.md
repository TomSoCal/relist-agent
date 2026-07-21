# Relist Agent v2.0.0 Development Instructions

## Critical Constraints

🛑 **Read CRITICAL_RULES.md first** — These are non-negotiable.

Core rules:
1. Always delist BEFORE creating new listing (never create duplicates)
2. Never mention "eBay" in user-facing text/UI
3. Get user confirmation for all destructive operations

---

## Scope Rules for One-Off Requests

**Do exactly what was asked. Nothing more.**

- No improvements, refactoring, renaming beyond the request
- No new files unless explicitly told
- No "while I'm at it" changes
- If additional work is needed, **STOP and list what needs approval first**

---

## Git Discipline

1. **COMMIT BEFORE RISK** — Before any debug code, refactoring, or uncertain edit:
   ```bash
   git add -A && git commit -m "checkpoint before <what you're about to try>"
   ```

2. **NO BLIND REVERTS** — Before running `git revert`, `git reset`, or `git checkout`:
   - Run `git status` and `git diff` first
   - Show exactly what uncommitted work would be lost
   - **STOP if there's uncommitted work without a checkpoint**

3. **UNDO ONLY WHAT YOU BROKE** — Don't fall back to older commits unless explicitly approved

4. **ASK BEFORE DESTRUCTIVE** — Any operation that could discard work requires explicit approval

5. **IF YOU BREAK IT, FIX IT FULLY** — Restore functionality completely, then report

---

## App-Specific Licensing Rules (v2.0.0+)

Relist Agent now uses app-specific licensing to prevent key sharing with other apps.

**Key Facts:**
- APP_ID = "relist-agent" (must not change)
- Licenses are tied to both the app AND the computer
- Same key cannot be used in Relist Agent and Panda Print simultaneously
- Server enforces cross-app rejection via update-key.php
- Customer name captured as eBay store name (prompted during activation)

**For Future Updates:**
1. Never change `APP_ID = "relist-agent"` in license_check.py
2. Registration payload MUST include: `"app": APP_ID` and `"customer_name": store_name`
3. Dual User-Agent pattern is REQUIRED:
   - GET requests (load_license_db): Use app-specific UA (`Relist-Agent/1.5.0`)
   - POST requests (register_key_on_server): Use Mozilla UA (bypasses Cloudflare)
4. Error messages with "registered for" must trigger immediate rejection (don't allow offline use)
5. Customer name should be visible in error messages for support clarity
6. Store name must be prompted during license validation and stored in config.json

**Testing Checklist:**
- Register a key that belongs to Panda Print, verify "registered for" error appears
- Confirm customer name (store name) displays in error message
- Verify app still works offline when no app-mismatch error occurred
- Multiple versions of same app (v2.0.0, v2.1.0) must share licenses on same PC
- Store name prompt appears during first-time activation
- Store name is saved and used in all future registrations

**Reference:** See memory files for complete technical details:
- panda_print_relist_agent_licensing.md — COMPLETE implementation status
- app_specific_licensing_technical.md — Dual User-Agent pattern, payload structure
- app_licensing_learnings.md — Why this approach, edge cases, testing discoveries

See LICENSING_GUIDE.md for detailed user-facing and developer documentation.

---

## Code Organization

| File | Purpose |
|------|---------|
| `ebay_relist_agent.py` | Main GUI application entry point |
| `gui_app.py` | GUI components and windows |
| `ebay_api.py` | eBay API communication |
| `license_check.py` | License validation (APP_ID, registration, verification) |
| `auth.py` | eBay authentication |
| `config.json` | User configuration (includes license key and store name) |
| `CRITICAL_RULES.md` | Non-negotiable business rules |
| `LICENSING_GUIDE.md` | Licensing system documentation |

---

## Testing Before Release

- [ ] Licensing works: Valid key activates app
- [ ] App mismatch detected: Panda Print key rejected with error
- [ ] Error message includes store name: "registered to user 'MyStore'"
- [ ] Store name saved: Relaunching app uses same store name
- [ ] Offline mode works: After activation, works without internet
- [ ] Multiple versions compatible: v2.0.0 and v2.1.0 share keys

---

## Communication Style

- Keep responses concise
- Don't explain what you're about to do; just do it and report results
- On uncertainty, ask for clarification; don't guess
- If work would touch something not mentioned, **STOP and ask first**
