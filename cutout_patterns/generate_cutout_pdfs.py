#!/usr/bin/env python3
"""
Generate tiled A4 1:1 cutout pattern PDFs for the AITY Xmas Tree 2026
at target heights of 40 cm, 85 cm, and 105 cm, including:
  - Exact KiCad Edge.Cuts tree outline
  - 60 LED center holes (5 mm circle + precision crosshair + LED index)
  - 15 mm overlap strips, registration crosshairs, and tile grid labels
  - Page 1 assembly overview & 100 mm print-scale verification bar

Requires `rsvg-convert` and `pdfunite`.
"""

import json
import math
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTLINE_JS = ROOT / "docs" / "pcb_outline.js"
LEDS_SVG = ROOT / "circuitpython" / "tannenbaum_leds.svg"
OUT_DIR = Path(__file__).resolve().parent

A4_SHORT = 210.0
A4_LONG = 297.0
MARGIN = 10.0
OVERLAP = 15.0

ORIENTATIONS = {
    "P": (A4_SHORT, A4_LONG),  # 210 x 297 mm -> print 190 x 277 mm
    "L": (A4_LONG, A4_SHORT),  # 297 x 210 mm -> print 277 x 190 mm
}

TARGET_HEIGHTS_CM = (40, 85, 105)


def load_tree_and_leds():
    outline_txt = OUTLINE_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.XMAS_PCB_OUTLINE\s*=\s*(\{.*\});", outline_txt, re.S)
    outline = json.loads(m.group(1))
    edge_path = outline["edgePath"]

    pts = [(float(x), float(y)) for x, y in re.findall(r"[ML]\s*([-\d.]+)\s+([-\d.]+)", edge_path)]
    min_x = min(x for x, _ in pts)
    max_x = max(x for x, _ in pts)
    min_y = min(y for _, y in pts)
    max_y = max(y for _, y in pts)

    # Parse closed subpaths into line segments for exact tile intersection checks
    edge_segments = []
    subpaths = edge_path.split("Z")
    for sp in subpaths:
        sp_pts = [(float(x), float(y)) for x, y in re.findall(r"[ML]\s*([-\d.]+)\s+([-\d.]+)", sp)]
        if len(sp_pts) >= 2:
            for i in range(len(sp_pts)):
                edge_segments.append((sp_pts[i], sp_pts[(i + 1) % len(sp_pts)]))

    tree = ET.parse(LEDS_SVG)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # In tannenbaum_leds.svg, <g transform="translate(16.522,7.316)"> maps to pcb_outline.js coords
    leds = []
    for elem in root.findall(".//svg:circle", ns):
        if "data-index" not in elem.attrib:
            continue
        idx = int(elem.attrib["data-index"])
        cx = float(elem.attrib["cx"]) + 16.5224
        cy = float(elem.attrib["cy"]) + 7.3155
        leds.append((idx, cx, cy))
    leds.sort(key=lambda item: item[0])

    return {
        "edge_path": edge_path,
        "edge_segments": edge_segments,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "width": max_x - min_x,
        "height": max_y - min_y,
        "leds": leds,
    }


def _row_x_span(data, scale: float, y1: float, y2: float):
    """Return (min_x, max_x) in tree-mm coords for outline + LEDs intersecting y in [y1, y2]."""
    xs = []
    ya, yb = y1 - 2.0, y2 + 2.0
    for (ax, ay), (bx, by) in data["edge_segments"]:
        x1 = (ax - data["min_x"]) * scale
        sy1 = (ay - data["min_y"]) * scale
        x2 = (bx - data["min_x"]) * scale
        sy2 = (by - data["min_y"]) * scale
        if max(sy1, sy2) < ya or min(sy1, sy2) > yb:
            continue
        for yy in (ya, yb):
            if (sy1 - yy) * (sy2 - yy) <= 0 and abs(sy2 - sy1) > 1e-9:
                t = (yy - sy1) / (sy2 - sy1)
                xs.append(x1 + t * (x2 - x1))
        if ya <= sy1 <= yb:
            xs.append(x1)
        if ya <= sy2 <= yb:
            xs.append(x2)
    for _idx, lx, ly in data["leds"]:
        px = (lx - data["min_x"]) * scale
        py = (ly - data["min_y"]) * scale
        if ya - 4.0 <= py <= yb + 4.0:
            xs.extend([px - 4.5, px + 4.5])
    if not xs:
        return None
    return min(xs), max(xs)


def plan_optimal_tiles(data, scale: float):
    """
    Choose per-row orientations ('P' or 'L') and per-row centered columns
    to minimize the total number of A4 pages while maintaining 15 mm overlaps.
    """
    from itertools import product

    tree_h_mm = data["height"] * scale
    best = None

    for n_rows in range(1, 8):
        for seq in product(("P", "L"), repeat=n_rows):
            row_phs = [ORIENTATIONS[o][1] - 2 * MARGIN for o in seq]
            cov_h = sum(row_phs) - OVERLAP * (n_rows - 1)
            if cov_h < tree_h_mm:
                continue
            if n_rows > 1 and cov_h - (row_phs[-1] - OVERLAP) >= tree_h_mm:
                continue

            oy = (cov_h - tree_h_mm) / 2.0
            y_cur = -oy
            tiles = []
            valid = True

            for r, (o, ph) in enumerate(zip(seq, row_phs)):
                page_w, page_h = ORIENTATIONS[o]
                pw = page_w - 2 * MARGIN
                sx = pw - OVERLAP
                span = _row_x_span(data, scale, y_cur, y_cur + ph)
                if span is None:
                    valid = False
                    break
                span_w = span[1] - span[0]
                n_cols = max(1, math.ceil((span_w - OVERLAP) / sx))
                row_cov_w = (n_cols - 1) * sx + pw
                x_center = (span[0] + span[1]) / 2.0
                x_start = x_center - row_cov_w / 2.0

                for c in range(n_cols):
                    gx = x_start + c * sx
                    tiles.append({
                        "r": r,
                        "c": c,
                        "n_cols": n_cols,
                        "orient": o,
                        "page_w": page_w,
                        "page_h": page_h,
                        "pw": pw,
                        "ph": ph,
                        "gx": gx,
                        "gy": y_cur,
                    })
                y_cur += ph - OVERLAP

            if not valid:
                continue

            # Prefer fewest tiles; tie-break on fewer rows, then Portrait preference
            p_count = sum(1 for o in seq if o == "P")
            score = (len(tiles), n_rows, -p_count)
            if best is None or score < best[0]:
                best = (score, seq, tiles)

    return best[1], best[2]


