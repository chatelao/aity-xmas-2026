#!/usr/bin/env python3
"""Compress esp32c6-portal/web_ui/index.html into main/include/web_ui_gz.h."""

import gzip
import pathlib
import sys


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    src_html = root / "web_ui" / "index.html"
    out_hdr = root / "main" / "include" / "web_ui_gz.h"

    raw = src_html.read_bytes()
    # Deterministic mtime=0 so generated header is reproducible across builds
    gz = gzip.compress(raw, compresslevel=9, mtime=0)

    lines = [
        "#ifndef WEB_UI_GZ_H",
        "#define WEB_UI_GZ_H",
        "",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        f"// Auto-generated from web_ui/index.html ({len(raw)} bytes raw -> {len(gz)} bytes gzip)",
        f"#define WEB_UI_GZ_LEN {len(gz)}U",
        "",
        "static const uint8_t WEB_UI_GZ_DATA[WEB_UI_GZ_LEN] = {",
    ]

    for i in range(0, len(gz), 16):
        chunk = ", ".join(f"0x{b:02x}" for b in gz[i : i + 16])
        lines.append(f"    {chunk},")

    lines.extend([
        "};",
        "",
        "#endif // WEB_UI_GZ_H",
        "",
    ])

    out_hdr.parent.mkdir(parents=True, exist_ok=True)
    out_hdr.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_hdr} ({len(raw)} B -> {len(gz)} B gzip, {100.0 * len(gz) / len(raw):.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
