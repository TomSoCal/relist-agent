# PandaSuite Commercial License Agreement

**Relist Agent v2.0+**  
**Part of PandaSuite by The Trashed Panda**

**Last Updated: 2026-07-27**

---

## 1. PRODUCT DEFINITION

This Commercial License Agreement ("Agreement") governs the use of **Relist Agent**, a component of **PandaSuite**, a suite of e-commerce automation applications designed by **The Trashed Panda**.

**Product Name:** Relist Agent  
**Product Version:** 2.0.0 and later  
**Publisher:** The Trashed Panda  
**Product Category:** eBay Automation & Listing Management  

---

## 2. LICENSE GRANT

### 2.1 Grant of Rights

Subject to the terms and conditions of this Agreement, The Trashed Panda grants you a **non-exclusive, non-transferable, revocable license** to:

- Install and use Relist Agent on your computer(s)
- Use Relist Agent to automate eBay listing management for your own business
- Access shared PandaSuite infrastructure (%appdata%\PandaSuite\) for API credential management
- Receive automatic updates and technical support during your license term

### 2.2 Permitted Use

You may use Relist Agent **solely for your own business purposes**, specifically:

- Refreshing your active eBay listings
- Managing listing lifecycle (create, edit, delist)
- Automating repetitive listing tasks
- Integrating with other PandaSuite applications

### 2.3 Restrictions

You may NOT:

- Resell, redistribute, or sublicense Relist Agent
- Reverse engineer, decompile, or disassemble the software
- Remove or modify any copyright, trademark, or license notices
- Use Relist Agent to provide services to third parties
- Rent, lease, or lend Relist Agent
- Create derivative works or modifications
- Use Relist Agent for any illegal purpose
- Violate eBay's Terms of Service or API Agreement

---

## 3. COMMERCIAL LICENSE TERMS

### 3.1 License Key

Your purchased license includes a **unique license key** tied to:
- Your computer (hardware-specific)
- Your eBay account
- Your purchase date and version

### 3.2 License Activation

- License key is **required for activation**
- One-time activation per computer
- Server-side verification via update-key.php
- Automatic re-validation on app updates

### 3.3 License Validity

- License is perpetual for the purchased version
- Updates and new versions may require new license
- License remains valid after app uninstall (data preserved in %appdata%\PandaSuite\)

### 3.4 Multi-Computer Use

- One license = one computer
- If you use multiple computers, you need multiple licenses
- Home + work computer? Purchase a second license
- Contact support for volume/multi-license discounts

---

## 4. PANDA SUITE INTEGRATION

### 4.1 Shared Infrastructure

Relist Agent shares credentials via PandaSuite:

```
%appdata%\PandaSuite\
├── ebay/              (shared API credentials)
│   ├── config.json   (eBay app_id, dev_id, cert_id)
│   └── tokens.json   (OAuth tokens)
├── relist-agent/      (your Relist Agent license)
├── panda-print/       (if you own Panda Print)
└── panda-profit/      (if you own Panda Profit)
```

### 4.2 API Credentials

- Your eBay API credentials are **YOUR responsibility**
- Store them securely in your PandaSuite folder
- Do not share your credentials with others
- Regenerate credentials if compromised

### 4.3 License Isolation

- Each PandaSuite app has its own license
- Relist Agent license cannot be used in Panda Print
- Licenses are app-specific and computer-specific
- Cannot transfer license between apps

---

## 5. SUPPORT & UPDATES

### 5.1 Technical Support

Included with your license:

- **Email Support:** support@thetrashedpanda.com
- **Response Time:** 24-48 hours (business days)
- **Coverage:** Bug fixes, setup assistance, troubleshooting
- **Scope:** Limited to Relist Agent functionality

NOT included:

- eBay API troubleshooting (contact eBay Support)
- Custom development or feature requests
- Dedicated account management

### 5.2 Automatic Updates

- New versions released periodically
- In-app update checker notifies you
- Updates are installed automatically (optional)
- Major version upgrades may require new license

### 5.3 Update Frequency

- Bug fixes: as needed
- Minor updates (v2.0.x): quarterly
- Major updates (v2.1, v3.0): annual or as needed

---

## 6. PRICING & PAYMENT

### 6.1 License Pricing

- **One-Time License:** $49.99 (perpetual for version purchased)
- **Payment Method:** Credit card via Stripe
- **Refund Policy:** 30-day money-back guarantee
- **No Subscription:** One-time purchase, no recurring fees

### 6.2 Volume Discounts

- 5+ licenses: 15% discount
- 10+ licenses: 20% discount
- Contact: sales@thetrashedpanda.com

### 6.3 Renewal

- Perpetual license for purchased version
- New major versions may require new license
- Existing customers get upgrade pricing (typically 20-30% discount)

---

## 7. INTELLECTUAL PROPERTY

### 7.1 Ownership

All intellectual property in Relist Agent and PandaSuite:

- **Copyright:** © 2026 The Trashed Panda. All rights reserved.
- **Trademarks:** "Relist Agent," "PandaSuite," "The Trashed Panda" are trademarks
- **Patents:** Any included algorithms and methods are proprietary
- **You Own:** Your data (listings, preferences, API credentials)

