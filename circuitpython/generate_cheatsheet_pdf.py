#!/usr/bin/env python3
"""
Generate circuitpython/cheatsheet_a4.pdf directly from:
  - circuitpython/tannenbaum_leds.svg
  - circuitpython/lib/tannenbaum_layout.py
  - circuitpython/lib/tannenbaum_palettes.py

Requires `rsvg-convert` (librsvg2-bin).
"""

from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
LEDS_SVG = HERE / "tannenbaum_leds.svg"
OUT_PDF = HERE / "cheatsheet_a4.pdf"

FONT_SANS = "DejaVu Sans, Arial, sans-serif"
FONT_MONO = "DejaVu Sans Mono, monospace"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def parse_leds_svg(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}

    leds = []
    for elem in root.findall(".//svg:circle", ns):
        idx_attr = elem.attrib.get("data-index")
        if idx_attr is None:
            continue
        idx = int(idx_attr)
        seg = int(elem.attrib["data-segment"])
        cx = float(elem.attrib["cx"])
        cy = float(elem.attrib["cy"])
        stroke = elem.attrib.get("stroke", "#495057")
        leds.append((idx, seg, cx, cy, stroke))
    leds.sort(key=lambda item: item[0])

    polylines = []
    for elem in root.findall(".//svg:polyline", ns):
        polylines.append((elem.attrib["points"], elem.attrib.get("stroke", "#495057")))

    outline_d = None
    for elem in root.findall(".//svg:path", ns):
        if elem.attrib.get("id") == "pcb-outline":
            outline_d = elem.attrib.get("d")
            break

    return leds, polylines, outline_d


def draw_card(lines, x, y, w, h, title, badge=None, accent="#0D6EFD"):
    lines.append(
        f'  <rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="2.0" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.35"/>'
    )
    lines.append(
        f'  <rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="7.0" rx="2.0" fill="#F8F9FA" stroke="#CED4DA" stroke-width="0.35"/>'
    )
    lines.append(
        f'  <rect x="{x+0.18:.2f}" y="{y+3.5:.2f}" width="{w-0.36:.2f}" height="3.5" fill="#F8F9FA"/>'
    )
    lines.append(
        f'  <line x1="{x:.2f}" y1="{y+7.0:.2f}" x2="{x+w:.2f}" y2="{y+7.0:.2f}" stroke="#DEE2E6" stroke-width="0.35"/>'
    )
    lines.append(
        f'  <rect x="{x+2.6:.2f}" y="{y+1.8:.2f}" width="1.2" height="3.4" rx="0.6" fill="{accent}"/>'
    )
    lines.append(
        f'  <text x="{x+5.0:.2f}" y="{y+4.75:.2f}" font-family="{FONT_SANS}" font-size="2.75" font-weight="bold" fill="#212529">{esc(title)}</text>'
    )
    if badge:
        lines.append(
            f'  <text x="{x+w-2.8:.2f}" y="{y+4.65:.2f}" text-anchor="end" font-family="{FONT_MONO}" font-size="1.95" fill="#6C757D">{esc(badge)}</text>'
        )


def draw_code_box(lines, x, y, w, code_lines, line_h=3.1, font_size=2.0, pad_y=1.8):
    h = pad_y * 2 + len(code_lines) * line_h - 0.5
    lines.append(
        f'  <rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="1.3" fill="#F8F9FA" stroke="#E9ECEF" stroke-width="0.3"/>'
    )
    KEYWORDS = {
        "import", "from", "while", "for", "in", "if", "elif", "else",
        "def", "return", "True", "False", "None", "and", "or", "not",
    }
    for idx, raw in enumerate(code_lines):
        ly = y + pad_y + 1.9 + idx * line_h
        if "#" in raw:
            code_part, comment_part = raw.split("#", 1)
            comment_part = "#" + comment_part
        else:
            code_part, comment_part = raw, ""

        tspans = []
        tokens = re.split(r"(\s+|[(),:=\[\]+*/%-]+)", code_part)
        for tok in tokens:
            if not tok:
                continue
            if tok in KEYWORDS:
                tspans.append(f'<tspan fill="#0B5ED7" font-weight="bold">{esc(tok)}</tspan>')
            elif re.match(r"^\d+(\.\d+)?$", tok):
                tspans.append(f'<tspan fill="#B02A37">{esc(tok)}</tspan>')
            elif tok.startswith('"') or tok.startswith("'"):
                tspans.append(f'<tspan fill="#146C43">{esc(tok)}</tspan>')
            else:
                tspans.append(f'<tspan fill="#212529">{esc(tok)}</tspan>')
        if comment_part:
            tspans.append(f'<tspan fill="#6C757D" font-style="italic">{esc(comment_part)}</tspan>')

        lines.append(
            f'  <text x="{x+2.2:.2f}" y="{ly:.2f}" xml:space="preserve" font-family="{FONT_MONO}" font-size="{font_size:.2f}">{"".join(tspans)}</text>'
        )
    return y + h


