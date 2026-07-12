# eBay Relist Agent — Frequently Asked Questions

## Installation & Setup

**Q: What are the system requirements?**
A: Windows PC or Mac with internet connection. The tool is distributed as an `.exe` (Windows) or `.dmg` (Mac). No need to install Python separately—everything is included in the executable.

**Q: How do I install it?**
A: 
1. Download the `.exe` (Windows) or `.dmg` (Mac)
2. Run the installer
3. Authenticate with your eBay seller account via the GUI
4. Configure your settings (schedule, number of items, etc.)
5. Enable the scheduled task to start automatic relisting

**Q: Do I need coding knowledge?**
A: No—it's completely point-and-click. Just configure your settings in the GUI and let it run automatically.

---

## How It Works

**Q: How does it choose which items to relist?**
A: The agent automatically relists your oldest active fixed-price listings. You decide how many items to relist per run (1–100+) in the settings.

**Q: When does it run?**
A: By default, 10:30 AM daily. You can customize the schedule in the Settings tab (select time and days of the week).

**Q: Can I use it with multiple eBay accounts?**
A: Yes—one license per eBay seller account. You can run the tool on different machines or accounts independently.

**Q: What happens to my listings when they're relisted?**
A: The old listing is ended, and a new listing is created with identical details:
- Same title, description, price
- Same quantity, condition, shipping settings
- Same item specifics and photos
- New item ID (eBay's requirement)

**Q: Will my inventory quantity be preserved?**
A: Yes—quantity is automatically carried over from the old listing to the new one.

---

## Safety & Compliance

**Q: Will this get my eBay account suspended?**
A: No—the tool uses eBay's official API and follows standard relisting practices. As long as you comply with eBay's policies (accurate listings, no spam, etc.), you're safe. **Important:** You are responsible for ensuring compliance with eBay's terms of service.

**Q: Is my eBay login safe?**
A: Your credentials are **NOT stored**. The tool uses secure OAuth tokens for eBay API access. Your password is never transmitted to our servers.

**Q: What credentials are required?**
A: You'll need to provide your eBay API credentials (App ID, Dev ID, Cert ID) during setup. These are stored locally on your machine and used only for API authentication.

**Q: Will this affect my seller ratings?**
A: No—relisting is a normal eBay action. In fact, many sellers see improved search visibility because eBay's algorithm favors "New Listings."

---

## Usage & Results

**Q: How much will my sales increase?**
A: Results vary widely depending on your inventory, pricing, competition, and market demand. Daily relisting boosts your visibility in eBay's "New Listings" algorithm, which can lead to more impressions and sales. Some sellers report 10–30% improvement; others see less impact.

**Q: Can I pause it during vacation?**
A: Yes—you can disable the scheduled task through the app's Settings tab. The scheduled task is managed through Windows Task Scheduler (or Mac's launchd), and the app provides an easy way to enable/disable it.

**Q: What if I stop using it?**
A: Your license is yours forever. Simply disable the scheduled task in the app. No data is lost—your settings are saved locally.

**Q: Can I relist specific items instead of oldest first?**
A: Currently, the tool relists based on age (oldest first). Custom selection isn't available in this version but may be considered for future updates.

---

## Features & Management

**Q: What is the "Find Duplicates" feature?**
A: Scans your inventory for items with the same SKU and displays them. This is view-only—no action is taken. Use it to review potential duplicates.

**Q: What is "Auto-Delist Dupes"?**
A: Automatically finds and removes true duplicate listings (matching both title AND SKU). It keeps the newest listing and delists older copies. You must confirm before deletion.

**Q: Can I edit listings before relisting?**
A: Currently, the tool relists with identical details. To edit before relisting, you can manually end a listing on eBay and manually create a new one, or request custom edits in a future version.

**Q: What's the "Activity Log"?**
A: Shows all relist operations—successful relists, failed attempts, zero-quantity items ended, etc. Useful for troubleshooting and verification.

