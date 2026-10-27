"""Builds the Asset List intake from one question list.

    python3 tools/asset-intake/build.py

Writes, next to this file:
  asset-list-printable.pdf   the paper version: instructions, an equipment record
                             (one per item), a tools list and a technology list
  AssetListForm.gs           the Apps Script that builds the Google Form and its
                             response Sheet in the Drive of whoever runs it
                             (operations@). buildAssetListForm makes it;
                             rebuildAssetListForm reshapes the live one in place.

The form opens on one question, "What are you entering?", and branches:
  Equipment   vehicles, trailers and machines, one per response (five pages)
  Tools       power tools, tools over $100, ladders and fall protection: who
              they belong to once, then one short page per tool, "Add tool 2?"
              after each, up to MAX_TOOLS per response
  Technology  one computer, tablet or phone per response

PAGES is the single source: the form, the PDF and the column mapping in
README.md all follow it, so the paper and the phone ask the same things.
"""

import argparse
import json
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

HERE = Path(__file__).resolve().parent

TITLE = "DB Asset Hub: Asset List"
DESCRIPTION = (
    "Start by choosing what you're entering: equipment, tools or technology. Each one asks only "
    "what fits. Equipment and technology: one item per response. Tools: up to 10 per response. "
    "After you submit, tap \"Submit another response\" for more. Skip anything you don't know; "
    "the office fills in the rest."
)
CONFIRMATION = "Saved. Tap \"Submit another response\" to add more."

TEAMS = ["Roofing", "Gutters", "Service", "Construction", "Shop / Office"]
EQUIPMENT_KINDS = [
    "Pickup truck", "Dump truck", "Box or flatbed truck", "Van", "Car or SUV",
    "Dump trailer", "Equipment trailer", "Enclosed trailer",
    "Skid steer or loader", "Lift or telehandler", "Roof conveyor or hoist",
    "Generator", "Air compressor", "Pressure washer",
]
TOOL_KINDS = [
    "Roofing nailer or nail gun", "Saw", "Drill or impact driver", "Grinder", "Other power tool",
    "Ladder", "Harness", "Lanyard or SRL", "Roof anchor", "Other tool or safety gear",
]
TECH_KINDS = ["Laptop", "Desktop computer", "Tablet or iPad", "Cell phone"]
MAX_TOOLS = 10

START = {
    "type": "nav", "title": "What are you entering?", "required": True,
    "help": "Pick one. You can come back with \"Submit another response\" for the others.",
    "choices": [
        {"label": "Equipment: vehicles, trailers and machines", "goto": "eq1"},
        {"label": "Tools: power tools, tools over $100, ladders and fall protection", "goto": "tools"},
        {"label": "Technology: computers, tablets and phones", "goto": "tech"},
    ],
}

