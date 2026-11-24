#!/usr/bin/env python3
"""
Generator für geprüfte 1:1 Verpackungsvorlagen (SVG, Maße in Millimetern)
für den 10 cm AITY Weihnachtsbaum 2026.

Wichtige konstruktive Verbesserungen aus dem KiCad-Hardware-Audit:
  1. Bereinigte Einzel-Außenkontur (entfernt die doppelte Innenkontur & Umkehr-Spikes
     aus docs/pcb_outline.js, damit Lasercutter nicht doppelt schneiden!).
  2. Echter geometrischer Parallel-Offset (+1.0 mm) für das Kontur-Inlay statt
     ungleichmäßiger Zentrums-Skalierung.
  3. Korrekte XIAO-Einbaulage (B.Cu, rot=180° -> USB-C zeigt nach OBEN bei Y≈66.2 mm!):
     Rückseiten-Aussparung nach oben erweitert (24 × 33 mm) für USB-C-Überstand.
  4. Konischer Wurzelstamm (14.0 mm oben -> 18.17 mm unten): Klemm-Standfuß mit
     1.75 mm Klemmschlitzen von unten + integriertem Sternhals-Aufhängeclip (9.9 mm Hals).
  5. Direkte Weltkoordinaten (keine verschachtelten SVG-Transforms auf Schnittpfaden)
     für maximale Kompatibilität mit LightBurn, Inkscape & Schneideplottern.

Erzeugte Dateien in packaging/templates/:
  - inlay_foam_1to1.svg               (Variante C & D: 2-lagiges Inlay mit +1 mm Offset)
  - folding_box_125x95x20_dieline.svg (Variante B: Faltschachtel 125x95x20 mm auf DIN A4)
  - flat_mail_card_a6.svg             (Variante A: DIN-A6 Klappkarte + Asttal-Laschen + Clip)
  - stand_insert_1to1.svg             (Variante B/D/F: Klemm-Standfuß + Sternhals-Aufhängeclip)
  - lantern_sleeve_125x90x18.svg      (Variante G: Diffusor-Laternen-Schuber auf DIN A4)
  - laser_slide_box_3mm.svg           (Variante D: 3-mm-Sperrholz Schiebebox mit Fingerzinken)
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB_OUTLINE_JS = ROOT / "docs" / "pcb_outline.js"
OUT_DIR = Path(__file__).resolve().parent / "templates"

# Exakte Koordinaten aus KiCad (lokal zum viewBox-Ursprung aus docs/pcb_outline.js)
TREE_MIN_X = 3.00
TREE_MAX_X = 72.41
TREE_MIN_Y = 3.00
TREE_MAX_Y = 102.60
TREE_CX = (TREE_MIN_X + TREE_MAX_X) / 2.0  # 37.705 mm
TREE_CY = (TREE_MIN_Y + TREE_MAX_Y) / 2.0  # 52.80 mm

# Rückseitige Bauteile (B.Cu, rot=180°):
# XIAO Zentrum (36.87, 77.87); USB-C ragt nach OBEN bis Y = 77.87 - 11.7 = 66.17 mm!
XIAO_X, XIAO_Y = 36.87, 77.87
BUZZER_X, BUZZER_Y = 47.02, 59.27


def load_clean_outer_polygon() -> list[tuple[float, float]]:
    """Extrahiert ausschließlich die äußere Platinenkontur ohne innere Goldrand-Schleife."""
    txt = PCB_OUTLINE_JS.read_text(encoding="utf-8")
    m = re.search(r"XMAS_PCB_OUTLINE\s*=\s*(\{.*\});?", txt, re.S)
    if not m:
        raise RuntimeError(f"Konnte XMAS_PCB_OUTLINE in {PCB_OUTLINE_JS} nicht finden.")
    data = json.loads(m.group(1))
    pts = [(float(x), float(y)) for x, y in re.findall(r"([0-9.]+)\s+([0-9.]+)", data["edgePath"])]
    # Indizes 0..119 = rechte Außenhälfte (Stern -> Stamm -> linke Astspitze 3.00, 82.86)
    # Indizes 120..304 = innere Offset-Kontur (wird übersprungen!)
    # Indizes 305..375 = linke Außenhälfte zurück zur Sternspitze
    raw_outer = pts[0:120] + pts[305:376]

    # Entferne Mikro-Duplikate und Umkehr-Spikes (< 0.05 mm)
    poly = raw_outer
    changed = True
    while changed:
        changed = False
        out: list[tuple[float, float]] = []
        for p in poly:
            if out and math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) < 0.05:
                changed = True
                continue
            if len(out) >= 2 and math.hypot(p[0] - out[-2][0], p[1] - out[-2][1]) < 0.05:
                out.pop()
                changed = True
                continue
            out.append(p)
        poly = out
    return poly


def offset_polygon(
    poly: list[tuple[float, float]], offset_mm: float, miter_limit: float = 1.8
) -> list[tuple[float, float]]:
    """Berechnet einen echten Parallel-Offset (+ nach außen, - nach innen) für ein CW-Polygon (Y nach unten)."""
    n = len(poly)
    out: list[tuple[float, float]] = []
    for i in range(n):
        p_prev = poly[(i - 1) % n]
        p_curr = poly[i]
        p_next = poly[(i + 1) % n]
        dx1, dy1 = p_curr[0] - p_prev[0], p_curr[1] - p_prev[1]
        dx2, dy2 = p_next[0] - p_curr[0], p_next[1] - p_curr[1]
        l1 = math.hypot(dx1, dy1)
        l2 = math.hypot(dx2, dy2)
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        # Außen-Normalen für im Uhrzeigersinn (Y-down) umlaufendes Polygon
        n1 = (dy1 / l1, -dx1 / l1)
        n2 = (dy2 / l2, -dx2 / l2)
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        bl = math.hypot(bx, by)
        if bl < 1e-4:
            out.append((p_curr[0] + n1[0] * offset_mm, p_curr[1] + n1[1] * offset_mm))
        else:
            bx /= bl
            by /= bl
            dot = bx * n1[0] + by * n1[1]
            scale = min(miter_limit, 1.0 / max(dot, 0.25))
            out.append((p_curr[0] + bx * offset_mm * scale, p_curr[1] + by * offset_mm * scale))
    return out


def poly_to_svg_path(poly: list[tuple[float, float]], target_cx: float, target_cy: float) -> str:
    """Backt die Zielposition direkt in Millimeter-Koordinaten (keine nested transforms)."""
    dx = target_cx - TREE_CX
    dy = target_cy - TREE_CY
    cmds = [f"M {poly[0][0] + dx:.2f} {poly[0][1] + dy:.2f}"]
    cmds.extend(f"L {x + dx:.2f} {y + dy:.2f}" for x, y in poly[1:])
    cmds.append("Z")
    return " ".join(cmds)


def svg_header(width_mm: float, height_mm: float, title: str) -> str:
    safe_title = title.replace("&", "&amp;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{width_mm:.2f}mm" height="{height_mm:.2f}mm"
     viewBox="0 0 {width_mm:.2f} {height_mm:.2f}">
  <title>{safe_title}</title>
  <style>
    .cut {{ fill: none; stroke: #d00000; stroke-width: 0.22; stroke-linejoin: round; stroke-linecap: round; }}
    .fold {{ fill: none; stroke: #0055cc; stroke-width: 0.22; stroke-dasharray: 3,2; }}
    .perf {{ fill: none; stroke: #d00000; stroke-width: 0.22; stroke-dasharray: 1.8,1.2; }}
    .engrave {{ fill: none; stroke: #2b6cb0; stroke-width: 0.2; stroke-linejoin: round; }}
    .ref {{ fill: none; stroke: #888888; stroke-width: 0.18; stroke-dasharray: 1.5,1.5; }}
    .guide {{ fill: none; stroke: #444444; stroke-width: 0.2; }}
    .label {{ font-family: sans-serif; font-size: 3.1px; fill: #333333; }}
    .label-sm {{ font-family: sans-serif; font-size: 2.3px; fill: #555555; }}
    .title {{ font-family: sans-serif; font-size: 4.3px; font-weight: bold; fill: #1b4332; }}
  </style>
"""


