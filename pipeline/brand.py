"""Provisional brand: a cartoon alpha-helix logo with a bound ligand, and the palette.

    python3 -m pipeline.brand        # writes assets/logo.svg and assets/logo-mark.svg

Palette: deep navy + emerald green, kept easy on the eyes. Every rendered surface
(issue page, graphical abstract, website) imports its colours from here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .common import ROOT

SITE_NAME = "FoldFeed"
SITE_NAME_EN = "構造生物学デイリー"  # Japanese descriptor shown under the wordmark

DEFAULT_THEME = "a"  # the colour scheme used for rendered graphical abstracts until the owner picks one

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


@dataclass(frozen=True)
class Theme:
    """One complete colour scheme: page, text, accent, graphical-abstract bar and structure colours."""
    key: str
    label: str
    ground: str      # page background
    paper: str       # background of the graphical abstract and other surfaces
    ink: str         # headings and body text
    ink2: str        # secondary text
    muted: str       # labels, captions
    hair: str        # the few rules that are kept
    accent: str      # the single accent colour (marks, ligand)
    accent_ink: str  # the accent as readable text on the ground
    soft: str        # tinted panel behind the structure
    bar: str         # top bar of the graphical abstract
    bar_text: str
    bar_muted: str
    entities: tuple  # colours of the polymer entities in the structure figure
    ligand: str
    loop_back: str   # logo: the far side of the helix
    loop_front: str  # logo: the near side of the helix


THEMES = {
    "a": Theme("a", "苔と墨", ground="#EDF1EE", paper="#FFFFFF", ink="#1B2420", ink2="#3A4741", muted="#68746D",
               hair="#C9D2CC", accent="#4A7C3A", accent_ink="#3A6A2D", soft="#E3EAE5",
               bar="#1B2420", bar_text="#FFFFFF", bar_muted="#A9B8AE",
               entities=("#4A7C3A", "#5A7D96", "#C28F2C", "#8E6B8F", "#B25C4A", "#6FA39A", "#8C8F4A", "#7A6F5E"),
               ligand="#DB5F2A", loop_back="#8FB27F", loop_front="#FFFFFF"),
    "b": Theme("b", "藍と朱", ground="#F0F1EF", paper="#FFFFFF", ink="#1B2638", ink2="#3B4659", muted="#6A7482",
               hair="#CDD1D8", accent="#C8442A", accent_ink="#B33A22", soft="#E4E7EB",
               bar="#1B2638", bar_text="#FFFFFF", bar_muted="#A6B0C2",
               entities=("#3C5A8C", "#C9A04B", "#5F9296", "#A5707A", "#7C8AA8", "#8A9A5B", "#9C7B55", "#6E6E8E"),
               ligand="#D4452B", loop_back="#8DA0C4", loop_front="#FFFFFF"),
    "c": Theme("c", "墨と蛍光", ground="#F3F4F1", paper="#FFFFFF", ink="#141516", ink2="#3A3D40", muted="#6E7377",
               hair="#D0D3D0", accent="#D2F13A", accent_ink="#141516", soft="#E9EBE7",
               bar="#141516", bar_text="#FFFFFF", bar_muted="#A5ABB0",
               entities=("#23282C", "#6F7A82", "#9BA5AC", "#3F4D57", "#818D95", "#B6BEC4", "#323B42", "#5E6A72"),
               ligand="#D2F13A", loop_back="#8A9096", loop_front="#FFFFFF"),
}


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


def logo_mark(x: float, y: float, s: float, bg: str = INK, back: str = EMERALD_SOFT,
              front: str = "#FFFFFF", dot: str = MINT) -> str:
    """SVG fragment: the mark in an s×s rounded square at (x, y)."""
    pts = _coil_points(x, y, s)
    back_segs, front_segs = [], []
    for (x1, y1, c1), (x2, y2, _) in zip(pts, pts[1:]):
        (front_segs if c1 >= 0 else back_segs).append(f"M{x1:.2f},{y1:.2f}L{x2:.2f},{y2:.2f}")
    w = s * 0.105  # thick, cartoon-ribbon weight
    dot_x, dot_y = x + s * 0.805, y + s * 0.205
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * 0.24:.2f}" fill="{bg}"/>'
            # back loops: soft emerald, slightly thinner, sitting behind
            f'<path d="{"".join(back_segs)}" stroke="{back}" stroke-width="{w * 0.92:.2f}" '
            f'stroke-linecap="round" fill="none"/>'
            # front loops: white, full weight
            f'<path d="{"".join(front_segs)}" stroke="{front}" stroke-width="{w:.2f}" '
            f'stroke-linecap="round" fill="none"/>'
            # bound ligand
            f'<circle cx="{dot_x:.2f}" cy="{dot_y:.2f}" r="{s * 0.092:.2f}" fill="{dot}" '
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