# Equipment pages. key/col map each answer to PLAYBOOK.md Appendix B (README.md).
EQUIPMENT = [
    {
        "id": "eq1", "title": "Equipment", "help": "One vehicle, trailer or machine per response.",
        "items": [
            {"key": "category", "col": "category", "type": "choice", "title": "Kind of equipment",
             "options": EQUIPMENT_KINDS, "other": True, "required": True},
            {"key": "name", "col": "name", "type": "text", "title": "Name or short description",
             "required": True,
             "help": "What you'd call it, e.g. \"2019 F-250, white, Alberto's truck\" or \"16 ft Big Tex dump trailer\"."},
            {"key": "unit_number", "col": "tag (office assigns)", "type": "text",
             "title": "Unit number or label it has now",
             "help": "If it's numbered or labeled today (Truck 7, T-3). Leave blank if not; the office assigns the Asset Hub tag."},
            {"key": "team", "col": "team", "type": "choice", "title": "Team", "options": TEAMS, "other": True},
            {"key": "assigned_to", "col": "assigned_to_email", "type": "text",
             "title": "Who usually drives or uses it", "help": "A name or a company email."},
        ],
    },
    {
        "id": "eq2", "title": "Make, model and ID",
        "help": "Vehicles: the VIN and GVWR are on the sticker in the driver's door jamb. Trailers: on the tongue. "
                "Machines: on the data plate.",
        "items": [
            {"key": "make", "col": "make", "type": "text", "title": "Make"},
            {"key": "model", "col": "model", "type": "text", "title": "Model"},
            {"key": "year", "col": "year", "type": "number", "title": "Year", "min": 1950, "max": 2030},
            {"key": "vin_serial", "col": "vin_serial", "type": "text", "title": "VIN or serial number",
             "help": "A VIN is 17 characters. Copy it exactly."},
            {"key": "plate", "col": "plate", "type": "text", "title": "License plate"},
            {"key": "plate_state", "col": "plate_state", "type": "text", "title": "Plate state", "help": "Usually OH."},
            {"key": "gvwr_lbs", "col": "gvwr_lbs", "type": "number", "title": "GVWR (lbs)", "min": 0, "max": 200000,
             "help": "Gross vehicle weight rating, from the door-jamb or tongue sticker. Vehicles and trailers only."},
            {"key": "is_cmv", "col": "is_cmv", "type": "choice", "title": "Commercial vehicle (DOT)?",
             "options": ["Yes", "No", "Not sure"],
             "help": "Yes if it has a USDOT number on the door, or it (or truck plus trailer) is rated 10,001 lb or more."},
        ],
    },
    {
        "id": "eq3", "title": "Meters and fuel", "help": "Today's readings.",
        "items": [
            {"key": "odometer", "col": "odometer", "type": "number", "title": "Odometer (miles)", "min": 0, "max": 9999999},
            {"key": "engine_hours", "col": "engine_hours", "type": "number", "title": "Engine hours",
             "min": 0, "max": 999999, "help": "From the hour meter, if it has one."},
            {"key": "fuel_type", "col": "fuel_type", "type": "choice", "title": "Fuel type",
             "options": ["Gasoline", "Diesel", "Electric / battery", "No fuel"], "other": True},
            {"key": "tank_gallons", "col": "tank_gallons", "type": "number", "title": "Tank size (gallons)", "min": 0, "max": 500},
            {"key": "fuel_card_ref", "col": "fuel_card_ref", "type": "text", "title": "Fuel card: last 4 digits",
             "maxLength": 8, "help": "Last 4 digits only. Never the whole card number."},
            {"key": "telematics_ref", "col": "telematics_ref", "type": "choice", "title": "GPS tracker",
             "options": ["Samsara", "Motive", "Geotab", "Has one, not sure which", "None", "Not sure"]},
        ],
    },
    {
        "id": "eq4", "title": "Purchase", "help": "Skip anything you don't know. The office fills these in.",
        "items": [
            {"key": "purchase_date", "col": "purchase_date", "type": "date", "title": "Purchase date"},
            {"key": "purchase_price", "col": "purchase_price", "type": "number", "title": "Purchase price ($)",
             "min": 0, "max": 5000000},
            {"key": "in_service_date", "col": "in_service_date", "type": "date", "title": "In service since"},
            {"key": "expected_life_years", "col": "expected_life_months (years x 12)", "type": "number",
             "title": "Expected life (years)", "min": 0, "max": 50},
        ],
    },
    {
        "id": "eq5", "title": "Condition and notes", "help": "",
        "items": [
            {"key": "notes", "col": "notes", "type": "paragraph", "title": "Notes",
             "help": "Condition, known problems, anything we should know."},
        ],
    },
]

TOOLS = {
    "id": "tools", "title": "Tools", "submitBefore": True,
    "help": "Power tools, any tool worth over $100 (use your judgment), every ladder and all fall-protection "
            "gear. Say whose they are once, then one short page per tool. Up to 10 per response; for more, "
            "submit and tap \"Submit another response\".",
    "items": [
        {"type": "text", "title": "Whose tools are these?", "required": True,
         "help": "Your name, or the crew or shop they belong to."},
        {"type": "choice", "title": "Tools: team", "options": TEAMS, "other": True},
        {"type": "text", "title": "Where are they kept?", "help": "Truck, trailer, shop, office."},
    ],
}


def tool_page(n):
    first = n == 1
    items = [
        {"type": "list", "title": f"Tool {n}: kind", "options": TOOL_KINDS, "required": True},
        {"type": "text", "title": f"Tool {n}: make and model", "required": True,
         "help": "e.g. DeWalt DCS570 circular saw, or Werner 28 ft fiberglass extension ladder." if first else ""},
        {"type": "text", "title": f"Tool {n}: serial number",
         "help": "On the data plate or label. Skip it if there isn't one." if first else ""},
        {"type": "number", "title": f"Tool {n}: value ($)", "min": 0, "max": 100000,
         "help": "About what it would cost to replace." if first else ""},
    ]
    if n < MAX_TOOLS:
        items.append({"type": "nav", "title": f"Add tool {n + 1}?", "required": True, "choices": [
            {"label": f"Yes, add tool {n + 1}", "goto": f"tool{n + 1}"},
            {"label": "No, that's all. Submit.", "goto": "SUBMIT"},
        ]})
    help_text = (f"That's {MAX_TOOLS}. Submit this one, then tap \"Submit another response\" for more."
                 if n == MAX_TOOLS else "")
    return {"id": f"tool{n}", "title": f"Tool {n}", "help": help_text, "items": items}