def calibration_bar(x: float, y: float, length_mm: float = 50.0) -> str:
    return f"""  <g id="calibration">
    <line x1="{x:.2f}" y1="{y:.2f}" x2="{x + length_mm:.2f}" y2="{y:.2f}" class="guide"/>
    <line x1="{x:.2f}" y1="{y - 1.5:.2f}" x2="{x:.2f}" y2="{y + 1.5:.2f}" class="guide"/>
    <line x1="{x + length_mm:.2f}" y1="{y - 1.5:.2f}" x2="{x + length_mm:.2f}" y2="{y + 1.5:.2f}" class="guide"/>
    <text x="{x + length_mm / 2:.2f}" y="{y - 1.8:.2f}" text-anchor="middle" class="label-sm">Kalibrierung: exakt {length_mm:.0f} mm (1:1 ohne Skalierung drucken/lasern)</text>
  </g>
"""


def star_hanger_clip_svg(cx: float, cy: float) -> str:
    """
    Kleiner Aufhänge-Clip (20 x 22 mm) für den 9.9 mm schmalen Sternhals (da PCB kein Bohrloch hat).
    Oben Ø 4 mm Loch für Goldkordel/Christbaumhaken, unten C-förmige Klammer mit 9.6 mm Rast-Öffnung.
    """
    w, h = 20.0, 22.0
    x0, y0 = cx - w / 2.0, cy - h / 2.0
    # Außenkontur mit unterem Einführ-Schlitz (7.8 mm Engstelle -> schnappt auf 10.2 mm Sternhals-Tasche)
    outer = (
        f"M {cx - 3.9:.2f},{y0 + h:.2f} "
        f"L {x0 + 2.5:.2f},{y0 + h:.2f} "
        f"Q {x0:.2f},{y0 + h:.2f} {x0:.2f},{y0 + h - 2.5:.2f} "
        f"L {x0:.2f},{y0 + 7.0:.2f} "
        f"Q {x0:.2f},{y0:.2f} {cx:.2f},{y0:.2f} "
        f"Q {x0 + w:.2f},{y0:.2f} {x0 + w:.2f},{y0 + 7.0:.2f} "
        f"L {x0 + w:.2f},{y0 + h - 2.5:.2f} "
        f"Q {x0 + w:.2f},{y0 + h:.2f} {x0 + w - 2.5:.2f},{y0 + h:.2f} "
        f"L {cx + 3.9:.2f},{y0 + h:.2f} "
        f"L {cx + 3.9:.2f},{y0 + h - 3.2:.2f} "
        f"L {cx + 5.3:.2f},{y0 + h - 4.5:.2f} "
        f"L {cx + 5.3:.2f},{y0 + 10.5:.2f} "
        f"L {cx - 5.3:.2f},{y0 + 10.5:.2f} "
        f"L {cx - 5.3:.2f},{y0 + h - 4.5:.2f} "
        f"L {cx - 3.9:.2f},{y0 + h - 3.2:.2f} Z"
    )
    return f"""  <g id="star_hanger_clip">
    <path d="{outer}" class="cut"/>
    <circle cx="{cx:.2f}" cy="{y0 + 5.0:.2f}" r="2.10" class="cut"/>
    <text x="{cx:.2f}" y="{y0 + h + 3.5:.2f}" text-anchor="middle" class="label-sm">Stern-Aufhängeclip</text>
  </g>"""


