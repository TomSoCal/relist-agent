"""create_delivery_pdfs.py
Generates one branded delivery PDF per event template.
Each PDF contains the Google Sheets /copy link, a thank-you note,
step-by-step setup instructions, and a tip box — all styled to match
the event's color theme.
"""

import os
import re
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN_FILE      = r'C:\Users\tom\agents\etsy\token.json'
DRIVE_FOLDER_ID = '1qHymhJWDap0cVk3jYWFQ4ZVy0pIrMVRX'
OUT_DIR         = Path(r'C:\Users\tom\agents\etsy\delivery-pdfs')
FONT_DIR        = r'C:\Windows\Fonts'
W, H            = letter   # 612 x 792 pts

OUT_DIR.mkdir(exist_ok=True)

# ── Register fonts ─────────────────────────────────────────────────────────────
def reg(name, file):
    path = os.path.join(FONT_DIR, file)
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path))
        return True
    return False

reg('Raleway',      'Raleway-Regular.ttf')   or reg('Raleway',      'calibri.ttf')
reg('Raleway-Bold', 'Raleway-Bold.ttf')      or reg('Raleway-Bold', 'calibrib.ttf')
reg('Raleway-SemiBold','Raleway-SemiBold.ttf') or reg('Raleway-SemiBold','calibrib.ttf')

# Fall back to built-in Helvetica names if TTF unavailable
FONT_REG  = 'Raleway'      if 'Raleway'       in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
FONT_BOLD = 'Raleway-Bold' if 'Raleway-Bold'  in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
FONT_SEMI = 'Raleway-SemiBold' if 'Raleway-SemiBold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'

