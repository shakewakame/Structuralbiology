"""Provisional brand: a cartoon alpha-helix logo with a bound ligand, and the palette.

    python3 -m pipeline.brand        # writes assets/logo.svg and assets/logo-mark.svg

Palette: deep navy + emerald green, kept easy on the eyes. Every rendered surface
(issue page, graphical abstract, website) imports its colours from here.
"""

from __future__ import annotations

import math

from .common import ROOT

SITE_NAME = "FoldFeed"
SITE_NAME_EN = "構造生物学デイリー"  # Japanese descriptor shown under the wordmark

# Core palette.
INK = "#16324F"        # deep navy — chrome bars, headings
EMERALD = "#1AA179"    # accent — rules, links, tags
EMERALD_DARK = "#0F7A5A"
EMERALD_SOFT = "#8FD3BE"  # the back loops of the logo coil
MINT = "#35C99A"       # the ligand dot
MUTED = "#5B6B73"      # secondary text
PANEL = "#EDF5F1"      # soft green-grey fill behind the structure
PAGE_BG = "#F7FAF9"
CARD_BG = "#FFFFFF"
HAIRLINE = "#D8E6E0"
BLUE = "#3B6FB6"       # kept for compatibility with older callers

FONT = "'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic',Meiryo,sans-serif"


def _coil_points(x: float, y: float, s: float, turns: float = 3.5, steps: int = 260):
    """A cartoon alpha helix seen from the side: loops drifting up and to the right."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        th = t * turns * 2 * math.pi
        px = x + s * (0.16 + 0.56 * t + 0.165 * math.cos(th))
        py = y + s * (0.52 - 0.16 * (t - 0.5) - 0.185 * math.sin(th))
        pts.append((px, py, math.cos(th)))
    return pts


def logo_mark(x: float, y: float, s: float, bg: str = INK) -> str:
    """SVG fragment: the mark in an s×s rounded square at (x, y)."""
    pts = _coil_points(x, y, s)
    back, front = [], []
    for (x1, y1, c1), (x2, y2, _) in zip(pts, pts[1:]):
        (front if c1 >= 0 else back).append(f"M{x1:.2f},{y1:.2f}L{x2:.2f},{y2:.2f}")
    w = s * 0.105  # thick, cartoon-ribbon weight
    dot_x, dot_y = x + s * 0.805, y + s * 0.205
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * 0.24:.2f}" fill="{bg}"/>'
            # back loops: soft emerald, slightly thinner, sitting behind
            f'<path d="{"".join(back)}" stroke="{EMERALD_SOFT}" stroke-width="{w * 0.92:.2f}" '
            f'stroke-linecap="round" fill="none"/>'
            # front loops: white, full weight
            f'<path d="{"".join(front)}" stroke="#FFFFFF" stroke-width="{w:.2f}" '
            f'stroke-linecap="round" fill="none"/>'
            # bound ligand
            f'<circle cx="{dot_x:.2f}" cy="{dot_y:.2f}" r="{s * 0.092:.2f}" fill="{MINT}" '
            f'stroke="{bg}" stroke-width="{s * 0.02:.2f}"/>')


def logo_svg(height: int = 64, subtitle: bool = True) -> str:
    s = height
    width = int(s * 6.6)
    sub = (f'<text x="{s * 1.26:.1f}" y="{s * 0.88:.1f}" font-size="{s * 0.16:.1f}" '
           f'letter-spacing="{s * 0.02:.1f}" fill="{MUTED}">{SITE_NAME_EN} · β</text>') if subtitle else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{s}" viewBox="0 0 {width} {s}" '
            f'font-family="{FONT}">'
            f'{logo_mark(0, 0, s)}'
            f'<text x="{s * 1.24:.1f}" y="{s * 0.57:.1f}" font-size="{s * 0.45:.1f}" font-weight="700" '
            f'fill="{INK}">{SITE_NAME}</text>{sub}</svg>\n')


def mark_svg(size: int = 128) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'{logo_mark(0, 0, size)}</svg>\n')


def main():
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    (out / "logo.svg").write_text(logo_svg(), encoding="utf-8")
    (out / "logo-mark.svg").write_text(mark_svg(), encoding="utf-8")
    print(f"wrote {out / 'logo.svg'} and {out / 'logo-mark.svg'}")


if __name__ == "__main__":
    main()
