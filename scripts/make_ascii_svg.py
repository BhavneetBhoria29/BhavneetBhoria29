#!/usr/bin/env python3
"""Convert source-prepped.png into a self-typing monochrome ASCII-art SVG.

Each row is revealed left-to-right on a top-to-bottom stagger (a block cursor
rides the wipe edge). Prints once and freezes -- no looping. SMIL animation so
GitHub plays it inside an <img>. STATIC=1 emits a frozen frame.
"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "source-prepped.png")
OUT = os.path.join(HERE, "..", "avi-ascii.svg")
STATIC = os.environ.get("STATIC") == "1"

COLS = 100                       # character grid width
RAMP = " .`:-=+*cs#%@"           # bright (sparse) -> dark (dense)
CW, CH = 6.0, 10.5               # char cell advance / line height (px)
FG = "#9aa4ad"                   # single light-gray fill (monochrome!)
CURSOR = "#39d353"
BG = "#0d1117"
FONT = "ui-monospace, 'SF Mono', 'DejaVu Sans Mono', Menlo, Consolas, monospace"

ROW_DUR = 0.5                    # seconds to wipe one row
STAGGER = 0.11                   # seconds between successive rows


def to_grid(img):
    g = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = g.shape
    rows = max(1, int(COLS * (h / w) * (CW / CH)))  # correct for cell aspect
    small = np.asarray(
        Image.fromarray(g.astype(np.uint8)).resize((COLS, rows), Image.LANCZOS),
        dtype=np.float32,
    )
    # bright -> sparse glyph (space); dark -> dense glyph
    idx = ((255.0 - small) / 255.0 * (len(RAMP) - 1)).round().astype(int)
    idx = idx.clip(0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row) for row in idx]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(lines):
    ncols = max((len(l) for l in lines), default=COLS)
    width = int(ncols * CW + 16)
    height = int(len(lines) * CH + 16)
    x0, y0 = 8, 12

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" '
        f'font-size="{CH:.1f}" role="img" aria-label="ASCII self-portrait">'
    ]
    p.append(f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>')

    full_w = ncols * CW

    for i, line in enumerate(lines):
        y = y0 + i * CH
        text = (
            f'<text x="{x0}" y="{y + CH - 2:.1f}" xml:space="preserve" '
            f'fill="{FG}" letter-spacing="0">{esc(line)}</text>'
        )
        if STATIC:
            p.append(text)
            continue

        begin = i * STAGGER
        clip_id = f"wipe{i}"
        # clip rect grows 0 -> full width => left-to-right reveal
        p.append(
            f'<clipPath id="{clip_id}"><rect x="{x0}" y="{y}" height="{CH:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{full_w:.1f}" '
            f'begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        p.append(f'<g clip-path="url(#{clip_id})">{text}</g>')
        # block cursor riding the wipe edge, disappears when the row finishes
        p.append(
            f'<rect y="{y}" width="{CW:.1f}" height="{CH:.1f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{x0}" to="{x0 + full_w:.1f}" '
            f'begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;0.9;0.9;0" '
            f'keyTimes="0;0.02;0.98;1" begin="{begin:.2f}s" dur="{ROW_DUR}s" '
            f'fill="freeze"/></rect>'
        )

    p.append("</svg>")
    return "".join(p)


def main():
    if not os.path.exists(SRC):
        raise SystemExit(
            f"missing {SRC} — run scripts/prep_photo.py <photo> first"
        )
    lines = to_grid(Image.open(SRC))
    with open(OUT, "w") as f:
        f.write(build(lines))
    print(f"wrote {OUT} ({len(lines)} rows)")


if __name__ == "__main__":
    main()