# ── Event definitions ─────────────────────────────────────────────────────────
EVENTS = [
    {
        "key":       "wedding",
        "label":     "WEDDING PLANNER",
        "full":      "Wedding Planning Spreadsheet Template",
        "nav":       "#1F3864",
        "gld":       "#C49A6C",
        "bg_light":  "#EAF0FB",
        "emoji":     "💍",
        "tab7":      "Seating Chart",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1RkD8HXoAV-gM2TBHCWaeE4kYw19c5vfSbPJY-MfWOCQ/copy",
    },
    {
        "key":       "quinceanera",
        "label":     "QUINCEAÑERA PLANNER",
        "full":      "Quinceanera Planning Spreadsheet Template",
        "nav":       "#6B2D8B",
        "gld":       "#C49A6C",
        "bg_light":  "#F5EDF9",
        "emoji":     "👑",
        "tab7":      "Court of Honor",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1MN3mtCo9_vtWloce1GeYbN5t_16YRpjLIG6vQF1dVKo/copy",
    },
    {
        "key":       "sweet16",
        "label":     "SWEET 16 PLANNER",
        "full":      "Sweet 16 Planning Spreadsheet Template",
        "nav":       "#C2185B",
        "gld":       "#F8BBD0",
        "bg_light":  "#FDE8F1",
        "emoji":     "🎀",
        "tab7":      "Party Planner",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1UJDbyyteqsAs7CTX4BVvxqHNO8-Of7iPwvXTdh1_jB4/copy",
    },
    {
        "key":       "babyshower",
        "label":     "BABY SHOWER PLANNER",
        "full":      "Baby Shower Planning Spreadsheet Template",
        "nav":       "#2E7D32",
        "gld":       "#A5D6A7",
        "bg_light":  "#EBF5EB",
        "emoji":     "🍼",
        "tab7":      "Gift Registry",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1WCPAu0V4HhNsHAyRuv00l5RcqzOq4uko0y6zfySHtiw/copy",
    },
    {
        "key":       "birthday",
        "label":     "MILESTONE BIRTHDAY PLANNER",
        "full":      "Milestone Birthday Planning Spreadsheet Template",
        "nav":       "#4A148C",
        "gld":       "#FFD700",
        "bg_light":  "#EDE7F6",
        "emoji":     "🎂",
        "tab7":      "Party Checklist",
        "sheet_url": "https://docs.google.com/spreadsheets/d/17i0mVJ4TgEXcPTirLKz_t-KCdI3AAP1Yq8kOQkCp0RA/copy",
    },
    {
        "key":       "corporate",
        "label":     "CORPORATE EVENT PLANNER",
        "full":      "Corporate Event & Gala Planning Spreadsheet Template",
        "nav":       "#1A237E",
        "gld":       "#B8860B",
        "bg_light":  "#E8EAF6",
        "emoji":     "🏢",
        "tab7":      "Sponsorship Tracker",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1u-jksreUNYZYF_zxgiADl9u56hgc8xvyfFfwZGyHsnM/copy",
    },
    {
        "key":       "bridalshower",
        "label":     "BRIDAL SHOWER PLANNER",
        "full":      "Bridal Shower Planning Spreadsheet Template",
        "nav":       "#880E4F",
        "gld":       "#F8BBD0",
        "bg_light":  "#FDE8F1",
        "emoji":     "💐",
        "tab7":      "Games & Activities",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1Wfbc26yv9yv71_QahMlMvLD9uXoioGTJ3WaA2waGFB4/copy",
    },
    {
        "key":       "graduation",
        "label":     "GRADUATION PARTY PLANNER",
        "full":      "Graduation Party Planning Spreadsheet Template",
        "nav":       "#1B5E20",
        "gld":       "#F9A825",
        "bg_light":  "#E8F5E9",
        "emoji":     "🎓",
        "tab7":      "Party Checklist",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1UJDbyyteqsAs7CTX4BVvxqHNO8-Of7iPwvXTdh1_jB4/copy",
    },
    {
        "key":       "bachelorette",
        "label":     "BACHELORETTE PARTY PLANNER",
        "nav":       "#A0006A",
        "gld":       "#F4C2C2",
        "bg_light":  "#FFF0F5",
        "emoji":     "🥂",
        "tab7":      "Memories & Wrap-Up",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1KGn5csCyidgS3oLgLMsG1zraLACwJasqVS9hHaWOcCs/copy",
        "tabs": [
            ("Dashboard",               "Budget overview, guest count, and countdown — updates automatically"),
            ("Guest List",              "RSVP, payment status, rooming assignments, and dietary notes"),
            ("Budget & Cost Split",     "Full budget tracker + per-person cost split calculator"),
            ("Accommodation",           "VRBO/Airbnb details, deposit, check-in/out, capacity"),
            ("Transportation",          "Flights, party bus, airport transfers, rideshare notes"),
            ("Activities & Itinerary",  "Full weekend schedule with costs and reservation status"),
            ("Food & Drinks",           "Restaurant reservations, grocery list, drink planning"),
            ("Games & Gifts",           "Game organizer and gift registry tracker"),
            ("Packing List",            "Who brings what — with packed checkbox"),
            ("Planning Checklist",      "3 months through day-before task list with owners"),
            ("Day-Of Timeline",         "Hour-by-hour schedule for the party day"),
            ("Memories & Wrap-Up",      "Capture favorite moments, quotes, and messages for the bride"),
            ("Instructions",            "Plain-English guide so the whole group can hit the ground running"),
        ],
    },
    {
        "key":       "retirement",
        "label":     "RETIREMENT PARTY PLANNER",
        "nav":       "#1E4D78",
        "gld":       "#C8A96E",
        "bg_light":  "#E8F0F8",
        "emoji":     "🎖️",
        "tab7":      "Event Running Order",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1LM2kl1R_nCfxI54MfnqQzQWRPF-aEU8casV8XOkDBg8/copy",
        "tabs": [
            ("Dashboard",               "Budget overview, guest count, and countdown — updates automatically"),
            ("Budget Tracker",          "Full line-item budget with auto-totals and conditional formatting"),
            ("Planning Timeline",       "8-weeks-out through day-of checklist with owners and due dates"),
            ("Guest List",              "RSVP, dietary notes, memory book contribution tracking"),
            ("Tribute & Memories",      "Career timeline, memorable quotes, and tribute speech planner"),
            ("Vendor Contacts",         "Contact info, deposits, balances, and contract status"),
            ("Decorations & Theme",     "Décor planning, career memorabilia display, photo arrangements"),
            ("Catering & Menu",         "Menu planner, dietary tracking, bar setup"),
            ("Group Gift",              "Contribution tracker with running total and payment status"),
            ("Event Running Order",     "Speech order, activity flow, and timing for the event"),
            ("Instructions",            "Plain-English guide so anyone can hit the ground running"),
        ],
    },
    {
        "key":       "debut",
        "label":     "FILIPINO DEBUT PLANNER",
        "nav":       "#7B0C28",
        "gld":       "#D4AF37",
        "bg_light":  "#F9EFF5",
        "emoji":     "🌸",
        "tab7":      "Cotillion Court",
        "sheet_url": "https://docs.google.com/spreadsheets/d/10-nA9nnIITQ6MajJVCYgUpyJLZw5zQDrF3ARZr9isUw/copy",
        "tabs": [
            ("Dashboard",               "Budget overview, guest count, and days-until-debut countdown"),
            ("Budget Tracker",          "Full line-item budget with auto-totals and conditional formatting"),
            ("Planning Timeline",       "12-months-out through day-of checklist"),
            ("Guest List",              "RSVP, meal choices, table assignments, thank-you tracking"),
            ("18 Roses",                "Name, relationship, rose color, message — for all 18 sponsors"),
            ("18 Candles",              "Name, relationship, candle color, message — for all 18"),
            ("18 Treasures",            "Name, gift/treasure, symbol, and message — for all 18"),
            ("Cotillion Court",         "Role, partner, dress color, measurements, rehearsal attendance"),
            ("Vendor Contacts",         "Contact info, deposits, balances, and contract status"),
            ("Emcee Program",           "Full program with pre-filled sample debut timeline"),
            ("Day-Of Timeline",         "Hour-by-hour schedule for the debut day"),
            ("Seating Chart",           "Table assignments — up to 30 tables, 10 seats each"),
            ("Attire Planner",          "Outfit details for the debutante and entire court"),
            ("Instructions",            "Plain-English guide so anyone can hit the ground running"),
        ],
    },
    {
        "key":       "genderreveal",
        "label":     "GENDER REVEAL PLANNER",
        "nav":       "#6B3FA0",
        "gld":       "#FFB347",
        "bg_light":  "#F0EBF9",
        "emoji":     "🎊",
        "tab7":      "Guest & Guess Tracker",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1uwbzbRwbnrKTKxKilZRT7pwi3e3obJIilvBPUlCp2pE/copy",
        "tabs": [
            ("Dashboard",               "Budget overview, guest count, and countdown — updates automatically"),
            ("Budget Tracker",          "Full line-item budget with auto-totals and conditional formatting"),
            ("Planning Timeline",       "Month-by-month checklist through day-of schedule"),
            ("Guest & Guess Tracker",   "RSVP + Baby Boy/Girl guess tracking with running tally"),
            ("Reveal Method Planner",   "Box, balloon, confetti, cake — plan your big moment step by step"),
            ("Theme & Decorations",     "Color palette, décor checklist, and vendor contacts"),
            ("Food & Drinks",           "Menu planner, dietary notes, themed food ideas"),
            ("Games & Activities",      "Game organizer with materials, cost, and host"),
            ("Vendor Contacts",         "Contact info, deposits, balances, and contract status"),
            ("Day-Of Timeline",         "Hour-by-hour schedule for the party day"),
            ("Instructions",            "Plain-English guide so anyone can hit the ground running"),
        ],
    },
    {
        "key":       "barmitzvah",
        "label":     "BAR & BAT MITZVAH PLANNER",
        "nav":       "#1A2B5E",
        "gld":       "#CFB53B",
        "bg_light":  "#E8EBF5",
        "emoji":     "✡️",
        "tab7":      "Candle Lighting",
        "sheet_url": "https://docs.google.com/spreadsheets/d/13_eTRfufNdrgqoZtggSFhOkcoE9qi6dtJWVBfFceeTU/copy",
        "tabs": [
            ("Dashboard",               "Budget overview, guest count, and countdown — updates automatically"),
            ("Budget Tracker",          "Full line-item budget with auto-totals and conditional formatting"),
            ("Master Planning Timeline","18-months-out through day-of checklist with owners"),
            ("Guest List",              "RSVP, meal choices, table numbers, and thank-you tracking"),
            ("Multi-Day Events",        "Friday night service, Shabbat lunch, Saturday party — all in one"),
            ("Vendor Contacts",         "Contact info, deposits, balances, and contract status"),
            ("Religious Preparation",   "Torah portion tracking, tutoring schedule, clergy coordination"),
            ("Candle Lighting",         "All 13 candle honorees: name, relationship, song, and speech notes"),
            ("Montage Planner",         "Photo/video montage: chapter list, photos needed, music"),
            ("Entertainment & Program", "DJ/band sets, games, hora, program sequence"),
            ("Mitzvah Project",         "Track charity/service project goals, milestones, and hours"),
            ("Seating Chart",           "Table assignments — up to 30 tables, 10 seats each"),
            ("Day-Of Timeline",         "Hour-by-hour schedule for the full celebration day"),
            ("Instructions",            "Plain-English guide so anyone can hit the ground running"),
        ],
    },
    # ── Batch 3 ───────────────────────────────────────────────────────────────
    {
        "key":       "anniversary",
        "label":     "ANNIVERSARY PARTY PLANNER",
        "nav":       "#1F3864",
        "gld":       "#C49A6C",
        "bg_light":  "#EAF0FB",
        "emoji":     "💞",
        "tab7":      "Vow Renewal Planner",
        "sheet_url": "https://docs.google.com/spreadsheets/d/13YnJZ7Z70aTxBmfPIdNExe6IQzLDz_4lf5V9ZXDimPU/copy",
    },
    {
        "key":       "bachbundle",
        "label":     "BACHELORETTE BUNDLE PLANNER",
        "nav":       "#A0006A",
        "gld":       "#F4C2C2",
        "bg_light":  "#FFF0F5",
        "emoji":     "🥂",
        "tab7":      "Weekend Timeline",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1ZjeKCM__d-NXkhI_Y8HIcwrZ-u2nQ7ppZy2t-XUcUG8/copy",
    },
    {
        "key":       "blockparty",
        "label":     "BLOCK PARTY PLANNER",
        "nav":       "#BF360C",
        "gld":       "#FFB300",
        "bg_light":  "#FFF3E0",
        "emoji":     "🎪",
        "tab7":      "Activity Schedule",
        "sheet_url": "https://docs.google.com/spreadsheets/d/14SBTzgNGAzJ_GGimpIwlIm3GE8pHlhnvdcT0EshxRUA/copy",
    },
    {
        "key":       "classreunion",
        "label":     "CLASS REUNION PLANNER",
        "nav":       "#1A237E",
        "gld":       "#F9A825",
        "bg_light":  "#E8EAF6",
        "emoji":     "🎓",
        "tab7":      "Memory Board",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1_2DCcd5n2a23jSJId3JYv5KV5s1e5qH-S_2dwsmJu2E/copy",
    },
    {
        "key":       "destwedding",
        "label":     "DESTINATION WEDDING PLANNER",
        "nav":       "#1F3864",
        "gld":       "#C49A6C",
        "bg_light":  "#EAF0FB",
        "emoji":     "✈️",
        "tab7":      "Travel Planner",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1DFlOli1-I8LtTM-kXwugfY-vLXCt8HetLrL8W8k0-gU/copy",
    },
    {
        "key":       "elopement",
        "label":     "ELOPEMENT PLANNER",
        "nav":       "#4A0072",
        "gld":       "#CE93D8",
        "bg_light":  "#F3E5F5",
        "emoji":     "💫",
        "tab7":      "Elopement Checklist",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1nBkmrKv3TKzXQMkjG8zu0UjWR2Yg8qAADc0tLxcgKVo/copy",
    },
    {
        "key":       "familyreunion",
        "label":     "FAMILY REUNION PLANNER",
        "nav":       "#1B5E20",
        "gld":       "#81C784",
        "bg_light":  "#E8F5E9",
        "emoji":     "👨‍👩‍👧‍👦",
        "tab7":      "Activity Planner",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1OqPP-MG-vh8dt6cDb6jh99Bjuz9E_wKDkwuO7724m2M/copy",
    },
    {
        "key":       "fundraiser",
        "label":     "FUNDRAISER & GALA PLANNER",
        "nav":       "#B71C1C",
        "gld":       "#FFB74D",
        "bg_light":  "#FFEBEE",
        "emoji":     "🙌",
        "tab7":      "Donor Tracker",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1P4WkhofQmTff1hqx48g_E66jPmS1LU5VJmhc1sY5mN0/copy",
    },
    {
        "key":       "hinduwedding",
        "label":     "HINDU WEDDING PLANNER",
        "nav":       "#B71C1C",
        "gld":       "#F9A825",
        "bg_light":  "#FFEBEE",
        "emoji":     "🪔",
        "tab7":      "Multi-Event Ceremonies",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1iOj3bXXERu_LP5FFE9SqhyvVao7J5mRTv2QwUp-mLmk/copy",
    },
    {
        "key":       "holidayparty",
        "label":     "HOLIDAY PARTY PLANNER",
        "nav":       "#B71C1C",
        "gld":       "#388E3C",
        "bg_light":  "#FFEBEE",
        "emoji":     "🎄",
        "tab7":      "Gift Exchange",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1pijA2Lwu2UOvU57Je5NgZa07TRMXTsohLv_Ba8LkrPA/copy",
    },
    {
        "key":       "jewishwedding",
        "label":     "JEWISH WEDDING PLANNER",
        "nav":       "#1A2B5E",
        "gld":       "#CFB53B",
        "bg_light":  "#E8EBF5",
        "emoji":     "✡️",
        "tab7":      "Jewish Traditions",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1g6USfrjfsjGyBy_ryCTJGimT3L5-gLdz46Pzg9H3z2A/copy",
    },
    {
        "key":       "multicurrency",
        "label":     "MULTI-CURRENCY EVENT PLANNER",
        "nav":       "#01579B",
        "gld":       "#F9A825",
        "bg_light":  "#E1F5FE",
        "emoji":     "🌍",
        "tab7":      "Currency Converter",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1CY6sCXgeBCnvAEBwX67vdtZ2Ise_Z52pdWUlONl7bho/copy",
    },
    {
        "key":       "muslimwedding",
        "label":     "MUSLIM WEDDING PLANNER",
        "nav":       "#1B5E20",
        "gld":       "#C8A96E",
        "bg_light":  "#E8F5E9",
        "emoji":     "🕌",
        "tab7":      "Nikah & Walima Planner",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1MBIazAHMR2RhlMeI59g2A3N7wqKa5CvV4qJZdUiULGM/copy",
    },
    {
        "key":       "virtualevent",
        "label":     "VIRTUAL EVENT PLANNER",
        "nav":       "#0D47A1",
        "gld":       "#64B5F6",
        "bg_light":  "#E3F2FD",
        "emoji":     "💻",
        "tab7":      "Run of Show",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1lcl3IIkDJSPnlhVKROSQ6cCyWNK7TeRpEw6C-0B2R4E/copy",
    },
    {
        "key":       "weddhoneymoon",
        "label":     "WEDDING & HONEYMOON PLANNER",
        "nav":       "#1F3864",
        "gld":       "#C49A6C",
        "bg_light":  "#EAF0FB",
        "emoji":     "🌴",
        "tab7":      "Honeymoon Planner",
        "sheet_url": "https://docs.google.com/spreadsheets/d/16wOjzx9IU2NQIcAQpkD6_ZuBFC-COb9Tea-06hnO2i8/copy",
    },
    # ── Batch 4 — Religious milestones ────────────────────────────────────────
    {"key":"baptism",        "label":"BAPTISM & CHRISTENING PLANNER",   "nav":"#1B4F8A","gld":"#D4AF37","bg_light":"#E3F0FF","emoji":"✝️", "tab7":"Ceremony Details",      "sheet_url":"https://docs.google.com/spreadsheets/d/1yRo63kjS4Yx4iyZrGwzyCobZxO_dMvqAAat582BFU-8/copy"},
    {"key":"firstcommunion", "label":"FIRST COMMUNION PLANNER",         "nav":"#2E7D32","gld":"#D4AF37","bg_light":"#E8F5E9","emoji":"🕊️", "tab7":"Ceremony & Prep",       "sheet_url":"https://docs.google.com/spreadsheets/d/1WeonLUkJHfvqJruQ_PzHam_l3C0-UpMCRqE7N0kLn3A/copy"},
    {"key":"confirmation",   "label":"CONFIRMATION PARTY PLANNER",      "nav":"#4A0080","gld":"#D4AF37","bg_light":"#F3E5F5","emoji":"🕊️", "tab7":"Ceremony Details",      "sheet_url":"https://docs.google.com/spreadsheets/d/17Ryuntj_wXBGFWwI3nFTL2efkUxcSwfucdvXPJMfZfk/copy"},
    # ── Batch 4 — Pre-wedding & occasions ────────────────────────────────────
    {"key":"prom",           "label":"PROM NIGHT PLANNER",              "nav":"#1A0050","gld":"#FFD700","bg_light":"#EDE7F6","emoji":"🎭", "tab7":"Group Coordinator",     "sheet_url":"https://docs.google.com/spreadsheets/d/11uSbPg7jK8JQSJGPKI3lRrpNSbaf5CJM2V42GoxGQeA/copy"},
    {"key":"vowrenewal",     "label":"VOW RENEWAL PLANNER",             "nav":"#8B0038","gld":"#D4AF37","bg_light":"#FCE4EC","emoji":"💍", "tab7":"Our Story",             "sheet_url":"https://docs.google.com/spreadsheets/d/1rkysXGeyx4X7dvPtswwors_vpd76VPz9iNZ6-QXmFXs/copy"},
    {"key":"engagementparty","label":"ENGAGEMENT PARTY PLANNER",        "nav":"#B5294D","gld":"#D4AF37","bg_light":"#FCE4EC","emoji":"💍", "tab7":"Couple's Story",        "sheet_url":"https://docs.google.com/spreadsheets/d/1Wfbc26yv9yv71_QahMlMvLD9uXoioGTJ3WaA2waGFB4/copy"},
    {"key":"rehearsaldinner","label":"REHEARSAL DINNER PLANNER",        "nav":"#2C3E7A","gld":"#C49A6C","bg_light":"#E8ECF8","emoji":"🥂", "tab7":"Toast & Seating",       "sheet_url":"https://docs.google.com/spreadsheets/d/1BNGZJfxad1rsl4nz5QCjp97lFbJPa76GNGTHcLddnHw/copy"},
    {"key":"babysprinkle",   "label":"BABY SPRINKLE PLANNER",           "nav":"#4CAF50","gld":"#FFD700","bg_light":"#E8F5E9","emoji":"🌧️", "tab7":"Gift Registry",         "sheet_url":"https://docs.google.com/spreadsheets/d/1yD1pnpzIi95k1q-5L7VkQpCk44YNKj-iCKYF5kUxvA4/copy"},
    {"key":"sipandsee",      "label":"SIP AND SEE PARTY PLANNER",       "nav":"#E91E8C","gld":"#FFD700","bg_light":"#FCE4EC","emoji":"👶", "tab7":"Baby Details",          "sheet_url":"https://docs.google.com/spreadsheets/d/1WCPAu0V4HhNsHAyRuv00l5RcqzOq4uko0y6zfySHtiw/copy"},
    # ── Batch 4 — Community ──────────────────────────────────────────────────
    {"key":"housewarming",   "label":"HOUSEWARMING PARTY PLANNER",      "nav":"#5D4037","gld":"#FF8F00","bg_light":"#FFF3E0","emoji":"🏡", "tab7":"House Tour Checklist",  "sheet_url":"https://docs.google.com/spreadsheets/d/1d4MAFKGR1hBVKKU0LLUqP8fLCcHnBNP5DEOjJkk-P0c/copy"},
    {"key":"surpriseparty",  "label":"SURPRISE PARTY PLANNER",          "nav":"#1B5E20","gld":"#FFD700","bg_light":"#E8F5E9","emoji":"🎉", "tab7":"Surprise Logistics HQ", "sheet_url":"https://docs.google.com/spreadsheets/d/1Na5AzKPGVzQ_GeWmA4NvlwH2bHO1KpmwfHC3ewsrS28/copy"},
    {"key":"sportsbanquet",  "label":"SPORTS BANQUET & AWARDS NIGHT",   "nav":"#1A237E","gld":"#FFD700","bg_light":"#E8EAF6","emoji":"🏆", "tab7":"Awards & Roster",       "sheet_url":"https://docs.google.com/spreadsheets/d/1UJDbyyteqsAs7CTX4BVvxqHNO8-Of7iPwvXTdh1_jB4/copy"},
    # ── Batch 4 — Cultural ───────────────────────────────────────────────────
    {"key":"hightea",        "label":"HIGH TEA & BRUNCH PLANNER",       "nav":"#880E4F","gld":"#D4AF37","bg_light":"#FCE4EC","emoji":"🫖", "tab7":"Menu & Tea Planner",    "sheet_url":"https://docs.google.com/spreadsheets/d/1MRwTFxqL6CHQjG-TUJ5kGZA6r29EVJ-qzRxNfnSxjQo/copy"},
    {"key":"eid",            "label":"EID AL-FITR CELEBRATION PLANNER", "nav":"#00695C","gld":"#D4AF37","bg_light":"#E0F2F1","emoji":"🌙", "tab7":"Eidi & Gifts Tracker",  "sheet_url":"https://docs.google.com/spreadsheets/d/1C-M1YfouzHN9YPfNGNWElhjeZbBAj9QEmYt8bOW-37g/copy"},
    {"key":"diwali",         "label":"DIWALI CELEBRATION PLANNER",      "nav":"#7B0D1E","gld":"#FFD700","bg_light":"#FFF8E1","emoji":"🪔", "tab7":"Traditions Planner",    "sheet_url":"https://docs.google.com/spreadsheets/d/1rt5qVmzZ8S1ZLxQBwOO3LO71vJrT3AvzSZuowkFZY_w/copy"},
    {"key":"diademuertos",   "label":"DÍA DE LOS MUERTOS PLANNER",      "nav":"#4A0010","gld":"#FF8C00","bg_light":"#FFF3E0","emoji":"💀", "tab7":"Ofrenda Planner",       "sheet_url":"https://docs.google.com/spreadsheets/d/1MN3mtCo9_vtWloce1GeYbN5t_16YRpjLIG6vQF1dVKo/copy"},
    # ── Batch 4 — Language variants ──────────────────────────────────────────
    {"key":"wedding_es",     "label":"PLANIFICADOR DE BODA",            "nav":"#1F3864","gld":"#C49A6C","bg_light":"#EAF0FB","emoji":"💍", "tab7":"Plano de Asientos",     "sheet_url":"https://docs.google.com/spreadsheets/d/1AHlLbOVwVuxUY-GlV79M8EFNfTZa2n9k492AL92_ZmM/copy"},
    {"key":"wedding_pt",     "label":"PLANEJADOR DE CASAMENTO",         "nav":"#1F3864","gld":"#C49A6C","bg_light":"#EAF0FB","emoji":"💍", "tab7":"Planta de Assentos",    "sheet_url":"https://docs.google.com/spreadsheets/d/12wAKaDUA3lIyDGOVTMlGiHknwYqLUJKUEfFIAeOBv18/copy"},
    {"key":"babyshower_es",  "label":"PLANIFICADOR DE BABY SHOWER",     "nav":"#4CAF50","gld":"#FFD700","bg_light":"#E8F5E9","emoji":"🍼", "tab7":"Registro de Regalos",   "sheet_url":"https://docs.google.com/spreadsheets/d/19TziX3IM5L7HigyjFMBrErRl7Oq7w60ie-1UbkJ62wQ/copy"},
    {"key":"retirement_es",  "label":"PLANIFICADOR FIESTA JUBILACIÓN",  "nav":"#1E4D78","gld":"#C8A96E","bg_light":"#E3EFF8","emoji":"🎖️","tab7":"Planif. de Homenaje",   "sheet_url":"https://docs.google.com/spreadsheets/d/1J-s0r0m6r3sG5pyebiRxeJaTamm8K5YTx_koisexcuY/copy"},
    {"key":"sweet16_es",     "label":"PLANIFICADOR DULCES DIECISÉIS",   "nav":"#C2185B","gld":"#9E9E9E","bg_light":"#FCE4EC","emoji":"🎂", "tab7":"Planificador Fiesta",      "sheet_url":"https://docs.google.com/spreadsheets/d/1UCaJ1DquRRXvI2WAD_eXkcnx8N8iPvCRalmr3_v0TrQ/copy"},
    {"key":"diademuertos_es","label":"PLANIFICADOR DÍA DE LOS MUERTOS", "nav":"#4A0010","gld":"#FF8C00","bg_light":"#FFF3E0","emoji":"💀", "tab7":"Planificador de Ofrenda",  "sheet_url":"https://docs.google.com/spreadsheets/d/1aizfWqGEQg5CuPIQvPLsgSfFiSD7jnIh0meqpL8tZNo/copy"},
    {"key":"finados_pt",      "label":"PLANEJADOR DO DIA DOS FINADOS",    "nav":"#1B4F00","gld":"#FFD700","bg_light":"#F1F8E9","emoji":"🕯️","tab7":"Planejador do Cemitério",  "sheet_url":"https://docs.google.com/spreadsheets/d/1PhxVcJLXBXK5G1Tc_4E0yWTwuItGpEER_lRRBzNY2ww/copy"},
    # ── New batch — Travel & Activity Planning ────────────────────────────────
    {"key":"roadtrip",        "label":"ROAD TRIP PLANNER",               "nav":"#0277BD","gld":"#FFD700","bg_light":"#E1F5FE","emoji":"🚗", "tab7":"Route Planner",                            "sheet_url":"https://docs.google.com/spreadsheets/d/15vLSxkEdBpHU3c2ohIZMpvD9kYXlZOvMAzRRH98QsWE/copy"},
    {"key":"kidsbirthday",     "label":"KIDS BIRTHDAY PARTY PLANNER",     "nav":"#7B1FA2","gld":"#FFD700","bg_light":"#F3E5F5","emoji":"🎉", "tab7":"Party Games & Activities",              "sheet_url":"https://docs.google.com/spreadsheets/d/17i0mVJ4TgEXcPTirLKz_t-KCdI3AAP1Yq8kOQkCp0RA/copy"},
    {"key":"microwedding",     "label":"MICRO WEDDING PLANNER",           "nav":"#C2185B","gld":"#FFD700","bg_light":"#FCE4EC","emoji":"💕", "tab7":"Ceremony Script Planner",                "sheet_url":"https://docs.google.com/spreadsheets/d/1ySaryVub9zLeZlv-KNTvEiQ5CM5tzEnOPhs7dVNfrTk/copy"},
    {"key":"honeymoon",        "label":"HONEYMOON PLANNER",               "nav":"#AD1457","gld":"#FFB6C1","bg_light":"#FCE4EC","emoji":"🌹", "tab7":"Day-by-Day Honeymoon Itinerary",        "sheet_url":"https://docs.google.com/spreadsheets/d/1nZ8KJkStQ2O6cafbwsP1X0Jwwnfu_4MzKAN73HM7AKU/copy"},
    {"key":"outdoorwedding",   "label":"OUTDOOR WEDDING PLANNER",         "nav":"#1B5E20","gld":"#8BC34A","bg_light":"#E8F5E9","emoji":"🌳", "tab7":"Weather & Logistics Plan",               "sheet_url":"https://docs.google.com/spreadsheets/d/1mEE9Hef-FvgGxa13c0IBxLLOh_Cb36rxXpj-2f-WKXU/copy"},
    {"key":"tailgate",         "label":"TAILGATE & GAME DAY PARTY",       "nav":"#0D47A1","gld":"#FFD700","bg_light":"#E3F2FD","emoji":"🏈", "tab7":"Grill Menu & Who Brings What",           "sheet_url":"https://docs.google.com/spreadsheets/d/12kkzk0z3I1c1HdnBhmXapWbzgkII7J404pRMbsB7yDI/copy"},
    {"key":"murdermystery",    "label":"MURDER MYSTERY PARTY PLANNER",    "nav":"#37474F","gld":"#B0BEC5","bg_light":"#ECEFF1","emoji":"🔍", "tab7":"Character & Clue Tracker",               "sheet_url":"https://docs.google.com/spreadsheets/d/1lg8Q1oy5zvIVjm1xftwf406wDS7CppmHEB8W5u2MY1Y/copy"},
    {"key":"corporateretreat", "label":"CORPORATE RETREAT PLANNER",       "nav":"#1A237E","gld":"#B8860B","bg_light":"#E8EAF6","emoji":"🎯", "tab7":"Sessions & Activities Schedule",        "sheet_url":"https://docs.google.com/spreadsheets/d/1u-jksreUNYZYF_zxgiADl9u56hgc8xvyfFfwZGyHsnM/copy"},
    {"key":"luau",             "label":"LUAU & HAWAIIAN PARTY PLANNER",   "nav":"#D84315","gld":"#00BCD4","bg_light":"#FBE9E7","emoji":"🌺", "tab7":"Tropical Theme Checklist",               "sheet_url":"https://docs.google.com/spreadsheets/d/1STcEZ5B-6-Zv_X8J3n-IDRpIIDmnZj_ZgrBiVzIrf4U/copy"},
    {"key":"movingplanner",    "label":"MOVING & RELOCATION PLANNER",     "nav":"#5D4037","gld":"#D2B48C","bg_light":"#EFEBE9","emoji":"📦", "tab7":"Box Inventory & Change of Address",    "sheet_url":"https://docs.google.com/spreadsheets/d/1yCXkjvH3uEun3yxmHFnBD6UgeNkBACYzD7fzWnSqy7k/copy"},
    # Vacation / travel
    {"key":"vacationplanner", "label":"VACATION TRIP PLANNER",             "nav":"#1565C0","gld":"#FFD700","bg_light":"#E3F2FD","emoji":"✈️", "tab7":"Day-by-Day Itinerary",    "sheet_url":"https://docs.google.com/spreadsheets/d/1PxWhLHI2xFYG-keIV0XFB_-Evnq7rpxggstQhHKVTaE/copy"},
    {"key":"familyvacation",  "label":"FAMILY VACATION PLANNER",           "nav":"#2E7D32","gld":"#FFD700","bg_light":"#E8F5E9","emoji":"👨‍👩‍👧‍👦","tab7":"Kids Packing List",        "sheet_url":"https://docs.google.com/spreadsheets/d/1snvoQLsrW507b0h9-n3i2sxMlPJfam-d9ah_2k4bmF8/copy"},
    {"key":"girlstrip",       "label":"GIRLS TRIP PLANNER",                "nav":"#880E4F","gld":"#FFD700","bg_light":"#FCE4EC","emoji":"✈️", "tab7":"Activities & Cost Split",  "sheet_url":"https://docs.google.com/spreadsheets/d/1fqs8urh0paiBiP-3kaBNK1WNj0O1uFGOLlDzufVVjWo/copy"},
    {"key":"cruiseplanner",   "label":"CRUISE VACATION PLANNER",           "nav":"#01579B","gld":"#FFD700","bg_light":"#E1F5FE","emoji":"🚢", "tab7":"Port Excursions Planner",  "sheet_url":"https://docs.google.com/spreadsheets/d/1pei1M0HrNt4NBoNxZj0CgDy7dd3MfQuDABAYdXS7O2o/copy"},
    {"key":"campingplanner",  "label":"CAMPING & GLAMPING PLANNER",        "nav":"#2E4A1E","gld":"#FF8F00","bg_light":"#F1F8E9","emoji":"⛺", "tab7":"Gear & Packing List",      "sheet_url":"https://docs.google.com/spreadsheets/d/1YzxT6BgmNtxQzFydTHb7Y7RZX7TfXVZUGMWKO6XeYiA/copy"},
    # ── New batch — Specialized Niches ────────────────────────────────────
    {
        "key": "fostercare",
        "label": "FOSTER CARE PLANNER",
        "nav": "#1565C0",
        "gld": "#90CAF9",
        "bg_light": "#E3F2FD",
        "emoji": "👶",
        "tab7": "Court Planning",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1RLrYzf9qA23VyBKUHUVGJBrAnqR6u9u-u6--mVv1u4A/copy",
        "tabs": [
            ("Dashboard", "Child overview, budget summary, quick stats"),
            ("Budget", "Monthly spending by category with auto-totals"),
            ("Medical", "Health conditions, medications, allergies, insurance"),
            ("Appointments", "Medical, dental, therapy, school, visitation, court dates"),
            ("Incident Log", "Behavioral, medical, safety incidents with actions"),
            ("Attachment Tracker", "Developmental milestones and emotional progress"),
            ("Court Planning", "Hearing preparation with document checklists"),
            ("Instructions", "Complete guide to using this foster care template"),
        ],
    },
    {
        "key": "specialneeds",
        "label": "SPECIAL NEEDS FAMILY PLANNER",
        "nav": "#4527A0",
        "gld": "#CE93D8",
        "bg_light": "#EDE7F6",
        "emoji": "❤️",
        "tab7": "Financial Aid",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1C2px5oD0ar3husvzxxQp9_v98ofrdffll_X30ZFF-4I/copy",
        "tabs": [
            ("Dashboard", "Child profile, IEP snapshot, budget overview"),
            ("Budget", "Therapy, equipment, medications, services costs"),
            ("IEP", "Educational goals, services, accommodations"),
            ("Medical", "Doctor visits, medications, appointment history"),
            ("Therapy Tracker", "Session notes, progress, home practice"),
            ("BehaviorSkills", "Behavior tracking and skill development"),
            ("Financial Aid", "Grants, programs, and funding opportunities"),
            ("Instructions", "Complete guide to managing special needs care"),
        ],
    },
    {
        "key": "pcos",
        "label": "PCOS TRACKER & HEALTH PLANNER",
        "nav": "#AD1457",
        "gld": "#F48FB1",
        "bg_light": "#FCE4EC",
        "emoji": "🌸",
        "tab7": "Fertility Goals",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1uG185YZqX3rKC7BXD7OBzgoJWIbbjmDmOYJktiOZ7OI/copy",
        "tabs": [
            ("Dashboard", "Current cycle, last 3 cycles summary, medications"),
            ("Cycle Tracker", "Period dates, cycle length, ovulation tracking"),
            ("Symptom Log", "Daily symptoms with severity and triggers"),
            ("Medications", "Current treatments, doses, effectiveness"),
            ("FoodEnergy", "Daily meals, energy, sleep, exercise, water"),
            ("Lab Results", "PCOS tests with reference ranges and status"),
            ("Fertility Goals", "Ovulation detection and fertility tracking"),
            ("Instructions", "Complete guide to tracking your PCOS health"),
        ],
    },
    {
        "key": "migraine",
        "label": "MIGRAINE TRACKER & MANAGEMENT",
        "nav": "#37474F",
        "gld": "#B0BEC5",
        "bg_light": "#ECEFF1",
        "emoji": "🧠",
        "tab7": "Emergency Contacts",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1aUfUlEiLVrD8t-bUw71WeMnoDs_4y1GKbUt5NL4ZTaM/copy",
        "tabs": [
            ("Dashboard", "Monthly stats, severity, triggers, medication effectiveness"),
            ("Migraine Log", "Each migraine with duration, severity, symptoms"),
            ("Trigger Tracker", "Potential triggers and confidence levels"),
            ("Medications", "Preventive and rescue medications with ratings"),
            ("Lifestyle", "Daily sleep, stress, caffeine, exercise, weather"),
            ("Doctor Notes", "Visit summaries and treatment plans"),
            ("Emergency Contacts", "Neurologist, ER preferences, migraine protocol"),
            ("Instructions", "Complete guide to tracking and managing migraines"),
        ],
    },
    {
        "key": "healthcrisis",
        "label": "HEALTH CRISIS & SERIOUS ILLNESS PLANNER",
        "nav": "#B71C1C",
        "gld": "#FFCDD2",
        "bg_light": "#FFEBEE",
        "emoji": "🏥",
        "tab7": "Hospital Prep",
        "sheet_url": "https://docs.google.com/spreadsheets/d/18zQQpcyollkBb9-MuGklWn_MsiUGGw9m2yWQdzYPUeU/copy",
        "tabs": [
            ("Dashboard", "Patient profile, emergency info, blood type, DNR status"),
            ("Medical History", "Diagnoses, surgeries, procedures, allergies"),
            ("Medications", "All current medications with doses and refills"),
            ("Appointments", "Doctor visits with outcomes and follow-ups"),
            ("Insurance", "Policy details, claims tracking, prior auths"),
            ("Care Team", "All providers with contact information"),
            ("Hospital Prep", "Hospital bag checklist, advance directives"),
            ("Instructions", "Guide to organizing your health crisis information"),
        ],
    },
    {
        "key": "petcare",
        "label": "PET CARE & BREEDER PLANNER",
        "nav": "#2E7D32",
        "gld": "#A5D6A7",
        "bg_light": "#E8F5E9",
        "emoji": "🐾",
        "tab7": "Certifications",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1MLuAXtFLs-eseSP8eVfWw3aOMDsDsL3itCfcW2R92wM/copy",
        "tabs": [
            ("Dashboard", "Pet roster, upcoming vaccinations and appointments"),
            ("Pet Profile", "Each pet's basic info, microchip, registration"),
            ("Vaccinations", "All vaccines with due dates and reminders"),
            ("Appointments", "Vet visits with reasons, outcomes, follow-ups"),
            ("Medications", "Current meds and preventive treatments calendar"),
            ("Breeding Log", "Litter info, puppy/kitten tracking, sales"),
            ("Certifications", "Show titles, health testing, breed certifications"),
            ("Instructions", "Guide to managing pet care records"),
        ],
    },
    {
        "key": "houseflipping",
        "label": "HOUSE FLIPPING PLANNER",
        "nav": "#E65100",
        "gld": "#FFB300",
        "bg_light": "#FFF3E0",
        "emoji": "🏠",
        "tab7": "Comps",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1gpGHll6vMTkEKbTbMOJOihdvpj77d5s8H2sQ70obU6U/copy",
        "tabs": [
            ("Dashboard", "Active deals, portfolio P&L, ROI metrics"),
            ("Deal Analyzer", "Property analysis with profit/ROI calculations"),
            ("Renovation Budget", "Costs by room with budgeted vs. actual"),
            ("Contractors", "Vendors with rates, licenses, insurance, ratings"),
            ("Financing", "Loan details, draw schedule, cost of capital"),
            ("Portfolio", "Completed flips with profit, ROI, hold time"),
            ("Comps", "Comparable sales for ARV justification"),
            ("Instructions", "Guide to tracking your flip projects"),
        ],
    },
    {
        "key": "realestate",
        "label": "REAL ESTATE PORTFOLIO TRACKER",
        "nav": "#1B5E20",
        "gld": "#81C784",
        "bg_light": "#E8F5E9",
        "emoji": "🏢",
        "tab7": "Tax Summary",
        "sheet_url": "https://docs.google.com/spreadsheets/d/13vvaS2LmGlbOvDXQR4HpnBsRUCeb84PEiyL8_pcDH9g/copy",
        "tabs": [
            ("Dashboard", "Portfolio overview, value, equity, income, expenses"),
            ("Property Inventory", "All properties with purchase, current value, mortgage"),
            ("Rental Income", "Monthly rent received by property and unit"),
            ("Expenses", "All costs by category (mortgage, insurance, repairs)"),
            ("Maintenance", "Repairs and upkeep with vendor info and costs"),
            ("Tenants", "Lease info, payment status, contact details"),
            ("Tax Summary", "Annual income and expenses for tax prep"),
            ("Instructions", "Guide to managing your rental portfolio"),
        ],
    },
    {
        "key": "sidehustle",
        "label": "SIDE HUSTLE INCOME TRACKER",
        "nav": "#F57F17",
        "gld": "#FFD54F",
        "bg_light": "#FFFDE7",
        "emoji": "💰",
        "tab7": "Goals",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1B4QOJs9ckDcwWzF3qZzvpVoJ1_BWdg0iGNJOLy6gOok/copy",
        "tabs": [
            ("Dashboard", "YTD income/expenses, goal progress, tax calculations"),
            ("Rideshare", "Trips, earnings, tips, miles, gas, net earnings"),
            ("Freelance", "Projects, clients, hours, rates, invoices, payments"),
            ("Shop", "Listings by platform with sales, COGS, fees, profit"),
            ("Expenses", "Business expenses by category with deductions"),
            ("Tax Prep", "Quarterly estimates and annual 1099 tracker"),
            ("Goals", "Monthly targets, weekly tracker, milestones"),
            ("Instructions", "Guide to tracking your side hustles"),
        ],
    },
    {
        "key": "granttracking",
        "label": "GRANT TRACKING & FUNDRAISING PLANNER",
        "nav": "#0D47A1",
        "gld": "#90CAF9",
        "bg_light": "#E3F2FD",
        "emoji": "🎯",
        "tab7": "Forecasting",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1MeMWyCLaco541CR4mRVPrzCX27yDuFW9zg221yPSgj0/copy",
        "tabs": [
            ("Dashboard", "Pipeline summary, financials, upcoming deadlines"),
            ("Grant Pipeline", "All opportunities with funder, deadline, stage"),
            ("Funder Directory", "Detailed funder info, focus areas, grant ranges"),
            ("Application Tracker", "Application timeline with key milestones"),
            ("Proposals", "Proposal status, word counts, section completion"),
            ("Awards", "Funded grants with reporting requirements"),
            ("Forecasting", "Pipeline projections and quarterly forecasts"),
            ("Instructions", "Guide to managing your grant pipeline"),
        ],
    },
    {
        "key": "contentcreator",
        "label": "CONTENT CREATOR INCOME TRACKER",
        "nav": "#6A1B9A",
        "gld": "#CE93D8",
        "bg_light": "#F3E5F5",
        "emoji": "📹",
        "tab7": "ContentCalendar",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1QVUe0YWp6xJ67GacBIxKwqZa0S7i2eDB_5b2pHopZl8/copy",
        "tabs": [
            ("Dashboard", "Total revenue by platform, monthly trends"),
            ("YouTube", "Video performance, views, watch time, earnings"),
            ("PodcastsSpotify", "Episode downloads, streams, listeners, revenue"),
            ("Patreon", "Patrons by tier, churn, revenue, subscriber notes"),
            ("Sponsorships", "Brand partnerships with deliverables and payments"),
            ("Affiliate", "Programs, commission rates, conversions, payouts"),
            ("ContentCalendar", "Publishing schedule, platforms, status"),
            ("Instructions", "Guide to growing your content business"),
        ],
    },
    {
        "key": "travelplanning",
        "label": "TRAVEL PLANNING & TRIP BUDGET",
        "nav": "#01579B",
        "gld": "#4FC3F7",
        "bg_light": "#E1F5FE",
        "emoji": "✈️",
        "tab7": "Settlement",
        "sheet_url": "https://docs.google.com/spreadsheets/d/12QJKQ3Vla1-j8gdDeOfvBTJoBJUgdKSBPqz_G9nDSOo/copy",
        "tabs": [
            ("Dashboard", "Trip dates, budget, spending, packing status"),
            ("Expenses", "All trip costs by category with currency conversion"),
            ("Itinerary", "Day-by-day activities with times and costs"),
            ("Accommodation", "Hotel/Airbnb details, check-in/out, booking"),
            ("Activities", "Attractions, tours, restaurants with booking status"),
            ("Packing", "Item checklist by category with status"),
            ("Settlement", "Expense splitting and trip summary"),
            ("Instructions", "Guide to planning your trip"),
        ],
    },
    {
        "key": "weddingvendor",
        "label": "WEDDING VENDOR MANAGEMENT",
        "nav": "#880E4F",
        "gld": "#F8BBD0",
        "bg_light": "#FCE4EC",
        "emoji": "💍",
        "tab7": "Contingency",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1_QljZy3uBknBd7-nPVZx5ZOSia-36PRiTgV-DDPRN3w/copy",
        "tabs": [
            ("Dashboard", "Active events, revenue, upcoming events, invoices"),
            ("Vendor Directory", "Vendors by category with contact and ratings"),
            ("Payments", "Invoice tracking with deposit due dates and status"),
            ("Timeline", "Event milestones and follow-up dates"),
            ("Communication", "Client interactions with action items"),
            ("Guest Logistics", "Hotel blocks, shuttles, accessibility, VIP guests"),
            ("Contingency", "Weather plans, backup vendors, emergency protocols"),
            ("Instructions", "Guide to managing your vendor business"),
        ],
    },
    {
        "key":       "road-trip",
        "label":     "ROAD TRIP PLANNER",
        "full":      "Road Trip Planning Spreadsheet Template",
        "nav":       "#0277BD",
        "gld":       "#FFD700",
        "bg_light":  "#E1F5FE",
        "emoji":     "🗺️",
        "tab7":      "Route Planner",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1Kd8nPZ13ReNB-rKeXpWetP3142a1WJ6COlJ8HUG3LIg/copy",
    },
    {
        "key":       "rv-vacation",
        "label":     "RV VACATION PLANNER",
        "full":      "RV Vacation Planning Spreadsheet Template",
        "nav":       "#2E7D32",
        "gld":       "#90A4AE",
        "bg_light":  "#E8F5E9",
        "emoji":     "🚐",
        "tab7":      "Maintenance Log",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1KBWBXfkDIqnjQ9DBphJJda2PO5fXWmK-XKtMvJ2C6zA/copy",
    },
    {
        "key":       "first-time-rv",
        "label":     "FIRST-TIME RV PLANNER",
        "full":      "First-Time RV Planning Spreadsheet Template",
        "nav":       "#00796B",
        "gld":       "#FFD700",
        "bg_light":  "#E0F2F1",
        "emoji":     "🚐",
        "tab7":      "System Learning",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1RmEr26yGsl5kGFyl7HC28UGq4R0T67KCBMjFER0aoiA/copy",
    },
]

