#!/usr/bin/env python3
"""
Generate circuitpython/cheatsheet_colors_a4.pdf directly from:
  - circuitpython/lib/tannenbaum_palettes.py

Requires `rsvg-convert` (librsvg2-bin).
"""

import ast
import colorsys
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PALETTES_PY = HERE / "lib" / "tannenbaum_palettes.py"
OUT_PDF = HERE / "cheatsheet_colors_a4.pdf"

sys.path.insert(0, str(HERE / "lib"))
import tannenbaum_palettes as tp  # noqa: E402

FONT_SANS = "DejaVu Sans, Arial, sans-serif"
FONT_MONO = "DejaVu Sans Mono, monospace"

PALETTE_CONST_NAMES = (
    "PAL_RETRO_C9",
    "PAL_HOLLY",
    "PAL_FAIRY_LIGHT",
    "PAL_RED_GREEN_WHITE",
    "PAL_RED_WHITE",
    "PAL_SNOW",
    "PAL_ICE",
    "PAL_BLUE_WHITE",
    "PAL_RAINBOW",
    "PAL_MAGENTA_GREEN",
)


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def rgb_to_hex(rgb) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def parse_single_colors(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    colors = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if isinstance(node.value, ast.Tuple) and len(node.value.elts) == 3:
            if all(
                isinstance(e, ast.Constant) and isinstance(e.value, int)
                for e in node.value.elts
            ):
                r, g, b = (e.value for e in node.value.elts)
                if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                    colors.append((target.id, (r, g, b), f"#{r:02X}{g:02X}{b:02X}"))
    return colors


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


def draw_code_box(lines, x, y, w, code_lines, line_h=3.05, font_size=1.95, pad_y=1.7):
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


def build_page1_svg(single_colors) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
        '  <rect width="210" height="297" fill="#FFFFFF"/>',
        # Header
        f'  <text x="12" y="16.5" font-family="{FONT_SANS}" font-size="3.75" font-weight="bold" fill="#212529">AITY Weihnachtsbaum 2026 — Farben &amp; Paletten (1/2)</text>',
        f'  <text x="198" y="16.5" text-anchor="end" font-family="{FONT_SANS}" font-size="2.45" fill="#6C757D">tannenbaum_palettes.py · {len(single_colors)} Einzelfarben · RGB &amp; HSV</text>',
        '  <rect x="12" y="20.5" width="186" height="8.5" rx="1.5" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>',
        f'  <text x="15" y="25.8" font-family="{FONT_SANS}" font-size="2.3" fill="#495057">'
        f'Start: <tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">from tannenbaum_palettes import RED, C9_RED, FAIRY_FULL, ...</tspan>'
        f'  ·  <tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">from tannenbaum_layout import hsv_to_rgb_gamma</tspan></text>',
    ]

    # Card 1: All 27 Single Colors (X=12, Y=32, W=186, H=96)
    c1_x, c1_y, c1_w, c1_h = 12.0, 32.0, 186.0, 96.0
    draw_card(lines, c1_x, c1_y, c1_w, c1_h, f"1. Alle {len(single_colors)} fertigen Farbkonstanten", "tannenbaum_palettes", "#D63384")
    lines.append(
        f'  <text x="{c1_x+2.8:.2f}" y="{c1_y+11.0:.2f}" font-family="{FONT_SANS}" font-size="2.1" fill="#495057">'
        'Jede Konstante ist ein fertiges <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">(R, G, B)</tspan>-Tupel — direkt einsetzbar mit <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">pixels[i] = FARBE</tspan> oder <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">pixels.fill(FARBE)</tspan>:</text>'
    )

    cols = 3
    rows_per_col = (len(single_colors) + cols - 1) // cols
    col_xs = [15.5, 76.5, 137.5]
    row_y0 = c1_y + 14.0
    row_step = 7.6
    sw_w, sw_h = 8.6, 5.4

    for idx, (name, (r, g, b), hex_c) in enumerate(single_colors):
        col = idx // rows_per_col
        row = idx % rows_per_col
        cx = col_xs[col]
        ry = row_y0 + row * row_step
        if row > 0:
            lines.append(
                f'  <line x1="{cx:.1f}" y1="{ry-1.1:.2f}" x2="{cx+57.5:.1f}" y2="{ry-1.1:.2f}" stroke="#F1F3F5" stroke-width="0.28"/>'
            )
        lines.append(
            f'  <rect x="{cx:.1f}" y="{ry:.2f}" width="{sw_w:.1f}" height="{sw_h:.1f}" rx="1.0" fill="{hex_c}" stroke="#ADB5BD" stroke-width="0.3"/>'
        )
        lines.append(
            f'  <text x="{cx+10.5:.1f}" y="{ry+2.45:.2f}" font-family="{FONT_MONO}" font-size="2.15" font-weight="bold" fill="#212529">{esc(name)}</text>'
        )
        lines.append(
            f'  <text x="{cx+10.5:.1f}" y="{ry+4.95:.2f}" font-family="{FONT_MONO}" font-size="1.8" fill="#6C757D">({r}, {g}, {b}) · {hex_c}</text>'
        )

    bg_y = c1_y + 83.2
    lines.append(
        f'  <rect x="{c1_x+2.6:.2f}" y="{bg_y:.2f}" width="{c1_w-5.2:.2f}" height="10.4" rx="1.2" fill="#FFF0F6" stroke="#FCC2D7" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{c1_x+4.2:.2f}" y="{bg_y+4.1:.2f}" font-family="{FONT_SANS}" font-size="1.95" fill="#212529">'
        f'<tspan font-weight="bold" fill="#A61E4D">Hinweis zu dunklen Farben &amp; BG_*:</tspan> '
        f'<tspan font-family="{FONT_MONO}" font-weight="bold">BG_DARK_GREEN</tspan>, <tspan font-family="{FONT_MONO}" font-weight="bold">BG_WARM_DARK</tspan> &amp; <tspan font-family="{FONT_MONO}" font-weight="bold">BG_BLACK</tspan> sind extra dunkel als Hintergrund für TwinkleFOX.</text>'
    )
    lines.append(
        f'  <text x="{c1_x+4.2:.2f}" y="{bg_y+8.1:.2f}" font-family="{FONT_SANS}" font-size="1.95" fill="#495057">'
        f'Glühlampen-Töne (<tspan font-family="{FONT_MONO}">C9_*</tspan>, <tspan font-family="{FONT_MONO}">FAIRY_*</tspan>) wirken auf NeoPixel-LEDs viel wärmer und natürlicher als auf dem Bildschirm.</text>'
    )

    # Card 2 (Bottom-Left): RGB-Farben mischen & dimmen (X=12, Y=131, W=91, H=155)
    c2_x, c2_y, c2_w, c2_h = 12.0, 131.0, 91.0, 155.0
    draw_card(lines, c2_x, c2_y, c2_w, c2_h, "2. RGB-Farben mischen & dimmen", "Farbmodell", "#0D6EFD")
    lines.append(
        f'  <text x="{c2_x+2.8:.2f}" y="{c2_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.08" fill="#495057">'
        'Jede LED mischt <tspan font-weight="bold" fill="#C92A2A">Rot</tspan>, <tspan font-weight="bold" fill="#2B8A3E">Grün</tspan> &amp; <tspan font-weight="bold" fill="#1864AB">Blau</tspan> (je <tspan font-family="DejaVu Sans Mono, monospace">0..255</tspan>). So entstehen Mischfarben:</text>'
    )

    # Custom color mix swatches (3x2 grid)
    mix_samples = [
        ("Gold", (255, 180, 0)),
        ("Warmweiß", (255, 200, 120)),
        ("Türkis", (0, 220, 200)),
        ("Rosa", (255, 80, 160)),
        ("Lila", (160, 0, 255)),
        ("Orange", (255, 90, 0)),
    ]
    for m_i, (m_name, m_rgb) in enumerate(mix_samples):
        mc = m_i % 3
        mr = m_i // 3
        mx = c2_x + 2.8 + mc * 29.0
        my = c2_y + 13.8 + mr * 9.8
        lines.append(
            f'  <rect x="{mx:.2f}" y="{my:.2f}" width="6.2" height="6.2" rx="1.0" fill="{rgb_to_hex(m_rgb)}" stroke="#ADB5BD" stroke-width="0.28"/>'
        )
        lines.append(
            f'  <text x="{mx+7.4:.2f}" y="{my+2.6:.2f}" font-family="{FONT_SANS}" font-size="1.95" font-weight="bold" fill="#212529">{esc(m_name)}</text>'
        )
        lines.append(
            f'  <text x="{mx+7.4:.2f}" y="{my+5.4:.2f}" font-family="{FONT_MONO}" font-size="1.65" fill="#6C757D">{m_rgb}</text>'
        )

    # Additive RGB visual strip
    add_y = c2_y + 34.5
    lines.append(
        f'  <rect x="{c2_x+2.6:.2f}" y="{add_y:.2f}" width="{c2_w-5.2:.2f}" height="15.0" rx="1.2" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{c2_x+4.2:.2f}" y="{add_y+3.8:.2f}" font-family="{FONT_SANS}" font-size="1.95" font-weight="bold" fill="#212529">Lichtfarben mischen (additiv):</text>'
    )
    add_items = [
        ("#FF0000", "#00FF00", "#FFFF00", "Rot + Grün = Gelb"),
        ("#FF0000", "#0000FF", "#FF00FF", "Rot + Blau = Magenta"),
        ("#00FF00", "#0000FF", "#00FFFF", "Grün + Blau = Cyan"),
        ("#FF0000", "#00FF00", "#FFFFFF", "Alle 3 = Weiß"),
    ]
    for a_i, (c_a, c_b, c_res, a_lbl) in enumerate(add_items):
        ax = c2_x + 4.2 + (a_i % 2) * 42.5
        ay = add_y + 6.0 + (a_i // 2) * 4.4
        lines.append(f'  <circle cx="{ax+1.4:.2f}" cy="{ay+1.2:.2f}" r="1.25" fill="{c_a}" stroke="#ADB5BD" stroke-width="0.2"/>')
        lines.append(f'  <circle cx="{ax+4.4:.2f}" cy="{ay+1.2:.2f}" r="1.25" fill="{c_b}" stroke="#ADB5BD" stroke-width="0.2"/>')
        lines.append(f'  <circle cx="{ax+7.4:.2f}" cy="{ay+1.2:.2f}" r="1.25" fill="{c_res}" stroke="#ADB5BD" stroke-width="0.2"/>')
        lines.append(f'  <text x="{ax+10.0:.2f}" y="{ay+1.85:.2f}" font-family="{FONT_SANS}" font-size="1.8" fill="#343A40">{esc(a_lbl)}</text>')

    code_end2 = draw_code_box(
        lines,
        c2_x + 2.6,
        c2_y + 52.0,
        c2_w - 5.2,
        [
            "# 1) Farbe abdunkeln (// 2 = ganzzahlig teilen):",
            "r, g, b = (255, 120, 0)",
            "dunkel = (r // 2, g // 2, b // 2)   # -> (127, 60, 0)",
            "",
            "# 2) Zwei Farben sanft mischen (t = 0.0 bis 1.0):",
            "def mische(f1, f2, t=0.5):",
            "    r = int(f1[0] * (1 - t) + f2[0] * t)",
            "    g = int(f1[1] * (1 - t) + f2[1] * t)",
            "    b = int(f1[2] * (1 - t) + f2[2] * t)",
            "    return (r, g, b)",
            "",
            "# Beispiel: 30% Rot + 70% Blau:",
            "pixels.fill(mische((255, 0, 0), (0, 0, 255), 0.7))",
            "",
            "# 3) Gesamthelligkeit aller 60 LEDs begrenzen:",
            "pixels = init_pixels(brightness=0.3) # 30% am Start",
            "pixels.brightness = 0.5              # Später ändern",
            "pixels.show()",
        ],
        line_h=3.02,
        font_size=1.9,
        pad_y=1.6,
    )

    tip2_y = code_end2 + 2.8
    lines.append(
        f'  <rect x="{c2_x+2.6:.2f}" y="{tip2_y:.2f}" width="{c2_w-5.2:.2f}" height="{c2_y+c2_h-tip2_y-2.6:.2f}" rx="1.2" fill="#FFF9DB" stroke="#FFE066" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{c2_x+4.2:.2f}" y="{tip2_y+4.2:.2f}" font-family="{FONT_SANS}" font-size="2.0" font-weight="bold" fill="#212529">Tipp: Warum nicht brightness=1.0?</text>'
    )
    lines.append(
        f'  <text x="{c2_x+4.2:.2f}" y="{tip2_y+8.4:.2f}" font-family="{FONT_SANS}" font-size="1.9" fill="#343A40">'
        '60 LEDs auf 100% blenden stark und brauchen viel USB-Strom.</text>'
    )
    lines.append(
        f'  <text x="{c2_x+4.2:.2f}" y="{tip2_y+12.4:.2f}" font-family="{FONT_SANS}" font-size="1.9" fill="#343A40">'
        'Mit <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">brightness=0.2</tspan> bis <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">0.4</tspan> leuchten Farben am besten!</text>'
    )

    # Card 3 (Bottom-Right): Regenbogen mit HSV (X=107, Y=131, W=91, H=155)
    c3_x, c3_y, c3_w, c3_h = 107.0, 131.0, 91.0, 155.0
    draw_card(lines, c3_x, c3_y, c3_w, c3_h, "3. Regenbogen mit HSV", "hsv_to_rgb_gamma", "#198754")
    lines.append(
        f'  <text x="{c3_x+2.8:.2f}" y="{c3_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.08" fill="#495057">'
        'Statt RGB einzeln gibst du <tspan font-weight="bold" fill="#212529">Farbton (h)</tspan>, <tspan font-weight="bold" fill="#212529">Sättigung (s)</tspan> &amp; <tspan font-weight="bold" fill="#212529">Helligkeit (v)</tspan> an:</text>'
    )

    # Hue spectrum bar (60 segments)
    bar_x = c3_x + 2.8
    bar_y = c3_y + 13.8
    bar_w = c3_w - 5.6
    bar_h = 6.2
    steps = 60
    seg_w = bar_w / steps
    for k in range(steps):
        h_val = k / (steps - 1)
        r_f, g_f, b_f = colorsys.hsv_to_rgb(h_val, 1.0, 1.0)
        hex_k = rgb_to_hex((int(r_f * 255), int(g_f * 255), int(b_f * 255)))
        lines.append(
            f'  <rect x="{bar_x + k * seg_w:.3f}" y="{bar_y:.2f}" width="{seg_w + 0.12:.3f}" height="{bar_h:.2f}" fill="{hex_k}"/>'
        )
    lines.append(
        f'  <rect x="{bar_x:.2f}" y="{bar_y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" rx="0.8" fill="none" stroke="#ADB5BD" stroke-width="0.3"/>'
    )

    hue_ticks = [
        (0.0, "0.0 Rot"),
        (0.17, "0.17 Gelb"),
        (0.33, "0.33 Grün"),
        (0.50, "0.50 Cyan"),
        (0.67, "0.67 Blau"),
        (0.83, "0.83 Mag."),
        (1.0, "1.0"),
    ]
    for frac, lbl in hue_ticks:
        tx = bar_x + frac * bar_w
        anchor = "start" if frac == 0.0 else ("end" if frac == 1.0 else "middle")
        lines.append(
            f'  <line x1="{tx:.2f}" y1="{bar_y+bar_h:.2f}" x2="{tx:.2f}" y2="{bar_y+bar_h+1.2:.2f}" stroke="#495057" stroke-width="0.3"/>'
        )
        lines.append(
            f'  <text x="{tx:.2f}" y="{bar_y+bar_h+3.4:.2f}" text-anchor="{anchor}" font-family="{FONT_SANS}" font-size="1.68" fill="#495057">{esc(lbl)}</text>'
        )

    # S and V mini gradient bars
    sv_y = c3_y + 26.2
    half_w = (bar_w - 4.0) / 2.0
    lines.append(
        f'  <text x="{bar_x:.2f}" y="{sv_y+2.2:.2f}" font-family="{FONT_SANS}" font-size="1.78" font-weight="bold" fill="#212529">s (Sättigung): 0.0 Weiß → 1.0 Satt</text>'
    )
    lines.append(
        f'  <text x="{bar_x+half_w+4.0:.2f}" y="{sv_y+2.2:.2f}" font-family="{FONT_SANS}" font-size="1.78" font-weight="bold" fill="#212529">v (Helligkeit): 0.0 Aus → 1.0 Hell</text>'
    )
    for k in range(30):
        t = k / 29.0
        r_s, g_s, b_s = colorsys.hsv_to_rgb(0.60, t, 1.0)
        r_v, g_v, b_v = colorsys.hsv_to_rgb(0.60, 1.0, t)
        sw_k = half_w / 30.0
        lines.append(
            f'  <rect x="{bar_x + k * sw_k:.3f}" y="{sv_y+3.3:.2f}" width="{sw_k + 0.1:.3f}" height="3.2" fill="{rgb_to_hex((int(r_s*255), int(g_s*255), int(b_s*255)))}"/>'
        )
        lines.append(
            f'  <rect x="{bar_x + half_w + 4.0 + k * sw_k:.3f}" y="{sv_y+3.3:.2f}" width="{sw_k + 0.1:.3f}" height="3.2" fill="{rgb_to_hex((int(r_v*255), int(g_v*255), int(b_v*255)))}"/>'
        )
    lines.append(
        f'  <rect x="{bar_x:.2f}" y="{sv_y+3.3:.2f}" width="{half_w:.2f}" height="3.2" rx="0.5" fill="none" stroke="#ADB5BD" stroke-width="0.25"/>'
    )
    lines.append(
        f'  <rect x="{bar_x+half_w+4.0:.2f}" y="{sv_y+3.3:.2f}" width="{half_w:.2f}" height="3.2" rx="0.5" fill="none" stroke="#ADB5BD" stroke-width="0.25"/>'
    )

    code_end3 = draw_code_box(
        lines,
        c3_x + 2.6,
        c3_y + 35.5,
        c3_w - 5.2,
        [
            "import time",
            "from tannenbaum_layout import (",
            "    NUM_PIXELS, NORM_COORDS, hsv_to_rgb_gamma,",
            ")",
            "",
            "# A) Eine einzelne Regenbogen-Farbe:",
            "pixels[0] = hsv_to_rgb_gamma(0.33, 1.0, 0.8)  # Grün",
            "",
            "# B) Statischer Regenbogen über alle 60 LEDs:",
            "for i in range(NUM_PIXELS):",
            "    pixels[i] = hsv_to_rgb_gamma(i / 60, 1.0, 0.8)",
            "pixels.show()",
            "",
            "# C) Laufender Regenbogen von unten nach oben:",
            "while True:",
            "    shift = time.monotonic() * 0.25",
            "    for i in range(NUM_PIXELS):",
            "        h = (NORM_COORDS[i][1] + shift) % 1.0",
            "        pixels[i] = hsv_to_rgb_gamma(h, 1.0, 0.8)",
            "    pixels.show()",
        ],
        line_h=2.95,
        font_size=1.88,
        pad_y=1.6,
    )

    tip3_y = code_end3 + 2.8
    lines.append(
        f'  <rect x="{c3_x+2.6:.2f}" y="{tip3_y:.2f}" width="{c3_w-5.2:.2f}" height="{c3_y+c3_h-tip3_y-2.6:.2f}" rx="1.2" fill="#E6FCF5" stroke="#96F2D7" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{c3_x+4.2:.2f}" y="{tip3_y+4.2:.2f}" font-family="{FONT_SANS}" font-size="2.0" font-weight="bold" fill="#087F5B">Warum heißt es hsv_to_rgb_gamma?</text>'
    )
    lines.append(
        f'  <text x="{c3_x+4.2:.2f}" y="{tip3_y+8.4:.2f}" font-family="{FONT_SANS}" font-size="1.9" fill="#212529">'
        'Das menschliche Auge sieht Helligkeit nicht linear — eine</text>'
    )
    lines.append(
        f'  <text x="{c3_x+4.2:.2f}" y="{tip3_y+12.2:.2f}" font-family="{FONT_SANS}" font-size="1.9" fill="#212529">'
        'halb so große Zahl wirkt auf LEDs noch fast gleich hell.</text>'
    )
    lines.append(
        f'  <text x="{c3_x+4.2:.2f}" y="{tip3_y+16.0:.2f}" font-family="{FONT_SANS}" font-size="1.9" fill="#212529">'
        '<tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold">_gamma</tspan> korrigiert das für sanfte Pastell- &amp; Farbverläufe.</text>'
    )

    # Footer
    lines.append(
        f'  <text x="105" y="292.5" text-anchor="middle" font-family="{FONT_SANS}" font-size="2.45" fill="#6C757D">'
        'AITY Weihnachtsbaum 2026 · Farben-Cheatsheet (Seite 1/2: Einzelfarben, RGB &amp; HSV) · Lizenz: CC-BY-NC-4.0</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def build_page2_svg() -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
        '  <rect width="210" height="297" fill="#FFFFFF"/>',
        # Header
        f'  <text x="12" y="16.5" font-family="{FONT_SANS}" font-size="3.75" font-weight="bold" fill="#212529">AITY Weihnachtsbaum 2026 — Farben &amp; Paletten (2/2)</text>',
        f'  <text x="198" y="16.5" text-anchor="end" font-family="{FONT_SANS}" font-size="2.45" fill="#6C757D">10 Farbpaletten · Verläufe · TwinkleFOX-Glitzer</text>',
        '  <rect x="12" y="20.5" width="186" height="8.5" rx="1.5" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>',
        f'  <text x="15" y="25.8" font-family="{FONT_SANS}" font-size="2.3" fill="#495057">'
        f'Paletten: <tspan font-family="{FONT_MONO}" font-weight="bold" fill="#212529">from tannenbaum_palettes import PALETTES, PALETTE_NAMES, color_from_palette, render_twinkle_tree</tspan></text>',
    ]

    # Card 4 (Top, full width): All 10 Color Palettes (X=12, Y=32, W=186, H=132)
    c4_x, c4_y, c4_w, c4_h = 12.0, 32.0, 186.0, 132.0
    draw_card(lines, c4_x, c4_y, c4_w, c4_h, "4. Die 10 fertigen Farbpaletten (PALETTES[0..9])", "16 Einträge + Verlauf", "#6610F2")

    sw_x0 = 76.0
    sw_w = 6.6
    sw_gap = 0.7
    sw_h = 5.6
    total_pal_w = 16 * sw_w + 15 * sw_gap

    lines.append(
        f'  <text x="15.5" y="{c4_y+12.2:.2f}" font-family="{FONT_SANS}" font-size="2.0" font-weight="bold" fill="#495057">Palette / Konstante</text>'
    )
    for col in range(16):
        cx = sw_x0 + col * (sw_w + sw_gap) + sw_w / 2.0
        lines.append(
            f'  <text x="{cx:.2f}" y="{c4_y+12.2:.2f}" text-anchor="middle" font-family="{FONT_MONO}" font-size="2.0" fill="#6C757D">{col}</text>'
        )

    row_y0 = c4_y + 14.5
    row_step = 11.4

    for p_idx, (pal, p_name, const_name) in enumerate(zip(tp.PALETTES, tp.PALETTE_NAMES, PALETTE_CONST_NAMES)):
        ry = row_y0 + p_idx * row_step
        if p_idx > 0:
            lines.append(
                f'  <line x1="15.5" y1="{ry-1.45:.2f}" x2="194.0" y2="{ry-1.45:.2f}" stroke="#F1F3F5" stroke-width="0.3"/>'
            )
        lines.append(
            f'  <text x="15.5" y="{ry+2.9:.2f}" font-family="{FONT_SANS}" font-size="2.35" font-weight="bold" fill="#212529">{p_idx}: {esc(p_name)}</text>'
        )
        lines.append(
            f'  <text x="15.5" y="{ry+6.2:.2f}" font-family="{FONT_MONO}" font-size="1.9" fill="#5F3DC4">{esc(const_name)}</text>'
        )

        # 16 discrete swatches
        for col, rgb in enumerate(pal):
            sx = sw_x0 + col * (sw_w + sw_gap)
            lines.append(
                f'  <rect x="{sx:.2f}" y="{ry:.2f}" width="{sw_w:.2f}" height="{sw_h:.2f}" rx="0.8" fill="{rgb_to_hex(rgb)}" stroke="#ADB5BD" stroke-width="0.24"/>'
            )

        # Smooth interpolated gradient strip underneath (blend=True)
        grad_y = ry + sw_h + 0.75
        grad_steps = 64
        g_step_w = total_pal_w / grad_steps
        for gs in range(grad_steps):
            idx_255 = int(gs * 255 / (grad_steps - 1))
            g_rgb = tp.color_from_palette(pal, idx_255, blend=True)
            lines.append(
                f'  <rect x="{sw_x0 + gs * g_step_w:.3f}" y="{grad_y:.2f}" width="{g_step_w + 0.1:.3f}" height="2.0" fill="{rgb_to_hex(g_rgb)}"/>'
            )
        lines.append(
            f'  <rect x="{sw_x0:.2f}" y="{grad_y:.2f}" width="{total_pal_w:.2f}" height="2.0" rx="0.4" fill="none" stroke="#CED4DA" stroke-width="0.2"/>'
        )

    # Card 5 (Bottom-Left): Paletten nutzen & eigene bauen (X=12, Y=167, W=91, H=119)
    c5_x, c5_y, c5_w, c5_h = 12.0, 167.0, 91.0, 119.0
    draw_card(lines, c5_x, c5_y, c5_w, c5_h, "5. Paletten nutzen & eigene bauen", "color_from_palette", "#FD7E14")

    # Visual comparison: blend=False vs blend=True on PAL_ICE
    comp_x = c5_x + 2.8
    comp_w = c5_w - 5.6
    comp_y = c5_y + 10.2
    lines.append(
        f'  <text x="{comp_x:.2f}" y="{comp_y+1.8:.2f}" font-family="{FONT_SANS}" font-size="1.9" font-weight="bold" fill="#212529">Unterschied bei <tspan font-family="{FONT_MONO}">color_from_palette(PAL_ICE, idx)</tspan>:</text>'
    )
    # blend=False
    lines.append(
        f'  <text x="{comp_x:.2f}" y="{comp_y+6.0:.2f}" font-family="{FONT_MONO}" font-size="1.78" fill="#495057">blend=False (16 Stufen):</text>'
    )
    b_bar_x = comp_x + 36.5
    b_bar_w = comp_w - 36.5
    for k in range(60):
        idx_255 = int(k * 255 / 59)
        c_no = tp.color_from_palette(tp.PAL_ICE, idx_255, blend=False)
        c_yes = tp.color_from_palette(tp.PAL_ICE, idx_255, blend=True)
        kw = b_bar_w / 60.0
        lines.append(f'  <rect x="{b_bar_x + k*kw:.3f}" y="{comp_y+3.5:.2f}" width="{kw+0.08:.3f}" height="3.6" fill="{rgb_to_hex(c_no)}"/>')
        lines.append(f'  <rect x="{b_bar_x + k*kw:.3f}" y="{comp_y+8.2:.2f}" width="{kw+0.08:.3f}" height="3.6" fill="{rgb_to_hex(c_yes)}"/>')
    lines.append(
        f'  <text x="{comp_x:.2f}" y="{comp_y+10.7:.2f}" font-family="{FONT_MONO}" font-size="1.78" fill="#495057">blend=True  (Verlauf):</text>'
    )
    lines.append(f'  <rect x="{b_bar_x:.2f}" y="{comp_y+3.5:.2f}" width="{b_bar_w:.2f}" height="3.6" rx="0.5" fill="none" stroke="#ADB5BD" stroke-width="0.22"/>')
    lines.append(f'  <rect x="{b_bar_x:.2f}" y="{comp_y+8.2:.2f}" width="{b_bar_w:.2f}" height="3.6" rx="0.5" fill="none" stroke="#ADB5BD" stroke-width="0.22"/>')

    code_end5 = draw_code_box(
        lines,
        c5_x + 2.6,
        c5_y + 24.5,
        c5_w - 5.2,
        [
            "from tannenbaum_palettes import (",
            "    PALETTES, PAL_ICE, RED, WHITE,",
            "    color_from_palette, blend_palette_toward,",
            ")",
            "",
            "# A) Farbverlauf über alle 60 LEDs (Index 0..255):",
            "for i in range(60):",
            "    idx = i * 255 // 59          # 0 unten .. 255 oben",
            "    pixels[i] = color_from_palette(PAL_ICE, idx)",
            "pixels.show()",
            "",
            "# B) Eigene Palette (muss genau 16 Farben haben!):",
            "GOLD = (255, 180, 0)",
            "MEINE_PAL = (RED,) * 8 + (GOLD,) * 8",
            "",
            "# C) Sanft zur nächsten Palette überblenden:",
            "akt_pal = blend_palette_toward(akt_pal, PALETTES[2])",
        ],
        line_h=3.0,
        font_size=1.88,
        pad_y=1.6,
    )

    tip5_y = code_end5 + 2.5
    lines.append(
        f'  <rect x="{c5_x+2.6:.2f}" y="{tip5_y:.2f}" width="{c5_w-5.2:.2f}" height="{c5_y+c5_h-tip5_y-2.6:.2f}" rx="1.2" fill="#FFF4E6" stroke="#FFD8A8" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{c5_x+4.2:.2f}" y="{tip5_y+4.4:.2f}" font-family="{FONT_SANS}" font-size="1.95" font-weight="bold" fill="#D9480F">So funktioniert der Index 0..255:</text>'
    )
    lines.append(
        f'  <text x="{c5_x+4.2:.2f}" y="{tip5_y+9.0:.2f}" font-family="{FONT_SANS}" font-size="1.85" fill="#212529">'
        'Jeder der 16 Einträge belegt 16 Schritte (0..15 = Feld 0, 240..255 = Feld 15).</text>'
    )
    lines.append(
        f'  <text x="{c5_x+4.2:.2f}" y="{tip5_y+13.2:.2f}" font-family="{FONT_SANS}" font-size="1.85" fill="#212529">'
        'Mit <tspan font-family="DejaVu Sans Mono, monospace">brightness=128</tspan> dimmst du die Farbe direkt beim Auslesen.</text>'
    )
    lines.append(
        f'  <text x="{c5_x+4.2:.2f}" y="{tip5_y+17.4:.2f}" font-family="{FONT_SANS}" font-size="1.85" fill="#212529">'
        'Tipp für eigene Streifen: <tspan font-family="DejaVu Sans Mono, monospace">(RED, WHITE) * 8</tspan> wechselt 8× ab.</text>'
    )
    lines.append(
        f'  <text x="{c5_x+4.2:.2f}" y="{tip5_y+21.6:.2f}" font-family="{FONT_SANS}" font-size="1.85" fill="#212529">'
        'Mit <tspan font-family="DejaVu Sans Mono, monospace">blend=False</tspan> erhältst du harte Farbsprünge statt Verläufe.</text>'
    )

    # Card 6 (Bottom-Right): TwinkleFOX-Glitzer & Effekte (X=107, Y=167, W=91, H=119)
    c6_x, c6_y, c6_w, c6_h = 107.0, 167.0, 91.0, 119.0
    draw_card(lines, c6_x, c6_y, c6_w, c6_h, "6. TwinkleFOX-Glitzer & Effekte", "render_twinkle_tree", "#20C997")
    lines.append(
        f'  <text x="{c6_x+2.8:.2f}" y="{c6_y+11.2:.2f}" font-family="{FONT_SANS}" font-size="2.05" fill="#495057">'
        'Funkelnde LEDs ohne Speicher-Array — ideal für echte Weihnachtsstimmung:</text>'
    )

    code_end6 = draw_code_box(
        lines,
        c6_x + 2.6,
        c6_y + 13.4,
        c6_w - 5.2,
        [
            "import time",
            "from tannenbaum_palettes import (",
            "    PAL_HOLLY, PAL_FAIRY_LIGHT, BG_DARK_GREEN,",
            "    render_twinkle_tree, compute_one_twinkle,",
            ")",
            "",
            "# A) Ganzer Baum (Zweige + eigener goldener Stern):",
            "while True:",
            "    ms = int(time.monotonic() * 1000)",
            "    render_twinkle_tree(",
            "        pixels, ms,",
            "        branch_palette=PAL_HOLLY,",
            "        star_palette=PAL_FAIRY_LIGHT,",
            "        speed=4, density=5,",
            "        bg_color=BG_DARK_GREEN,   # Dezentes Grün",
            "    )",
            "    pixels.show()",
            "",
            "# B) Nur 1 Pixel funkeln lassen:",
            "pixels[55] = compute_one_twinkle(ms, 55, PAL_FAIRY_LIGHT)",
        ],
        line_h=2.92,
        font_size=1.86,
        pad_y=1.5,
    )

    p6_y = code_end6 + 2.5
    lines.append(
        f'  <rect x="{c6_x+2.6:.2f}" y="{p6_y:.2f}" width="{c6_w-5.2:.2f}" height="{c6_y+c6_h-p6_y-2.6:.2f}" rx="1.2" fill="#E6FCF5" stroke="#96F2D7" stroke-width="0.3"/>'
    )
    lines.append(
        f'  <text x="{c6_x+4.2:.2f}" y="{p6_y+4.1:.2f}" font-family="{FONT_SANS}" font-size="1.95" font-weight="bold" fill="#087F5B">TwinkleFOX-Parameter im Überblick:</text>'
    )
    tw_params = [
        ("speed (0..8)", "Funkel-Tempo (Standard: 4, 8 = sehr schnell)"),
        ("density (0..8)", "Funkel-Dichte (Standard: 5, 8 = alle LEDs)"),
        ("star_palette", "Eigene Palette nur für den Stern (LEDs 50..59)"),
        ("bg_color", "Hintergrund: BG_BLACK, BG_DARK_GREEN, BG_WARM_DARK"),
        ("cool_incandescent", "True = warmes Ausglühen wie bei Glühlampen"),
    ]
    for t_i, (p_k, p_v) in enumerate(tw_params):
        ty = p6_y + 8.1 + t_i * 4.15
        lines.append(
            f'  <text x="{c6_x+4.2:.2f}" y="{ty:.2f}" font-family="{FONT_MONO}" font-size="1.8" font-weight="bold" fill="#212529">{esc(p_k)}</text>'
            f'  <text x="{c6_x+27.5:.2f}" y="{ty:.2f}" font-family="{FONT_SANS}" font-size="1.8" fill="#343A40">{esc(p_v)}</text>'
        )

    # Footer
    lines.append(
        f'  <text x="105" y="292.5" text-anchor="middle" font-family="{FONT_SANS}" font-size="2.45" fill="#6C757D">'
        'AITY Weihnachtsbaum 2026 · Farben-Cheatsheet (Seite 2/2: Farbpaletten &amp; TwinkleFOX) · Lizenz: CC-BY-NC-4.0</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main():
    single_colors = parse_single_colors(PALETTES_PY)

    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "page1.svg"
        p2 = Path(tmpdir) / "page2.svg"
        p1.write_text(build_page1_svg(single_colors), encoding="utf-8")
        p2.write_text(build_page2_svg(), encoding="utf-8")
        subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", str(OUT_PDF), str(p1), str(p2)],
            check=True,
        )
    print(f"Generated {OUT_PDF} from {PALETTES_PY.name}")


if __name__ == "__main__":
    main()