def build_page1_svg() -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
        '  <rect width="210" height="297" fill="#FFFFFF"/>',
        # Header
        f'  <text x="12" y="16.5" font-family="{FONT_SANS}" font-size="4.0" font-weight="bold" fill="#212529">AITY Weihnachtsbaum 2026 — Cheatsheet (1/2)</text>',
        f'  <text x="198" y="16.5" text-anchor="end" font-family="{FONT_SANS}" font-size="2.65" fill="#6C757D">CircuitPython · 60 LEDs (D10) · Taster D5 &amp; D6</text>',
        '  <rect x="12" y="20.5" width="186" height="8.5" rx="1.5" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>',
        f'  <text x="15" y="25.8" font-family="{FONT_SANS}" font-size="2.35" fill="#495057">'
        f'Start: <tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">from tannenbaum_layout import NUM_PIXELS, init_pixels, init_buttons</tspan>'
        f'  ·  <tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">pixels = init_pixels()</tspan>'
        f'  ·  <tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">btn_d5, btn_d6 = init_buttons()</tspan></text>',
    ]

    col1_x = 12.0
    col_w = 91.0

    # Card 1: Variablen, Farben (RGB) & Listen (Y = 32, H = 56)
    c1_y, c1_h = 32.0, 56.0
    draw_card(lines, col1_x, c1_y, col_w, c1_h, "1. Variablen, Farben (RGB) & Listen", "Grundlagen", "#0D6EFD")
    lines.append(
        f'  <text x="{col1_x+2.8:.2f}" y="{c1_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.15" fill="#495057">'
        'Farben bestehen aus <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">(Rot, Grün, Blau)</tspan> von <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">0</tspan> (aus) bis <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">255</tspan> (hell):</text>'
    )
    draw_code_box(
        lines,
        col1_x + 2.6,
        c1_y + 13.2,
        col_w - 5.2,
        [
            "pos = 0                   # Ganze Zahl: LED-Nummer 0 bis 59",
            "helligkeit = 0.3          # Kommazahl: 0.0 (aus) bis 1.0 (max)",
            "aktiv = True              # Wahrheitswert: True oder False",
            "",
            "ROT   = (255, 0, 0)       # Nur Rot an",
            "GRUEN = (0, 255, 0)       # Nur Grün an   | GELB = (255, 255, 0)",
            "BLAU  = (0, 0, 255)       # Nur Blau an   | AUS  = (0, 0, 0)",
            "r, g, b = ROT             # Farbe wieder in 3 Werte aufteilen",
            "",
            "farben = [ROT, GRUEN, BLAU] # Liste mit mehreren Farben",
            "anzahl = len(farben)      # Wie viele Elemente? -> 3",
            "erste  = farben[0]        # Erstes Element (Zählung startet bei 0!)",
        ],
        line_h=3.1,
        font_size=1.98,
        pad_y=1.8,
    )

    # Card 2: Bedingungen (if / elif / else) (Y = 91, H = 64)
    c2_y, c2_h = 91.0, 64.0
    draw_card(lines, col1_x, c2_y, col_w, c2_h, "2. Entscheidungen: if / elif / else", "Bedingungen", "#6610F2")
    lines.append(
        f'  <text x="{col1_x+2.8:.2f}" y="{c2_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.08" fill="#495057">'
        'Mit <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">if</tspan> (falls), <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">elif</tspan> (sonst falls) &amp; <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">else</tspan> (sonst) entscheidest du:</text>'
    )
    draw_code_box(
        lines,
        col1_x + 2.6,
        c2_y + 13.2,
        col_w - 5.2,
        [
            "if pos < 18:              # Wenn pos kleiner als 18 (Zweig Unten)",
            "    farbe = (0, 180, 255) #   4 Leerzeichen eingerückt!",
            "elif pos < 50:            # Sonst, falls pos kleiner als 50",
            "    farbe = (0, 255, 80)  #   Zweige Mitte/Oben oder Stiel",
            "else:                     # In allen anderen Fällen (50 bis 59)",
            "    farbe = (255, 180, 0) #   Stern an der Spitze",
            "",
            "# Vergleichen: == (gleich), != (ungleich), <, <=, >, >=",
            "# Verknüpfen:  and (beide wahr), or (eins wahr), not (umkehren)",
        ],
        line_h=3.12,
        font_size=1.98,
        pad_y=1.8,
    )
    op_y = c2_y + 46.2
    lines.append(
        f'  <rect x="{col1_x+2.6:.2f}" y="{op_y:.2f}" width="{col_w-5.2:.2f}" height="15.5" rx="1.2" fill="#FFF9DB" stroke="#FFE066" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{col1_x+4.4:.2f}" y="{op_y+4.1:.2f}" font-family="{FONT_SANS}" font-size="2.05" font-weight="bold" fill="#212529">Die 3 häufigsten Fehler (so vermeidest du sie!):</text>'
    )
    lines.append(
        f'  <text x="{col1_x+4.4:.2f}" y="{op_y+8.0:.2f}" font-family="{FONT_SANS}" font-size="1.95" fill="#212529">'
        '1. Doppelpunkt <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">:</tspan> nach <tspan font-family="DejaVu Sans Mono, monospace">if/for/while/def</tspan>  ·  2. Genau <tspan font-weight="bold">4 Leerzeichen</tspan> einrücken</text>'
    )
    lines.append(
        f'  <text x="{col1_x+4.4:.2f}" y="{op_y+12.2:.2f}" font-family="{FONT_SANS}" font-size="1.95" fill="#212529">'
        '3. <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">=</tspan> speichert einen Wert (<tspan font-family="DejaVu Sans Mono, monospace">pos = 0</tspan>), <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">==</tspan> vergleicht (<tspan font-family="DejaVu Sans Mono, monospace">if pos == 0:</tspan>)</text>'
    )

    # Card 3: For-Schleife (for loop) (Y = 158, H = 58)
    c3_y, c3_h = 158.0, 58.0
    draw_card(lines, col1_x, c3_y, col_w, c3_h, "3. Zählschleife: for ... in ...", "Wiederholen", "#198754")
    lines.append(
        f'  <text x="{col1_x+2.8:.2f}" y="{c3_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.15" fill="#495057">'
        'Perfekt, um viele LEDs nacheinander zu färben, ohne 60 Zeilen zu tippen:</text>'
    )
    draw_code_box(
        lines,
        col1_x + 2.6,
        c3_y + 13.2,
        col_w - 5.2,
        [
            "# 1) Alle 60 LEDs durchlaufen (i ist 0, 1, 2, ..., 59):",
            "for i in range(NUM_PIXELS):",
            "    pixels[i] = (0, i * 4, 255 - i * 4)",
            "pixels.show()",
            "",
            "# 2) Bestimmter Bereich: range(start, stop_ohne, schritt):",
            "for i in range(0, 18):       # LEDs 0 bis 17 (Zweig Unten)",
            "    pixels[i] = ROT",
            "for i in range(0, 60, 3):    # Jede 3. LED: 0, 3, 6, ..., 57",
            "    pixels[i] = (255, 180, 0)",
            "",
            "# 3) Nur ausgewählte LED-Nummern aus einer Liste:",
            "for led in (51, 52, 55, 56, 59): # Die 5 äußeren Sternspitzen",
            "    pixels[led] = (255, 255, 255)",
        ],
        line_h=2.95,
        font_size=1.96,
        pad_y=1.6,
    )

    # Card 4: While-Schleife, Pausen & Funktionen (Y = 219, H = 67)
    c4_y, c4_h = 219.0, 67.0
    draw_card(lines, col1_x, c4_y, col_w, c4_h, "4. Endlosschleife (while), Pause & def", "Animationen", "#D63384")
    lines.append(
        f'  <text x="{col1_x+2.8:.2f}" y="{c4_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.15" fill="#495057">'
        '<tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">while True:</tspan> wiederholt sich ewig. Mit <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">print()</tspan> siehst du Werte in der Konsole:</text>'
    )
    draw_code_box(
        lines,
        col1_x + 2.6,
        c4_y + 13.2,
        col_w - 5.2,
        [
            "import time",
            "",
            "def zeige_led(nr, farbe=ROT):  # Eigener Befehl (Funktion)",
            "    pixels.fill((0, 0, 0))",
            "    pixels[nr] = farbe",
            "    pixels.show()",
            "",
            "# A) Einfach zum Starten: kurz warten mit time.sleep(Sekunden)",
            "pos = 0",
            "while True:",
            "    zeige_led(pos)",
            "    pos = (pos + 1) % 60       # % 60: nach 59 springt es auf 0!",
            "    print(\"LED:\", pos)         # Zum Testen in der Konsole",
            "    time.sleep(0.2)            # 0.2 Sekunden Pause",
            "",
            "# B) Profi-Trick (ohne Pause für Taster): siehe Vorlage in Box 7!",
        ],
        line_h=2.98,
        font_size=1.96,
        pad_y=1.6,
    )

    # Right column: X = 107, W = 91
    col2_x = 107.0

    # Card 5: Taster D5 & D6 abfragen (Y = 32, H = 77)
    c5_y, c5_h = 32.0, 77.0
    draw_card(lines, col2_x, c5_y, col_w, c5_h, "5. Taster D5 & D6 abfragen", "tannenbaum_layout", "#FD7E14")
    lines.append(
        f'  <text x="{col2_x+2.8:.2f}" y="{c5_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.15" fill="#495057">'
        '<tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">init_buttons()</tspan> richtet beide Taster fertig ein (inkl. Schutz vor Doppelklicks):</text>'
    )
    draw_code_box(
        lines,
        col2_x + 2.6,
        c5_y + 13.2,
        col_w - 5.2,
        [
            "from tannenbaum_layout import init_buttons",
            "",
            "btn_d5, btn_d6 = init_buttons()   # Taster D5 & D6 starten",
            "",
            "while True:",
            "    # A) Einmal beim Antippen (Klick) -> perfekt zum Umschalten!",
            "    if btn_d5.pressed():",
            "        modus = (modus + 1) % 4   # Zählt 0 -> 1 -> 2 -> 3 -> 0",
            "",
            "    # B) Solange gedrückt gehalten -> z.B. Turbo oder Blitzlicht",
            "    if btn_d6.is_pressed:",
            "        pixels.fill((255, 255, 255))",
            "        pixels.show()",
        ],
        line_h=3.02,
        font_size=1.98,
        pad_y=1.7,
    )

    bt_y = c5_y + 56.8
    lines.append(
        f'  <rect x="{col2_x+2.6:.2f}" y="{bt_y:.2f}" width="{col_w-5.2:.2f}" height="17.8" rx="1.2" fill="#FFF4E6" stroke="#FFD8A8" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{col2_x+4.2:.2f}" y="{bt_y+4.1:.2f}" font-family="{FONT_SANS}" font-size="2.05" font-weight="bold" fill="#212529">Welche Abfrage nehme ich wofür?</text>'
    )
    btn_rows = [
        ("btn.pressed()", "Einmal pro Klick", "Farbe, Modus oder Schritt wechseln"),
        ("btn.is_pressed", "Solange gehalten", "Rückwärts laufen, Turbo, Aufleuchten"),
    ]
    for r_i, (m_name, m_ret, m_use) in enumerate(btn_rows):
        ry = bt_y + 8.6 + r_i * 4.8
        lines.append(
            f'  <text x="{col2_x+4.2:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.95" font-weight="bold" fill="#D9480F">{esc(m_name)}</text>'
        )
        lines.append(
            f'  <text x="{col2_x+25.5:.2f}" y="{ry:.2f}" font-family="{FONT_SANS}" font-size="1.95" font-weight="bold" fill="#212529">{esc(m_ret)}</text>'
        )
        lines.append(
            f'  <text x="{col2_x+49.5:.2f}" y="{ry:.2f}" font-family="{FONT_SANS}" font-size="1.95" fill="#495057">{esc(m_use)}</text>'
        )

    # Card 6: Einzelne Pixel & Baum zeichnen (Y = 112, H = 82)
    c6_y, c6_h = 112.0, 82.0
    draw_card(lines, col2_x, c6_y, col_w, c6_h, "6. Einzelne Pixel & Baum zeichnen", "init_pixels()", "#20C997")
    lines.append(
        f'  <text x="{col2_x+2.8:.2f}" y="{c6_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.15" fill="#495057">'
        'Wichtig: Erst <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">pixels.show()</tspan> schickt deine Farben wirklich an die LEDs!</text>'
    )
    draw_code_box(
        lines,
        col2_x + 2.6,
        c6_y + 13.2,
        col_w - 5.2,
        [
            "from tannenbaum_layout import init_pixels, hsv_to_rgb_gamma",
            "",
            "# 60 LEDs starten (Helligkeit 0.3 = 30%, schont die Augen!)",
            "pixels = init_pixels(brightness=0.3)",
            "",
            "pixels.fill((0, 0, 0))          # Alle 60 LEDs ausschalten",
            "pixels[0]  = (255, 0, 0)        # Erste LED (unten rechts) rot",
            "pixels[55] = (255, 255, 255)    # Oberste Sternspitze weiß",
            "",
            "# Farbe auslesen & abdunkeln (// 2 = halb so hell):",
            "r, g, b = pixels[0]",
            "pixels[0] = (r // 2, g // 2, b // 2)",
            "",
            "# Regenbogenfarbe per Farbton (0.0=Rot, 0.33=Grün, 0.66=Blau):",
            "pixels[10] = hsv_to_rgb_gamma(0.33, 1.0, 0.8)",
            "pixels.brightness = 0.5         # Gesamthelligkeit ändern",
            "pixels.show()                   # Jetzt auf dem Baum anzeigen!",
        ],
        line_h=3.02,
        font_size=1.94,
        pad_y=1.7,
    )
    nt_y = c6_y + 68.8
    lines.append(
        f'  <rect x="{col2_x+2.6:.2f}" y="{nt_y:.2f}" width="{col_w-5.2:.2f}" height="10.8" rx="1.2" fill="#E6FCF5" stroke="#96F2D7" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{col2_x+4.2:.2f}" y="{nt_y+4.2:.2f}" font-family="{FONT_SANS}" font-size="2.05" font-weight="bold" fill="#087F5B">Tipp — Holz-Baum statt Platine (PCB)?</text>'
    )
    lines.append(
        f'  <text x="{col2_x+4.2:.2f}" y="{nt_y+8.4:.2f}" font-family="{FONT_SANS}" font-size="1.95" fill="#212529">'
        f'Mit <tspan font-family="{FONT_MONO}">init_pixels(tree_type="Holz")</tspan> läuft der mittlere Zweig richtig herum.</text>'
    )

    # Card 7: Komplettes Programm-Template (Y = 197, H = 89)
    c7_y, c7_h = 197.0, 89.0
    draw_card(lines, col2_x, c7_y, col_w, c7_h, "7. Lauflicht-Vorlage (code.py)", "Zum Ausprobieren", "#0D6EFD")
    lines.append(
        f'  <text x="{col2_x+2.8:.2f}" y="{c7_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.15" fill="#495057">'
        'Komet mit Schweif! Kombiniert <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">while</tspan>, <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">if/else</tspan>, <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">for</tspan> und beide Taster:</text>'
    )
    draw_code_box(
        lines,
        col2_x + 2.6,
        c7_y + 13.2,
        col_w - 5.2,
        [
            "import time",
            "from tannenbaum_layout import NUM_PIXELS, init_pixels, init_buttons",
            "from tannenbaum_palettes import RED, GREEN, BLUE, WHITE",
            "",
            "pixels = init_pixels(brightness=0.3)",
            "btn_d5, btn_d6 = init_buttons()",
            "FARBEN = (RED, GREEN, BLUE, WHITE)",
            "farb_idx = 0",
            "pos = 0",
            "last_step = time.monotonic()           # Timer ohne sleep-Pause",
            "",
            "while True:",
            "    now = time.monotonic()",
            "    if btn_d5.pressed():               # D5 tippen: nächste Farbe",
            "        farb_idx = (farb_idx + 1) % len(FARBEN)",
            "    if (now - last_step) >= 0.05:      # Alle 0.05s ein Schritt",
            "        last_step = now",
            "        if btn_d6.is_pressed:          # D6 halten: rückwärts!",
            "            pos = (pos - 1) % NUM_PIXELS",
            "        else:",
            "            pos = (pos + 1) % NUM_PIXELS",
            "        for i in range(NUM_PIXELS):    # Schweif sanft abdunkeln",
            "            r, g, b = pixels[i]",
            "            pixels[i] = (r // 2, g // 2, b // 2)",
            "        pixels[pos] = FARBEN[farb_idx] # Kopf-LED hell setzen",
            "        pixels.show()",
        ],
        line_h=2.73,
        font_size=1.88,
        pad_y=1.5,
    )

    # Footer
    lines.append(
        f'  <text x="105" y="292.5" text-anchor="middle" font-family="{FONT_SANS}" font-size="2.45" fill="#6C757D">'
        'AITY Weihnachtsbaum 2026 · CircuitPython Cheatsheet (Seite 1/2: Python, Taster &amp; Pixel) · Lizenz: CC-BY-NC-4.0</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def build_page2_svg(leds, polylines, outline_d=None) -> str:
    xs = [c[2] for c in leds]
    ys = [c[3] for c in leds]
    if outline_d:
        for mx, my in re.findall(r"[ML]\s*([-\d.]+)\s+([-\d.]+)", outline_d):
            xs.append(float(mx))
            ys.append(float(my))
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
        '  <rect width="210" height="297" fill="#FFFFFF"/>',
        # Header
        f'  <text x="12" y="16.5" font-family="{FONT_SANS}" font-size="4.0" font-weight="bold" fill="#212529">AITY Weihnachtsbaum 2026 — Cheatsheet (2/2)</text>',
        f'  <text x="198" y="16.5" text-anchor="end" font-family="{FONT_SANS}" font-size="2.65" fill="#6C757D">tannenbaum_layout.py · tannenbaum_palettes.py</text>',
        '  <rect x="12" y="20.5" width="186" height="8.5" rx="1.5" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>',
        f'  <text x="15" y="25.8" font-family="{FONT_SANS}" font-size="2.35" fill="#495057">'
        f'Pixelgruppen: <tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">fill_seg(id, farbe)</tspan> (5 Segmente)  ·  '
        f'<tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">fill_vseg(id, farbe)</tspan> &amp; '
        f'<tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">VirtualSegment(id)</tspan> (6 Segmente inkl. Stern Innen/Außen)</text>',
    ]

    # Top-Left Card: Reference Tree Map (X=12, Y=32, W=68, H=132)
    map_x, map_y, map_w, map_h = 12.0, 32.0, 68.0, 132.0
    draw_card(lines, map_x, map_y, map_w, map_h, "8. LED-Karte & Segmente", "0..59", "#198754")

    ref_scale = min(60.0 / (x_max - x_min), 102.0 / (y_max - y_min))
    tree_w = (x_max - x_min) * ref_scale
    ref_ox = map_x + (map_w - tree_w) / 2.0 - x_min * ref_scale
    ref_oy = map_y + 10.5 - y_min * ref_scale

    lines.append(f'  <g transform="translate({ref_ox:.3f},{ref_oy:.3f}) scale({ref_scale:.4f})">')
    if outline_d:
        lines.append(
            f'    <path d="{outline_d}" fill="#F8F9FA" fill-opacity="0.6" stroke="#868E96" stroke-width="0.35" stroke-linejoin="round"/>'
        )
    for pts, color in polylines:
        lines.append(
            f'    <polyline points="{pts}" fill="none" stroke="{color}" stroke-width="0.25" stroke-opacity="0.45" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    for idx, _, cx, cy, color in leds:
        lines.append(
            f'    <circle cx="{cx:.3f}" cy="{cy:.3f}" r="0.92" fill="#FFFFFF" stroke="{color}" stroke-width="0.26"/>'
        )
        lines.append(
            f'    <text x="{cx:.3f}" y="{cy+0.32:.3f}" text-anchor="middle" font-family="{FONT_SANS}" font-size="0.9" font-weight="bold" fill="#212529">{idx}</text>'
        )
    lines.append("  </g>")

    leg_y0 = map_y + 115.0
    leg_items = [
        ("#1971C2", "0: Zweig Unten (0–17)", 15.0, leg_y0),
        ("#2F9E44", "1: Zweig Mitte (18–31)", 46.5, leg_y0),
        ("#7048E8", "2: Zweig Oben (32–44)", 15.0, leg_y0 + 4.8),
        ("#C2255C", "3: Stiel (45–49)", 46.5, leg_y0 + 4.8),
        ("#E8590C", "4/5: Stern Innen (50,53,54,57,58) / Außen (51,52,55,56,59)", 15.0, leg_y0 + 9.6),
    ]
    for col_hex, label, lx, ly in leg_items:
        lines.append(f'  <circle cx="{lx:.1f}" cy="{ly-0.7:.1f}" r="1.0" fill="{col_hex}"/>')
        lines.append(
            f'  <text x="{lx+2.1:.1f}" y="{ly:.1f}" font-family="{FONT_SANS}" font-size="1.92" fill="#343A40">{esc(label)}</text>'
        )

    # Top-Right Card: Pixelgruppen & Segmente zeichnen (X=83, Y=32, W=115, H=132)
    seg_x, seg_y, seg_w, seg_h = 83.0, 32.0, 115.0, 132.0
    draw_card(lines, seg_x, seg_y, seg_w, seg_h, "9. Pixelgruppen färben (Segmente & VirtualSegment)", "tannenbaum_layout", "#0D6EFD")

    tbl_x = seg_x + 2.8
    tbl_y = seg_y + 9.2
    tbl_w = seg_w - 5.6
    lines.append(
        f'  <rect x="{tbl_x:.2f}" y="{tbl_y:.2f}" width="{tbl_w:.2f}" height="32.5" rx="1.2" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{tbl_x+2.0:.2f}" y="{tbl_y+3.8:.2f}" font-family="{FONT_SANS}" font-size="2.0" font-weight="bold" fill="#495057">ID</text>'
        f'  <text x="{tbl_x+8.5:.2f}" y="{tbl_y+3.8:.2f}" font-family="{FONT_SANS}" font-size="2.0" font-weight="bold" fill="#495057">Virtuelles Segment (6)</text>'
        f'  <text x="{tbl_x+44.5:.2f}" y="{tbl_y+3.8:.2f}" font-family="{FONT_SANS}" font-size="2.0" font-weight="bold" fill="#495057">Lineares Segment (5)</text>'
        f'  <text x="{tbl_x+75.5:.2f}" y="{tbl_y+3.8:.2f}" font-family="{FONT_SANS}" font-size="2.0" font-weight="bold" fill="#495057">LEDs (Nummern)</text>'
    )
    lines.append(
        f'  <line x1="{tbl_x:.2f}" y1="{tbl_y+5.2:.2f}" x2="{tbl_x+tbl_w:.2f}" y2="{tbl_y+5.2:.2f}" stroke="#DEE2E6" stroke-width="0.3"/>'
    )
    vseg_rows = [
        ("0", "VSEG_BOUGH_LOW", "SEG_BOUGH_LOW", "18 LEDs: 0..17 (Zweig Unten)"),
        ("1", "VSEG_BOUGH_MID", "SEG_BOUGH_MID", "14 LEDs: 18..31 (Zweig Mitte)"),
        ("2", "VSEG_BOUGH_HIGH", "SEG_BOUGH_HIGH", "13 LEDs: 32..44 (Zweig Oben)"),
        ("3", "VSEG_STEM", "SEG_STEM", "5 LEDs:  45..49 (Stiel)"),
        ("4", "VSEG_STAR_INNER", "SEG_STAR (50..59)", "5 LEDs:  (50, 53, 54, 57, 58) Innen"),
        ("5", "VSEG_STAR_OUTER", "SEG_STAR (50..59)", "5 LEDs:  (51, 52, 55, 56, 59) Außen"),
    ]
    for r_idx, (vid, vconst, sconst, desc) in enumerate(vseg_rows):
        ry = tbl_y + 9.0 + r_idx * 4.3
        lines.append(
            f'  <text x="{tbl_x+2.0:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.95" font-weight="bold" fill="#212529">{vid}</text>'
            f'  <text x="{tbl_x+8.5:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.95" font-weight="bold" fill="#0B5ED7">{vconst}</text>'
            f'  <text x="{tbl_x+44.5:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.9" fill="#495057">{sconst}</text>'
            f'  <text x="{tbl_x+75.5:.2f}" y="{ry:.2f}" font-family="{FONT_SANS}" font-size="1.9" fill="#212529">{esc(desc)}</text>'
        )

    draw_code_box(
        lines,
        seg_x + 2.8,
        seg_y + 43.5,
        seg_w - 5.6,
        [
            "from tannenbaum_layout import (",
            "    init_pixels, fill_seg, fill_vseg, VirtualSegment, VIRTUAL_SEGMENTS,",
            "    SEG_BOUGH_LOW, SEG_STAR, VSEG_STAR_INNER, VSEG_STAR_OUTER,",
            ")",
            "pixels = init_pixels(brightness=0.3)   # Startet & merkt sich pixels",
            "",
            "# A) Ganzes Segment auf einmal färben (Zweige, Stiel oder Stern):",
            "fill_seg(SEG_BOUGH_LOW, (0, 120, 20))  # Zweig Unten (0..17) dunkelgrün",
            "fill_seg(SEG_STAR, (255, 180, 0))      # Ganzer Stern (50..59) gold",
            "",
            "fill_vseg(VSEG_STAR_INNER, (255, 40, 0))   # Nur innerer Stern rot",
            "fill_vseg(VSEG_STAR_OUTER, (255, 220, 0))  # Nur äußere Spitzen gelb",
            "pixels.show()",
            "",
            "# B) VirtualSegment wie einen eigenen kleinen LED-Streifen nutzen:",
            "spitzen = VirtualSegment(VSEG_STAR_OUTER)  # 5 LEDs: (51, 52, 55, 56, 59)",
            "spitzen.fill((255, 60, 0))                 # Alle 5 Spitzen orange",
            "spitzen[2] = (255, 255, 255)               # 3. Spitze (LED 55) weiß!",
            "anzahl = len(spitzen)                      # -> 5",
            "pixels.show()",
            "",
            "# C) Schleife durch alle 6 Segmente nacheinander:",
            "for vseg_id in range(len(VIRTUAL_SEGMENTS)):",
            "    vseg = VirtualSegment(vseg_id)",
            "    for k in range(len(vseg)):             # k zählt 0 bis len(vseg)-1",
            "        vseg[k] = (0, 200, 255)",
        ],
        line_h=3.12,
        font_size=1.98,
        pad_y=1.8,
    )

    # Bottom-Left Card: Koordinaten, Wellen & Profi-Effekte (X=12, Y=167, W=91, H=119)
    geo_x, geo_y, geo_w, geo_h = 12.0, 167.0, 91.0, 119.0
    draw_card(lines, geo_x, geo_y, geo_w, geo_h, "10. Koordinaten, Wellen & Effekte", "tannenbaum_layout", "#6610F2")
    lines.append(
        f'  <text x="{geo_x+2.8:.2f}" y="{geo_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.1" fill="#495057">'
        'Jede LED <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">i</tspan> kennt ihre Position auf dem Baum — ideal für Farbverläufe &amp; Wellen:</text>'
    )
    draw_code_box(
        lines,
        geo_x + 2.6,
        geo_y + 13.2,
        geo_w - 5.2,
        [
            "from tannenbaum_layout import (",
            "    NORM_COORDS, PIXEL_COORDS, POLAR_TREE,",
            "    CENTER_STAR, CENTER_TREE, build_distance_lut, hsv_to_rgb_gamma,",
            ")",
            "",
            "# 1) Einfach: Position von 0.0 bis 1.0 (links->rechts, unten->oben)",
            "nx, ny = NORM_COORDS[i]             # ny=0.0 unten, ny=1.0 Spitze",
            "for i in range(60):                 # Regenbogen von unten nach oben",
            "    pixels[i] = hsv_to_rgb_gamma(NORM_COORDS[i][1], 1.0, 0.8)",
            "pixels.show()",
            "",
            "# 2) Kreiswelle: Abstand jeder LED zum Stern (einmal berechnen!)",
            "abstand = build_distance_lut(CENTER_STAR) # 60 Abstände in mm",
            "for i in range(60):",
            "    if abstand[i] < 25.0:           # Alle LEDs im 25mm-Kreis",
            "        pixels[i] = (255, 180, 0)",
            "",
            "# 3) Exakte Position in Millimetern + Segment-Nummer:",
            "x_mm, y_mm, seg_id = PIXEL_COORDS[i]",
            "",
            "# 4) Profi-Tipp für Spiralen & Wirbel (Abstand & Winkel zur Mitte):",
            "radius_mm, winkel = POLAR_TREE[i]   # Oder POLAR_STAR[i]",
        ],
        line_h=3.02,
        font_size=1.9,
        pad_y=1.7,
    )
    anc_y = geo_y + 89.2
    lines.append(
        f'  <rect x="{geo_x+2.6:.2f}" y="{anc_y:.2f}" width="{geo_w-5.2:.2f}" height="27.2" rx="1.2" fill="#F3F0FF" stroke="#D0BFFF" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{geo_x+4.2:.2f}" y="{anc_y+4.2:.2f}" font-family="{FONT_SANS}" font-size="2.05" font-weight="bold" fill="#5F3DC4">Wichtige Mittelpunkte für Wellen (EPICENTERS):</text>'
    )
    anc_rows = [
        ("CENTER_STAR", "(21.16, 61.90) mm", "Mitte des Sterns oben"),
        ("CENTER_STEM", "(23.75, 42.81) mm", "Mitte des Stiels unter dem Stern"),
        ("CENTER_TREE", "(19.43, 34.28) mm", "Mitte des gesamten Baums"),
        ("CENTER_BASE", "(20.58, 12.80) mm", "Mitte der unteren Zweige"),
        ("WIDTH_MM / HEIGHT_MM", "38.86 / 68.55 mm", "Breite & Höhe des LED-Felds"),
    ]
    for r_i, (k_name, k_val, k_desc) in enumerate(anc_rows):
        ry = anc_y + 8.3 + r_i * 4.1
        lines.append(
            f'  <text x="{geo_x+4.2:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.85" font-weight="bold" fill="#212529">{k_name}</text>'
            f'  <text x="{geo_x+29.5:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.82" fill="#5F3DC4">{k_val}</text>'
            f'  <text x="{geo_x+50.5:.2f}" y="{ry:.2f}" font-family="{FONT_SANS}" font-size="1.85" fill="#495057">{esc(k_desc)}</text>'
        )

    # Bottom-Right Card: Farbpaletten & TwinkleFOX-Engine (X=107, Y=167, W=91, H=119)
    pal_x, pal_y, pal_w, pal_h = 107.0, 167.0, 91.0, 119.0
    draw_card(lines, pal_x, pal_y, pal_w, pal_h, "11. Farbpaletten & TwinkleFOX-Glitzer", "tannenbaum_palettes", "#D63384")
    lines.append(
        f'  <text x="{pal_x+2.8:.2f}" y="{pal_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.1" fill="#495057">'
        'Fertige Weihnachtsfarben, 10 Paletten &amp; Funkel-Effekt mit einem Befehl:</text>'
    )
    draw_code_box(
        lines,
        pal_x + 2.6,
        pal_y + 13.2,
        pal_w - 5.2,
        [
            "import time",
            "from tannenbaum_palettes import (",
            "    PALETTES, PALETTE_NAMES, PAL_ICE, PAL_FAIRY_LIGHT,",
            "    color_from_palette, blend_palette_toward, render_twinkle_tree,",
            ")",
            "# Auch einzelne Farben fertig dabei: RED, GREEN, BLUE, WHITE,",
            "# BLACK, C9_RED, FAIRY_FULL, HOLLY_GRN, SNOW_WHITE, MAGENTA, ...",
            "",
            "# A) Sanften Farbverlauf (0..255) aus einer Palette holen:",
            "for i in range(60):",
            "    pixels[i] = color_from_palette(PAL_ICE, i * 255 // 59)",
            "pixels.show()",
            "",
            "# B) Ganzen Baum funkeln lassen (Stern in eigenem Warmgold):",
            "pal_idx = 0",
            "akt_pal = PALETTES[pal_idx]",
            "while True:",
            "    if btn_d5.pressed():                  # D5: nächste Palette",
            "        pal_idx = (pal_idx + 1) % len(PALETTES)",
            "        print(\"Palette:\", PALETTE_NAMES[pal_idx])",
            "    akt_pal = blend_palette_toward(akt_pal, PALETTES[pal_idx])",
            "    ms = int(time.monotonic() * 1000)     # Zeit in Millisekunden",
            "    render_twinkle_tree(",
            "        pixels, ms, akt_pal,",
            "        star_palette=PAL_FAIRY_LIGHT,     # Stern funkelt gold",
            "        speed=4, density=5                # 0 (sanft) bis 8 (wild)",
            "    )",
            "    pixels.show()",
        ],
        line_h=2.92,
        font_size=1.88,
        pad_y=1.6,
    )

    pt_y = pal_y + 98.2
    lines.append(
        f'  <rect x="{pal_x+2.6:.2f}" y="{pt_y:.2f}" width="{pal_w-5.2:.2f}" height="18.4" rx="1.2" fill="#FFF0F6" stroke="#FCC2D7" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{pal_x+4.2:.2f}" y="{pt_y+3.7:.2f}" font-family="{FONT_SANS}" font-size="1.95" font-weight="bold" fill="#A61E4D">Die 10 Paletten in PALETTES[0..9]:</text>'
    )
    pal_left = [
        "0: PAL_RETRO_C9 (Retro C9)",
        "1: PAL_HOLLY (Tannengrün/Beeren)",
        "2: PAL_FAIRY_LIGHT (Warmgold)",
        "3: PAL_RED_GREEN_WHITE",
        "4: PAL_RED_WHITE (Zuckerstange)",
    ]
    pal_right = [
        "5: PAL_SNOW (Glitzerschnee)",
        "6: PAL_ICE (Eis-Kristall)",
        "7: PAL_BLUE_WHITE (Winternacht)",
        "8: PAL_RAINBOW (Regenbogen)",
        "9: PAL_MAGENTA_GREEN",
    ]
    for r_i in range(5):
        ry = pt_y + 6.9 + r_i * 2.65
        lines.append(
            f'  <text x="{pal_x+4.2:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.72" fill="#212529">{esc(pal_left[r_i])}</text>'
            f'  <text x="{pal_x+46.5:.2f}" y="{ry:.2f}" font-family="{FONT_MONO}" font-size="1.72" fill="#212529">{esc(pal_right[r_i])}</text>'
        )

    # Footer
    lines.append(
        f'  <text x="105" y="292.5" text-anchor="middle" font-family="{FONT_SANS}" font-size="2.45" fill="#6C757D">'
        'AITY Weihnachtsbaum 2026 · CircuitPython Cheatsheet (Seite 2/2: Tannenbaum-Bibliotheken) · Lizenz: CC-BY-NC-4.0</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main():
    leds, polylines, outline_d = parse_leds_svg(LEDS_SVG)

    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "page1.svg"
        p2 = Path(tmpdir) / "page2.svg"
        p1.write_text(build_page1_svg(), encoding="utf-8")
        p2.write_text(build_page2_svg(leds, polylines, outline_d), encoding="utf-8")
        subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", str(OUT_PDF), str(p1), str(p2)],
            check=True,
        )
    print(f"Generated {OUT_PDF}")


if __name__ == "__main__":
    main()
