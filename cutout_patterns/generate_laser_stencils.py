#!/usr/bin/env python3
"""
Generate 1:1 scale laser-cuttable SVGs for each Ornament spray stencil step
at target tree heights of 40 cm, 85 cm, and 105 cm.

Each SVG:
  - Uses physical millimeter units (1 user unit = 1 mm, width/height in mm)
  - Includes a 50 mm (5 cm) solid border on all 4 sides around the ornament
    for sticking protective painter's tape / masking paper
  - Bakes the 1:1 scale and border offset directly into path coordinates
    (no nested transforms, for maximum laser-cutter software compatibility)
  - Uses red (#FF0000, 0.1 mm stroke, fill="none") for laser cut paths
    (outer card border, stencil cutout(s), and 2 mm corner alignment holes
    on multi-layer stencils)
  - Uses blue (#0000FF) for an optional engrave/reference label
"""

import html
import re
from pathlib import Path

from generate_cutout_pdfs import (
    TARGET_HEIGHTS_CM,
    _simplify_path_d,
    load_ornament_stencils,
    load_tree_and_leds,
)

OUT_DIR = Path(__file__).resolve().parent / "laser_stencils"
BORDER_MM = 50.0  # 5 cm protective border on all 4 sides
ALIGN_HOLE_OFFSET_MM = 10.0
ALIGN_HOLE_RADIUS_MM = 1.0  # 2.0 mm diameter

STEP_SLUGS = {
    "kugel": [
        "step1_base_silhouette",
        "step2_stripes_hanger",
        "step3_center_dots",
    ],
    "schnee-gross": [
        "step1_base_silhouette",
        "step2_inner_cutouts",
    ],
    "schnee-klein": [
        "step1_full_silhouette",
    ],
    "glitzer": [
        "step1_full_silhouette",
    ],
}


def _transform_path_d(d: str, offset_x: float, offset_y: float, scale: float) -> str:
    """Apply uniform scale and translation directly to an M/L/Z SVG path string."""
    tokens = re.findall(r"[MLZmlz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
    out = []
    i = 0
    cmd = None
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("M", "L", "Z", "m", "l", "z"):
            cmd = tok.upper()
            i += 1
            if cmd == "Z":
                out.append("Z")
            continue
        if cmd in ("M", "L") and i + 1 < len(tokens):
            x = offset_x + float(tokens[i]) * scale
            y = offset_y + float(tokens[i + 1]) * scale
            out.append(f"{cmd} {x:.4f} {y:.4f}")
            cmd = "L"
            i += 2
        else:
            i += 1
    return " ".join(out)


def build_stencil_svg(
    item: dict,
    step_idx: int,
    layer_label: str,
    path_d: str,
    height_cm: int,
    scale: float,
) -> str:
    ow = item["w"] * scale
    oh = item["h"] * scale
    card_w = ow + 2.0 * BORDER_MM
    card_h = oh + 2.0 * BORDER_MM

    # Simplify to 0.02 mm tolerance for smooth laser motion without stutter
    eps_pcb = 0.02 / scale
    simplified_d = _simplify_path_d(path_d, eps_pcb)
    cut_d = _transform_path_d(simplified_d, BORDER_MM, BORDER_MM, scale)

    is_multi = len(item["layers"]) > 1
    clean_label = layer_label.replace("&amp;", "&")
    title_text = f"{item['title']} ({height_cm} cm) - {clean_label}"

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{card_w:.4f}mm" height="{card_h:.4f}mm" '
            f'viewBox="0 0 {card_w:.4f} {card_h:.4f}">'
        ),
        f"  <title>{html.escape(title_text)} | CC-BY-NC-4.0</title>",
        '  <g id="cut" stroke="#FF0000" stroke-width="0.1" fill="none" stroke-linejoin="round">',
        f'    <rect id="outer-border" x="0" y="0" width="{card_w:.4f}" height="{card_h:.4f}"/>',
        f'    <path id="stencil-cut" d="{cut_d}"/>',
    ]

    if is_multi:
        ax1 = ALIGN_HOLE_OFFSET_MM
        ax2 = card_w - ALIGN_HOLE_OFFSET_MM
        ay1 = ALIGN_HOLE_OFFSET_MM
        ay2 = card_h - ALIGN_HOLE_OFFSET_MM
        for idx, (ax, ay) in enumerate(((ax1, ay1), (ax2, ay1), (ax1, ay2), (ax2, ay2)), start=1):
            lines.append(
                f'    <circle id="align-hole-{idx}" cx="{ax:.4f}" cy="{ay:.4f}" r="{ALIGN_HOLE_RADIUS_MM:.4f}"/>'
            )

    lines.extend([
        "  </g>",
        '  <g id="engrave-label" stroke="none" fill="#0000FF" font-family="Arial, Helvetica, sans-serif" font-size="4">',
        f'    <text x="16" y="11.5">{html.escape(title_text)} | 5cm border | CC-BY-NC-4.0</text>',
        "  </g>",
        "</svg>",
        "",
    ])
    return "\n".join(lines)


def main():
    data = load_tree_and_leds()
    ornaments = load_ornament_stencils()

    total_files = 0
    for height_cm in TARGET_HEIGHTS_CM:
        scale = (height_cm * 10.0) / data["height"]
        height_dir = OUT_DIR / f"{height_cm}cm"
        height_dir.mkdir(parents=True, exist_ok=True)

        for item in ornaments:
            slug = item["slug"]
            step_names = STEP_SLUGS[slug]
            for step_idx, ((layer_label, path_d, _ghost_d, _union_fill), step_name) in enumerate(
                zip(item["layers"], step_names), start=1
            ):
                svg_content = build_stencil_svg(
                    item=item,
                    step_idx=step_idx,
                    layer_label=layer_label,
                    path_d=path_d,
                    height_cm=height_cm,
                    scale=scale,
                )
                out_path = height_dir / f"{slug}_{height_cm}cm_{step_name}.svg"
                out_path.write_text(svg_content, encoding="utf-8")
                total_files += 1

    print(f"Generated {total_files} laser-cut stencil SVGs in {OUT_DIR}")


if __name__ == "__main__":
    main()