# ── Google Drive: fetch sheet URLs ────────────────────────────────────────────
def get_sheet_urls() -> dict:
    """Return {search_keyword: copy_url} for each sheet in Drive folder."""
    creds = Credentials.from_authorized_user_file(TOKEN_FILE,
        ['https://www.googleapis.com/auth/drive'])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    svc = build('drive', 'v3', credentials=creds)
    results = svc.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.spreadsheet'",
        fields='files(id,name,webViewLink)',
        pageSize=50,
    ).execute()

    mapping = {}
    for f in results.get('files', []):
        # Convert /edit URL to /copy URL
        copy_url = re.sub(r'/edit(\?.*)?$', '/copy', f['webViewLink'])
        mapping[f['name']] = copy_url
        print(f"  Found: {f['name']}")
    return mapping


def find_url_for_event(ev: dict, url_map: dict) -> str:
    """Return copy URL for event — use sheet_url if hardcoded, else search Drive."""
    if ev.get('sheet_url'):
        return ev['sheet_url']
    primary = ev.get('search', ev.get('label', '')).lower().split()[0]
    for name, url in url_map.items():
        if primary in name.lower():
            return url
    print(f"  WARNING: no sheet found for '{ev.get('search','?')}' — using placeholder URL")
    return "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/copy"