TECH = {
    "id": "tech", "title": "Technology", "submitBefore": True,
    "help": "One computer, tablet or phone the company issued, per response. Submit, then tap "
            "\"Submit another response\" for the next device.",
    "items": [
        {"type": "choice", "title": "Device type", "options": TECH_KINDS, "other": True, "required": True},
        {"type": "text", "title": "Device make", "required": True, "help": "Apple, Dell, HP, Samsung."},
        {"type": "text", "title": "Device model", "required": True,
         "help": "iPhone 15, Latitude 5440, iPad (10th generation)."},
        {"type": "text", "title": "Device serial number", "required": True,
         "help": "iPhone and iPad: Settings, General, About. Android: Settings, About phone. "
                 "Laptops: the sticker underneath, or Settings, About."},
        {"type": "text", "title": "Issued to", "required": True, "help": "A name or a company email."},
        {"type": "choice", "title": "Device team", "options": TEAMS, "other": True},
        {"type": "text", "title": "Phone number", "help": "Cell phones only."},
        {"type": "date", "title": "Device purchase date"},
        {"type": "number", "title": "Device purchase price ($)", "min": 0, "max": 20000},
        {"type": "paragraph", "title": "Device notes", "help": "Condition, case, charger, anything we should know."},
    ],
}

PAGES = ([{"id": "start", "title": "", "help": "", "items": [START]}]
         + EQUIPMENT + [TOOLS] + [tool_page(n) for n in range(1, MAX_TOOLS + 1)] + [TECH])

# ---------------------------------------------------------------- the PDF ---

NAVY = HexColor("#1A4789")
NAVY_200 = HexColor("#B9CDF0")
GREEN = HexColor("#3CC84A")
INK = HexColor("#0E1113")
MUTED = HexColor("#6B6F72")
LABEL = HexColor("#7D766A")
LINE = HexColor("#9AA6B5")
HAIR = HexColor("#D8DFE8")
TINT = HexColor("#F4F6F9")

FONTS = {
    "Sans": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "Sans-Bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "Mono": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-SemiBold.ttf",
}
for name, path in FONTS.items():
    pdfmetrics.registerFont(TTFont(name, path))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")

M = 36  # page margin
PAGE_COUNT = 4


def mono(c, x, y, text, size=7, color=LABEL, space=0.9):
    c.saveState()  # character spacing is graphics state: keep it out of the body text
    t = c.beginText(x, y)
    t.setFont("Mono", size)
    t.setCharSpace(space)
    t.setFillColor(color)
    t.textOut(text.upper())
    c.drawText(t)
    c.restoreState()


def header(c, w, h, eyebrow, title, band=50, sub=None):
    c.setFillColor(NAVY)
    c.rect(0, h - band, w, band, stroke=0, fill=1)
    c.setFillColor(GREEN)
    c.rect(0, h - band - 3, w, 3, stroke=0, fill=1)
    mono(c, M, h - 18, eyebrow, size=7, color=NAVY_200, space=1.1)
    c.setFillColor(white)
    c.setFont("Sans-Bold", 20 if band <= 60 else 30)
    c.drawString(M, h - (40 if band <= 60 else 62), title.upper())
    if sub:
        c.setFont("Sans", 11)
        c.setFillColor(NAVY_200)
        c.drawString(M, h - 82, sub)


def footer(c, page, note):
    mono(c, M, 22, f"DB Asset Hub · Asset List · page {page} of {PAGE_COUNT} · {note}", size=6.5, color=MUTED, space=0.6)


def section(c, x, y, w, number, title, note=None):
    mono(c, x, y, f"{number} · {title}", size=8, color=NAVY, space=1.0)
    if note:
        c.setFont("Sans", 8)
        c.setFillColor(MUTED)
        c.drawRightString(x + w, y, note)
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.line(x, y - 4, x + w, y - 4)
    return y - 16


def box(c, x, y, w, label, h=20):
    """A labeled write-in box whose label sits at y; returns the y below it."""
    mono(c, x, y, label, size=6.5)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(x, y - 4 - h, w, h, 2, stroke=1, fill=0)
    return y - 4 - h - 10


def comb(c, x, y, w, label, cells, h=22):
    mono(c, x, y, label, size=6.5)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(x, y - 4 - h, w, h, 2, stroke=1, fill=0)
    step = w / cells
    c.setStrokeColor(HAIR)
    for i in range(1, cells):
        c.line(x + i * step, y - 4 - h + 4, x + i * step, y - 4)
    return y - 4 - h - 10


