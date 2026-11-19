#!/usr/bin/env python3
"""
Generate tiled A4 1:1 cutout pattern PDFs for the AITY Xmas Tree 2026
at target heights of 40 cm, 85 cm, and 105 cm, including:
  - Exact KiCad Edge.Cuts tree outline
  - 60 LED center holes (5 mm circle + precision crosshair + LED index)
  - 15 mm overlap strips, registration crosshairs, and tile grid labels
  - Page 1 assembly overview & 100 mm print-scale verification bar

Requires only the Python 3 standard library (generates PDF 1.4 directly with
built-in Helvetica Type1 fonts and zero transparency for universal printer
compatibility).
"""

import json
import math
import re
import zlib
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


MM_TO_PT = 72.0 / 25.4


def _hex_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return (
        int(h[0:2], 16) / 255.0,
        int(h[2:4], 16) / 255.0,
        int(h[4:6], 16) / 255.0,
    )


def _winansi_text(s: str) -> str:
    s = (
        s.replace("\u2702", "CUT")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
    )
    return s


def _pdf_escape(b: bytes) -> bytes:
    out = bytearray()
    for byte in b:
        if byte in (40, 41, 92):  # (, ), \
            out.append(92)
        out.append(byte)
    return bytes(out)


def _approx_text_width(text: str, size: float, bold: bool = False) -> float:
    w = 0.0
    for ch in text:
        if ch in " iIl1.,|!:;'`":
            w += 0.28
        elif ch in "fjt()[]{}/-":
            w += 0.34
        elif ch in "MWmw@#%&":
            w += 0.82
        elif ch.isupper():
            w += 0.66
        else:
            w += 0.52
    if bold:
        w *= 1.06
    return w * size