def generate_inlay_foam(outer_poly: list[tuple[float, float]]) -> None:
    """Variante C & D: 2-lagiges Schaumstoff-/Karton-Inlay (je 95 x 130 mm) mit echtem +1.0 mm Offset."""
    inlay_w, inlay_h = 95.0, 130.0
    margin = 10.0
    gap = 12.0
    page_w = margin * 2 + inlay_w * 2 + gap
    page_h = margin * 2 + inlay_h + 18.0

    l1_x, l1_y = margin, margin + 10.0
    l2_x, l2_y = margin + inlay_w + gap, margin + 10.0

    cx1, cy1 = l1_x + inlay_w / 2.0, l1_y + inlay_h / 2.0
    cx2, cy2 = l2_x + inlay_w / 2.0, l2_y + inlay_h / 2.0

    offset_poly = offset_polygon(outer_poly, 1.0)
    cut_tree_d = poly_to_svg_path(offset_poly, cx1, cy1)
    ref_tree_d = poly_to_svg_path(outer_poly, cx2, cy2)

    # Rückseitige Aussparungen auf Lage 2:
    # XIAO (36.87, 77.87), USB-C zeigt nach OBEN (Y=66.2)!
    # Wir erstrecken das XIAO-Fenster von lokal Y = 60.0 (Platz für USB-C-Überstand) bis Y = 91.0 (31 mm hoch, 24 mm breit)
    xiao_win_x = cx2 + (XIAO_X - TREE_CX) - 12.0
    xiao_win_y = cy2 + (60.0 - TREE_CY)
    xiao_win_w, xiao_win_h = 24.0, 31.0

    buz_cx = cx2 + (BUZZER_X - TREE_CX)
    buz_cy = cy2 + (BUZZER_Y - TREE_CY)
    buz_w, buz_h = 13.0, 13.0

    # Finger-Greifmulden auf Höhe der mittleren Ast-Taille (lokal Y = 53 mm -> cy1)
    notch_y = cy1
    notch_r = 8.5

    parts = [
        svg_header(page_w, page_h, "AITY Weihnachtsbaum 2026 - 2-lagiges Inlay 1:1 (Geprüft)"),
        f'  <text x="{margin:.2f}" y="7.5" class="title">AITY Weihnachtsbaum 2026 – 2-lagiges Inlay (1:1, 95 × 130 mm)</text>',
        f'  <text x="{margin:.2f}" y="11.5" class="label-sm">Bereinigte Einzelkontur mit echtem +1,0 mm Parallel-Offset • XIAO-Fenster nach oben für USB-C erweitert</text>',
        f'  <g id="layer1_top">',
        f'    <rect x="{l1_x:.2f}" y="{l1_y:.2f}" width="{inlay_w:.2f}" height="{inlay_h:.2f}" rx="3" ry="3" class="cut"/>',
        f'    <path d="{cut_tree_d}" class="cut"/>',
        f'    <circle cx="{cx1 - 29.5:.2f}" cy="{notch_y:.2f}" r="{notch_r:.2f}" class="cut"/>',
        f'    <circle cx="{cx1 + 29.5:.2f}" cy="{notch_y:.2f}" r="{notch_r:.2f}" class="cut"/>',
        f'    <text x="{cx1:.2f}" y="{l1_y + 6.0:.2f}" text-anchor="middle" class="label">LAGE 1 (Oben): +1,0 mm Parallel-Kontur</text>',
        f'    <text x="{cx1:.2f}" y="{l1_y + inlay_h - 4.0:.2f}" text-anchor="middle" class="label-sm">2 Finger-Greifmulden (Ø 17 mm) an der mittleren Ast-Taille</text>',
        f'  </g>',
        f'  <g id="layer2_bottom">',
        f'    <rect x="{l2_x:.2f}" y="{l2_y:.2f}" width="{inlay_w:.2f}" height="{inlay_h:.2f}" rx="3" ry="3" class="cut"/>',
        f'    <path d="{ref_tree_d}" class="ref"/>',
        f'    <rect x="{xiao_win_x:.2f}" y="{xiao_win_y:.2f}" width="{xiao_win_w:.2f}" height="{xiao_win_h:.2f}" rx="2" ry="2" class="cut"/>',
        f'    <rect x="{buz_cx - buz_w/2:.2f}" y="{buz_cy - buz_h/2:.2f}" width="{buz_w:.2f}" height="{buz_h:.2f}" rx="1.5" ry="1.5" class="cut"/>',
        f'    <text x="{xiao_win_x + xiao_win_w/2:.2f}" y="{xiao_win_y + 18.0:.2f}" text-anchor="middle" class="label-sm">XIAO + USB-C ↑</text>',
        f'    <text x="{buz_cx:.2f}" y="{buz_cy + 1.0:.2f}" text-anchor="middle" class="label-sm">Buzzer</text>',
        f'    <text x="{cx2:.2f}" y="{l2_y + 6.0:.2f}" text-anchor="middle" class="label">LAGE 2 (Unten): Flächige FR4-Auflage</text>',
        f'    <text x="{cx2:.2f}" y="{l2_y + inlay_h - 4.0:.2f}" text-anchor="middle" class="label-sm">Aussparung XIAO+USB-C (24×31 mm) &amp; Buzzer (13×13 mm)</text>',
        f'  </g>',
        calibration_bar(margin, page_h - 4.5, 50.0),
        "</svg>\n",
    ]
    (OUT_DIR / "inlay_foam_1to1.svg").write_text("\n".join(parts), encoding="utf-8")