def render_svg_to_pdf(svg_text: str, out_pdf: Path):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as tmp:
        tmp.write(svg_text)
        tmp_svg = Path(tmp.name)
    try:
        subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", str(out_pdf), str(tmp_svg)],
            check=True,
        )
    finally:
        tmp_svg.unlink(missing_ok=True)


def build_overview_svg(data, height_cm: int, scale: float, row_seq, tiles) -> str:
    tree_w_mm = data["width"] * scale
    min_gx = min(t["gx"] for t in tiles)
    max_gx = max(t["gx"] + t["pw"] for t in tiles)
    min_gy = min(t["gy"] for t in tiles)
    max_gy = max(t["gy"] + t["ph"] for t in tiles)
    grid_w_mm = max_gx - min_gx
    grid_h_mm = max_gy - min_gy

    orients_used = sorted(set(row_seq))
    if orients_used == ["P"]:
        orient_desc = "Portrait"
    elif orients_used == ["L"]:
        orient_desc = "Landscape"
    else:
        orient_desc = "Mixed Portrait + Landscape"

    # Overview page is always A4 Portrait (210 x 297 mm)
    ov_w, ov_h = A4_SHORT, A4_LONG
    box_x, box_y, box_w, box_h = 15.0, 52.0, 180.0, 195.0
    ov_scale = min(box_w / grid_w_mm, box_h / grid_h_mm)
    draw_w = grid_w_mm * ov_scale
    draw_h = grid_h_mm * ov_scale
    gx0 = box_x + (box_w - draw_w) / 2.0
    gy0 = box_y + (box_h - draw_h) / 2.0

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ov_w}mm" height="{ov_h}mm" viewBox="0 0 {ov_w} {ov_h}">',
        f'  <rect width="{ov_w}" height="{ov_h}" fill="#FFFFFF"/>',
        f'  <text x="15" y="20" font-family="DejaVu Sans, Arial, sans-serif" font-size="6.5" font-weight="bold" fill="#111111">AITY Xmas Tree 2026 — {height_cm} cm A4 Cutout Pattern</text>',
        f'  <text x="15" y="27.5" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.6" fill="#444444">Tree Size: {tree_w_mm / 10.0:.1f} cm × {height_cm}.0 cm  |  {len(tiles)} A4 Tiles ({orient_desc})  |  Overlap: {OVERLAP:.0f} mm</text>',
        f'  <text x="15" y="34" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.4" fill="#B02A37" font-weight="bold">IMPORTANT: Print at 100% ("Actual Size" / Scale 1.0) — do NOT enable "Fit to Page".</text>',
        # 100 mm calibration bar
        '  <g transform="translate(15, 39)">',
        '    <line x1="0" y1="3" x2="100" y2="3" stroke="#111111" stroke-width="0.45"/>',
        '    <line x1="0" y1="0.5" x2="0" y2="5.5" stroke="#111111" stroke-width="0.45"/>',
        '    <line x1="50" y1="1.2" x2="50" y2="4.8" stroke="#111111" stroke-width="0.35"/>',
        '    <line x1="100" y1="0.5" x2="100" y2="5.5" stroke="#111111" stroke-width="0.45"/>',
        '    <text x="50" y="2.0" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.8" fill="#111111">Scale Check: 100 mm (10 cm)</text>',
        '  </g>',
    ]

    # Draw each active tile rectangle
    for t in tiles:
        tx = gx0 + (t["gx"] - min_gx) * ov_scale
        ty = gy0 + (t["gy"] - min_gy) * ov_scale
        tw = t["pw"] * ov_scale
        th = t["ph"] * ov_scale
        label = f"R{t['r'] + 1}C{t['c'] + 1} ({t['orient']})"
        lines.append(
            f'  <rect x="{tx:.3f}" y="{ty:.3f}" width="{tw:.3f}" height="{th:.3f}" '
            f'fill="none" stroke="#ADB5BD" stroke-width="0.28" stroke-dasharray="1.5 1.0"/>'
        )
        lines.append(
            f'  <text x="{tx + 2.2:.3f}" y="{ty + 4.8:.3f}" font-family="DejaVu Sans, Arial, sans-serif" '
            f'font-size="2.8" font-weight="bold" fill="#495057">{label}</text>'
        )

    # Draw scaled tree outline in overview
    tree_ov_scale = scale * ov_scale
    tx0 = gx0 + (0.0 - min_gx - data["min_x"] * scale) * ov_scale
    ty0 = gy0 + (0.0 - min_gy - data["min_y"] * scale) * ov_scale
    lines.append(f'  <g transform="translate({tx0:.4f},{ty0:.4f}) scale({tree_ov_scale:.6f})">')
    lines.append(
        f'    <path d="{data["edge_path"]}" fill="#E9F5EE" fill-opacity="0.55" '
        f'stroke="#111111" stroke-width="{0.45 / tree_ov_scale:.5f}" stroke-linejoin="round"/>'
    )
    for _idx, lx, ly in data["leds"]:
        lines.append(
            f'    <circle cx="{lx:.3f}" cy="{ly:.3f}" r="{1.3 / tree_ov_scale:.5f}" '
            f'fill="none" stroke="#1971C2" stroke-width="{0.25 / tree_ov_scale:.5f}"/>'
        )
    lines.append("  </g>")

    lines.append(
        f'  <text x="15" y="264" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.9" fill="#444444">'
        f'Assembly: Trim/fold along the {MARGIN:.0f} mm margin &amp; {OVERLAP:.0f} mm overlap guides, align (+) crosshairs, and glue/tape tiles in order.</text>'
    )
    lines.append(
        '  <text x="15" y="270" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.9" fill="#444444">'
        'LED Holes: Each of the 60 LED positions (0–59) is marked with a 5 mm center circle and crosshair (+). (P)=Portrait, (L)=Landscape.</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)


def _overlap_reg_xs(gx_a1: float, gx_a2: float, gx_b1: float, gx_b2: float):
    """Return grid-X positions for registration crosshairs along a shared horizontal seam."""
    ox1 = max(gx_a1, gx_b1)
    ox2 = min(gx_a2, gx_b2)
    if ox2 - ox1 < 12.0:
        return []
    if ox2 - ox1 >= 40.0:
        return [ox1 + 10.0, ox2 - 10.0]
    return [(ox1 + ox2) / 2.0]


def build_tile_svg(data, height_cm: int, scale: float, tile, tiles, n_rows: int) -> str:
    page_w = tile["page_w"]
    page_h = tile["page_h"]
    pw = tile["pw"]
    ph = tile["ph"]
    r = tile["r"]
    c = tile["c"]
    gx = tile["gx"]
    gy = tile["gy"]

    # Map tree-mm coords -> page coords: page_x = MARGIN + (tree_x - gx)
    tx = MARGIN - gx - data["min_x"] * scale
    ty = MARGIN - gy - data["min_y"] * scale

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_w}mm" height="{page_h}mm" viewBox="0 0 {page_w} {page_h}">',
        f'  <rect width="{page_w}" height="{page_h}" fill="#FFFFFF"/>',
        '  <defs>',
        f'    <clipPath id="print-clip"><rect x="{MARGIN}" y="{MARGIN}" width="{pw}" height="{ph}"/></clipPath>',
        '  </defs>',
    ]

    # Clipped 1:1 tree + LED center holes
    lines.append('  <g clip-path="url(#print-clip)">')
    lines.append(f'    <g transform="translate({tx:.4f},{ty:.4f}) scale({scale:.6f})">')
    lines.append(
        f'      <path d="{data["edge_path"]}" fill="none" stroke="#000000" '
        f'stroke-width="{0.45 / scale:.5f}" stroke-linejoin="round"/>'
    )
    lines.append("    </g>")

    hole_r = 2.5
    cross_arm = 4.0
    sw_circle = 0.28
    sw_cross = 0.20
    for idx, lx, ly in data["leds"]:
        px = tx + lx * scale
        py = ty + ly * scale
        if px < MARGIN - 10 or px > page_w - MARGIN + 10 or py < MARGIN - 10 or py > page_h - MARGIN + 10:
            continue
        lines.append(
            f'    <circle cx="{px:.3f}" cy="{py:.3f}" r="{hole_r}" fill="none" stroke="#1971C2" stroke-width="{sw_circle}"/>'
        )
        lines.append(
            f'    <line x1="{px - cross_arm:.3f}" y1="{py:.3f}" x2="{px + cross_arm:.3f}" y2="{py:.3f}" stroke="#1971C2" stroke-width="{sw_cross}"/>'
        )
        lines.append(
            f'    <line x1="{px:.3f}" y1="{py - cross_arm:.3f}" x2="{px:.3f}" y2="{py + cross_arm:.3f}" stroke="#1971C2" stroke-width="{sw_cross}"/>'
        )
        lines.append(
            f'    <text x="{px + 3.4:.3f}" y="{py + 1.1:.3f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.8" font-weight="bold" fill="#1971C2">{idx}</text>'
        )

    lines.append("  </g>")

    # Printable boundary
    lines.append(
        f'  <rect x="{MARGIN}" y="{MARGIN}" width="{pw}" height="{ph}" '
        f'fill="none" stroke="#868E96" stroke-width="0.25" stroke-dasharray="2.0 1.5"/>'
    )

    def add_reg_mark(mx: float, my: float):
        lines.append(f'  <circle cx="{mx:.2f}" cy="{my:.2f}" r="2.0" fill="none" stroke="#D9480F" stroke-width="0.28"/>')
        lines.append(f'  <line x1="{mx - 3.2:.2f}" y1="{my:.2f}" x2="{mx + 3.2:.2f}" y2="{my:.2f}" stroke="#D9480F" stroke-width="0.28"/>')
        lines.append(f'  <line x1="{mx:.2f}" y1="{my - 3.2:.2f}" x2="{mx:.2f}" y2="{my + 3.2:.2f}" stroke="#D9480F" stroke-width="0.28"/>')

    def add_tick_v(mx: float, my: float):
        lines.append(f'  <line x1="{mx - 2.2:.2f}" y1="{my:.2f}" x2="{mx + 2.2:.2f}" y2="{my:.2f}" stroke="#D9480F" stroke-width="0.30"/>')

    def add_tick_h(mx: float, my: float):
        lines.append(f'  <line x1="{mx:.2f}" y1="{my - 2.2:.2f}" x2="{mx:.2f}" y2="{my + 2.2:.2f}" stroke="#D9480F" stroke-width="0.30"/>')

    x_left_cut = MARGIN
    x_right_glue = page_w - MARGIN - OVERLAP
    y_top_cut = MARGIN
    y_bottom_glue = page_h - MARGIN - OVERLAP

    v_ticks = [MARGIN + ph * f for f in (0.25, 0.5, 0.75)]
    h_ticks = [MARGIN + pw * f for f in (0.25, 0.5, 0.75)]

    has_left = c > 0
    has_right = c + 1 < tile["n_cols"]
    above_overlaps = [
        ot for ot in tiles
        if ot["r"] == r - 1 and min(gx + pw, ot["gx"] + ot["pw"]) - max(gx, ot["gx"]) >= 12.0
    ]
    below_overlaps = [
        ot for ot in tiles
        if ot["r"] == r + 1 and min(gx + pw, ot["gx"] + ot["pw"]) - max(gx, ot["gx"]) >= 12.0
    ]

    # Left cut line (aligns onto previous column's right glue line)
    if has_left:
        lines.append(
            f'  <line x1="{x_left_cut}" y1="{MARGIN}" x2="{x_left_cut}" y2="{page_h - MARGIN}" '
            f'stroke="#D9480F" stroke-width="0.35" stroke-dasharray="3.0 1.5"/>'
        )
        for ty_tick in v_ticks:
            add_tick_v(x_left_cut, ty_tick)
        lines.append(
            f'  <text x="{x_left_cut - 2.0}" y="{page_h / 2:.1f}" transform="rotate(-90 {x_left_cut - 2.0} {page_h / 2:.1f})" '
            f'text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.5" font-weight="bold" fill="#D9480F">'
            f'✂ CUT ON THIS LINE &amp; ALIGN ON R{r + 1}C{c}</text>'
        )

    # Right glue-under line
    if has_right:
        lines.append(
            f'  <rect x="{x_right_glue}" y="{MARGIN}" width="{OVERLAP}" height="{ph}" '
            f'fill="#FFF4E6" fill-opacity="0.45" stroke="none"/>'
        )
        lines.append(
            f'  <line x1="{x_right_glue}" y1="{MARGIN}" x2="{x_right_glue}" y2="{page_h - MARGIN}" '
            f'stroke="#D9480F" stroke-width="0.35" stroke-dasharray="3.0 1.5"/>'
        )
        for ty_tick in v_ticks:
            add_tick_v(x_right_glue, ty_tick)
        lines.append(
            f'  <text x="{x_right_glue + 7.5}" y="{page_h / 2:.1f}" transform="rotate(-90 {x_right_glue + 7.5} {page_h / 2:.1f})" '
            f'text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.5" font-weight="bold" fill="#D9480F">'
            f'GLUE AREA (15mm) — Align R{r + 1}C{c + 2} cut edge ON line</text>'
        )

    # Top cut line (aligns onto previous row's bottom glue line)
    if above_overlaps:
        above_labels = ", ".join(f"R{ot['r'] + 1}C{ot['c'] + 1}" for ot in above_overlaps)
        lines.append(
            f'  <line x1="{MARGIN}" y1="{y_top_cut}" x2="{page_w - MARGIN}" y2="{y_top_cut}" '
            f'stroke="#D9480F" stroke-width="0.35" stroke-dasharray="3.0 1.5"/>'
        )
        for tx_tick in h_ticks:
            add_tick_h(tx_tick, y_top_cut)
        lines.append(
            f'  <text x="{page_w / 2:.1f}" y="{y_top_cut - 1.4}" text-anchor="middle" '
            f'font-family="DejaVu Sans, Arial, sans-serif" font-size="2.4" font-weight="bold" fill="#D9480F">'
            f'✂ CUT ON THIS LINE &amp; ALIGN ON {above_labels}</text>'
        )
        for ot in above_overlaps:
            for rx_g in _overlap_reg_xs(gx, gx + pw, ot["gx"], ot["gx"] + ot["pw"]):
                add_reg_mark(MARGIN + (rx_g - gx), y_top_cut)

    # Bottom glue-under line
    if below_overlaps:
        below_labels = ", ".join(f"R{ot['r'] + 1}C{ot['c'] + 1}" for ot in below_overlaps)
        lines.append(
            f'  <rect x="{MARGIN}" y="{y_bottom_glue}" width="{pw}" height="{OVERLAP}" '
            f'fill="#FFF4E6" fill-opacity="0.45" stroke="none"/>'
        )
        lines.append(
            f'  <line x1="{MARGIN}" y1="{y_bottom_glue}" x2="{page_w - MARGIN}" y2="{y_bottom_glue}" '
            f'stroke="#D9480F" stroke-width="0.35" stroke-dasharray="3.0 1.5"/>'
        )
        for tx_tick in h_ticks:
            add_tick_h(tx_tick, y_bottom_glue)
        lines.append(
            f'  <text x="{page_w / 2:.1f}" y="{y_bottom_glue + 8.5}" text-anchor="middle" '
            f'font-family="DejaVu Sans, Arial, sans-serif" font-size="2.5" font-weight="bold" fill="#D9480F">'
            f'GLUE AREA (15mm) — Align {below_labels} cut edge ON line</text>'
        )
        for ot in below_overlaps:
            for rx_g in _overlap_reg_xs(gx, gx + pw, ot["gx"], ot["gx"] + ot["pw"]):
                add_reg_mark(MARGIN + (rx_g - gx), y_bottom_glue)

    # Vertical seam registration crosshairs (at top & bottom of left cut / right glue lines)
    if has_left:
        add_reg_mark(x_left_cut, y_top_cut)
        add_reg_mark(x_left_cut, y_bottom_glue)
    if has_right:
        add_reg_mark(x_right_glue, y_top_cut)
        add_reg_mark(x_right_glue, y_bottom_glue)

    # Header badge in top margin
    orient_word = "Portrait" if tile["orient"] == "P" else "Landscape"
    lines.append(
        f'  <text x="{MARGIN}" y="4.8" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.9" font-weight="bold" fill="#212529">'
        f'AITY Xmas Tree 2026 · {height_cm} cm (1:1) · Tile R{r + 1}C{c + 1} ({orient_word}, Row {r + 1}/{n_rows})</text>'
    )
    lines.append(
        f'  <text x="{page_w - MARGIN}" y="4.8" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.6" fill="#6C757D">'
        f'Print 100% / Actual Size</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


def _split_polygon_loops(pts):
    """Split a KiCad fp_poly (with zero-width hole bridges) into disjoint closed loops sorted by area."""
    from collections import defaultdict

    clean = []
    for p in pts:
        if not clean or p != clean[-1]:
            clean.append(p)
    if len(clean) > 1 and clean[0] == clean[-1]:
        clean.pop()

    edges = [(clean[i], clean[(i + 1) % len(clean)]) for i in range(len(clean))]
    edge_set = defaultdict(int)
    for e in edges:
        edge_set[e] += 1

    kept = []
    for u, v in edges:
        if edge_set[(v, u)] > 0:
            edge_set[(v, u)] -= 1
            edge_set[(u, v)] -= 1
        elif edge_set[(u, v)] > 0:
            kept.append((u, v))
            edge_set[(u, v)] -= 1

    adj = defaultdict(list)
    for u, v in kept:
        adj[u].append(v)

    loops = []
    while adj:
        start = next(iter(adj))
        loop = [start]
        cur = adj[start].pop()
        if not adj[start]:
            del adj[start]
        while cur != start:
            loop.append(cur)
            nxt = adj[cur].pop()
            if not adj[cur]:
                del adj[cur]
            cur = nxt
        loops.append(loop)

    def _area(lp):
        s = 0.0
        for i in range(len(lp)):
            x1, y1 = lp[i]
            x2, y2 = lp[(i + 1) % len(lp)]
            s += x1 * y2 - x2 * y1
        return abs(s) * 0.5

    loops.sort(key=_area, reverse=True)
    return loops


def _loops_to_path_d(loops) -> str:
    parts = []
    for lp in loops:
        if not lp:
            continue
        segs = [f"M {lp[0][0]:.4f} {lp[0][1]:.4f}"]
        for x, y in lp[1:]:
            segs.append(f"L {x:.4f} {y:.4f}")
        segs.append("Z")
        parts.append(" ".join(segs))
    return " ".join(parts)


def load_ornament_stencils():
    """Load the 4 ornament SVGs and split each into multi-layer spray-paint stencil layers."""
    svg_dir = OUT_DIR / "svg"
    specs = [
        ("kugel", "Bauble (Kugel)"),
        ("schnee-gross", "Snowflake Large"),
        ("schnee-klein", "Snowflake Small"),
        ("glitzer", "Sparkle (Glitzer)"),
    ]
    ornaments = []
    for slug, title in specs:
        root = ET.parse(svg_dir / f"{slug}.svg").getroot()
        path_el = root.findall(".//{http://www.w3.org/2000/svg}path")[0]
        d = path_el.attrib["d"]
        subpaths = [s.strip() for s in d.split("Z") if s.strip()]

        sp_pts_list = []
        all_pts = []
        for sp in subpaths:
            pts = [(round(float(x), 4), round(float(y), 4)) for x, y in re.findall(r"[ML]\s*([-\d.]+)\s+([-\d.]+)", sp)]
            sp_pts_list.append(pts)
            all_pts.extend(pts)

        min_x = min(x for x, _ in all_pts)
        max_x = max(x for x, _ in all_pts)
        min_y = min(y for _, y in all_pts)
        max_y = max(y for _, y in all_pts)

        # Normalize to (0, 0) origin
        norm_sps = [[(x - min_x, y - min_y) for x, y in pts] for pts in sp_pts_list]
        w = max_x - min_x
        h = max_y - min_y

        layers = []
        if slug == "kugel":
            main_loops = _split_polygon_loops(norm_sps[4])
            l1 = _loops_to_path_d([main_loops[0]])
            layers.append(("Layer 1/3: Base Silhouette", l1, None, False))
            layers.append(("Layer 2/3: Stripes &amp; Hanger", _loops_to_path_d(main_loops[1:]), l1, False))
            layers.append(("Layer 3/3: Center Dots", _loops_to_path_d(norm_sps[:4]), l1, False))
        elif slug == "schnee-gross":
            main_loops = _split_polygon_loops(norm_sps[0])
            l1 = _loops_to_path_d([main_loops[0]])
            layers.append(("Layer 1/2: Base Silhouette", l1, None, False))
            layers.append(("Layer 2/2: Inner Cutouts", _loops_to_path_d(main_loops[1:]), l1, False))
        else:
            layers.append(("Layer 1/1: Full Silhouette", _loops_to_path_d(norm_sps), None, False))

        ornaments.append({
            "slug": slug,
            "title": title,
            "w": w,
            "h": h,
            "layers": layers,
            "edge_d": None,
        })
    return ornaments


def _extract_kicad_gr_polys(pcb_path: Path):
    txt = pcb_path.read_text(encoding="utf-8")
    res = []
    idx = 0
    while True:
        pos = txt.find("(gr_poly", idx)
        if pos == -1:
            break
        depth = 0
        end = pos
        for i in range(pos, len(txt)):
            if txt[i] == "(":
                depth += 1
            elif txt[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        block = txt[pos:end]
        idx = end
        m_layer = re.search(r'\(layer\s+"([^"]+)"\)', block)
        layer = m_layer.group(1) if m_layer else ""
        pts = [(float(x), float(y)) for x, y in re.findall(r"\(xy\s+([-\d.]+)\s+([-\d.]+)\)", block)]
        if pts:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            res.append((layer, pts, min(xs), max(xs), min(ys), max(ys)))
    return res


def _edge_segments_near_bbox(edge_pts, x1, x2, y1, y2, margin=2.0):
    """Return SVG path string of Edge.Cuts segments near the given bbox."""
    parts = []
    n = len(edge_pts)
    for i in range(n):
        ax, ay = edge_pts[i]
        bx, by = edge_pts[(i + 1) % n]
        if max(ax, bx) < x1 - margin or min(ax, bx) > x2 + margin:
            continue
        if max(ay, by) < y1 - margin or min(ay, by) > y2 + margin:
            continue
        parts.append(f"M {ax - x1:.4f} {ay - y1:.4f} L {bx - x1:.4f} {by - y1:.4f}")
    return " ".join(parts) if parts else None


def load_pcb_artwork_stencils():
    """Extract 2-step Parcels, Stem Wood Grain, and Tree Branch Feathers stencils from KiCad PCB."""
    pcb_path = ROOT / "kicad" / "aity-xmas-tree-2026.kicad_pcb"
    polys = _extract_kicad_gr_polys(pcb_path)

    edge_pts = next(pts for layer, pts, *_ in polys if layer == "Edge.Cuts")
    silk = [(i, pts, x1, x2, y1, y2) for i, (layer, pts, x1, x2, y1, y2) in enumerate(polys) if layer == "F.SilkS"]
    poly_by_idx = {i: (pts, x1, x2, y1, y2) for i, pts, x1, x2, y1, y2 in silk}

    items = []

    # 1. Parcels (2-step: Step 1 = 3 solid boxes, Step 2 = 3 ribbons & bows)
    parcel_specs = [
        (227, 117.32),  # Left parcel
        (207, 119.37),  # Middle parcel
        (89, 118.25),   # Right parcel
    ]
    px1 = min(poly_by_idx[i][1] for i, _ in parcel_specs)
    px2 = max(poly_by_idx[i][2] for i, _ in parcel_specs)
    py1 = min(poly_by_idx[i][3] for i, _ in parcel_specs)
    py2 = max(poly_by_idx[i][4] for i, _ in parcel_specs)

    box_paths = []
    ribbon_paths = []
    for pid, box_top in parcel_specs:
        pts, bx1, bx2, _by1, by2 = poly_by_idx[pid]
        bw = bx2 - bx1
        bh = by2 - box_top
        # Step 1: Solid parcel box
        box_paths.append(
            f"M {bx1 - px1:.4f} {box_top - py1:.4f} "
            f"L {bx2 - px1:.4f} {box_top - py1:.4f} "
            f"L {bx2 - px1:.4f} {by2 - py1:.4f} "
            f"L {bx1 - px1:.4f} {by2 - py1:.4f} Z"
        )
        # Step 2: Bow (main outer loop clipped/extracted above box_top) + vertical & horizontal ribbon bands
        main_loop = _split_polygon_loops(pts)[0]
        bow_pts = [(x - px1, y - py1) for x, y in main_loop if y <= box_top + 0.08]
        if len(bow_pts) >= 3:
            ribbon_paths.append(_loops_to_path_d([bow_pts]))

        rw = max(0.35, bw * 0.14)
        rh = max(0.32, bh * 0.15)
        cx_b = (bx1 + bx2) / 2.0 - px1
        cy_b = (box_top + by2) / 2.0 - py1
        # Vertical ribbon
        ribbon_paths.append(
            f"M {cx_b - rw / 2:.4f} {box_top - py1:.4f} "
            f"L {cx_b + rw / 2:.4f} {box_top - py1:.4f} "
            f"L {cx_b + rw / 2:.4f} {by2 - py1:.4f} "
            f"L {cx_b - rw / 2:.4f} {by2 - py1:.4f} Z"
        )
        # Horizontal ribbon
        ribbon_paths.append(
            f"M {bx1 - px1:.4f} {cy_b - rh / 2:.4f} "
            f"L {bx2 - px1:.4f} {cy_b - rh / 2:.4f} "
            f"L {bx2 - px1:.4f} {cy_b + rh / 2:.4f} "
            f"L {bx1 - px1:.4f} {cy_b + rh / 2:.4f} Z"
        )

    l1_parcels = " ".join(box_paths)
    l2_ribbons = " ".join(ribbon_paths)
    items.append({
        "slug": "parcels",
        "title": "Parcels (3 Gifts)",
        "w": px2 - px1,
        "h": py2 - py1,
        "layers": [
            ("Layer 1/2: Parcel Boxes", l1_parcels, None, False),
            ("Layer 2/2: Ribbons &amp; Bows", l2_ribbons, l1_parcels, True),
        ],
        "edge_d": _edge_segments_near_bbox(edge_pts, px1, px2, py1, py2, margin=1.5),
    })

    # 2. Tree Stem (Wood Grain) — exclude snowflake poly[127] and parcels/dots
    parcel_ids = {227, 207, 89, 127}
    stem_polys = [
        (i, pts, x1, x2, y1, y2)
        for i, pts, x1, x2, y1, y2 in silk
        if i not in parcel_ids and y2 > 107.0 and x1 > 123.5 and x2 < 141.0 and (y2 - y1) > 0.35
    ]
    sx1 = min(p[2] for p in stem_polys)
    sx2 = max(p[3] for p in stem_polys)
    sy1 = min(p[4] for p in stem_polys)
    sy2 = max(p[5] for p in stem_polys)
    stem_d = _loops_to_path_d([[(x - sx1, y - sy1) for x, y in pts] for _, pts, *_ in stem_polys])
    items.append({
        "slug": "stem",
        "title": "Tree Stem (Wood Grain)",
        "w": sx2 - sx1,
        "h": sy2 - sy1,
        "layers": [
            ("Layer 1/1: Wood Grain (align green edge)", stem_d, None, False),
        ],
        "edge_d": _edge_segments_near_bbox(edge_pts, sx1, sx2, sy1, sy2, margin=2.0),
    })

    # 3. Tree Branch Feathers (Left & Right Tiers 1..4)
    branch_groups = [
        ("branch-l1", "Branch Feather L1 (Top Left)", [178]),
        ("branch-r1", "Branch Feather R1 (Top Right)", [125]),
        ("branch-l2", "Branch Feather L2 (Upper Left)", [257]),
        ("branch-r2", "Branch Feather R2 (Upper Right)", [59]),
        ("branch-l3", "Branch Feather L3 (Mid Left)", [168]),
        ("branch-r3", "Branch Feather R3 (Mid Right)", [152, 232]),
        ("branch-l4", "Branch Feather L4 (Bottom Left)", [17]),
        ("branch-r4", "Branch Feather R4 (Bottom Right)", [196]),
    ]
    for slug, title, idxs in branch_groups:
        grp = [poly_by_idx[i] for i in idxs]
        bx1 = min(g[1] for g in grp)
        bx2 = max(g[2] for g in grp)
        by1 = min(g[3] for g in grp)
        by2 = max(g[4] for g in grp)
        # Split into 2 halves if huge (e.g. L4/R4 at 105cm) so every piece fits A4 Portrait
        b_d = _loops_to_path_d([[(x - bx1, y - by1) for x, y in g[0]] for g in grp])
        items.append({
            "slug": slug,
            "title": title,
            "w": bx2 - bx1,
            "h": by2 - by1,
            "layers": [
                ("Layer 1/1: Pine Needles (align green edge)", b_d, None, False),
            ],
            "edge_d": _edge_segments_near_bbox(edge_pts, bx1, bx2, by1, by2, margin=2.0),
        })

    return items


def build_stencil_pages_svgs(stencils, height_cm: int, scale: float):
    """Build A4 Portrait SVG pages containing 1:1 scaled multi-layer spray stencils."""
    page_w, page_h = A4_SHORT, A4_LONG
    pad = 12.0       # Page outer margin
    gap = 6.0        # Gap between stencil cards
    card_pad = 10.0  # Spray-masking border around stencil inside each card
    header_h = 9.0   # Title band inside card above spray area
    top_y = 28.0     # Below page title
    max_cw = page_w - 2 * pad
    max_ch = page_h - top_y - pad

    # Build card specs, automatically splitting oversized branch cards into 2 overlapping A4 halves
    cards = []
    for item in stencils:
        ow = item["w"] * scale
        oh = item["h"] * scale
        cw = max(48.0, ow + 2 * card_pad)
        ch = header_h + oh + 2 * card_pad
        is_multi = len(item["layers"]) > 1

        if cw <= max_cw and ch <= max_ch:
            for layer_label, path_d, ghost_d, union_fill in item["layers"]:
                cards.append({
                    "title": item["title"],
                    "layer_label": layer_label,
                    "path_d": path_d,
                    "ghost_d": ghost_d,
                    "union_fill": union_fill,
                    "edge_d": item["edge_d"],
                    "is_multi": is_multi,
                    "ow": ow,
                    "oh": oh,
                    "cw": cw,
                    "ch": ch,
                    "clip_x": None,
                    "clip_w": None,
                })
        else:
            # Split horizontally into 2 overlapping A4 halves (15 mm overlap)
            half_ow = ow / 2.0 + 7.5
            half_cw = half_ow + 2 * card_pad
            for part_idx, clip_x in enumerate((0.0, ow - half_ow), start=1):
                for layer_label, path_d, ghost_d, union_fill in item["layers"]:
                    cards.append({
                        "title": f"{item['title']} — Part {part_idx}/2",
                        "layer_label": layer_label,
                        "path_d": path_d,
                        "ghost_d": ghost_d,
                        "union_fill": union_fill,
                        "edge_d": item["edge_d"],
                        "is_multi": is_multi,
                        "ow": half_ow,
                        "oh": oh,
                        "cw": half_cw,
                        "ch": ch,
                        "clip_x": clip_x,
                        "clip_w": half_ow,
                    })

    # Shelf-pack cards onto A4 pages
    pages = []
    cur_cards = []
    x_cur = pad
    y_cur = top_y
    row_h = 0.0

    for card in cards:
        if x_cur + card["cw"] > page_w - pad + 1e-6:
            x_cur = pad
            y_cur += row_h + gap
            row_h = 0.0
        if y_cur + card["ch"] > page_h - pad + 1e-6:
            pages.append(cur_cards)
            cur_cards = []
            x_cur = pad
            y_cur = top_y
            row_h = 0.0
        cur_cards.append((x_cur, y_cur, card))
        x_cur += card["cw"] + gap
        row_h = max(row_h, card["ch"])

    if cur_cards:
        pages.append(cur_cards)

    svgs = []
    total_pages = len(pages)
    for pi, placed in enumerate(pages, start=1):
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_w}mm" height="{page_h}mm" viewBox="0 0 {page_w} {page_h}">',
            f'  <rect width="{page_w}" height="{page_h}" fill="#FFFFFF"/>',
            f'  <text x="{pad}" y="14" font-family="DejaVu Sans, Arial, sans-serif" font-size="4.2" font-weight="bold" fill="#111111">AITY Xmas Tree 2026 · {height_cm} cm — Spray Stencils ({pi}/{total_pages})</text>',
            f'  <text x="{pad}" y="20.0" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.8" fill="#444444">Cut WHITE shapes (keep gray mask). Multi-layer: cut the 4 corner ALIGN dots in Layer 1 so Layer 2/3 snap right onto them.</text>',
            f'  <text x="{page_w - pad}" y="14" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.8" fill="#6C757D">Print 100% / Actual Size</text>',
            '  <defs>',
        ]

        # Define clipPaths for any split cards
        for ci, (cx, cy, card) in enumerate(placed):
            if card["clip_x"] is not None:
                ox_c = cx + (card["cw"] - card["ow"]) / 2.0
                oy_c = cy + header_h + (card["ch"] - header_h - card["oh"]) / 2.0
                lines.append(
                    f'    <clipPath id="clip_{pi}_{ci}"><rect x="{ox_c - 1.0:.2f}" y="{oy_c - 2.0:.2f}" '
                    f'width="{card["clip_w"] + 2.0:.2f}" height="{card["oh"] + 4.0:.2f}"/></clipPath>'
                )
        lines.append('  </defs>')

        for ci, (cx, cy, card) in enumerate(placed):
            cw, ch = card["cw"], card["ch"]
            lines.append(
                f'  <rect x="{cx:.2f}" y="{cy:.2f}" width="{cw:.2f}" height="{ch:.2f}" '
                f'fill="#F1F3F5" stroke="#495057" stroke-width="0.30" stroke-dasharray="2.5 1.5"/>'
            )
            lines.append(
                f'  <text x="{cx + 2.5:.2f}" y="{cy + 4.2:.2f}" font-family="DejaVu Sans, Arial, sans-serif" '
                f'font-size="2.6" font-weight="bold" fill="#212529">{card["title"]}</text>'
            )
            lines.append(
                f'  <text x="{cx + 2.5:.2f}" y="{cy + 7.6:.2f}" font-family="DejaVu Sans, Arial, sans-serif" '
                f'font-size="2.2" font-weight="bold" fill="#D9480F">{card["layer_label"]}</text>'
            )

            # 4 corner registration crosshairs + 2.0 mm cutout ALIGN dots on multi-layer stencils
            rx1 = cx + 4.0
            rx2 = cx + cw - 4.0
            ry1 = cy + header_h + 4.0
            ry2 = cy + ch - 4.0
            for rx in (rx1, rx2):
                for ry in (ry1, ry2):
                    if card["is_multi"]:
                        # 2.0 mm white cutout hole to spray/mark alignment dots in Layer 1 and match in Layer 2/3
                        lines.append(f'  <circle cx="{rx:.2f}" cy="{ry:.2f}" r="1.0" fill="#FFFFFF" stroke="#D9480F" stroke-width="0.28"/>')
                    else:
                        lines.append(f'  <circle cx="{rx:.2f}" cy="{ry:.2f}" r="1.6" fill="none" stroke="#D9480F" stroke-width="0.25"/>')
                    lines.append(f'  <line x1="{rx - 2.6:.2f}" y1="{ry:.2f}" x2="{rx + 2.6:.2f}" y2="{ry:.2f}" stroke="#D9480F" stroke-width="0.25"/>')
                    lines.append(f'  <line x1="{rx:.2f}" y1="{ry - 2.6:.2f}" x2="{rx:.2f}" y2="{ry + 2.6:.2f}" stroke="#D9480F" stroke-width="0.25"/>')
            if card["is_multi"]:
                lines.append(
                    f'  <text x="{rx1 + 2.2:.2f}" y="{ry1 + 0.9:.2f}" font-family="DejaVu Sans, Arial, sans-serif" '
                    f'font-size="1.9" font-weight="bold" fill="#D9480F">ALIGN</text>'
                )

            ox = cx + (cw - card["ow"]) / 2.0 - (card["clip_x"] or 0.0)
            oy = cy + header_h + (ch - header_h - card["oh"]) / 2.0
            clip_attr = f' clip-path="url(#clip_{pi}_{ci})"' if card["clip_x"] is not None else ""
            lines.append(f'  <g{clip_attr}>')
            lines.append(f'    <g transform="translate({ox:.4f},{oy:.4f}) scale({scale:.6f})">')

            # Faint ghost outline of Layer 1 on Layer 2/3 for effortless visual alignment
            if card["ghost_d"]:
                lines.append(
                    f'      <path d="{card["ghost_d"]}" fill="none" stroke="#ADB5BD" '
                    f'stroke-width="{0.25 / scale:.5f}" stroke-dasharray="{1.2 / scale:.4f} {1.0 / scale:.4f}"/>'
                )

            # Tree Edge alignment guide (for stem & branch feathers)
            if card["edge_d"]:
                lines.append(
                    f'      <path d="{card["edge_d"]}" fill="none" stroke="#2B8A3E" '
                    f'stroke-width="{0.35 / scale:.5f}" stroke-dasharray="{2.0 / scale:.4f} {1.2 / scale:.4f}"/>'
                )

            # Main cutout shape(s)
            if card["union_fill"]:
                # Draw outer union outline cleanly without interior overlap lines
                lines.append(
                    f'      <path d="{card["path_d"]}" fill="none" stroke="#000000" '
                    f'stroke-width="{0.65 / scale:.5f}" stroke-linejoin="round"/>'
                )
                lines.append(
                    f'      <path d="{card["path_d"]}" fill="#FFFFFF" stroke="none"/>'
                )
            else:
                lines.append(
                    f'      <path d="{card["path_d"]}" fill="#FFFFFF" stroke="#000000" '
                    f'stroke-width="{0.35 / scale:.5f}" stroke-linejoin="round"/>'
                )

            lines.append("    </g>")
            lines.append("  </g>")

        lines.append("</svg>")
        svgs.append("\n".join(lines))
    return svgs


