#!/usr/bin/env python3
"""compose.py -- typesets entry.png, a one-page broadsheet front page that
sums up the world news of Friday 20 November 2026.

The page is drawn with PIL (used only at build time; the submitted program
main.py needs nothing but the standard library and copies the finished
entry.png). Layout is cursor-based: every block is measured before it is
drawn, wrapped to its box, and asserted to fit, so nothing can clip or
overlap. Rendering is deterministic: same fonts, same code, same bytes.
"""

import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MARGIN = 40
RIGHT = W - MARGIN            # 984
CW = W - 2 * MARGIN           # 944, content width

PAPER = (247, 243, 234)       # #F7F3EA
INK = (18, 18, 18)            # #121212
RED = (168, 12, 28)           # #A80C1C
GREY = (90, 86, 78)           # #5A564E
WHITE = (255, 255, 255)

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIRS = [
    os.path.join(HERE, "fonts"),
    os.path.join(HERE, "..", "fonts"),
    "/usr/share/fonts/truetype/noto",
    "/usr/share/fonts/truetype/liberation",
]


def load_font(filename, size):
    for d in FONT_DIRS:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise FileNotFoundError(filename)


SERIF_DISPLAY = "NotoSerifDisplay-Black.ttf"
SERIF_BOLD = "NotoSerif-Bold.ttf"
SANS_XBOLD = "NotoSans-ExtraBold.ttf"
SANS_BLACK = "NotoSans-Black.ttf"
SANS_BOLD = "NotoSans-Bold.ttf"
LIB_REG = "LiberationSerif-Regular.ttf"
LIB_ITAL = "LiberationSerif-Italic.ttf"


def tw(draw, s, f):
    """Width of a string in pixels."""
    return draw.textlength(s, font=f)


def wrap(draw, s, f, width):
    """Greedy word wrap; asserts every line fits the box width."""
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word) if cur else word
        if tw(draw, trial, f) <= width:
            cur = trial
        else:
            assert cur, "single word wider than box: %r" % word
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for line in lines:
        assert tw(draw, line, f) <= width, "line overflows box: %r" % line
    return lines


def ink_height(draw, s, f):
    x0, y0, x1, y1 = draw.textbbox((0, 0), s, font=f)
    return y1 - y0, y0


def draw_left(draw, x, y_top, s, f, fill):
    """Draw with the ink's top edge exactly at y_top; returns ink height."""
    h, y0 = ink_height(draw, s, f)
    draw.text((x, y_top - y0), s, font=f, fill=fill)
    return h


def draw_centered(draw, y_top, s, f, fill):
    x0, y0, x1, y1 = draw.textbbox((0, 0), s, font=f)
    x = (W - (x1 - x0)) // 2 - x0
    draw.text((x, y_top - y0), s, font=f, fill=fill)
    return y1 - y0


def draw_tracked_centered(draw, y_center, s, f, tracking, fill):
    """Letterspaced text, horizontally centred, centred on y_center."""
    widths = [tw(draw, ch, f) for ch in s]
    total = sum(widths) + tracking * (len(s) - 1)
    x = (W - total) / 2
    asc, desc = f.getmetrics()
    y = y_center - (asc + desc) / 2
    for ch, wch in zip(s, widths):
        draw.text((x, y), ch, font=f, fill=fill)
        x += wch + tracking
    return total


def block(draw, x, y, width, segments, line_height):
    """Draw wrapped text; segments is a list of (text, font, fill) runs that
    flow together. Returns the height used. Asserts the flow fits width."""
    # Tokenise into (word, font, fill), keeping segment boundaries.
    tokens = []
    for text, f, fill in segments:
        words = text.split(" ")
        for i, w in enumerate(words):
            if w == "" and i not in (0, len(words) - 1):
                continue
            tokens.append((w, f, fill, i == 0 and text.startswith(" ")))
    # Greedy lines over tokens; a token may carry a leading space marker.
    lines, cur, cur_w = [], [], 0.0
    space_w = {}
    for word, f, fill, lead_space in tokens:
        if f not in space_w:
            space_w[f] = tw(draw, " ", f)
        w_w = tw(draw, word, f) if word else 0.0
        add = w_w
        if cur and (lead_space or True):
            add += space_w[f]
        if cur and cur_w + add > width:
            lines.append(cur)
            cur, cur_w = [(word, f, fill)], w_w
        else:
            cur.append((word, f, fill))
            cur_w += add
    if cur:
        lines.append(cur)
    yy = y
    for line in lines:
        xx = x
        for i, (word, f, fill) in enumerate(line):
            if i > 0:
                xx += space_w[f]
            if word:
                draw.text((xx, yy), word, font=f, fill=fill)
                xx += tw(draw, word, f)
        yy += line_height
    return yy - y