def generate_folding_box_dieline(outer_poly: list[tuple[float, float]]) -> None:
    """Variante B: 1:1 Stanzvorlage (Dieline) für Klappdeckel-Faltschachtel 125 x 95 x 20 mm auf DIN A4."""
    page_w, page_h = 297.0, 210.0
    L, W, H, tuck = 125.0, 95.0, 20.0, 15.0

    total_w = tuck + W + H + W + H  # 245 mm
    total_h = H + L + H             # 165 mm
    x0 = (page_w - total_w) / 2.0
    y0 = (page_h - total_h) / 2.0 + 4.0

    x_tuck = x0
    x_lid = x_tuck + tuck
    x_spine = x_lid + W
    x_base = x_spine + H
    x_front = x_base + W
    x_end = x_front + H

    y_top = y0
    y_body_top = y0 + H
    y_body_bot = y_body_top + L
    y_bot = y_body_bot + H
    dust_w = 16.0

    # Daumen-Öffnungsmulde an der Vorderwand (halbrund R=7 mm) zum leichten Öffnen
    mid_y = (y_body_top + y_body_bot) / 2.0

    cut_paths = [
        f"M {x_lid:.2f},{y_body_top:.2f} L {x_tuck + 3:.2f},{y_body_top + 2:.2f} "
        f"Q {x_tuck:.2f},{y_body_top + 2:.2f} {x_tuck:.2f},{y_body_top + 5:.2f} "
        f"L {x_tuck:.2f},{y_body_bot - 5:.2f} "
        f"Q {x_tuck:.2f},{y_body_bot - 2:.2f} {x_tuck + 3:.2f},{y_body_bot - 2:.2f} "
        f"L {x_lid:.2f},{y_body_bot:.2f}",
        f"M {x_lid:.2f},{y_body_top:.2f} L {x_spine:.2f},{y_body_top:.2f}",
        f"M {x_lid:.2f},{y_body_bot:.2f} L {x_spine:.2f},{y_body_bot:.2f}",
        f"M {x_spine:.2f},{y_body_top:.2f} L {x_spine + 2:.2f},{y_body_top - dust_w:.2f} "
        f"L {x_base - 2:.2f},{y_body_top - dust_w:.2f} L {x_base:.2f},{y_body_top:.2f}",
        f"M {x_spine:.2f},{y_body_bot:.2f} L {x_spine + 2:.2f},{y_body_bot + dust_w:.2f} "
        f"L {x_base - 2:.2f},{y_body_bot + dust_w:.2f} L {x_base:.2f},{y_body_bot:.2f}",
        f"M {x_base:.2f},{y_body_top:.2f} L {x_base:.2f},{y_top:.2f} "
        f"L {x_front:.2f},{y_top:.2f} L {x_front:.2f},{y_body_top:.2f}",
        f"M {x_base:.2f},{y_body_bot:.2f} L {x_base:.2f},{y_bot:.2f} "
        f"L {x_front:.2f},{y_bot:.2f} L {x_front:.2f},{y_body_bot:.2f}",
        f"M {x_front:.2f},{y_body_top:.2f} L {x_front + 2:.2f},{y_body_top - dust_w:.2f} "
        f"L {x_end - 2:.2f},{y_body_top - dust_w:.2f} L {x_end:.2f},{y_body_top:.2f} "
        f"L {x_end:.2f},{mid_y - 7:.2f} A 7 7 0 0 0 {x_end:.2f},{mid_y + 7:.2f} "
        f"L {x_end:.2f},{y_body_bot:.2f} L {x_end - 2:.2f},{y_body_bot + dust_w:.2f} "
        f"L {x_front + 2:.2f},{y_body_bot + dust_w:.2f} L {x_front:.2f},{y_body_bot:.2f}",
    ]

    fold_lines = [
        (x_lid, y_body_top, x_lid, y_body_bot),
        (x_spine, y_body_top, x_spine, y_body_bot),
        (x_base, y_body_top, x_base, y_body_bot),
        (x_front, y_body_top, x_front, y_body_bot),
        (x_spine, y_body_top, x_end, y_body_top),
        (x_spine, y_body_bot, x_end, y_body_bot),
    ]

    base_cx, base_cy = x_base + W / 2.0, y_body_top + L / 2.0
    lid_cx, lid_cy = x_lid + W / 2.0, y_body_top + L / 2.0
    ref_tree_d = poly_to_svg_path(outer_poly, base_cx, base_cy)

    parts = [
        svg_header(page_w, page_h, "AITY Weihnachtsbaum 2026 - Faltschachtel 125x95x20 mm (DIN A4)"),
        '  <text x="12" y="10" class="title">Variante B: Faltschachtel 125 × 95 × 20 mm (CH B4 / DE Großbrief, passt 1:1 auf DIN A4)</text>',
        '  <text x="12" y="14.5" class="label-sm">Rot = Schnitt (inkl. Griffmulde rechts) • Blau = Falz • Für Versand im Umschlag H von 20 auf 16 mm reduzieren</text>',
        '  <g id="cuts">',
        *[f'    <path d="{p}" class="cut"/>' for p in cut_paths],
        '  </g>',
        '  <g id="folds">',
        *[f'    <line x1="{a:.2f}" y1="{b:.2f}" x2="{c:.2f}" y2="{d:.2f}" class="fold"/>' for a, b, c, d in fold_lines],
        '  </g>',
        '  <g id="reference">',
        f'    <path d="{ref_tree_d}" class="ref"/>',
        f'    <text x="{lid_cx:.2f}" y="{lid_cy - 4:.2f}" text-anchor="middle" class="label">DECKEL (95 × 125 mm)</text>',
        f'    <text x="{lid_cx:.2f}" y="{lid_cy + 2:.2f}" text-anchor="middle" class="label-sm">Außen: AITY XMAS 2026 • Innen: Widmung</text>',
        f'    <text x="{x_spine + H/2:.2f}" y="{lid_cy:.2f}" text-anchor="middle" transform="rotate(-90 {x_spine + H/2:.2f} {lid_cy:.2f})" class="label-sm">RÜCKEN (20 mm)</text>',
        f'    <text x="{base_cx:.2f}" y="{y_body_top + 7:.2f}" text-anchor="middle" class="label">BODEN (95 × 125 mm)</text>',
        f'    <text x="{x_front + H/2:.2f}" y="{lid_cy:.2f}" text-anchor="middle" transform="rotate(-90 {x_front + H/2:.2f} {lid_cy:.2f})" class="label-sm">VORDERWAND (20 mm)</text>',
        f'    <text x="{x_tuck + tuck/2:.2f}" y="{lid_cy:.2f}" text-anchor="middle" transform="rotate(-90 {x_tuck + tuck/2:.2f} {lid_cy:.2f})" class="label-sm">LASCHE</text>',
        '  </g>',
        calibration_bar(12.0, page_h - 5.5, 100.0),
        "</svg>\n",
    ]
    (OUT_DIR / "folding_box_125x95x20_dieline.svg").write_text("\n".join(parts), encoding="utf-8")


