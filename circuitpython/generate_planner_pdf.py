#!/usr/bin/env python3
"""
Generate circuitpython/animation_planner_a4.pdf directly from:
  - circuitpython/tannenbaum_leds.svg
  - circuitpython/lib/palettes.svg

Requires `rsvg-convert` (librsvg2-bin).
"""

from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
LEDS_SVG = HERE / "tannenbaum_leds.svg"
PALETTES_SVG = HERE / "lib" / "palettes.svg"
OUT_PDF = HERE / "animation_planner_a4.pdf"

SEGMENT_NAMES = {
    0: "Bough Low (0–17)",
    1: "Bough Mid (18–31)",
    2: "Bough High (32–44)",
    3: "Stem (45–49)",
    4: "Star (50–59)",
}


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

    return leds, polylines


def parse_palettes_svg(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}

    texts = []
    for elem in root.findall(".//svg:text", ns):
        x = float(elem.attrib["x"])
        y = float(elem.attrib["y"])
        txt = "".join(elem.itertext()).strip()
        if x < 50 and y > 55:
            texts.append((y, txt))
    texts.sort(key=lambda t: t[0])

    rects = []
    for elem in root.findall(".//svg:rect", ns):
        if "x" not in elem.attrib or "y" not in elem.attrib:
            continue
        x = float(elem.attrib["x"])
        y = float(elem.attrib["y"])
        fill = elem.attrib.get("fill", "#FFFFFF")
        rects.append((y, x, fill))

    palettes = []
    for i in range(0, len(texts), 2):
        title_y, title = texts[i]
        _, const_name = texts[i + 1]
        row_rects = sorted(
            [r for r in rects if abs(r[0] - (title_y - 10)) < 5],
            key=lambda r: r[1],
        )
        colors = [r[2] for r in row_rects]
        palettes.append((title, const_name, colors))

    return palettes


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_page1_svg(leds, polylines) -> str:
    xs = [c[2] for c in leds]
    ys = [c[3] for c in leds]
    x_min, x_max = min(xs), max(xs)
    y_min = min(ys)

    seg_colors = {}
    for _, seg, _, _, stroke in leds:
        if seg not in seg_colors:
            seg_colors[seg] = stroke

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
        '  <rect width="210" height="297" fill="#FFFFFF"/>',
        '  <text x="12" y="17" font-family="DejaVu Sans, Arial, sans-serif" font-size="4.6" font-weight="bold" fill="#212529">AITY Xmas Tree 2026 — Animation Planner</text>',
        '  <text x="198" y="17" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.0" fill="#6C757D">60 NeoPixels · D10 Data · D5/D6 Buttons</text>',
        '  <rect x="12" y="21.5" width="186" height="9" rx="1.5" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>',
        '  <text x="15" y="27" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#495057">Animation:</text>',
        '  <text x="87" y="27" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#495057">Speed / FPS:</text>',
        '  <text x="135" y="27" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#495057">Btn D5:</text>',
        '  <text x="162" y="27" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#495057">Btn D6:</text>',
        '  <rect x="12" y="34" width="84" height="150" rx="2" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.35"/>',
        '  <text x="15" y="40" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.4" font-weight="bold" fill="#212529">Reference Map (Pixel Index 0–59)</text>',
    ]

    ref_scale = 1.66
    tree_w = (x_max - x_min) * ref_scale
    ref_ox = 12 + (84 - tree_w) / 2.0 - x_min * ref_scale
    ref_oy = 43.0 - y_min * ref_scale

    lines.append(f'  <g transform="translate({ref_ox:.3f},{ref_oy:.3f}) scale({ref_scale:.4f})">')
    for pts, color in polylines:
        lines.append(
            f'    <polyline points="{pts}" fill="none" stroke="{color}" stroke-width="0.25" stroke-opacity="0.4" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    for idx, _, cx, cy, color in leds:
        lines.append(
            f'    <circle cx="{cx:.3f}" cy="{cy:.3f}" r="0.92" fill="#FFFFFF" stroke="{color}" stroke-width="0.25"/>'
        )
        lines.append(
            f'    <text x="{cx:.3f}" y="{cy+0.32:.3f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="0.92" font-weight="bold" fill="#212529">{idx}</text>'
        )
    lines.append('  </g>')

    leg_positions = [
        (16, 170.0), (56, 170.0),
        (16, 175.0), (56, 175.0),
        (16, 180.0),
    ]
    for seg_id in sorted(seg_colors):
        lx, ly = leg_positions[seg_id]
        color = seg_colors[seg_id]
        name = SEGMENT_NAMES.get(seg_id, f"Segment {seg_id}")
        lines.append(f'  <circle cx="{lx}" cy="{ly-0.8}" r="1.1" fill="{color}"/>')
        lines.append(
            f'  <text x="{lx+2.4}" y="{ly}" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.3" fill="#343A40">{seg_id}: {esc(name)}</text>'
        )

    lines.append('  <rect x="100" y="34" width="98" height="150" rx="2" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.35"/>')
    lines.append('  <text x="103" y="40" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.4" font-weight="bold" fill="#212529">Notes, Timing &amp; Code Sketch</text>')
    for gy in range(47, 180, 6):
        for gx in range(105, 196, 6):
            lines.append(f'  <circle cx="{gx}" cy="{gy}" r="0.22" fill="#CED4DA"/>')

    frame_w = 43.5
    frame_gap = 4.0
    frame_y = 188.0
    frame_h = 97.0
    fr_scale = 0.96
    fr_tree_w = (x_max - x_min) * fr_scale

    for fi in range(4):
        fx = 12.0 + fi * (frame_w + frame_gap)
        lines.append(f'  <rect x="{fx:.2f}" y="{frame_y:.2f}" width="{frame_w:.2f}" height="{frame_h:.2f}" rx="2" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.35"/>')
        lines.append(f'  <text x="{fx+3:.2f}" y="{frame_y+5.5:.2f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#212529">Frame {fi+1}</text>')
        lines.append(f'  <text x="{fx+frame_w-3:.2f}" y="{frame_y+5.5:.2f}" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.6" fill="#6C757D">t = ______</text>')
        fox = fx + (frame_w - fr_tree_w) / 2.0 - x_min * fr_scale
        foy = frame_y + 9.5 - y_min * fr_scale
        lines.append(f'  <g transform="translate({fox:.3f},{foy:.3f}) scale({fr_scale:.4f})">')
        for _, _, cx, cy, _ in leds:
            lines.append(f'    <circle cx="{cx:.3f}" cy="{cy:.3f}" r="0.86" fill="#FFFFFF" stroke="#495057" stroke-width="0.24"/>')
        lines.append('  </g>')
        for li in range(3):
            ly = frame_y + 81.0 + li * 5.2
            lines.append(f'  <line x1="{fx+3:.2f}" y1="{ly:.2f}" x2="{fx+frame_w-3:.2f}" y2="{ly:.2f}" stroke="#DEE2E6" stroke-width="0.3"/>')

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def build_page2_svg(palettes) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
        '  <rect width="210" height="297" fill="#FFFFFF"/>',
        '  <text x="12" y="17" font-family="DejaVu Sans, Arial, sans-serif" font-size="4.6" font-weight="bold" fill="#212529">AITY Xmas Tree 2026 — Color Palettes</text>',
        '  <text x="198" y="17" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.0" fill="#6C757D">TwinkleFOX · {0} Palettes × 16 Entries</text>'.format(len(palettes)),
        '  <rect x="12" y="21.5" width="186" height="9" rx="1.5" fill="#F8F9FA" stroke="#DEE2E6" stroke-width="0.3"/>',
        '  <text x="15" y="27" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.8" fill="#495057">Import: <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">from tannenbaum_palettes import PALETTES</tspan>   ·   Usage: <tspan font-family="DejaVu Sans Mono, monospace" font-weight="bold" fill="#212529">PALETTES[id][0..15]</tspan></text>',
        '  <rect x="12" y="34" width="186" height="148" rx="2" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.35"/>',
        '  <text x="16" y="40.5" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.4" font-weight="bold" fill="#212529">Built-in Color Palettes (Index 0–15)</text>',
    ]

    sw_x0 = 75.0
    sw_w = 6.8
    sw_gap = 0.7
    sw_h = 6.8

    for col in range(16):
        cx = sw_x0 + col * (sw_w + sw_gap) + sw_w / 2.0
        lines.append(f'  <text x="{cx:.2f}" y="47.5" text-anchor="middle" font-family="DejaVu Sans Mono, monospace" font-size="2.3" fill="#6C757D">{col}</text>')

    row_y0 = 49.5
    row_step = 13.0

    for r_idx, (title, const_name, colors) in enumerate(palettes):
        ry = row_y0 + r_idx * row_step
        if r_idx > 0:
            lines.append(f'  <line x1="16" y1="{ry-1.8:.2f}" x2="194" y2="{ry-1.8:.2f}" stroke="#F1F3F5" stroke-width="0.3"/>')
        lines.append(f'  <text x="16" y="{ry+3.0:.2f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.7" font-weight="bold" fill="#212529">{esc(title)}</text>')
        lines.append(f'  <text x="16" y="{ry+6.2:.2f}" font-family="DejaVu Sans Mono, monospace" font-size="2.1" fill="#6C757D">{esc(const_name)}</text>')
        for col, hex_c in enumerate(colors):
            sx = sw_x0 + col * (sw_w + sw_gap)
            lines.append(f'  <rect x="{sx:.2f}" y="{ry:.2f}" width="{sw_w:.2f}" height="{sw_h:.2f}" rx="0.9" fill="{hex_c}" stroke="#ADB5BD" stroke-width="0.25"/>')
        uniq = list(dict.fromkeys(colors))
        lines.append(f'  <text x="{sw_x0:.2f}" y="{ry+9.6:.2f}" font-family="DejaVu Sans Mono, monospace" font-size="1.9" fill="#868E96">{" · ".join(uniq)}</text>')

    lines.append('  <rect x="12" y="186" width="186" height="46" rx="2" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.35"/>')
    lines.append('  <text x="16" y="192.5" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.4" font-weight="bold" fill="#212529">Custom Palette Sketch</text>')
    for col in range(16):
        cx = sw_x0 + col * (sw_w + sw_gap) + sw_w / 2.0
        lines.append(f'  <text x="{cx:.2f}" y="197.5" text-anchor="middle" font-family="DejaVu Sans Mono, monospace" font-size="2.2" fill="#6C757D">{col}</text>')

    for c_row in range(2):
        cy = 200.0 + c_row * 14.5
        lines.append(f'  <text x="16" y="{cy+4.8:.2f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="2.7" font-weight="bold" fill="#495057">Custom {c_row+1}:</text>')
        lines.append(f'  <line x1="34" y1="{cy+5.2:.2f}" x2="71" y2="{cy+5.2:.2f}" stroke="#DEE2E6" stroke-width="0.3"/>')
        for col in range(16):
            sx = sw_x0 + col * (sw_w + sw_gap)
            lines.append(f'  <rect x="{sx:.2f}" y="{cy:.2f}" width="{sw_w:.2f}" height="8.2" rx="0.9" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.3"/>')

    lines.append('  <rect x="12" y="236" width="186" height="49" rx="2" fill="#FFFFFF" stroke="#CED4DA" stroke-width="0.35"/>')
    lines.append('  <text x="16" y="242.5" font-family="DejaVu Sans, Arial, sans-serif" font-size="3.4" font-weight="bold" fill="#212529">Palette Notes &amp; Segment Color Assignment</text>')
    for gy in range(249, 282, 6):
        for gx in range(17, 195, 6):
            lines.append(f'  <circle cx="{gx}" cy="{gy}" r="0.22" fill="#CED4DA"/>')

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main():
    leds, polylines = parse_leds_svg(LEDS_SVG)
    palettes = parse_palettes_svg(PALETTES_SVG)

    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "page1.svg"
        p2 = Path(tmpdir) / "page2.svg"
        p1.write_text(build_page1_svg(leds, polylines), encoding="utf-8")
        p2.write_text(build_page2_svg(palettes), encoding="utf-8")
        subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", str(OUT_PDF), str(p1), str(p2)],
            check=True,
        )
    print(f"Generated {OUT_PDF} from {LEDS_SVG.name} and {PALETTES_SVG.name}")


if __name__ == "__main__":
    main()