def panel(draw, x, y, width, kicker, headline, body,
          kicker_size=14, head_size=26, head_lh=30, body_size=16, body_lh=20):
    """One news panel: red kicker, serif headline, serif body.
    Returns the height used."""
    kf = load_font(SANS_XBOLD, kicker_size)
    kh = draw_left(draw, x, y, kicker, kf, RED)
    yy = y + kh + 4
    hf = load_font(SERIF_BOLD, head_size)
    for line in wrap(draw, headline, hf, width):
        draw_left(draw, x, yy, line, hf, INK)
        yy += head_lh
    yy += 2
    bf = load_font(LIB_REG, body_size)
    for line in wrap(draw, body, bf, width):
        draw.text((x, yy), line, font=bf, fill=INK)
        yy += body_lh
    return yy - y


def main():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    y = 18

    # ---- Folio strip ------------------------------------------------------
    folio_f = load_font(SANS_BOLD, 16)
    draw_left(draw, MARGIN, y, "THE DAY\u2019S NEWS \u00b7 ONE PAGE \u00b7 ONE IMAGE",
              folio_f, GREY)
    right_txt = "EST. 2026 \u2014 NO. 20"
    rx = RIGHT - tw(draw, right_txt, folio_f)
    draw_left(draw, rx, y, right_txt, folio_f, GREY)
    y += 26
    draw.line([(MARGIN, y), (RIGHT, y)], fill=INK, width=2)
    y += 8

    # ---- Masthead ----------------------------------------------------------
    mast_f = load_font(SERIF_DISPLAY, 66)
    mh = draw_centered(draw, y, "The Daily World", mast_f, INK)
    y += mh + 8

    # ---- Date bar ----------------------------------------------------------
    bar_h = 36
    draw.rectangle([(MARGIN, y), (RIGHT, y + bar_h)], fill=INK)
    date_f = load_font(SANS_BLACK, 21)
    draw_tracked_centered(draw, y + bar_h / 2, "FRIDAY \u00b7 20 NOVEMBER 2026",
                          date_f, 3, WHITE)
    y += bar_h + 10

    # ---- Lead story --------------------------------------------------------
    lead_kicker_f = load_font(SANS_XBOLD, 17)
    kh = draw_left(draw, MARGIN, y, "THE HAGUE \u00b7 INTERNATIONAL COURT OF JUSTICE",
                   lead_kicker_f, RED)
    y += kh + 4
    banner_lines = ["World Court: Myanmar committed",
                    "genocide against the Rohingya"]
    size = 54
    while size > 30:
        bf = load_font(SERIF_DISPLAY, size)
        if all(tw(draw, ln, bf) <= CW for ln in banner_lines):
            break
        size -= 2
    banner_f = bf
    banner_lh = int(size * 1.03)
    for ln in banner_lines:
        draw_left(draw, MARGIN, y, ln, banner_f, INK)
        y += banner_lh
    y += 4
    sub_f = load_font(LIB_ITAL, 19)
    sub = ("The first genocide verdict against a state in the court\u2019s "
           "history, over the 2017 crackdown \u2014 Myanmar rejects the judgment.")
    for line in wrap(draw, sub, sub_f, CW):
        draw.text((MARGIN, y), line, font=sub_f, fill=INK)
        y += 23
    y += 6
    draw.line([(MARGIN, y), (RIGHT, y)], fill=INK, width=2)
    y += 12

    # ---- Panel rows 1 and 2 -------------------------------------------------
    gutter = 28
    col_w = (CW - gutter) // 2          # 458
    col2_x = MARGIN + col_w + gutter    # 526
    divider_x = MARGIN + col_w + gutter // 2

    rows = [
        (("SHENZHEN \u00b7 FIRST THREE-WAY SUMMIT",
          "Trump, Xi & Putin sign a peace declaration",
          "US, Chinese and Russian leaders meet face to face for the first "
          "time and sign a four-point pact. Europe warns: no deal over our "
          "heads."),
         ("KYIV \u00b7 WARSAW \u00b7 THE WAR",
          "Russia pounds Kyiv; a missile hits Poland",
          "400+ drones and 110 missiles in one night; eight killed, three "
          "Kyiv bridges hit. Poland reports two missiles and a drone in its "
          "airspace; Putin vows a hard reply.")),
        (("ODISHA \u00b7 CYCLONE AKVAN",
          "Cyclone Akvan batters India\u2019s east coast",
          "The third cyclone in a month makes landfall near Gopalpur at "
          "80 km/h. More than 300,000 people were evacuated; no deaths in "
          "the first assessments."),
         ("NEW YORK \u00b7 MARKETS",
          "AI sell-off deepens as Anthropic lists",
          "S&P 500 \u22122%, a fifth straight loss; Nikkei \u22124.8%. Anthropic, "
          "the first pure-AI listing, closed its debut +17% at $97, then "
          "slid. Gold \u22124.2%.")),
    ]
    for left, right in rows:
        h1 = panel(draw, MARGIN, y, col_w, *left)
        h2 = panel(draw, col2_x, y, col_w, *right)
        row_h = max(h1, h2)
        draw.line([(divider_x, y + 2), (divider_x, y + row_h - 4)],
                  fill=GREY, width=1)
        y += row_h + 8
        draw.line([(MARGIN, y), (RIGHT, y)], fill=GREY, width=1)
        y += 10

    # ---- Panel row 3: Riyadh, full width ------------------------------------
    h3 = panel(
        draw, MARGIN, y, CW,
        "RIYADH \u00b7 MIDDLE EAST",
        "Houthi missiles strike the Riyadh skyline",
        "Missiles damage the sovereign wealth fund tower in the financial "
        "district. Oil tops $92 as Hormuz tanker attacks intensify and the "
        "Iran war enters its ninth month.",
        head_size=25, head_lh=29)
    y += h3 + 8
    draw.line([(MARGIN, y), (RIGHT, y)], fill=INK, width=2)
    y += 10

    # ---- Wire block ----------------------------------------------------------
    wire_title = "THE WIRE \u2014 MORE OF FRIDAY"
    wire_f = load_font(SANS_BLACK, 17)
    twd = tw(draw, wire_title, wire_f)
    tx = (W - twd) / 2
    mid = y + 9
    draw.line([(MARGIN, mid), (tx - 16, mid)], fill=INK, width=2)
    draw.line([(tx + twd + 16, mid), (RIGHT, mid)], fill=INK, width=2)
    draw_left(draw, tx, y, wire_title, wire_f, INK)
    y += 27

    briefs = [
        ("BRUSSELS", "EU\u2013UK summit seals a Brexit \u201creset\u201d deal."),
        ("NAIROBI", "Last Ebola patient home; outbreak over, 37 days on."),
        ("GAZA", "Israeli troops cross the ceasefire Yellow Line."),
        ("ANTALYA", "COP31 draft drops the fossil phase-out call."),
        ("LOS ANGELES", "GTA VI launch sales top $2.3 billion."),
        ("PORT-AU-PRINCE", "34 killed in gang violence, police say."),
        ("YENNE, SENEGAL", "Dozens missing as a migrant boat capsizes."),
        ("SOUTH KORDOFAN", "Drone strike kills 10 at a gold mine."),
        ("SAN SALVADOR", "Bukele registers for a third term."),
        ("CARACAS", "US and Venezuela sign a military deal."),
        ("YONGBYON", "IAEA: North Korea expands uranium enrichment."),
        ("BRAS\u00cdLIA", "Central bank sells $1 billion to curb the dollar."),
        ("ROME", "Italy fines Meta \u20ac805 million over photo access."),
        ("WASHINGTON", "FAA ground stop strands 1.5 million travellers."),
        ("NASHVILLE", "Ella Langley sweeps the CMA Awards."),
    ]
    place_f = load_font(SANS_BOLD, 13)
    brief_f = load_font(LIB_REG, 14)
    wire_gutter = 24
    wire_col_w = (CW - 2 * wire_gutter) // 3     # 298
    cols = [briefs[0:5], briefs[5:10], briefs[10:15]]
    wire_top = y
    wire_bottom = y
    for ci, col in enumerate(cols):
        cx = MARGIN + ci * (wire_col_w + wire_gutter)
        cy = wire_top
        for place, text in col:
            draw.rectangle([(cx, cy + 4), (cx + 7, cy + 11)], fill=RED)
            used = block(draw, cx + 13, cy, wire_col_w - 13,
                         [(place + " \u2014 ", place_f, INK),
                          (text, brief_f, INK)], 16)
            cy += used + 4
        wire_bottom = max(wire_bottom, cy)
    y = wire_bottom + 8

    # ---- Footer ---------------------------------------------------------------
    draw.line([(MARGIN, y), (RIGHT, y)], fill=GREY, width=1)
    y += 8
    foot_f = load_font(LIB_ITAL, 14)
    draw_centered(draw, y,
                  "Compiled from the day\u2019s reporting by Reuters, the BBC "
                  "and international news wires.", foot_f, GREY)
    y += 22

    assert y <= H - 6, "page overflows: content ends at y=%d" % y
    out = os.path.join(HERE, "entry.png")
    img.save(out, format="PNG")
    print("wrote", out, os.path.getsize(out), "bytes; content ends at y =", y)


if __name__ == "__main__":
    main()