### 7.2 Use of Data

We collect minimal data:

- License activation status (verification only)
- App version and update checks
- Crash reports (optional, for debugging)
- NO tracking of your listings or eBay sales data

Your data stays on your computer in:
- `%appdata%\PandaSuite\` (shared credentials)
- Local log files and backups
- We do NOT transmit your listing data to our servers

---

## 8. WARRANTIES & DISCLAIMERS

### 8.1 Limited Warranty

Relist Agent is provided "AS-IS" with no warranty:

- No warranty that it will meet your needs
- No warranty of merchantability or fitness
- No warranty of error-free operation
- No warranty that it complies with eBay's current terms

### 8.2 eBay Compliance

**Important:** Relist Agent is an unofficial tool. It:

- Uses eBay's public Trading API
- Complies with eBay API Terms of Service
- Is NOT endorsed or supported by eBay
- Could be restricted or blocked by eBay at any time

**Use at your own risk.** The Trashed Panda is not responsible for:

- eBay account suspension or restrictions
- eBay API changes or deprecation
- Loss of listings or data
- Compliance with eBay's Seller Standards

### 8.3 Limitation of Liability

**To the maximum extent permitted by law:**

The Trashed Panda is NOT liable for:

- Loss of data, revenue, or profits
- Business interruption
- Indirect, incidental, or consequential damages
- Any damages over the amount you paid for the license

---

## 9. TERMINATION

### 9.1 Termination by You

You may terminate this license anytime by:

- Uninstalling Relist Agent
- Not renewing after license expiration (if subscription model added)
- Requesting deletion via support

### 9.2 Termination by The Trashed Panda

We may terminate your license if you:

- Violate any term of this Agreement
- Use it for illegal purposes
- Share your license key with others
- Reverse engineer or tamper with the software
- Violate eBay's Terms of Service

Termination may include:

- License key deactivation
- Revocation of access to PandaSuite infrastructure
- Deletion of your data (upon request)

### 9.3 Survival

Upon termination:

- Your license rights end immediately
- You must uninstall the software
- Termination does not affect already-completed tasks
- You may export your data (if available)

---

## 10. CHANGES TO THIS AGREEMENT

### 10.1 Right to Modify

The Trashed Panda may update this Agreement:

- You'll be notified of material changes
- Continued use = acceptance of new terms
- You have 30 days to review before changes take effect

### 10.2 Notification

Updates to this Agreement will be:

- Posted on thetrashedpanda.com
- Included in release notes
- Sent via email (if you opt-in)

---

## 11. GOVERNING LAW & JURISDICTION

- This Agreement is governed by laws of **California**
- Disputes will be resolved through binding arbitration
- Location: San Francisco, California
- Arbitration rules: American Arbitration Association (AAA)

**No Class Actions:**

- You agree to resolve disputes on an individual basis
- No class action lawsuits against The Trashed Panda

---

## 12. CONTACT & SUPPORT

### 12.1 Support Channels

**Email:** support@thetrashedpanda.com  
**Website:** https://thetrashedpanda.com  
**Hours:** Monday-Friday, 9 AM - 5 PM PT  

### 12.2 Bug Reports

Found a bug? Help us improve:

- Email: bugs@thetrashedpanda.com
- Include: version number, OS, steps to reproduce
- We'll investigate within 48 hours

### 12.3 Feature Requests

Have an idea?

- Email: features@thetrashedpanda.com
- We review all requests quarterly
- No guarantee of implementation

---

## 13. ENTIRE AGREEMENT

This Agreement constitutes the entire agreement between you and The Trashed Panda regarding Relist Agent.

**Previous Agreements:** Any prior agreements, licenses, or terms are superseded by this Agreement.

**Severability:** If any term is found invalid, remaining terms remain in effect.

---

## SCHEDULE A: PRODUCT VERSIONS

### Current Version
- **v2.0.0:** July 2026 (current)
- **v2.0.1:** August 2026 (planned)
- **v2.1.0:** December 2026 (planned)

### Legacy Versions
- **v1.5.0:** No longer supported (but licenses still valid)
- **v1.0.x:** No longer supported (but licenses still valid)

### Support Lifecycle
- **Current version:** Full support
- **Previous 2 versions:** Critical bugs only
- **Older versions:** Community support only (no SLA)

---

## SCHEDULE B: PANDA SUITE INTEGRATION

Relist Agent is part of PandaSuite. You may also use:

- **Panda Print** (if licensed separately) — Label printing & management
- **Panda Profit** (if licensed separately) — Analytics & reporting
- **Future Apps** (TBD) — Amazon, Etsy, other platforms

Each app:
- Requires its own license (not shared)
- Shares API credentials via %appdata%\PandaSuite\
- Operates independently

---

## ACCEPTANCE

By installing and using Relist Agent, you acknowledge that you have:

- Read this entire Agreement
- Understood the terms and conditions
- Agreed to be bound by this Agreement
- Accept all limitations and disclaimers

**You agree to these terms by activating your license.**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-27 | Initial commercial license |

---

**© 2026 The Trashed Panda. All Rights Reserved.**

**Last Updated:** July 27, 2026

