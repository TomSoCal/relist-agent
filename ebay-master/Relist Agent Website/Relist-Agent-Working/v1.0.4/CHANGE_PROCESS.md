# Change Process — MANDATORY

**NEVER GUESS. ALWAYS VERIFY FIRST.**

This process MUST be followed before ANY code change, rebuild, or testing.

---

## Step 1: Understand Current State

1. **Check git log:**
   ```bash
   git log --oneline -10
   ```
   → See recent commits and last known states

2. **Check git diff:**
   ```bash
   git diff HEAD~1 HEAD -- [file]
   ```
   → See exactly what changed in the last commit

3. **Check actual file contents:**
   - Read the file you're about to change
   - Don't assume what's there
   - Use Read tool, not assumptions

4. **Check actual data:**
   - If a config file is involved, read it
   - If a log file should exist, check for it
   - If a function should load something, verify it actually does
   - Use actual file inspection: `Get-Content`, `cat`, `python -c`

---

## Step 2: Identify the Problem

1. **Read user feedback carefully** - what exactly is broken?
   - "not showing" = visibility issue
   - "not working" = logic issue
   - "not loading" = data issue

2. **Look at debug logs** - what does the app say?
   - Check `.ebay_relist_agent_data/` folder
   - Read relevant debug logs
   - Look for error messages

3. **Find the code responsible:**
   - Search for the function that handles this
   - Read the entire function, not just one line
   - Check what it's supposed to do vs what it's actually doing

4. **Compare to last known good state:**
   ```bash
   git diff [commit-hash] HEAD -- [file]
   ```
   → What changed since it last worked?

---

## Step 3: Verify the Root Cause

Before touching ANY code:

1. **Trace the data flow:**
   - Where does the data come from?
   - How is it passed to the function?
   - Where should it be used?
   - Is it being used from the right place?

2. **Check for path issues:**
   - Is the function loading from the right location?
   - Is it using a local import vs. passed-in parameter?
   - Is it using ASSETS_DIR vs BASE_DIR correctly?

3. **Check for timing issues:**
   - Is the function called at the right time?
   - Is data loaded before it's used?

4. **Verify with test/inspection:**
   - Print config values
   - Check what's actually being loaded
   - Use Python REPL or small test script to verify

---

## Step 4: Make ONE Change Only

1. **Make a single, surgical fix** to ONE file
2. **Change only the line(s) needed** - nothing else
3. **Document it in CHANGES.md:**
   ```
   ## Commit: [name]
   - **File:** [path] line [number]
   - **What changed:** [brief description]
   - **Why:** [root cause explanation]
   - **Expected fix:** [what should now work]
   ```

4. **Commit with detailed message:**
   ```bash
   git commit -m "fix: [specific issue]

   Root cause: [why it was broken]
   
   Changed: [what file, what line]
   From: [old code]
   To: [new code]
   
   This fixes: [what the user reported]"
   ```

---

## Step 5: Rebuild and Test

1. **Kill all running processes:**
   ```powershell
   Get-Process | Where-Object {$_.Name -like "*Relist*"} | Stop-Process -Force
   ```

2. **Clean build:**
   ```bash
   rm -rf build/ dist/
   pyinstaller "Relist Agent v1.5.0.spec" --noconfirm
   ```

3. **Rename EXE cleanly**

4. **Test ONE thing:**
   - Run the app
   - Open the specific window/feature that was broken
   - Check the debug log for that feature
   - Verify: does it show the expected behavior?

5. **Verify nothing else broke:**
   - Check other features still work
   - Look at debug logs for other features

---

## Step 6: Report Findings

Report EXACTLY:
- ✅ What was fixed
- ✅ How you verified it works
- ✅ What logs show as evidence
- ⚠️ Any other issues found

Example:
```
✅ EXCLUSIONS FIX VERIFIED
- Root cause: load_excluded_from_config() was importing fresh config instead of using self.config_dict
- Fix: Changed line 901 to use self.config_dict.get("excluded_skus", [])
- Verification: exclusions_debug.log now shows "Loaded 552 SKUs" instead of "Loaded 0 SKUs"
- Other features: Store name display and search filter remain unchanged
```

---

## RED FLAGS — STOP IF YOU SEE THESE

- ❌ "I think the code does X" → READ IT FIRST
- ❌ "This should be the issue" → VERIFY FIRST
- ❌ "Let me try changing this" → CHECK GIT DIFF FIRST
- ❌ "I'll rebuild and see" → UNDERSTAND THE PROBLEM FIRST
- ❌ Multiple changes to the same file → ONE CHANGE ONLY
- ❌ Touching code that wasn't mentioned → DON'T TOUCH IT
- ❌ No evidence in debug logs → KEEP INVESTIGATING

---

## Process Checklist

Before claiming a fix is done:

- [ ] Read actual file contents (not assumptions)
- [ ] Checked git log and diff
- [ ] Reviewed debug logs
- [ ] Identified root cause with evidence
- [ ] Made ONE change only
- [ ] Committed with detailed message
- [ ] Updated CHANGES.md
- [ ] Rebuilt clean
- [ ] Tested the specific feature
- [ ] Verified no other features broke
- [ ] Reported with debug log evidence

**If ANY of these are missing, the fix is not complete.**