---

## Troubleshooting

**Q: The app won't start. What do I do?**
A: 
1. Make sure you're on Windows 10+ or Mac 10.14+
2. Check your internet connection
3. Try running as Administrator (Windows) or with full permissions (Mac)
4. Email support@thetrashedpanda.com with your error message

**Q: A relist failed. Why?**
A: Common reasons:
- eBay API is temporarily unavailable
- Item violates current eBay policies
- Your account has restrictions or limited API access
- Network connection dropped

Check the Activity Log for error details. The agent will retry automatically on the next scheduled run.

**Q: I want to change the schedule. How?**
A: Open Settings in the app, select your preferred time and days, and click "Update Schedule." Changes take effect immediately.

**Q: Can I adjust how many items relist per run?**
A: Yes—in Settings, change the "Items per run" value (default: 10). This applies to your next scheduled run.

---

## Support & Refunds

**Q: Do you offer refunds?**
A: No—once purchased, the license is final. However, if the tool is non-functional or doesn't meet expectations, contact support for troubleshooting.

**Q: What if the tool stops working after an eBay API update?**
A: We'll update the tool when possible to maintain compatibility. However, we cannot guarantee compatibility forever if eBay makes major API changes. See the Terms of Service for liability limits.

**Q: How do I get support?**
A: Email support@thetrashedpanda.com with:
- Your operating system (Windows 10, Mac 12, etc.)
- The exact error message or issue
- Steps you've already tried
- Screenshot of the Activity Log (if applicable)

We'll respond with troubleshooting steps or a fix.

**Q: What's included in the license?**
A: 
- The Relist Agent executable (Windows + Mac)
- Automatic updates for bug fixes and minor improvements
- Email support
- Lifetime use on one eBay account

---

## Technical Questions

**Q: Where is my data stored?**
A: All data (settings, activity log, cache) is stored locally on your machine in a config folder. Nothing is uploaded to our servers.

**Q: Does it work on Mac M1/M2?**
A: Yes—the Mac version includes native support for Apple Silicon.

**Q: Can I run it on a server or headless?**
A: The scheduled task runs in the background. The GUI is optional for setup/configuration, but the agent itself doesn't require the app to be running—Windows Task Scheduler or Mac's launchd handles scheduling.

**Q: Does it use a lot of internet bandwidth?**
A: No—minimal bandwidth. Only API calls to eBay and email notifications consume data (negligible amounts).

**Q: Can I export my activity log?**
A: Currently, the Activity Log is displayed in the app. You can take screenshots or copy/paste into Excel. Export to CSV may be added in future versions.

---

## Legal & Terms

**Q: Am I responsible for eBay compliance?**
A: Yes—you use this tool at your own discretion. You're responsible for ensuring your listings comply with eBay policies, local laws, and any applicable regulations. The tool is a utility; compliance is your responsibility.

**Q: Is there a Terms of Service?**
A: Yes—see the included TOS document for full details on liability, warranty disclaimers, and usage restrictions.

**Q: What data does the tool collect?**
A: None—the tool collects zero data about your usage. All processing happens locally on your machine.

---

## Updates & Future

**Q: How often is the tool updated?**
A: Updates are released as needed for bug fixes and eBay API compatibility. You'll be notified of updates in the app.

**Q: What's planned for future versions?**
A: Possible improvements:
- Custom relist logic (by category, price, etc.)
- Advanced scheduling (weekends off, vacation mode, etc.)
- Bulk editing before relist
- CSV export for Activity Log
- Multi-account management

**Q: Can I request a feature?**
A: Yes—email support@thetrashedpanda.com with your feature request. No guarantee it will be implemented, but we'll consider popular requests.

---

## Still Have Questions?

Email: **support@thetrashedpanda.com**

Include:
- Your question or issue
- Your operating system
- Screenshot (if relevant)
- Any error messages

We'll respond within 24–48 hours.