def generate_for_height(data, stencils, height_cm: int):
    target_h_mm = height_cm * 10.0
    scale = target_h_mm / data["height"]
    tree_w_mm = data["width"] * scale

    row_seq, tiles = plan_optimal_tiles(data, scale)
    n_rows = len(row_seq)
    stencil_svgs = build_stencil_pages_svgs(stencils, height_cm, scale)

    out_pdf = OUT_DIR / f"tree_cutout_a4_{height_cm}cm.pdf"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        page_pdfs = []

        ov_pdf = tmp / "page_00_overview.pdf"
        render_svg_to_pdf(build_overview_svg(data, height_cm, scale, row_seq, tiles), ov_pdf)
        page_pdfs.append(ov_pdf)

        for tile in tiles:
            p_pdf = tmp / f"page_{tile['r'] + 1}_{tile['c'] + 1}.pdf"
            svg_str = build_tile_svg(data, height_cm, scale, tile, tiles, n_rows)
            render_svg_to_pdf(svg_str, p_pdf)
            page_pdfs.append(p_pdf)

        for si, s_svg in enumerate(stencil_svgs, start=1):
            s_pdf = tmp / f"page_stencil_{si}.pdf"
            render_svg_to_pdf(s_svg, s_pdf)
            page_pdfs.append(s_pdf)

        subprocess.run(["pdfunite", *[str(p) for p in page_pdfs], str(out_pdf)], check=True)

    p_cnt = sum(1 for t in tiles if t["orient"] == "P")
    l_cnt = sum(1 for t in tiles if t["orient"] == "L")
    print(
        f"Generated {out_pdf} ({len(page_pdfs)} pages: 1 overview + {len(tiles)} tiles "
        f"[{p_cnt}P/{l_cnt}L] + {len(stencil_svgs)} stencil page(s), rows={''.join(row_seq)}, {tree_w_mm / 10:.1f}x{height_cm}cm)"
    )


def main():
    data = load_tree_and_leds()
    stencils = load_ornament_stencils() + load_pcb_artwork_stencils()
    for h_cm in TARGET_HEIGHTS_CM:
        generate_for_height(data, stencils, h_cm)


if __name__ == "__main__":
    main()