# ── PDF drawing helpers ───────────────────────────────────────────────────────
def hex_c(h: str) -> HexColor:
    return HexColor(h)


def make_header_canvas(canvas, doc, ev):
    """Draw the decorative page header on every page."""
    nav = hex_c(ev['nav'])
    gld = hex_c(ev['gld'])
    W_pt, H_pt = letter

    # Full-width navy banner
    canvas.setFillColor(nav)
    canvas.rect(0, H_pt - 1.15*inch, W_pt, 1.15*inch, fill=1, stroke=0)

    # Gold accent stripe at bottom of banner
    canvas.setFillColor(gld)
    canvas.rect(0, H_pt - 1.15*inch, W_pt, 0.06*inch, fill=1, stroke=0)

    # Shop name — left
    canvas.setFillColor(gld)
    canvas.setFont(FONT_BOLD, 11)
    canvas.drawString(0.5*inch, H_pt - 0.55*inch, "ThePlannedEvent")

    # Event label — center
    canvas.setFillColor(white)
    canvas.setFont(FONT_BOLD, 15)
    label = ev['label']
    tw = canvas.stringWidth(label, FONT_BOLD, 15)
    canvas.drawString((W_pt - tw) / 2, H_pt - 0.6*inch, label)

    # "INSTANT DOWNLOAD" — right
    canvas.setFillColor(gld)
    canvas.setFont(FONT_REG, 9)
    tag = "INSTANT DOWNLOAD"
    tw2 = canvas.stringWidth(tag, FONT_REG, 9)
    canvas.drawString(W_pt - 0.5*inch - tw2, H_pt - 0.55*inch, tag)

    # Footer bar
    canvas.setFillColor(nav)
    canvas.rect(0, 0, W_pt, 0.45*inch, fill=1, stroke=0)
    canvas.setFillColor(gld)
    canvas.rect(0, 0.45*inch, W_pt, 0.04*inch, fill=1, stroke=0)

    canvas.setFillColor(white)
    canvas.setFont(FONT_REG, 8)
    footer = "ThePlannedEvent  •  Questions? Contact us through Etsy  •  Thank you for your purchase!"
    fw = canvas.stringWidth(footer, FONT_REG, 8)
    canvas.drawString((W_pt - fw) / 2, 0.16*inch, footer)