def generate_flat_mail_card_a6(outer_poly: list[tuple[float, float]]) -> None:
    """
    Variante A: DIN-A6 Klappkarte (offen 210 x 148 mm) mit überprüften Haltelaschen
    in den natürlichen Ast-Tälern (Y_lokal = 39.5 mm & 88.5 mm) + herausdrückbarem Stern-Clip.
    """
    card_w, card_h = 210.0, 148.0
    margin = 10.0
    page_w = card_w + 2 * margin
    page_h = card_h + 2 * margin + 14.0

    x0, y0 = margin, margin + 8.0
    fold_x = x0 + card_w / 2.0

    tree_cx = fold_x + 52.5
    tree_cy = y0 + card_h / 2.0 - 2.0
    ref_tree_d = poly_to_svg_path(outer_poly, tree_cx, tree_cy)

    # Geprüfte Haltelaschen in den Ast-Einschnürungen (verdecken KEINE LEDs!):
    # 1) Obere Ast-Taille bei lokal Y = 39.5 mm (Breite dort 25.0 mm -> X = ±12.5 mm)
    y_waist_top = tree_cy + (39.5 - TREE_CY)
    # 2) Untere Stamm-Taille unter den untersten Ästen bei lokal Y = 88.8 mm (Breite dort 14.0 mm -> X = ±7.0 mm)
    y_waist_bot = tree_cy + (88.8 - TREE_CY)

    # C-förmige Einstecklaschen links/rechts in den beiden Taillen (halten den Baum formschlüssig!)
    tab_cuts = [
        # Oben links & rechts
        f"M {tree_cx - 17.5:.2f},{y_waist_top - 4.0:.2f} L {tree_cx - 11.5:.2f},{y_waist_top - 2.5:.2f} "
        f"L {tree_cx - 11.5:.2f},{y_waist_top + 2.5:.2f} L {tree_cx - 17.5:.2f},{y_waist_top + 4.0:.2f}",
        f"M {tree_cx + 17.5:.2f},{y_waist_top - 4.0:.2f} L {tree_cx + 11.5:.2f},{y_waist_top - 2.5:.2f} "
        f"L {tree_cx + 11.5:.2f},{y_waist_top + 2.5:.2f} L {tree_cx + 17.5:.2f},{y_waist_top + 4.0:.2f}",
        # Unten links & rechts (Stamm-Hals)
        f"M {tree_cx - 13.0:.2f},{y_waist_bot - 3.5:.2f} L {tree_cx - 6.8:.2f},{y_waist_bot - 2.0:.2f} "
        f"L {tree_cx - 6.8:.2f},{y_waist_bot + 4.0:.2f} L {tree_cx - 13.0:.2f},{y_waist_bot + 5.0:.2f}",
        f"M {tree_cx + 13.0:.2f},{y_waist_bot - 3.5:.2f} L {tree_cx + 6.8:.2f},{y_waist_bot - 2.0:.2f} "
        f"L {tree_cx + 6.8:.2f},{y_waist_bot + 4.0:.2f} L {tree_cx + 13.0:.2f},{y_waist_bot + 5.0:.2f}",
    ]
    tab_folds = [
        (tree_cx - 17.5, y_waist_top - 4.0, tree_cx - 17.5, y_waist_top + 4.0),
        (tree_cx + 17.5, y_waist_top - 4.0, tree_cx + 17.5, y_waist_top + 4.0),
        (tree_cx - 13.0, y_waist_bot - 3.5, tree_cx - 13.0, y_waist_bot + 5.0),
        (tree_cx + 13.0, y_waist_bot - 3.5, tree_cx + 13.0, y_waist_bot + 5.0),
    ]

    xiao_win_x = tree_cx + (XIAO_X - TREE_CX) - 12.0
    xiao_win_y = tree_cy + (60.0 - TREE_CY)

    parts = [
        svg_header(page_w, page_h, "AITY Weihnachtsbaum 2026 - Flat-Mail Klappkarte A6 (1:1)"),
        f'  <text x="{margin:.2f}" y="7.5" class="title">Variante A: „Flat-Mail“ DIN-A6 Klappkarte (offen 210 × 148 mm, geprüft)</text>',
        f'  <text x="{margin:.2f}" y="11.5" class="label-sm">4 C-Haltelaschen greifen exakt in die Ast-Taillen (verdecken 0 LEDs) • Gestrichelt = XIAO/USB-C Zone hinten</text>',
        f'  <rect x="{x0:.2f}" y="{y0:.2f}" width="{card_w:.2f}" height="{card_h:.2f}" class="cut"/>',
        f'  <line x1="{fold_x:.2f}" y1="{y0:.2f}" x2="{fold_x:.2f}" y2="{y0 + card_h:.2f}" class="fold"/>',
        f'  <g id="inside_left">',
        f'    <text x="{x0 + 52.5:.2f}" y="{y0 + 16:.2f}" text-anchor="middle" class="title">Frohe Weihnachten!</text>',
        f'    <text x="{x0 + 52.5:.2f}" y="{y0 + 22:.2f}" text-anchor="middle" class="label-sm">Dein AITY Weihnachtsbaum 2026 • 60 NeoPixel &amp; Musik</text>',
        f'    <rect x="{x0 + 12:.2f}" y="{y0 + 28:.2f}" width="81" height="54" rx="3" ry="3" class="ref"/>',
        f'    <text x="{x0 + 52.5:.2f}" y="{y0 + 56:.2f}" text-anchor="middle" class="label-sm">Platz für persönliche Widmung</text>',
        f'    <rect x="{x0 + 12:.2f}" y="{y0 + 90:.2f}" width="30" height="30" rx="2" ry="2" class="ref"/>',
        f'    <text x="{x0 + 27:.2f}" y="{y0 + 106:.2f}" text-anchor="middle" class="label-sm">WLAN-QR</text>',
        f'    <text x="{x0 + 46:.2f}" y="{y0 + 97:.2f}" class="label-sm">1. USB-C hinten oben einstecken</text>',
        f'    <text x="{x0 + 46:.2f}" y="{y0 + 104:.2f}" class="label-sm">2. WLAN „AITY-XMAS“ verbinden</text>',
        f'    <text x="{x0 + 46:.2f}" y="{y0 + 111:.2f}" class="label-sm">3. 9 Goldkugeln = Touch-Pins!</text>',
        f'    <text x="{x0 + 52.5:.2f}" y="{y0 + 136:.2f}" text-anchor="middle" class="label-sm">Nur 5V USB • Kein Spielzeug &lt; 3 J. • Elektronik-Recycling</text>',
        f'  </g>',
        f'  <g id="inside_right">',
        f'    <path d="{ref_tree_d}" class="ref"/>',
        *[f'    <path d="{p}" class="cut"/>' for p in tab_cuts],
        *[f'    <line x1="{a:.2f}" y1="{b:.2f}" x2="{c:.2f}" y2="{d:.2f}" class="fold"/>' for a, b, c, d in tab_folds],
        f'    <rect x="{xiao_win_x:.2f}" y="{xiao_win_y:.2f}" width="24.0" height="31.0" rx="2" ry="2" class="ref"/>',
        f'    <text x="{xiao_win_x + 12:.2f}" y="{xiao_win_y + 16:.2f}" text-anchor="middle" class="label-sm">XIAO + USB-C ↑</text>',
        f'    <text x="{tree_cx:.2f}" y="{y0 + 10:.2f}" text-anchor="middle" class="label">Baum-Halterung (4 Asttal-Laschen)</text>',
        f'  </g>',
        calibration_bar(margin, page_h - 4.5, 50.0),
        "</svg>\n",
    ]
    (OUT_DIR / "flat_mail_card_a6.svg").write_text("\n".join(parts), encoding="utf-8")