class PdfPageBuilder:
    def __init__(self, width_mm: float, height_mm: float):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.width_pt = width_mm * MM_TO_PT
        self.height_pt = height_mm * MM_TO_PT
        self.cmds = [
            f"{MM_TO_PT:.8f} 0 0 -{MM_TO_PT:.8f} 0 {self.height_pt:.4f} cm"
        ]

    def push_clip(self, x: float, y: float, w: float, h: float):
        self.cmds.append(f"q {x:.4f} {y:.4f} {w:.4f} {h:.4f} re W n")

    def push_transform(self, tx: float, ty: float, scale: float):
        self.cmds.append(f"q {scale:.6f} 0 0 {scale:.6f} {tx:.4f} {ty:.4f} cm")

    def pop(self):
        self.cmds.append("Q")

    def _set_stroke(self, stroke: str, stroke_width: float, dash=None, linejoin=None):
        r, g, b = _hex_rgb(stroke)
        self.cmds.append(f"{r:.4f} {g:.4f} {b:.4f} RG {stroke_width:.5f} w")
        self.cmds.append("1 j" if linejoin == "round" else "0 j")
        if dash:
            d_str = " ".join(f"{v:.4f}" for v in dash)
            self.cmds.append(f"[{d_str}] 0 d")
        else:
            self.cmds.append("[] 0 d")

    def _set_fill(self, fill: str):
        r, g, b = _hex_rgb(fill)
        self.cmds.append(f"{r:.4f} {g:.4f} {b:.4f} rg")

    def rect(self, x: float, y: float, w: float, h: float, fill=None, stroke=None, stroke_width=0.3, dash=None):
        if fill:
            self._set_fill(fill)
        if stroke:
            self._set_stroke(stroke, stroke_width, dash=dash)
        self.cmds.append(f"{x:.4f} {y:.4f} {w:.4f} {h:.4f} re")
        if fill and stroke:
            self.cmds.append("B")
        elif fill:
            self.cmds.append("f")
        elif stroke:
            self.cmds.append("S")

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke="#000000", stroke_width=0.3, dash=None):
        self._set_stroke(stroke, stroke_width, dash=dash)
        self.cmds.append(f"{x1:.4f} {y1:.4f} m {x2:.4f} {y2:.4f} l S")

    def circle(self, cx: float, cy: float, r: float, fill=None, stroke=None, stroke_width=0.3):
        if fill:
            self._set_fill(fill)
        if stroke:
            self._set_stroke(stroke, stroke_width)
        k = 0.5522847498 * r
        self.cmds.append(
            f"{cx + r:.4f} {cy:.4f} m "
            f"{cx + r:.4f} {cy + k:.4f} {cx + k:.4f} {cy + r:.4f} {cx:.4f} {cy + r:.4f} c "
            f"{cx - k:.4f} {cy + r:.4f} {cx - r:.4f} {cy + k:.4f} {cx - r:.4f} {cy:.4f} c "
            f"{cx - r:.4f} {cy - k:.4f} {cx - k:.4f} {cy - r:.4f} {cx:.4f} {cy - r:.4f} c "
            f"{cx + k:.4f} {cy - r:.4f} {cx + r:.4f} {cy - k:.4f} {cx + r:.4f} {cy:.4f} c h"
        )
        if fill and stroke:
            self.cmds.append("B")
        elif fill:
            self.cmds.append("f")
        elif stroke:
            self.cmds.append("S")

    def path(self, d: str, fill=None, stroke=None, stroke_width=0.3, dash=None, linejoin=None):
        if not d:
            return
        tokens = re.findall(r"[MLZmlz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
        if not tokens:
            return
        if fill:
            self._set_fill(fill)
        if stroke:
            self._set_stroke(stroke, stroke_width, dash=dash, linejoin=linejoin)
        path_cmds = []
        i = 0
        cmd = None
        while i < len(tokens):
            tok = tokens[i]
            if tok in ("M", "L", "Z", "m", "l", "z"):
                cmd = tok.upper()
                i += 1
                if cmd == "Z":
                    path_cmds.append("h")
                continue
            if cmd in ("M", "L") and i + 1 < len(tokens):
                x = float(tokens[i])
                y = float(tokens[i + 1])
                op = "m" if cmd == "M" else "l"
                path_cmds.append(f"{x:.4f} {y:.4f} {op}")
                cmd = "L"
                i += 2
            else:
                i += 1
        if not path_cmds:
            return
        for k in range(0, len(path_cmds), 8):
            self.cmds.append(" ".join(path_cmds[k : k + 8]))
        if fill and stroke:
            self.cmds.append("B")
        elif fill:
            self.cmds.append("f")
        elif stroke:
            self.cmds.append("S")

    def text(self, x: float, y: float, content: str, size: float, fill="#111111", bold=False, anchor="start", rotate_neg90=False):
        clean = _winansi_text(content)
        font_ref = "/F2" if bold else "/F1"
        r, g, b = _hex_rgb(fill)
        tw = _approx_text_width(clean, size, bold=bold)

        if rotate_neg90:
            # In Y-down mm space, text reads bottom-to-top; shift along Y for anchor
            if anchor == "middle":
                y += tw / 2.0
            elif anchor == "end":
                y += tw
            tm = f"0 -1 -1 0 {x:.4f} {y:.4f} Tm"
        else:
            if anchor == "middle":
                x -= tw / 2.0
            elif anchor == "end":
                x -= tw
            tm = f"1 0 0 -1 {x:.4f} {y:.4f} Tm"

        raw_bytes = clean.encode("latin-1", errors="replace")
        esc = _pdf_escape(raw_bytes).decode("latin-1")
        self.cmds.append(f"BT {r:.4f} {g:.4f} {b:.4f} rg {font_ref} {size:.3f} Tf {tm} ({esc}) Tj ET")

    def stream_bytes(self) -> bytes:
        return ("\n".join(self.cmds) + "\n").encode("latin-1")


def _rdp_simplify(pts, eps: float):
    """Iterative Ramer-Douglas-Peucker polyline simplification."""
    if len(pts) <= 3 or eps <= 0.0:
        return pts
    keep = [False] * len(pts)
    keep[0] = True
    keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        s, e = stack.pop()
        if e <= s + 1:
            continue
        ax, ay = pts[s]
        bx, by = pts[e]
        dx, dy = bx - ax, by - ay
        len_sq = dx * dx + dy * dy
        max_d = -1.0
        idx = -1
        for i in range(s + 1, e):
            px, py = pts[i]
            if len_sq == 0.0:
                d = math.hypot(px - ax, py - ay)
            else:
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
                d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
            if d > max_d:
                max_d = d
                idx = i
        if max_d > eps and idx != -1:
            keep[idx] = True
            stack.append((s, idx))
            stack.append((idx, e))
    return [p for p, k in zip(pts, keep) if k]


def _simplify_path_d(d: str, eps: float) -> str:
    """Simplify each subpath in an M/L/Z SVG path string within tolerance eps."""
    if not d:
        return d
    out_parts = []
    chunks = re.split(r"([Zz])", d.strip())
    i = 0
    while i < len(chunks):
        seg = chunks[i].strip()
        closed = i + 1 < len(chunks) and chunks[i + 1] in ("Z", "z")
        i += 2 if closed else 1
        if not seg:
            continue
        sub_ms = re.split(r"(?=[Mm])", seg)
        for sub in sub_ms:
            sub = sub.strip()
            if not sub:
                continue
            pts = [(float(x), float(y)) for x, y in re.findall(r"[MLml]\s*([-\d.]+)\s+([-\d.]+)", sub)]
            if not pts:
                continue
            spts = _rdp_simplify(pts, eps)
            cmds = [f"M {spts[0][0]:.4f} {spts[0][1]:.4f}"]
            for x, y in spts[1:]:
                cmds.append(f"L {x:.4f} {y:.4f}")
            if closed:
                cmds.append("Z")
            out_parts.append(" ".join(cmds))
    return " ".join(out_parts)


def write_pdf_document(pages: list, out_pdf: Path):
    """Write a clean, zero-transparency PDF 1.4 with standard Type1 Helvetica fonts."""
    # Object numbering:
    # 1: Catalog, 2: Pages, 3: Font F1 (Helvetica), 4: Font F2 (Helvetica-Bold)
    # Then per page: (content_obj_id, page_obj_id)
    objects = []
    page_ids = []
    next_id = 5
    page_entries = []

    for page in pages:
        content_id = next_id
        page_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        page_entries.append((page, content_id, page_id))

    kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append((1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    objects.append((2, f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>".encode("ascii")))
    objects.append((3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"))
    objects.append((4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"))

    for page, content_id, page_id in page_entries:
        raw_stream = page.stream_bytes()
        stream = zlib.compress(raw_stream, level=9)
        content_body = (
            f"<< /Length {len(stream)} /Filter /FlateDecode >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream"
        )
        objects.append((content_id, content_body))
        page_body = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {page.width_pt:.4f} {page.height_pt:.4f}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects.append((page_id, page_body))

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for obj_id, body in objects:
        offsets[obj_id] = len(out)
        out.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        out.extend(body)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    total_objs = len(objects) + 1
    out.extend(f"xref\n0 {total_objs}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for obj_id in range(1, total_objs):
        out.extend(f"{offsets[obj_id]:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    out_pdf.write_bytes(bytes(out))


def build_overview_page(data, height_cm: int, scale: float, row_seq, tiles) -> PdfPageBuilder:
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

    ov_w, ov_h = A4_SHORT, A4_LONG
    p = PdfPageBuilder(ov_w, ov_h)
    p.rect(0, 0, ov_w, ov_h, fill="#FFFFFF")

    p.text(15, 20, f"AITY Xmas Tree 2026 - {height_cm} cm A4 Cutout Pattern", 6.5, fill="#111111", bold=True)
    p.text(
        15,
        27.5,
        f"Tree Size: {tree_w_mm / 10.0:.1f} cm x {height_cm}.0 cm  |  {len(tiles)} A4 Tiles ({orient_desc})  |  Overlap: {OVERLAP:.0f} mm",
        3.6,
        fill="#444444",
    )
    p.text(
        15,
        34,
        'IMPORTANT: Print at 100% ("Actual Size" / Scale 1.0) - do NOT enable "Fit to Page".',
        3.4,
        fill="#B02A37",
        bold=True,
    )

    # 100 mm calibration bar
    p.text(65, 39.8, "Scale Check: 100 mm (10 cm)", 2.8, fill="#111111", anchor="middle")
    p.line(15, 43.0, 115, 43.0, stroke="#111111", stroke_width=0.45)
    p.line(15, 40.5, 15, 45.5, stroke="#111111", stroke_width=0.45)
    p.line(65, 41.2, 65, 44.8, stroke="#111111", stroke_width=0.35)
    p.line(115, 40.5, 115, 45.5, stroke="#111111", stroke_width=0.45)

    box_x, box_y, box_w, box_h = 15.0, 52.0, 180.0, 195.0
    ov_scale = min(box_w / grid_w_mm, box_h / grid_h_mm)
    draw_w = grid_w_mm * ov_scale
    draw_h = grid_h_mm * ov_scale
    gx0 = box_x + (box_w - draw_w) / 2.0
    gy0 = box_y + (box_h - draw_h) / 2.0

    # Draw scaled tree outline in overview (opaque light green fill, behind tile grid)
    tree_ov_scale = scale * ov_scale
    tx0 = gx0 + (0.0 - min_gx - data["min_x"] * scale) * ov_scale
    ty0 = gy0 + (0.0 - min_gy - data["min_y"] * scale) * ov_scale
    p.push_transform(tx0, ty0, tree_ov_scale)
    p.path(
        data["edge_path"],
        fill="#F1F9F4",
        stroke="#111111",
        stroke_width=0.45 / tree_ov_scale,
        linejoin="round",
    )
    for _idx, lx, ly in data["leds"]:
        p.circle(lx, ly, 1.3 / tree_ov_scale, stroke="#1971C2", stroke_width=0.25 / tree_ov_scale)
    p.pop()

    # Draw each active tile rectangle on top
    for t in tiles:
        tx = gx0 + (t["gx"] - min_gx) * ov_scale
        ty = gy0 + (t["gy"] - min_gy) * ov_scale
        tw = t["pw"] * ov_scale
        th = t["ph"] * ov_scale
        label = f"R{t['r'] + 1}C{t['c'] + 1} ({t['orient']})"
        p.rect(tx, ty, tw, th, stroke="#ADB5BD", stroke_width=0.28, dash=(1.5, 1.0))
        p.text(tx + 2.2, ty + 4.8, label, 2.8, fill="#495057", bold=True)

    p.text(
        15,
        264,
        f"Assembly: Trim/fold along the {MARGIN:.0f} mm margin & {OVERLAP:.0f} mm overlap guides, align (+) crosshairs, and glue/tape tiles in order.",
        2.9,
        fill="#444444",
    )
    p.text(
        15,
        270,
        "LED Holes: Each of the 60 LED positions (0-59) is marked with a 5 mm center circle and crosshair (+). (P)=Portrait, (L)=Landscape.",
        2.9,
        fill="#444444",
    )
    return p


def _overlap_reg_xs(gx_a1: float, gx_a2: float, gx_b1: float, gx_b2: float):
    """Return grid-X positions for registration crosshairs along a shared horizontal seam."""
    ox1 = max(gx_a1, gx_b1)
    ox2 = min(gx_a2, gx_b2)
    if ox2 - ox1 < 12.0:
        return []
    if ox2 - ox1 >= 40.0:
        return [ox1 + 10.0, ox2 - 10.0]
    return [(ox1 + ox2) / 2.0]


def build_tile_page(data, height_cm: int, scale: float, tile, tiles, n_rows: int) -> PdfPageBuilder:
    page_w = tile["page_w"]
    page_h = tile["page_h"]
    pw = tile["pw"]
    ph = tile["ph"]
    r = tile["r"]
    c = tile["c"]
    gx = tile["gx"]
    gy = tile["gy"]

    tx = MARGIN - gx - data["min_x"] * scale
    ty = MARGIN - gy - data["min_y"] * scale

    p = PdfPageBuilder(page_w, page_h)
    p.rect(0, 0, page_w, page_h, fill="#FFFFFF")

    x_left_cut = MARGIN
    x_right_glue = page_w - MARGIN - OVERLAP
    y_top_cut = MARGIN
    y_bottom_glue = page_h - MARGIN - OVERLAP

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

    # Opaque light-orange glue-area highlights drawn BEHIND the tree & lines (no transparency)
    if has_right:
        p.rect(x_right_glue, MARGIN, OVERLAP, ph, fill="#FFF9F2")
    if below_overlaps:
        p.rect(MARGIN, y_bottom_glue, pw, OVERLAP, fill="#FFF9F2")

    # Clipped 1:1 tree + LED center holes
    p.push_clip(MARGIN, MARGIN, pw, ph)
    p.push_transform(tx, ty, scale)
    p.path(data["edge_path"], stroke="#000000", stroke_width=0.45 / scale, linejoin="round")
    p.pop()

    hole_r = 2.5
    cross_arm = 4.0
    sw_circle = 0.28
    sw_cross = 0.20
    for idx, lx, ly in data["leds"]:
        px = tx + lx * scale
        py = ty + ly * scale
        if px < MARGIN - 10 or px > page_w - MARGIN + 10 or py < MARGIN - 10 or py > page_h - MARGIN + 10:
            continue
        p.circle(px, py, hole_r, stroke="#1971C2", stroke_width=sw_circle)
        p.line(px - cross_arm, py, px + cross_arm, py, stroke="#1971C2", stroke_width=sw_cross)
        p.line(px, py - cross_arm, px, py + cross_arm, stroke="#1971C2", stroke_width=sw_cross)
        p.text(px + 3.4, py + 1.1, str(idx), 2.8, fill="#1971C2", bold=True)
    p.pop()

    # Printable boundary
    p.rect(MARGIN, MARGIN, pw, ph, stroke="#868E96", stroke_width=0.25, dash=(2.0, 1.5))

    def add_reg_mark(mx: float, my: float):
        p.circle(mx, my, 2.0, stroke="#D9480F", stroke_width=0.28)
        p.line(mx - 3.2, my, mx + 3.2, my, stroke="#D9480F", stroke_width=0.28)
        p.line(mx, my - 3.2, mx, my + 3.2, stroke="#D9480F", stroke_width=0.28)

    def add_tick_v(mx: float, my: float):
        p.line(mx - 2.2, my, mx + 2.2, my, stroke="#D9480F", stroke_width=0.30)

    def add_tick_h(mx: float, my: float):
        p.line(mx, my - 2.2, mx, my + 2.2, stroke="#D9480F", stroke_width=0.30)

    v_ticks = [MARGIN + ph * f for f in (0.25, 0.5, 0.75)]
    h_ticks = [MARGIN + pw * f for f in (0.25, 0.5, 0.75)]

    # Left cut line
    if has_left:
        p.line(x_left_cut, MARGIN, x_left_cut, page_h - MARGIN, stroke="#D9480F", stroke_width=0.35, dash=(3.0, 1.5))
        for ty_tick in v_ticks:
            add_tick_v(x_left_cut, ty_tick)
        p.text(
            x_left_cut - 2.0,
            page_h / 2.0,
            f"CUT ON THIS LINE & ALIGN ON R{r + 1}C{c}",
            2.5,
            fill="#D9480F",
            bold=True,
            anchor="middle",
            rotate_neg90=True,
        )

    # Right glue-under line
    if has_right:
        p.line(x_right_glue, MARGIN, x_right_glue, page_h - MARGIN, stroke="#D9480F", stroke_width=0.35, dash=(3.0, 1.5))
        for ty_tick in v_ticks:
            add_tick_v(x_right_glue, ty_tick)
        p.text(
            x_right_glue + 7.5,
            page_h / 2.0,
            f"GLUE AREA (15mm) - Align R{r + 1}C{c + 2} cut edge ON line",
            2.5,
            fill="#D9480F",
            bold=True,
            anchor="middle",
            rotate_neg90=True,
        )

    # Top cut line
    if above_overlaps:
        above_labels = ", ".join(f"R{ot['r'] + 1}C{ot['c'] + 1}" for ot in above_overlaps)
        p.line(MARGIN, y_top_cut, page_w - MARGIN, y_top_cut, stroke="#D9480F", stroke_width=0.35, dash=(3.0, 1.5))
        for tx_tick in h_ticks:
            add_tick_h(tx_tick, y_top_cut)
        p.text(
            page_w / 2.0,
            y_top_cut - 1.4,
            f"CUT ON THIS LINE & ALIGN ON {above_labels}",
            2.4,
            fill="#D9480F",
            bold=True,
            anchor="middle",
        )
        for ot in above_overlaps:
            for rx_g in _overlap_reg_xs(gx, gx + pw, ot["gx"], ot["gx"] + ot["pw"]):
                add_reg_mark(MARGIN + (rx_g - gx), y_top_cut)

    # Bottom glue-under line
    if below_overlaps:
        below_labels = ", ".join(f"R{ot['r'] + 1}C{ot['c'] + 1}" for ot in below_overlaps)
        p.line(MARGIN, y_bottom_glue, page_w - MARGIN, y_bottom_glue, stroke="#D9480F", stroke_width=0.35, dash=(3.0, 1.5))
        for tx_tick in h_ticks:
            add_tick_h(tx_tick, y_bottom_glue)
        p.text(
            page_w / 2.0,
            y_bottom_glue + 8.5,
            f"GLUE AREA (15mm) - Align {below_labels} cut edge ON line",
            2.5,
            fill="#D9480F",
            bold=True,
            anchor="middle",
        )
        for ot in below_overlaps:
            for rx_g in _overlap_reg_xs(gx, gx + pw, ot["gx"], ot["gx"] + ot["pw"]):
                add_reg_mark(MARGIN + (rx_g - gx), y_bottom_glue)

    # Vertical seam registration crosshairs
    if has_left:
        add_reg_mark(x_left_cut, y_top_cut)
        add_reg_mark(x_left_cut, y_bottom_glue)
    if has_right:
        add_reg_mark(x_right_glue, y_top_cut)
        add_reg_mark(x_right_glue, y_bottom_glue)

    # Header badge in top margin
    orient_word = "Portrait" if tile["orient"] == "P" else "Landscape"
    p.text(
        MARGIN,
        4.8,
        f"AITY Xmas Tree 2026 · {height_cm} cm (1:1) · Tile R{r + 1}C{c + 1} ({orient_word}, Row {r + 1}/{n_rows})",
        2.9,
        fill="#212529",
        bold=True,
    )
    p.text(page_w - MARGIN, 4.8, "Print 100% / Actual Size", 2.6, fill="#6C757D", anchor="end")
    return p


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


def build_stencil_pages(stencils, height_cm: int, scale: float):
    """Build A4 Portrait PDF pages containing 1:1 scaled multi-layer spray stencils."""
    page_w, page_h = A4_SHORT, A4_LONG
    pad = 12.0       # Page outer margin
    gap = 6.0        # Gap between stencil cards
    card_pad = 10.0  # Spray-masking border around stencil inside each card
    header_h = 9.0   # Title band inside card above spray area
    top_y = 28.0     # Below page title
    max_cw = page_w - 2 * pad
    max_ch = page_h - top_y - pad

    # Build card specs, automatically splitting oversized branch cards into 2 overlapping A4 halves
    eps_pcb = 0.10 / scale
    cards = []
    for item in stencils:
        ow = item["w"] * scale
        oh = item["h"] * scale
        cw = max(48.0, ow + 2 * card_pad)
        ch = header_h + oh + 2 * card_pad
        is_multi = len(item["layers"]) > 1
        s_edge_d = _simplify_path_d(item["edge_d"], eps_pcb) if item["edge_d"] else None

        if cw <= max_cw and ch <= max_ch:
            for layer_label, path_d, ghost_d, union_fill in item["layers"]:
                cards.append({
                    "title": item["title"],
                    "layer_label": layer_label,
                    "path_d": _simplify_path_d(path_d, eps_pcb),
                    "ghost_d": _simplify_path_d(ghost_d, eps_pcb) if ghost_d else None,
                    "union_fill": union_fill,
                    "edge_d": s_edge_d,
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
                        "title": f"{item['title']} - Part {part_idx}/2",
                        "layer_label": layer_label,
                        "path_d": _simplify_path_d(path_d, eps_pcb),
                        "ghost_d": _simplify_path_d(ghost_d, eps_pcb) if ghost_d else None,
                        "union_fill": union_fill,
                        "edge_d": s_edge_d,
                        "is_multi": is_multi,
                        "ow": half_ow,
                        "oh": oh,
                        "cw": half_cw,
                        "ch": ch,
                        "clip_x": clip_x,
                        "clip_w": half_ow,
                    })

    # Shelf-pack cards onto A4 pages
    pages_cards = []
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
            pages_cards.append(cur_cards)
            cur_cards = []
            x_cur = pad
            y_cur = top_y
            row_h = 0.0
        cur_cards.append((x_cur, y_cur, card))
        x_cur += card["cw"] + gap
        row_h = max(row_h, card["ch"])

    if cur_cards:
        pages_cards.append(cur_cards)

    pdf_pages = []
    total_pages = len(pages_cards)
    for pi, placed in enumerate(pages_cards, start=1):
        p = PdfPageBuilder(page_w, page_h)
        p.rect(0, 0, page_w, page_h, fill="#FFFFFF")
        p.text(pad, 14, f"AITY Xmas Tree 2026 · {height_cm} cm - Spray Stencils ({pi}/{total_pages})", 4.2, fill="#111111", bold=True)
        p.text(
            pad,
            20.0,
            "Cut WHITE shapes (keep gray mask). Multi-layer: cut the 4 corner ALIGN dots in Layer 1 so Layer 2/3 snap right onto them.",
            2.8,
            fill="#444444",
        )
        p.text(page_w - pad, 14, "Print 100% / Actual Size", 2.8, fill="#6C757D", anchor="end")

        for _ci, (cx, cy, card) in enumerate(placed):
            cw, ch = card["cw"], card["ch"]
            p.rect(cx, cy, cw, ch, fill="#F1F3F5", stroke="#495057", stroke_width=0.30, dash=(2.5, 1.5))
            p.text(cx + 2.5, cy + 4.2, card["title"], 2.6, fill="#212529", bold=True)
            p.text(cx + 2.5, cy + 7.6, card["layer_label"].replace("&amp;", "&"), 2.2, fill="#D9480F", bold=True)

            # 4 corner registration crosshairs + 2.0 mm cutout ALIGN dots on multi-layer stencils
            rx1 = cx + 4.0
            rx2 = cx + cw - 4.0
            ry1 = cy + header_h + 4.0
            ry2 = cy + ch - 4.0
            for rx in (rx1, rx2):
                for ry in (ry1, ry2):
                    if card["is_multi"]:
                        p.circle(rx, ry, 1.0, fill="#FFFFFF", stroke="#D9480F", stroke_width=0.28)
                    else:
                        p.circle(rx, ry, 1.6, stroke="#D9480F", stroke_width=0.25)
                    p.line(rx - 2.6, ry, rx + 2.6, ry, stroke="#D9480F", stroke_width=0.25)
                    p.line(rx, ry - 2.6, rx, ry + 2.6, stroke="#D9480F", stroke_width=0.25)
            if card["is_multi"]:
                p.text(rx1 + 2.2, ry1 + 0.9, "ALIGN", 1.9, fill="#D9480F", bold=True)

            ox = cx + (cw - card["ow"]) / 2.0 - (card["clip_x"] or 0.0)
            oy = cy + header_h + (ch - header_h - card["oh"]) / 2.0

            has_clip = card["clip_x"] is not None
            if has_clip:
                ox_c = cx + (cw - card["ow"]) / 2.0
                oy_c = cy + header_h + (ch - header_h - card["oh"]) / 2.0
                p.push_clip(ox_c - 1.0, oy_c - 2.0, card["clip_w"] + 2.0, card["oh"] + 4.0)

            p.push_transform(ox, oy, scale)

            if card["ghost_d"]:
                p.path(
                    card["ghost_d"],
                    stroke="#ADB5BD",
                    stroke_width=0.25 / scale,
                    dash=(1.2 / scale, 1.0 / scale),
                )

            if card["edge_d"]:
                p.path(
                    card["edge_d"],
                    stroke="#2B8A3E",
                    stroke_width=0.35 / scale,
                    dash=(2.0 / scale, 1.2 / scale),
                )

            if card["union_fill"]:
                p.path(card["path_d"], stroke="#000000", stroke_width=0.65 / scale, linejoin="round")
                p.path(card["path_d"], fill="#FFFFFF")
            else:
                p.path(card["path_d"], fill="#FFFFFF", stroke="#000000", stroke_width=0.35 / scale, linejoin="round")

            p.pop()
            if has_clip:
                p.pop()

        pdf_pages.append(p)
    return pdf_pages


def generate_for_height(data, stencils, height_cm: int):
    target_h_mm = height_cm * 10.0
    scale = target_h_mm / data["height"]
    tree_w_mm = data["width"] * scale

    row_seq, tiles = plan_optimal_tiles(data, scale)
    n_rows = len(row_seq)
    stencil_pages = build_stencil_pages(stencils, height_cm, scale)

    out_pdf = OUT_DIR / f"tree_cutout_a4_{height_cm}cm.pdf"

    pages = [build_overview_page(data, height_cm, scale, row_seq, tiles)]
    for tile in tiles:
        pages.append(build_tile_page(data, height_cm, scale, tile, tiles, n_rows))
    pages.extend(stencil_pages)

    write_pdf_document(pages, out_pdf)

    p_cnt = sum(1 for t in tiles if t["orient"] == "P")
    l_cnt = sum(1 for t in tiles if t["orient"] == "L")
    print(
        f"Generated {out_pdf} ({len(pages)} pages: 1 overview + {len(tiles)} tiles "
        f"[{p_cnt}P/{l_cnt}L] + {len(stencil_pages)} stencil page(s), rows={''.join(row_seq)}, {tree_w_mm / 10:.1f}x{height_cm}cm)"
    )


def main():
    data = load_tree_and_leds()
    stencils = load_ornament_stencils() + load_pcb_artwork_stencils()
    for h_cm in TARGET_HEIGHTS_CM:
        generate_for_height(data, stencils, h_cm)


if __name__ == "__main__":
    main()
