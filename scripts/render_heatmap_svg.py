#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 contribution heatmap SVG.

Boxes reveal once on load with a diagonal top-left -> bottom-right slide, then
freeze (no looping). Self-contained SVG so GitHub plays the CSS animation.
"""
import json
import os
from datetime import datetime

STATIC = os.environ.get("STATIC") == "1"  # emit frozen final frame (no animation)

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data", "contributions.json")
OUT = os.path.join(HERE, "..", "contrib-heatmap.svg")

# --- layout -----------------------------------------------------------------
CELL = 13          # box + gap
BOX = 11
RADIUS = 2.5
PAD_L = 30         # room for weekday labels
PAD_T = 34         # room for title + month labels
PAD_R = 20
PAD_B = 46         # room for legend + footer

# GitHub-ish green ramp; index by level 0..4 (top end nudged brighter)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG = "#0d1117"
FG = "#8b949e"
FG_BRIGHT = "#c9d1d9"
ACCENT = "#39d353"
FONT = "ui-monospace, 'SF Mono', 'DejaVu Sans Mono', Menlo, Consolas, monospace"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load():
    with open(DATA) as f:
        return json.load(f)


def build_grid(days):
    """Return (cells, n_cols). Each cell: (col, row, day). Sunday = row 0."""
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    # snap back to the Sunday that starts that week (weekday: Mon=0..Sun=6)
    start_sunday = first
    while start_sunday.weekday() != 6:  # 6 == Sunday
        start_sunday = start_sunday.fromordinal(start_sunday.toordinal() - 1)

    cells, max_col = [], 0
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
        delta = (dt - start_sunday).days
        col, row = delta // 7, delta % 7
        cells.append((col, row, d))
        max_col = max(max_col, col)
    return cells, max_col + 1, start_sunday


def month_labels(cells):
    """First column index at which each month first appears."""
    seen, labels = set(), []
    for col, row, d in cells:
        m = d["date"][:7]
        if m not in seen:
            seen.add(m)
            month = int(d["date"][5:7]) - 1
            labels.append((col, MONTHS[month]))
    return labels


def render(data):
    days = data["days"]
    stats = data["stats"]
    cells, n_cols, _ = build_grid(days)

    width = PAD_L + n_cols * CELL + PAD_R
    height = PAD_T + 7 * CELL + PAD_B

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img" '
        f'aria-label="GitHub contribution heatmap">'
    )

    # animation: diagonal reveal, plays once then holds (forwards, no iteration)
    if STATIC:
        parts.append('<style>.c,.fx{opacity:1}</style>')
    else:
        parts.append(
            '<style>'
            '@keyframes cell-in{from{opacity:0;transform:translate(-4px,-4px) scale(.4)}'
            'to{opacity:1;transform:translate(0,0) scale(1)}}'
            '.c{opacity:0;transform-box:fill-box;transform-origin:center;'
            'animation:cell-in .45s ease-out forwards}'
            '@keyframes fade-in{to{opacity:1}}'
            '.fx{opacity:0;animation:fade-in .6s ease-out forwards}'
            '@media (prefers-reduced-motion: reduce){'
            '.c,.fx{animation:none;opacity:1;transform:none}}'
            '</style>'
        )

    # panel
    parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="{BG}"/>'
    )

    # title (fake shell prompt)
    parts.append(
        f'<text x="{PAD_L-14}" y="20" fill="{FG_BRIGHT}" font-size="12">'
        f'<tspan fill="{ACCENT}">bhav@github</tspan> ~ $ '
        f'<tspan fill="{FG}">git log --graph --all</tspan></text>'
    )

    # month labels
    for col, label in month_labels(cells):
        x = PAD_L + col * CELL
        parts.append(
            f'<text x="{x}" y="{PAD_T-4}" fill="{FG}" font-size="9">{label}</text>'
        )

    # weekday labels (Mon / Wed / Fri like GitHub)
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = PAD_T + row * CELL + BOX - 1
        parts.append(
            f'<text x="0" y="{y}" fill="{FG}" font-size="8">{label}</text>'
        )

    # cells — animation-delay drives the diagonal wipe
    total_reveal = 2.4  # seconds across the whole diagonal
    max_diag = (max(c for c, _, _ in cells) + 6) or 1
    for col, row, d in cells:
        x = PAD_L + col * CELL
        y = PAD_T + row * CELL
        color = PALETTE[min(d["level"], len(PALETTE) - 1)]
        delay = (col + row) / max_diag * total_reveal
        parts.append(
            f'<rect class="c" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
            f'rx="{RADIUS}" fill="{color}" style="animation-delay:{delay:.2f}s"/>'
        )

    # legend (Less -> More), fades in after the grid
    legend_y = PAD_T + 7 * CELL + 20
    lx = width - PAD_R - (len(PALETTE) * (BOX + 2)) - 66
    parts.append(
        f'<g class="fx" style="animation-delay:{total_reveal+.2:.2f}s">'
        f'<text x="{lx-6}" y="{legend_y+BOX-2}" fill="{FG}" font-size="9" '
        f'text-anchor="end">Less</text>'
    )
    for i, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx + i*(BOX+2)}" y="{legend_y}" width="{BOX}" height="{BOX}" '
            f'rx="{RADIUS}" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{lx + len(PALETTE)*(BOX+2) + 4}" y="{legend_y+BOX-2}" '
        f'fill="{FG}" font-size="9">More</text></g>'
    )

    # footer stats
    footer_y = legend_y + BOX - 2
    footer = (
        f'{stats["total_last_year"]:,} contributions in the last year   '
        f'\u2022   \u25B2 longest streak {stats["longest_streak"]}d'
    )
    parts.append(
        f'<text class="fx" x="{PAD_L-14}" y="{footer_y}" fill="{FG_BRIGHT}" '
        f'font-size="10" style="animation-delay:{total_reveal+.35:.2f}s">{footer}</text>'
    )

    parts.append("</svg>")
    return "".join(parts)


def main():
    svg = render(load())
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
