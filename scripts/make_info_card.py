#!/usr/bin/env python3
"""Hand-authored neofetch-style info card as a self-contained animated SVG.

Lines fade + slide in on a short stagger so the panel looks like it is
printing next to the ASCII portrait. STATIC=1 emits a frozen frame.
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

BG = "#0d1117"
FG = "#c9d1d9"
DIM = "#8b949e"
KEY = "#39d353"      # neofetch-style bold key color
ACCENT = "#58a6ff"   # user@host accent
FONT = "ui-monospace, 'SF Mono', 'DejaVu Sans Mono', Menlo, Consolas, monospace"

TITLE_USER = "bhav"
TITLE_HOST = "github"

# (key, value) rows.  key="" renders a full-width value line; key=None a rule.
ROWS = [
    ("Role",    "AI Engineer \u2014 RAG / Agentic / LLMOps"),
    ("Focus",   "the eval & observability layer most skip"),
    ("Now",     "MSc AI @ BTU Cottbus  \u00b7  open to EU relocation"),
    ("Prev",    "ML Engineer @ Resolute Worldwise (3+ yrs)"),
    (None, None),
    ("Orchestr","LangGraph \u00b7 LangChain \u00b7 LlamaIndex \u00b7 MCP"),
    ("Serving", "FastAPI \u00b7 Celery/Redis \u00b7 Docker \u00b7 K8s"),
    ("Cloud",   "AWS EKS/Lambda/S3 \u00b7 Terraform IaC"),
    ("Eval",    "RAGAS \u00b7 Langfuse \u00b7 Prometheus \u00b7 Grafana"),
    (None, None),
    ("Ships",   "4 prod-grade agentic systems, full observability"),
    ("Metrics", "0.90 context precision \u00b7 sub-200ms p95"),
    ("Cert",    "IBM RAG & Agentic AI Professional (2026)"),
    ("Langs",   "EN C2 \u00b7 DE B1\u2192B2 \u00b7 Python (daily: Claude Code)"),
]

# terminal color-block row, neofetch signature
BLOCKS = ["#161b22", "#f85149", "#39d353", "#d29922",
          "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]

LINE_H = 22
PAD_X = 18
PAD_TOP = 20
CHAR_W = 7.4       # approx monospace advance at 12.5px
KEY_COL = 78       # px width reserved for the key column


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    # width: fit the longest "key value" line
    longest = max(len((k or "") + (v or "")) for k, v in ROWS) + 12
    width = int(PAD_X * 2 + max(longest * CHAR_W, 360))
    n_visual = len(ROWS) + 4  # title, rule, blocks, breathing room
    height = int(PAD_TOP + n_visual * LINE_H + 24)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img" '
        f'aria-label="Profile info card">'
    ]

    if STATIC:
        p.append("<style>.ln{opacity:1}</style>")
    else:
        p.append(
            "<style>"
            "@keyframes ln-in{from{opacity:0;transform:translateX(-8px)}"
            "to{opacity:1;transform:translateX(0)}}"
            ".ln{opacity:0;animation:ln-in .4s ease-out forwards}"
            "@media (prefers-reduced-motion: reduce){.ln{animation:none;opacity:1;transform:none}}"
            "</style>"
        )

    p.append(f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>')

    y = PAD_TOP + 6
    idx = 0

    def delay(i):
        return f'style="animation-delay:{i*0.09:.2f}s"'

    # title line:  user@host
    p.append(
        f'<text class="ln" {delay(idx)} x="{PAD_X}" y="{y}" font-size="12.5">'
        f'<tspan fill="{ACCENT}" font-weight="bold">{TITLE_USER}@{TITLE_HOST}</tspan></text>'
    )
    idx += 1
    y += LINE_H

    # underline rule (dashes), matching neofetch
    dash = "\u2500" * 34
    p.append(
        f'<text class="ln" {delay(idx)} x="{PAD_X}" y="{y}" font-size="12.5" '
        f'fill="{DIM}">{dash}</text>'
    )
    idx += 1
    y += LINE_H

    for k, v in ROWS:
        if k is None:
            idx += 1
            y += LINE_H // 2 + 4
            continue
        if k == "":
            p.append(
                f'<text class="ln" {delay(idx)} x="{PAD_X}" y="{y}" font-size="12.5" '
                f'fill="{FG}">{esc(v)}</text>'
            )
        else:
            p.append(
                f'<text class="ln" {delay(idx)} x="{PAD_X}" y="{y}" font-size="12.5">'
                f'<tspan fill="{KEY}" font-weight="bold">{esc(k)}</tspan>'
                f'<tspan fill="{DIM}">:</tspan>'
                f'<tspan fill="{FG}" x="{PAD_X + KEY_COL}">{esc(v)}</tspan></text>'
            )
        idx += 1
        y += LINE_H

    # neofetch color blocks
    y += 6
    bx = PAD_X
    p.append(f'<g class="ln" {delay(idx)}>')
    for c in BLOCKS:
        p.append(f'<rect x="{bx}" y="{y-12}" width="16" height="16" rx="2" fill="{c}"/>')
        bx += 20
    p.append("</g>")

    p.append("</svg>")
    return "".join(p)


def main():
    with open(OUT, "w") as f:
        f.write(build())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