def generate_stand_insert() -> None:
    """
    Variante B, D & F: Geprüfter Klemm-Standfuß + Sternhals-Aufhängeclip (1:1).
    Löst das Problem des konischen Stamms (14.0 -> 18.17 mm):
    Zwei geschlitzte Stützwangen (Klemmschlitz 1.75 mm für 1.6 mm FR4) klemmen die
    Platine links/rechts am Stammfuß fest; die Mitte bleibt hinten frei für das USB-C-Kabel!
    """
    page_w, page_h = 185.0, 98.0
    margin = 10.0

    # Grundplatte: 74 x 46 mm (passt bequem in jede Box ab 95 x 125 mm)
    base_x, base_y = margin, margin + 12.0
    base_w, base_h = 74.0, 46.0

    # Stamm-Aufnahmenut in der Grundplatte: 19.0 x 1.8 mm (nimmt die 18.17 mm Unterkante sicher auf)
    pcb_slot_w, pcb_slot_h = 19.0, 1.8
    pcb_slot_x = base_x + (base_w - pcb_slot_w) / 2.0
    pcb_slot_y = base_y + 18.0

    # Zwei Steckschlitze links/rechts (Abstand 12 mm -> greifen genau in den 18.2 mm Stammfuß!)
    # für 2.0 mm Graupappe/Karton
    mat_t = 2.0
    cheek_slot_l = 18.0
    s1_x = base_x + (base_w / 2.0) - 7.5 - mat_t / 2.0
    s2_x = base_x + (base_w / 2.0) + 7.5 - mat_t / 2.0
    s_y = base_y + 11.0

    # Stützwangen mit vertikalem 1.75 mm Klemmschlitz von oben (10 mm tief) für das 1.6 mm FR4-Board!
    def slotted_cheek_path(ox: float, oy: float) -> str:
        # Breite 32 mm, Höhe 26 mm + 2 mm Bodenzapfen (18 mm lang, passend zu cheek_slot_l)
        # Oben bei X = ox + 11.0 sitzt der 1.75 mm breite, 10 mm tiefe Klemmschlitz für die Platine
        sx = ox + 10.12
        sw = 1.75
        return (
            f"M {ox:.2f},{oy + 24:.2f} "
            f"L {ox + 7:.2f},{oy + 24:.2f} "
            f"L {ox + 7:.2f},{oy + 26:.2f} "
            f"L {ox + 25:.2f},{oy + 26:.2f} "
            f"L {ox + 25:.2f},{oy + 24:.2f} "
            f"L {ox + 32:.2f},{oy + 24:.2f} "
            f"L {ox + 20:.2f},{oy:.2f} "
            f"L {sx + sw:.2f},{oy:.2f} "
            f"L {sx + sw:.2f},{oy + 10.5:.2f} "
            f"L {sx:.2f},{oy + 10.5:.2f} "
            f"L {sx:.2f},{oy:.2f} "
            f"L {ox + 6:.2f},{oy:.2f} Z"
        )

    c1_x, c1_y = base_x + base_w + 12.0, base_y
    c2_x, c2_y = base_x + base_w + 12.0, base_y + 30.0
    clip_cx, clip_cy = base_x + base_w + 64.0, base_y + 22.0

    parts = [
        svg_header(page_w, page_h, "AITY Weihnachtsbaum 2026 - Klemm-Standfuß & Sternclip 1:1"),
        f'  <text x="{margin:.2f}" y="8" class="title">Klemm-Standfuß &amp; Sternhals-Aufhängeclip (1:1, geprüft)</text>',
        f'  <text x="{margin:.2f}" y="12.5" class="label-sm">1,75 mm FR4-Klemmschlitze halten den konischen Stamm (14→18,2 mm) spielfrei • Inkl. Sternclip (9,9 mm Hals)</text>',
        f'  <g id="stand_base">',
        f'    <rect x="{base_x:.2f}" y="{base_y:.2f}" width="{base_w:.2f}" height="{base_h:.2f}" rx="4" ry="4" class="cut"/>',
        f'    <rect x="{pcb_slot_x:.2f}" y="{pcb_slot_y:.2f}" width="{pcb_slot_w:.2f}" height="{pcb_slot_h:.2f}" rx="0.4" ry="0.4" class="cut"/>',
        f'    <rect x="{s1_x:.2f}" y="{s_y:.2f}" width="{mat_t:.2f}" height="{cheek_slot_l:.2f}" class="cut"/>',
        f'    <rect x="{s2_x:.2f}" y="{s_y:.2f}" width="{mat_t:.2f}" height="{cheek_slot_l:.2f}" class="cut"/>',
        f'    <text x="{base_x + base_w/2:.2f}" y="{base_y + 7:.2f}" text-anchor="middle" class="label">Grundplatte (74 × 46 mm)</text>',
        f'    <text x="{base_x + base_w/2:.2f}" y="{base_y + base_h - 4:.2f}" text-anchor="middle" class="label-sm">Mitte hinten offen für USB-C Bogen</text>',
        f'  </g>',
        f'  <g id="stand_cheeks">',
        f'    <path d="{slotted_cheek_path(c1_x, c1_y)}" class="cut"/>',
        f'    <text x="{c1_x + 16:.2f}" y="{c1_y + 21:.2f}" text-anchor="middle" class="label-sm">Klemmwange L</text>',
        f'    <path d="{slotted_cheek_path(c2_x, c2_y)}" class="cut"/>',
        f'    <text x="{c2_x + 16:.2f}" y="{c2_y + 21:.2f}" text-anchor="middle" class="label-sm">Klemmwange R</text>',
        f'  </g>',
        star_hanger_clip_svg(clip_cx, clip_cy),
        calibration_bar(margin, page_h - 5.0, 50.0),
        "</svg>\n",
    ]
    (OUT_DIR / "stand_insert_1to1.svg").write_text("\n".join(parts), encoding="utf-8")


def generate_lantern_sleeve(outer_poly: list[tuple[float, float]]) -> None:
    """
    Variante G (NEU): „Laternen-Sleeve“ Diffusor-Schuber (125 x 90 x 18 mm, großbrieftauglich!).
    Abwicklung des Außenschubers passt auf DIN A4 (297 x 210 mm):
    Breite = 90 (Front) + 18 (Seite) + 90 (Rückseite) + 18 (Seite) + 15 (Klebelasche) = 231 mm.
    Front hat ein ausgestanztes Baum-Sichtfenster (+1.5 mm Offset), das von innen mit
    115 g/m² Pergaminpapier hinterklebt wird -> Verpackung wird zur leuchtenden Tischlaterne!
    Rückseite hat Schalllöcher über dem Buzzer und eine ausbrechbare USB-C-Kabeldurchführung.
    """
    page_w, page_h = 297.0, 210.0
    W, H, L, glue = 90.0, 18.0, 125.0, 15.0
    total_w = W + H + W + H + glue  # 231 mm
    x0 = (page_w - total_w) / 2.0
    y0 = (page_h - L) / 2.0 + 4.0

    x_front = x0
    x_s1 = x_front + W
    x_back = x_s1 + H
    x_s2 = x_back + W
    x_glue = x_s2 + H
    x_end = x_glue + glue

    # Front-Fenster (Baumkontur + 1.5 mm Offset für schönen Lichtschein)
    front_cx, front_cy = x_front + W / 2.0, y0 + L / 2.0
    window_poly = offset_polygon(outer_poly, 1.5)
    window_d = poly_to_svg_path(window_poly, front_cx, front_cy)

    # Rückseite ist beim Herumfalten gespiegelt in X!
    # Buzzer liegt auf Vorderansicht rechts der Mitte (+9.3 mm) -> auf Außen-Rückwand links der Mitte (-9.3 mm)
    back_cx, back_cy = x_back + W / 2.0, y0 + L / 2.0
    buz_back_x = back_cx - (BUZZER_X - TREE_CX)
    buz_back_y = back_cy + (BUZZER_Y - TREE_CY)

    # Vorperforierte USB-C Kabel-Durchführung unten mittig an der Rückwand (14 x 10 mm)
    usb_port_x = back_cx - 7.0
    usb_port_y = y0 + L - 14.0

    outer_sleeve = (
        f"M {x_front:.2f},{y0:.2f} L {x_s2:.2f},{y0:.2f} "
        f"L {x_end:.2f},{y0 + 3:.2f} L {x_end:.2f},{y0 + L - 3:.2f} "
        f"L {x_s2:.2f},{y0 + L:.2f} L {x_front:.2f},{y0 + L:.2f} Z"
    )
    folds = [
        (x_s1, y0, x_s1, y0 + L),
        (x_back, y0, x_back, y0 + L),
        (x_s2, y0, x_s2, y0 + L),
    ]

    parts = [
        svg_header(page_w, page_h, "AITY Weihnachtsbaum 2026 - Variante G Laternen-Sleeve 125x90x18 mm"),
        '  <text x="12" y="10" class="title">Variante G (NEU): „Laternen-Sleeve“ Diffusor-Schuber (125 × 90 × 18 mm, DIN A4)</text>',
        '  <text x="12" y="14.5" class="label-sm">Frontfenster innen mit Pergaminpapier (115 g/m²) hinterkleben → Schachtel leuchtet im Betrieb als Tischlaterne!</text>',
        f'  <path d="{outer_sleeve}" class="cut"/>',
        f'  <path d="{window_d}" class="cut"/>',
        *[f'  <line x1="{a:.2f}" y1="{b:.2f}" x2="{c:.2f}" y2="{d:.2f}" class="fold"/>' for a, b, c, d in folds],
        # 3 dezente Schalllöcher über dem Buzzer
        f'  <circle cx="{buz_back_x - 3.5:.2f}" cy="{buz_back_y:.2f}" r="1.4" class="cut"/>',
        f'  <circle cx="{buz_back_x:.2f}" cy="{buz_back_y:.2f}" r="1.4" class="cut"/>',
        f'  <circle cx="{buz_back_x + 3.5:.2f}" cy="{buz_back_y:.2f}" r="1.4" class="cut"/>',
        # Ausbrech-Klappe für USB-C Kabel im Laternen-Betrieb
        f'  <path d="M {usb_port_x:.2f},{y0 + L:.2f} L {usb_port_x:.2f},{usb_port_y:.2f} '
        f'L {usb_port_x + 14:.2f},{usb_port_y:.2f} L {usb_port_x + 14:.2f},{y0 + L:.2f}" class="perf"/>',
        # Beschriftungen
        f'  <text x="{front_cx:.2f}" y="{y0 + 7:.2f}" text-anchor="middle" class="label">FRONT (Pergamin-Fenster)</text>',
        f'  <text x="{back_cx:.2f}" y="{y0 + 7:.2f}" text-anchor="middle" class="label">RÜCKSEITE (90 × 125 mm)</text>',
        f'  <text x="{buz_back_x:.2f}" y="{buz_back_y - 3.5:.2f}" text-anchor="middle" class="label-sm">Buzzer-Schalllöcher</text>',
        f'  <text x="{back_cx:.2f}" y="{usb_port_y - 2.0:.2f}" text-anchor="middle" class="label-sm">USB-C Perforation</text>',
        f'  <text x="{x_glue + glue/2:.2f}" y="{y0 + L/2:.2f}" text-anchor="middle" transform="rotate(-90 {x_glue + glue/2:.2f} {y0 + L/2:.2f})" class="label-sm">KLEBELASCHE (15 mm)</text>',
        calibration_bar(12.0, page_h - 5.5, 100.0),
        "</svg>\n",
    ]
    (OUT_DIR / "lantern_sleeve_125x90x18.svg").write_text("\n".join(parts), encoding="utf-8")