def checks(c, x, y, w, label, options, cols, other=False, row_h=13):
    """A labeled grid of checkboxes; returns the y below it."""
    if label:
        mono(c, x, y, label, size=6.5)
        y -= 13
    items = list(options) + (["Other:"] if other else [])
    col_w = w / cols
    for i, opt in enumerate(items):
        cx = x + (i % cols) * col_w
        cy = y - (i // cols) * row_h
        c.setStrokeColor(INK)
        c.setLineWidth(0.7)
        c.rect(cx, cy - 1.5, 8, 8, stroke=1, fill=0)
        c.setFont("Sans", 8.5)
        c.setFillColor(INK)
        c.drawString(cx + 12, cy, opt)
        if opt == "Other:":
            tw = c.stringWidth(opt, "Sans", 8.5)
            c.setStrokeColor(LINE)
            c.line(cx + 16 + tw, cy - 2, cx + col_w * (cols - i % cols) - 8, cy - 2)
    rows = (len(items) + cols - 1) // cols
    return y - (rows - 1) * row_h - 18


def para(c, x, y, w, text, size=10, leading=14, color=INK, font="Sans"):
    style = ParagraphStyle("p", fontName=font, fontSize=size, leading=leading, textColor=color)
    p = Paragraph(text, style)
    _, ph = p.wrap(w, 1000)
    p.drawOn(c, x, y - ph)
    return y - ph


def grid(c, x, y, cols, rows, row_h=27, head_h=18):
    """A numbered write-in table: navy header row, alternate rows tinted."""
    total = sum(cw for _, cw in cols)
    c.setFillColor(NAVY)
    c.rect(x, y - head_h, total, head_h, stroke=0, fill=1)
    cx = x
    for name, cw in cols:
        mono(c, cx + 5, y - 12, name, size=6.5, color=white, space=0.7)
        cx += cw
    top = y - head_h
    for r in range(rows):
        ry = top - (r + 1) * row_h
        if r % 2 == 1:
            c.setFillColor(TINT)
            c.rect(x, ry, total, row_h, stroke=0, fill=1)
        c.setFillColor(MUTED)
        c.setFont("Sans", 8)
        c.drawCentredString(x + 10, ry + 10, str(r + 1))
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.rect(x, top - rows * row_h, total, rows * row_h, stroke=1, fill=0)
    for r in range(1, rows):
        c.line(x, top - r * row_h, x + total, top - r * row_h)
    cx = x
    for _, cw in cols[:-1]:
        cx += cw
        c.line(cx, top, cx, top - rows * row_h)


def page_instructions(c):
    w, h = letter
    header(c, w, h, "Deitemeyer Brothers · DB Asset Hub", "Asset List", band=100,
           sub="Every truck, trailer, machine, tool and device we track")
    x, cw = M + 4, w - 2 * M - 8
    y = h - 130

    mono(c, x, y, "What this is", size=8, color=NAVY, space=1.0)
    y = para(c, x, y - 8, cw,
             "We're building <b>DB Asset Hub</b>: one place for daily inspections, repairs and maintenance "
             "on everything we own. It starts with a list of what we have.") - 18

    mono(c, x, y, "Three kinds of entries", size=8, color=NAVY, space=1.0)
    y -= 8
    for group, items in [
        ("Equipment", "vehicles, trailers and machines: pickups, dump and box trucks, vans, cars; dump, "
                      "equipment and enclosed trailers; skid steers, lifts, roof conveyors and hoists, "
                      "generators, compressors, pressure washers. <i>Page 2, one per item.</i>"),
        ("Tools", "power tools, and any tool worth over $100 (use your best judgment), plus every ladder and "
                  "all fall-protection gear: harnesses, lanyards, SRLs, roof anchors. <i>Page 3, fifteen to a page.</i>"),
        ("Technology", "computers, laptops, tablets and cell phones the company issued. "
                       "<i>Page 4, twelve to a page.</i>"),
    ]:
        y = para(c, x, y, cw, f"<b>{group}:</b> {items}") - 4
    y -= 14

    mono(c, x, y, "Two ways to fill it in", size=8, color=NAVY, space=1.0)
    y = para(c, x, y - 8, cw,
             "<b>On a phone, tablet or computer:</b> use the online form Carl sends you. It starts with "
             "<b>What are you entering?</b> and then asks only what fits. Tools go in up to ten at a time. "
             "After you submit, tap <b>Submit another response</b> for more.") - 6
    y = para(c, x, y, cw, "<b>On paper:</b> print the pages you need and give them to Carl.") - 18

    mono(c, x, y, "Where to find it", size=8, color=NAVY, space=1.0)
    y -= 10
    rows = [
        ("VIN (17 characters)", "Driver's door-jamb sticker, or the dash under the windshield. Trailers: the tongue."),
        ("GVWR", "The same door-jamb or tongue sticker."),
        ("Odometer", "The dash."),
        ("Engine hours", "The hour meter, on the dash or the engine."),
        ("Serial number", "The data plate or label on the machine or tool."),
        ("Device serial", "iPhone, iPad: Settings, General, About. Android: About phone. Laptop: sticker underneath."),
        ("Plate", "The plate itself, or the registration in the glove box."),
    ]
    for i, (k, v) in enumerate(rows):
        rh = 20
        if i % 2 == 0:
            c.setFillColor(TINT)
            c.rect(x, y - rh + 6, cw, rh, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Sans-Bold", 9.5)
        c.drawString(x + 6, y - 8, k)
        c.setFont("Sans", 9.5)
        c.drawString(x + 130, y - 8, v)
        y -= rh
    y -= 18

    mono(c, x, y, "Good to know", size=8, color=NAVY, space=1.0)
    y -= 8
    for line in [
        "Skip anything you don't know. The office fills in the rest.",
        "Fuel cards: write the <b>last 4 digits only</b>, never the whole number.",
        "Copy VINs and serial numbers exactly. They are how we match records later.",
        "Leave the <b>Office use</b> boxes blank. The office gives each asset its tag (like TRL-03).",
        "Questions? Ask Carl.",
    ]:
        c.setFillColor(GREEN)
        c.rect(x, y - 9, 4, 4, stroke=0, fill=1)
        y = para(c, x + 12, y, cw - 12, line) - 5

    footer(c, 1, "Oct 2026")


def page_equipment(c):
    w, h = letter
    header(c, w, h, "Deitemeyer Brothers · DB Asset Hub · one per vehicle, trailer or machine", "Equipment record")
    x, cw = M, w - 2 * M
    gap = 12
    y = h - 72

    third = (cw - 2 * gap) / 3
    box(c, x, y, third * 1.3, "Filled in by", 18)
    box(c, x + third * 1.3 + gap, y, third * 0.7, "Date", 18)
    c.setFillColor(TINT)
    c.roundRect(x + 2 * third + 2 * gap - 4, y - 28, third + 4, 34, 3, stroke=0, fill=1)
    y = box(c, x + 2 * third + 2 * gap, y, third - 4, "Office use: tag", 18) - 2

    q = {i["key"]: i for s in EQUIPMENT for i in s["items"]}

    y = section(c, x, y, cw, "01", "What is it")
    y = checks(c, x, y, cw, q["category"]["title"], EQUIPMENT_KINDS, cols=4, other=True)
    y = box(c, x, y, cw, q["name"]["title"])
    half = (cw - gap) / 2
    box(c, x, y, half * 0.6, q["unit_number"]["title"].replace(" it has now", ""))
    y = box(c, x + half * 0.6 + gap, y, cw - half * 0.6 - gap, q["assigned_to"]["title"])
    y = checks(c, x, y, cw, "Team", TEAMS, cols=6, other=True) - 2

    y = section(c, x, y, cw, "02", "Make, model and ID", note="Door-jamb sticker · trailer tongue · data plate")
    box(c, x, y, cw * 0.36, "Make")
    box(c, x + cw * 0.36 + gap, y, cw * 0.44, "Model")
    y = box(c, x + cw * 0.8 + 2 * gap, y, cw * 0.2 - 2 * gap, "Year")
    y = comb(c, x, y, cw, "VIN (17 characters) or serial number", 20)
    box(c, x, y, cw * 0.36, "License plate")
    box(c, x + cw * 0.36 + gap, y, cw * 0.16, "Plate state")
    y = box(c, x + cw * 0.52 + 2 * gap, y, cw * 0.48 - 2 * gap, "GVWR (lbs)")
    y = checks(c, x, y, cw * 0.42, "Commercial vehicle (DOT)?", ["Yes", "No", "Not sure"], cols=3)
    c.setFont("Sans", 7.5)
    c.setFillColor(MUTED)
    c.drawString(x + cw * 0.45, y + 18, "Yes if it has a USDOT number, or is rated 10,001 lb or more (with trailer).")
    y -= 2

    y = section(c, x, y, cw, "03", "Meters and fuel", note="Today's readings")
    box(c, x, y, half, "Odometer (miles)")
    y = box(c, x + half + gap, y, half, "Engine hours (hour meter)")
    y = checks(c, x, y, cw, "Fuel type", ["Gasoline", "Diesel", "Electric / battery", "No fuel"], cols=5, other=True)
    box(c, x, y, half, "Tank size (gallons)")
    y = box(c, x + half + gap, y, half, "Fuel card: last 4 digits only")
    y = checks(c, x, y, cw, "GPS tracker", ["Samsara", "Motive", "Geotab", "Has one, not sure which", "None", "Not sure"],
               cols=3) - 2

    y = section(c, x, y, cw, "04", "Purchase", note="Skip if you don't know. The office fills these in.")
    quarter = (cw - 3 * gap) / 4
    for i, lab in enumerate(["Purchase date", "Purchase price ($)", "In service since", "Expected life (years)"]):
        b = box(c, x + i * (quarter + gap), y, quarter, lab)
    y = b - 2

    y = section(c, x, y, cw, "05", "Condition and notes")
    c.setStrokeColor(HAIR)
    c.setLineWidth(0.7)
    for i in range(4):
        c.line(x, y - 14 - i * 20, x + cw, y - 14 - i * 20)

    footer(c, 2, "print one per vehicle, trailer or machine")


def page_tools(c):
    w, h = landscape(letter)
    header(c, w, h, "Deitemeyer Brothers · DB Asset Hub · power tools, tools over $100, ladders, fall protection",
           "Tools")
    x = M
    y = h - 74
    box(c, x, y, 230, "Whose tools are these?", 16)
    box(c, x + 242, y, 150, "Team", 16)
    box(c, x + 404, y, 180, "Where are they kept?", 16)
    box(c, x + 596, y, 124, "Date", 16)
    y -= 40
    c.setFont("Sans", 8.5)
    c.setFillColor(MUTED)
    c.drawString(x, y, "Kind: " + ", ".join(k.lower() for k in TOOL_KINDS) + ".")
    y -= 10
    grid(c, x, y, [("#", 20), ("Kind", 118), ("Make and model", 220), ("Serial number", 150),
                   ("Value ($)", 70), ("Notes", 142)], rows=14)
    footer(c, 3, "print as many as you need")


def page_technology(c):
    w, h = landscape(letter)
    header(c, w, h, "Deitemeyer Brothers · DB Asset Hub · computers, tablets and phones the company issued",
           "Technology")
    x = M
    y = h - 74
    box(c, x, y, 230, "Filled in by", 16)
    box(c, x + 242, y, 124, "Date", 16)
    y -= 40
    c.setFont("Sans", 8.5)
    c.setFillColor(MUTED)
    c.drawString(x, y, "Type: laptop, desktop, tablet or iPad, cell phone, other. "
                       "Serial: Settings, About (phone or tablet), or the sticker underneath (laptop).")
    y -= 10
    grid(c, x, y, [("#", 20), ("Type", 84), ("Make", 80), ("Model", 106), ("Serial number", 140),
                   ("Issued to", 112), ("Phone number", 90), ("Notes", 88)], rows=14)
    footer(c, 4, "print as many as you need")


def build_pdf(path):
    c = canvas.Canvas(str(path), pagesize=letter, pageCompression=1)
    c.setTitle(TITLE)
    c.setAuthor("Deitemeyer Brothers")
    page_instructions(c)
    c.showPage()
    page_equipment(c)
    c.showPage()
    c.setPageSize(landscape(letter))
    page_tools(c)
    c.showPage()
    c.setPageSize(landscape(letter))
    page_technology(c)
    c.showPage()
    c.save()


# ------------------------------------------------------- the Apps Script ---

GS_TEMPLATE = r"""/**
 * DB Asset Hub: builds the Asset List Google Form and its response Sheet.
 *
 * GENERATED by tools/asset-intake/build.py in bledsoecw/DB-Asset-Hub, from the
 * same question list as the printable PDF. Change the questions there, not here.
 *
 * Run it signed in as the account that owns the form:
 * operations@deitemeyerbrothers.com.
 *
 * buildAssetListForm    makes the form, its responses Sheet and the "DB Asset
 *                       Hub: Asset List" folder, and emails the links. Running
 *                       it again never makes a second form; it shows the links
 *                       and links the printable PDF if one is in the folder.
 * rebuildAssetListForm  reshapes the existing form to these questions. Same
 *                       form, same link. The answers already in come out in
 *                       their own tab ("Before rebuild ...") and new answers go
 *                       to a fresh tab in the same Sheet.
 *
 * The form opens on "What are you entering?" and branches to equipment (one
 * per response), tools (up to 10 per response, "Add tool 2?" after each) or
 * technology (one device per response).
 */
var FOLDER_NAME = 'DB Asset Hub: Asset List';
var SPEC = __SPEC__;

function buildAssetListForm() {
  logAccount_();
  var props = PropertiesService.getScriptProperties();
  var existing = props.getProperty('FORM_ID');
  if (existing) {
    try {
      var old = FormApp.openById(existing);
      linkPrintable_(old);
      report_(old, 'exists');
      return;
    } catch (e) {
      props.deleteProperty('FORM_ID'); // the old form is gone: make a new one
    }
  }
  var folder = folder_();
  var form = FormApp.create(SPEC.title);
  settings_(form);
  addPages_(form);
  var sheet = SpreadsheetApp.create(SPEC.title + ' (responses)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
  DriveApp.getFileById(form.getId()).moveTo(folder);
  DriveApp.getFileById(sheet.getId()).moveTo(folder);
  props.setProperty('FORM_ID', form.getId());
  props.setProperty('SHEET_ID', sheet.getId());
  linkPrintable_(form);
  report_(form, 'new');
}

function rebuildAssetListForm() {
  logAccount_();
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('FORM_ID');
  if (!id) throw new Error('There is no form to rebuild in this script yet. Run buildAssetListForm instead.');
  var form = FormApp.openById(id);
  var sheetId = props.getProperty('SHEET_ID') || form.getDestinationId();
  var ss = SpreadsheetApp.openById(sheetId);

  // Keep what is already in: unlink the current responses tab and name it, so
  // the new questions land in a clean tab of their own.
  var stamp = Utilities.formatDate(new Date(), 'America/New_York', 'yyyy-MM-dd HH:mm');
  var linked = ss.getSheets().filter(function (sh) { return !!sh.getFormUrl(); });
  var kept = 0;
  linked.forEach(function (sh) { kept += Math.max(sh.getLastRow() - 1, 0); });
  form.removeDestination();
  linked.forEach(function (sh, i) {
    sh.setName('Before rebuild ' + stamp + (linked.length > 1 ? ' (' + (i + 1) + ')' : ''));
  });

  form.getItems().forEach(function (item) { form.deleteItem(item); });
  settings_(form);
  addPages_(form);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheetId);
  props.setProperty('SHEET_ID', sheetId);
  linkPrintable_(form);
  Logger.log(kept + ' earlier response(s) are in the tab "Before rebuild ' + stamp + '". New ones go to the newest tab.');
  report_(form, 'rebuilt');
}

function logAccount_() {
  Logger.log('Running as ' + Session.getEffectiveUser().getEmail() +
    ' (this account owns the form, the Sheet and the folder, and gets the email)');
}

function settings_(form) {
  form.setTitle(SPEC.title);
  form.setDescription(SPEC.description);
  form.setCollectEmail(true);
  try { form.setRequireLogin(true); } catch (e) { /* not a Workspace account */ }
  form.setAllowResponseEdits(true);
  form.setShowLinkToRespondAgain(true);
  form.setProgressBar(true);
  form.setConfirmationMessage(SPEC.confirmation);
  form.setAcceptingResponses(true);
  try { form.setPublished(true); } catch (e) { /* older Forms: always published */ }
}

// Pages in order. The first has no page break; every other page starts with
// one. A page marked submitBefore ends the path before it (equipment ends
// before tools, the last tool before technology). Choices that jump to a page
// are set last, once every page break exists.
function addPages_(form) {
  var breaks = {};
  var jumps = [];
  SPEC.pages.forEach(function (page, i) {
    if (i > 0) {
      var pb = form.addPageBreakItem().setTitle(page.title).setHelpText(page.help || '');
      if (page.submitBefore) pb.setGoToPage(FormApp.PageNavigationType.SUBMIT);
      breaks[page.id] = pb;
    }
    page.items.forEach(function (q) {
      if (q.type === 'nav') {
        var item = form.addMultipleChoiceItem().setTitle(q.title).setHelpText(q.help || '').setRequired(true);
        jumps.push({ item: item, q: q });
      } else {
        addItem_(form, q);
      }
    });
  });
  jumps.forEach(function (j) {
    j.item.setChoices(j.q.choices.map(function (c) {
      return c.goto === 'SUBMIT'
        ? j.item.createChoice(c.label, FormApp.PageNavigationType.SUBMIT)
        : j.item.createChoice(c.label, breaks[c.goto]);
    }));
  });
}

function addItem_(form, q) {
  var item;
  if (q.type === 'choice') {
    item = form.addMultipleChoiceItem().setChoiceValues(q.options);
    if (q.other) item.showOtherOption(true);
  } else if (q.type === 'list') {
    item = form.addListItem().setChoiceValues(q.options);
  } else if (q.type === 'paragraph') {
    item = form.addParagraphTextItem();
  } else if (q.type === 'date') {
    item = form.addDateItem().setIncludesYear(true);
  } else {
    item = form.addTextItem();
    if (q.type === 'number') {
      item.setValidation(FormApp.createTextValidation()
        .setHelpText('Numbers only, no commas.')
        .requireNumberBetween(q.min, q.max)
        .build());
    } else if (q.maxLength) {
      item.setValidation(FormApp.createTextValidation()
        .setHelpText('At most ' + q.maxLength + ' characters. Last 4 digits only.')
        .requireTextLengthLessThanOrEqualTo(q.maxLength)
        .build());
    }
  }
  item.setTitle(q.title);
  if (q.help) item.setHelpText(q.help);
  if (q.required) item.setRequired(true);
}

// The folder in the running account's My Drive: the one made before, or one
// already there by that name, or a new one.
function folder_() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('FOLDER_ID');
  if (id) {
    try { return DriveApp.getFolderById(id); } catch (e) { /* gone: find or make another */ }
  }
  var found = DriveApp.getRootFolder().getFoldersByName(FOLDER_NAME);
  var folder = found.hasNext() ? found.next() : DriveApp.createFolder(FOLDER_NAME);
  props.setProperty('FOLDER_ID', folder.getId());
  return folder;
}

// The printable version is whatever PDF sits in the folder. Shares it with the
// company (view only) and puts its link in the form's description.
function printable_() {
  var pdfs = folder_().getFilesByType(MimeType.PDF);
  return pdfs.hasNext() ? pdfs.next() : null;
}

function linkPrintable_(form) {
  var pdf = printable_();
  if (!pdf) return;
  try {
    pdf.setSharing(DriveApp.Access.DOMAIN_WITH_LINK, DriveApp.Permission.VIEW);
  } catch (e) {
    Logger.log('Could not share the printable PDF with the company: ' + e);
  }
  if (form.getDescription().indexOf(pdf.getUrl()) === -1) {
    form.setDescription(SPEC.description + '\n\nPrefer paper? Print this version: ' + pdf.getUrl());
  }
}

function report_(form, status) {
  var live = form.getPublishedUrl();
  var link = live;
  try { link = form.shortenFormUrl(live); } catch (e) { /* the long link works too */ }
  var sheetId = PropertiesService.getScriptProperties().getProperty('SHEET_ID') || form.getDestinationId();
  var pdf = printable_();
  var heading = {
    'new': 'The Asset List form is ready.',
    'exists': 'The Asset List form already exists. Its links:',
    'rebuilt': 'The Asset List form is rebuilt. Same link as before:'
  }[status];
  var lines = [
    heading,
    'Send this link to whoever fills it in: ' + link,
    'Edit the form: ' + form.getEditUrl(),
    'Responses (Google Sheet): https://docs.google.com/spreadsheets/d/' + sheetId + '/edit',
    'Drive folder: ' + folder_().getUrl(),
    pdf ? 'Printable version: ' + pdf.getUrl()
        : 'No printable PDF in the folder yet. Drop it into the folder and run this again to link it from the form.'
  ];
  Logger.log(lines.join('\n'));
  if (status === 'new') {
    MailApp.sendEmail(Session.getEffectiveUser().getEmail(),
      'DB Asset Hub: Asset List form links', lines.join('\n\n'));
  }
}
"""

MANIFEST = {"timeZone": "America/New_York", "exceptionLogging": "STACKDRIVER", "runtimeVersion": "V8"}


def build_gs():
    def clean(q):
        return {k: v for k, v in q.items() if k not in ("key", "col") and v != ""}

    spec = {
        "title": TITLE,
        "description": DESCRIPTION,
        "confirmation": CONFIRMATION,
        "pages": [
            {"id": p["id"], "title": p["title"], "help": p["help"],
             **({"submitBefore": True} if p.get("submitBefore") else {}),
             "items": [clean(i) for i in p["items"]]}
            for p in PAGES
        ],
    }
    return GS_TEMPLATE.replace("__SPEC__", json.dumps(spec, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-json", help="also write the Drive import JSON (Code + manifest) here")
    args = ap.parse_args()
    build_pdf(HERE / "asset-list-printable.pdf")
    gs = build_gs()
    (HERE / "AssetListForm.gs").write_text(gs, encoding="utf-8")
    if args.project_json:
        project = {"files": [
            {"name": "Code", "type": "server_js", "source": gs},
            {"name": "appsscript", "type": "json", "source": json.dumps(MANIFEST, indent=2)},
        ]}
        Path(args.project_json).write_text(json.dumps(project), encoding="utf-8")
    print("wrote", HERE / "asset-list-printable.pdf", "and", HERE / "AssetListForm.gs")


if __name__ == "__main__":
    main()