def build_pdf(ev: dict, copy_url: str):
    out_path = OUT_DIR / f"{ev['key']}_delivery.pdf"
    nav = hex_c(ev['nav'])
    gld = hex_c(ev['gld'])
    bg  = hex_c(ev['bg_light'])

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=0.55*inch,
        rightMargin=0.55*inch,
        topMargin=1.35*inch,
        bottomMargin=0.65*inch,
    )

    styles = getSampleStyleSheet()

    def sty(name, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, **{'fontName': FONT_REG, **kw})

    s_h1 = sty('H1', fontName=FONT_BOLD,   fontSize=22, leading=28, textColor=nav,
                spaceAfter=4, alignment=TA_CENTER)
    s_h2 = sty('H2', fontName=FONT_BOLD,   fontSize=14, leading=20, textColor=nav,
                spaceBefore=14, spaceAfter=6)
    s_body = sty('Body', fontSize=11, leading=17, textColor=HexColor('#333333'),
                 spaceAfter=6)
    s_small = sty('Small', fontSize=9, leading=13, textColor=HexColor('#666666'),
                  spaceAfter=4)
    s_center = sty('Center', fontSize=11, leading=16, textColor=HexColor('#333333'),
                   alignment=TA_CENTER, spaceAfter=4)
    s_url = sty('URL', fontName=FONT_BOLD, fontSize=10, leading=15,
                textColor=nav, alignment=TA_CENTER, spaceAfter=0)
    s_step_num = sty('StepNum', fontName=FONT_BOLD, fontSize=16, leading=20,
                     textColor=white)
    s_step_txt = sty('StepTxt', fontName=FONT_BOLD, fontSize=11, leading=15,
                     textColor=nav, spaceAfter=2)
    s_step_sub = sty('StepSub', fontSize=10, leading=14, textColor=HexColor('#555555'))
    s_tip = sty('Tip', fontSize=10, leading=15, textColor=HexColor('#444444'))

    story = []

    # ── Thank-you block ───────────────────────────────────────────────────────
    story.append(Paragraph(f"{ev['emoji']} Thank You for Your Purchase!", s_h1))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=1.5, color=gld, spaceAfter=10))

    story.append(Paragraph(
        "You're all set to start planning your perfect event! Your "
        f"<b>{ev['label'].title()}</b> template is a professional-grade "
        "Google Sheets file packed with everything you need — budgets, "
        "guest lists, vendor tracking, timelines, and more.",
        s_body
    ))
    story.append(Paragraph(
        "Follow the three simple steps below to open your template and "
        "save your own editable copy to Google Drive — it only takes "
        "about 30 seconds.",
        s_body
    ))
    story.append(Spacer(1, 8))

    # ── Access link box ───────────────────────────────────────────────────────
    story.append(Paragraph("YOUR TEMPLATE LINK", sty('LinkHdr',
        fontName=FONT_BOLD, fontSize=10, leading=14, textColor=nav,
        spaceBefore=4, spaceAfter=4)))

    link_label = "Click here to open your template"
    link_cell = Paragraph(
        f'<link href="{copy_url}" color="#1F3864"><u>{link_label}</u></link>',
        sty('LinkCell', fontName=FONT_BOLD, fontSize=12, leading=18,
            textColor=nav, alignment=TA_CENTER)
    )
    url_cell = Paragraph(copy_url, sty('URLraw', fontSize=8, leading=12,
        textColor=HexColor('#666666'), alignment=TA_CENTER))

    link_table = Table(
        [[link_cell], [url_cell]],
        colWidths=[doc.width],
    )
    link_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), bg),
        ('BOX',          (0,0), (-1,-1), 2, nav),
        ('LINEBELOW',    (0,0), (-1, 0), 0.5, gld),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('LEFTPADDING',  (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(link_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "If the link above is not clickable, copy and paste the URL into "
        "your browser's address bar.",
        s_small
    ))
    story.append(Spacer(1, 12))

    # ── Steps ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("HOW TO GET STARTED", sty('SecHdr',
        fontName=FONT_BOLD, fontSize=12, leading=18, textColor=nav,
        spaceBefore=4, spaceAfter=8)))

    STEPS = [
        ("1", "Click the link above",
         "The link will open the template in Google Sheets. "
         "You must be signed into a Google account."),
        ("2", 'Select "Make a Copy"',
         'Go to File  →  Make a Copy. Give it a name like '
         f'"{ev["label"].title()}" and click OK. '
         "This saves an editable copy to your own Google Drive."),
        ("3", "Start planning!",
         "All formulas and charts are already set up. Just click any "
         "yellow highlighted cell and start entering your details. "
         "Check the Instructions tab for a full walkthrough."),
    ]

    step_rows = []
    for num, title, desc in STEPS:
        num_cell = Paragraph(num, sty(f'SN{num}', fontName=FONT_BOLD,
            fontSize=18, leading=22, textColor=white, alignment=TA_CENTER))
        txt_cell = [
            Paragraph(title, s_step_txt),
            Paragraph(desc, s_step_sub),
        ]
        step_rows.append([num_cell, txt_cell])

    step_table = Table(step_rows, colWidths=[0.55*inch, doc.width - 0.55*inch])
    step_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (0,-1), nav),
        ('BACKGROUND',    (1,0), (1,-1), bg),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',         (0,0), (0,-1),  'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (0,-1),   0),
        ('LEFTPADDING',   (1,0), (1,-1),  12),
        ('RIGHTPADDING',  (0,0), (-1,-1),  8),
        ('LINEBELOW',     (0,0), (-1,-2), 0.5, HexColor('#CCCCCC')),
        ('BOX',           (0,0), (-1,-1), 1.5, nav),
    ]))
    story.append(step_table)
    story.append(Spacer(1, 14))

    # ── What's included ───────────────────────────────────────────────────────
    story.append(Paragraph("WHAT'S INCLUDED IN YOUR TEMPLATE", sty('IncHdr',
        fontName=FONT_BOLD, fontSize=12, leading=18, textColor=nav,
        spaceBefore=4, spaceAfter=8)))

    default_tabs = [
        ("Dashboard",               "Live budget overview with auto-updating charts"),
        ("Budget Tracker",          "Full line-item budget with auto-totals & conditional formatting"),
        ("Vendor Directory",        "Contact details, deposits, balances, and contract status"),
        ("Guest List",              "RSVP tracking, meal choices, dietary notes, and table numbers"),
        ("Venue & Logistics",       "Ceremony, reception, parking, A/V, and accommodation details"),
        ("Planning Timeline",       "Month-by-month checklist + hour-by-hour day-of schedule"),
        (ev['tab7'],                "Event-specific planning tab"),
        ("Instructions",            "Plain-English guide so anyone can hit the ground running"),
    ]
    tabs = ev.get('tabs', default_tabs)

    tab_data = []
    for i, (tab, desc) in enumerate(tabs):
        num_p = Paragraph(str(i+1), sty(f'TN{i}', fontName=FONT_BOLD,
            fontSize=10, leading=14, textColor=white, alignment=TA_CENTER))
        tab_p = Paragraph(f"<b>{tab}</b>", sty(f'TTab{i}', fontName=FONT_SEMI,
            fontSize=10, leading=14, textColor=nav))
        desc_p = Paragraph(desc, sty(f'TDesc{i}', fontSize=9, leading=13,
            textColor=HexColor('#555555')))
        tab_data.append([num_p, tab_p, desc_p])

    tab_table = Table(tab_data,
        colWidths=[0.35*inch, 1.8*inch, doc.width - 0.35*inch - 1.8*inch])
    tab_style = [
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',         (0,0), (0,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (0,-1),  0),
        ('LEFTPADDING',   (1,0), (1,-1),  8),
        ('LEFTPADDING',   (2,0), (2,-1),  6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('BOX',           (0,0), (-1,-1), 1, nav),
        ('LINEBELOW',     (0,0), (-1,-2), 0.4, HexColor('#DDDDDD')),
    ]
    for i in range(len(tabs)):
        tab_style.append(('BACKGROUND', (0,i), (0,i), nav))
        bg_row = bg if i % 2 == 0 else white
        tab_style.append(('BACKGROUND', (1,i), (2,i), bg_row))
    tab_table.setStyle(TableStyle(tab_style))
    story.append(tab_table)
    story.append(Spacer(1, 14))

    # ── Pro tip box ───────────────────────────────────────────────────────────
    tip_inner = [
        [Paragraph(
            "<b>Pro Tip:</b> Share your copy with a co-planner by clicking "
            "the Share button in Google Sheets and entering their email. "
            "They can view or edit in real time — no extra software needed!",
            s_tip
        )]
    ]
    tip_table = Table(tip_inner, colWidths=[doc.width])
    tip_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), bg),
        ('BOX',           (0,0), (-1,-1), 2, gld),
        ('LINEBEFORE',    (0,0), (0,-1),  5, gld),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 14),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
    ]))
    story.append(tip_table)
    story.append(Spacer(1, 10))

    # ── Support note ──────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Need help? Message us through Etsy and we'll get back to you "
        "within 24 hours. We want your event to be absolutely perfect!",
        sty('Support', fontSize=10, leading=15, textColor=HexColor('#555555'),
            alignment=TA_CENTER, spaceBefore=4)
    ))

    # ── Build with header/footer on every page ────────────────────────────────
    def on_page(canvas, doc):
        canvas.saveState()
        make_header_canvas(canvas, doc, ev)
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"  Saved: {out_path.name}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    # If keys passed as args, only build those; otherwise build all missing
    requested = set(sys.argv[1:])
    if not requested:
        # Build only events whose PDF doesn't exist yet
        requested = {ev['key'] for ev in EVENTS if not (OUT_DIR / f"{ev['key']}_delivery.pdf").exists()}
        if not requested:
            print("All PDFs already exist. Pass key names to force rebuild.")
            sys.exit(0)

    print("Fetching sheet URLs from Google Drive...")
    url_map = get_sheet_urls()

    for ev in EVENTS:
        if ev['key'] not in requested:
            continue
        copy_url = find_url_for_event(ev, url_map)
        print(f"\nBuilding PDF: {ev['label']}")
        print(f"  URL: {copy_url}")
        build_pdf(ev, copy_url)

    print(f"\nAll PDFs saved to: {OUT_DIR}")