def _box_tabbed_edge(
    x1: float, y1: float, x2: float, y2: float, n_tabs: int, depth: float, start_out: bool
) -> list[tuple[float, float]]:
    """Erzeugt Punkte für eine gezinkte Kante von (x1,y1) nach (x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    # Rechts-Normale (für CW-Polygon = nach außen, wenn depth > 0)
    nx, ny = dy / length, -dx / length
    pts: list[tuple[float, float]] = []
    segs = 2 * n_tabs + 1
    step = length / segs
    for i in range(segs):
        is_out = (i % 2 == 1) if not start_out else (i % 2 == 0)
        d = depth if is_out else 0.0
        p_start = (x1 + ux * (i * step) + nx * d, y1 + uy * (i * step) + ny * d)
        p_end = (x1 + ux * ((i + 1) * step) + nx * d, y1 + uy * ((i + 1) * step) + ny * d)
        pts.extend([p_start, p_end])
    return pts


def _pts_to_path(pts: list[tuple[float, float]]) -> str:
    cleaned = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - cleaned[-1][0], p[1] - cleaned[-1][1]) > 1e-3:
            cleaned.append(p)
    cmds = [f"M {cleaned[0][0]:.2f} {cleaned[0][1]:.2f}"]
    cmds.extend(f"L {x:.2f} {y:.2f}" for x, y in cleaned[1:])
    cmds.append("Z")
    return " ".join(cmds)


def generate_laser_slide_box_3mm(outer_poly: list[tuple[float, float]]) -> None:
    """
    Variante D (NEU): Kompletter 1:1 Lasercutter-Teilesatz für eine 3.0 mm Sperrholz-Schiebebox.
    Außenmaß: 130 x 98 x 24 mm (Innenmaß: 124 x 92 x 18 mm + 3 mm Schiebedeckel).
    Enthält: Boden, Schiebedeckel (mit Baum-Gravur & Namensfeld), 2 Seitenwände, Rückwand,
    abgesenkte Vorderwand (für Deckel-Einschub) und 2 innere Deckel-Auflageleisten.
    """
    t = 3.0
    box_l, box_w, box_h = 130.0, 98.0, 24.0
    page_w, page_h = 310.0, 230.0
    m = 10.0

    # 1. Bodenplatte (130 x 98 mm, Zapfen nach innen versetzt, also Kerben an den Rändern)
    bx, by = m, m + 12.0
    base_pts = (
        _box_tabbed_edge(bx + t, by + t, bx + box_l - t, by + t, 3, -t, False)
        + _box_tabbed_edge(bx + box_l - t, by + t, bx + box_l - t, by + box_w - t, 2, -t, False)
        + _box_tabbed_edge(bx + box_l - t, by + box_w - t, bx + t, by + box_w - t, 3, -t, False)
        + _box_tabbed_edge(bx + t, by + box_w - t, bx + t, by + t, 2, -t, False)
    )

    # 2. Schiebedeckel (126.5 x 91.4 mm -> läuft mit 0.3 mm Spiel zwischen den Seitenwänden!)
    lid_l, lid_w = box_l - t - 0.5, box_w - 2 * t - 0.6
    lx, ly = bx + box_l + 10.0, by + 3.0
    lid_cx, lid_cy = lx + lid_l / 2.0, ly + lid_w / 2.0
    # Baum auf dem Deckel um -90° gedreht darstellen? Nein, Deckel ist 126.5 x 91.4 (quer),
    # wir drehen die Baum-Gravur um -90°, damit der 100 mm hohe Baum perfekt längs auf den 126.5 mm Deckel passt!
    rot_poly = [(TREE_CY - y + lid_cx, x - TREE_CX + lid_cy) for x, y in outer_poly]
    rot_cmds = [f"M {rot_poly[0][0]:.2f} {rot_poly[0][1]:.2f}"]
    rot_cmds.extend(f"L {x:.2f} {y:.2f}" for x, y in rot_poly[1:])
    rot_cmds.append("Z")
    lid_engrave_d = " ".join(rot_cmds)

    # 3. Zwei Längs-Seitenwände (130 x 24 mm) unten auf dem Bogen
    sw1_x, sw1_y = m, by + box_w + 10.0
    sw2_x, sw2_y = m, sw1_y + box_h + 8.0

    def side_wall_pts(sx: float, sy: float) -> list[tuple[float, float]]:
        return (
            [(sx, sy), (sx + box_l, sy)]
            + _box_tabbed_edge(sx + box_l, sy, sx + box_l, sy + box_h - t, 1, -t, False)
            + _box_tabbed_edge(sx + box_l, sy + box_h - t, sx, sy + box_h - t, 3, t, True)
            + _box_tabbed_edge(sx, sy + box_h - t, sx, sy, 1, -t, False)
        )

    # 4. Rückwand (98 x 24 mm) & Vorderwand (98 x 20.8 mm -> 3.2 mm niedriger für Deckel-Einschub!)
    bw_x, bw_y = m + box_l + 10.0, sw1_y
    fw_x, fw_y = bw_x, sw2_y
    fw_h = box_h - t - 0.2  # 20.8 mm

    back_pts = (
        [(bw_x + t, bw_y), (bw_x + box_w - t, bw_y)]
        + _box_tabbed_edge(bw_x + box_w - t, bw_y, bw_x + box_w - t, bw_y + box_h - t, 1, t, False)
        + _box_tabbed_edge(bw_x + box_w - t, bw_y + box_h - t, bw_x + t, bw_y + box_h - t, 2, t, True)
        + _box_tabbed_edge(bw_x + t, bw_y + box_h - t, bw_x + t, bw_y, 1, t, False)
    )
    front_pts = (
        [(fw_x + t, fw_y), (fw_x + box_w - t, fw_y)]
        + _box_tabbed_edge(fw_x + box_w - t, fw_y, fw_x + box_w - t, fw_y + fw_h - t, 1, t, False)
        + _box_tabbed_edge(fw_x + box_w - t, fw_y + fw_h - t, fw_x + t, fw_y + fw_h - t, 2, t, True)
        + _box_tabbed_edge(fw_x + t, fw_y + fw_h - t, fw_x + t, fw_y, 1, t, False)
    )

    # 5. Zwei innere Deckel-Auflageleisten (124 x 17.6 mm), werden innen an die Seitenwände geklebt,
    #    damit der 3 mm Schiebedeckel bündig unter der Oberkante läuft!
    r1_x, r1_y = bw_x + box_w + 8.0, sw1_y
    r2_x, r2_y = r1_x + 22.0, sw1_y
    rail_l, rail_w = box_l - 2 * t, box_h - 2 * t - 0.4  # 124 x 17.6 mm (vertikal platziert)

    parts = [
        svg_header(page_w, page_h, "AITY Weihnachtsbaum 2026 - Variante D 3mm Laser-Schiebebox"),
        f'  <text x="{m:.2f}" y="8" class="title">Variante D: „Maker-Laser“ Schiebebox für 3,0 mm Sperrholz (130 × 98 × 24 mm, 1:1)</text>',
        f'  <text x="{m:.2f}" y="12.5" class="label-sm">Rot = Laserschnitt • Blau = Gravur auf Schiebedeckel (inkl. Namensfeld für Workshop-Kids!)</text>',
        # Boden
        f'  <path d="{_pts_to_path(base_pts)}" class="cut"/>',
        f'  <text x="{bx + box_l/2:.2f}" y="{by + box_w/2:.2f}" text-anchor="middle" class="label">BODEN (130 × 98 mm)</text>',
        # Schiebedeckel + Daumenmulde + Baumgravur + Namensfeld
        f'  <rect x="{lx:.2f}" y="{ly:.2f}" width="{lid_l:.2f}" height="{lid_w:.2f}" rx="1.5" ry="1.5" class="cut"/>',
        f'  <circle cx="{lx + lid_l - 8.0:.2f}" cy="{lid_cy:.2f}" r="4.5" class="engrave"/>',
        f'  <path d="{lid_engrave_d}" class="engrave"/>',
        f'  <rect x="{lx + 8:.2f}" y="{ly + 6:.2f}" width="42" height="12" rx="1.5" ry="1.5" class="engrave"/>',
        f'  <text x="{lx + 29:.2f}" y="{ly + 13.2:.2f}" text-anchor="middle" class="label-sm">Name / Widmung</text>',
        f'  <text x="{lid_cx:.2f}" y="{ly + lid_w - 4:.2f}" text-anchor="middle" class="label-sm">SCHIEBEDECKEL ({lid_l:.1f} × {lid_w:.1f} mm)</text>',
        # Seitenwände
        f'  <path d="{_pts_to_path(side_wall_pts(sw1_x, sw1_y))}" class="cut"/>',
        f'  <text x="{sw1_x + box_l/2:.2f}" y="{sw1_y + 13:.2f}" text-anchor="middle" class="label-sm">SEITENWAND 1 (130 × 24 mm)</text>',
        f'  <path d="{_pts_to_path(side_wall_pts(sw2_x, sw2_y))}" class="cut"/>',
        f'  <text x="{sw2_x + box_l/2:.2f}" y="{sw2_y + 13:.2f}" text-anchor="middle" class="label-sm">SEITENWAND 2 (130 × 24 mm)</text>',
        # Rück- & Vorderwand
        f'  <path d="{_pts_to_path(back_pts)}" class="cut"/>',
        f'  <text x="{bw_x + box_w/2:.2f}" y="{bw_y + 13:.2f}" text-anchor="middle" class="label-sm">RÜCKWAND</text>',
        f'  <path d="{_pts_to_path(front_pts)}" class="cut"/>',
        f'  <text x="{fw_x + box_w/2:.2f}" y="{fw_y + 11:.2f}" text-anchor="middle" class="label-sm">VORDERWAND (Deckelspalt)</text>',
        # 2 Auflageleisten
        f'  <rect x="{r1_x:.2f}" y="{r1_y - 35:.2f}" width="{rail_w:.2f}" height="{rail_l:.2f}" class="cut"/>',
        f'  <rect x="{r2_x:.2f}" y="{r2_y - 35:.2f}" width="{rail_w:.2f}" height="{rail_l:.2f}" class="cut"/>',
        f'  <text x="{r1_x + 20:.2f}" y="{r1_y + rail_l - 30:.2f}" text-anchor="middle" class="label-sm">2× Deckelleiste innen</text>',
        calibration_bar(m, page_h - 4.5, 50.0),
        "</svg>\n",
    ]
    (OUT_DIR / "laser_slide_box_3mm.svg").write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outer_poly = load_clean_outer_polygon()
    generate_inlay_foam(outer_poly)
    generate_folding_box_dieline(outer_poly)
    generate_flat_mail_card_a6(outer_poly)
    generate_stand_insert()
    generate_lantern_sleeve(outer_poly)
    generate_laser_slide_box_3mm(outer_poly)
    print(f"Alle 6 geprüften Verpackungsvorlagen erfolgreich erzeugt in: {OUT_DIR}")


if __name__ == "__main__":
    main()
