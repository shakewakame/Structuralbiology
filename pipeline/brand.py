"""Provisional brand: a logo mark (an alpha-helix coil with a bound ligand) and the wordmark.

    python3 -m pipeline.brand        # writes assets/logo.svg and assets/logo-mark.svg
"""

from __future__ import annotations

import math

from .common import ROOT

SITE_NAME = "構造生物学デイリー"
SITE_NAME_EN = "STRUCTURAL BIOLOGY DAILY"
INK, MUTED, BLUE, ACCENT = "#1F2A44", "#5A6478", "#3B6FB6", "#E4572E"
FONT = "'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic',Meiryo,sans-serif"


def _coil_points(x: float, y: float, s: float, turns: float = 2.5, steps: int = 200):
    """A helix seen from the side, rising towards the ligand like a cartoon alpha helix."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        th = t * turns * 2 * math.pi
        px = x + s * (0.18 + 0.58 * t + 0.16 * math.cos(th))
        py = y + s * (0.50 - 0.15 * (t - 0.5) - 0.18 * math.sin(th))
        pts.append((px, py, math.cos(th)))
    return pts


def logo_mark(x: float, y: float, s: float, bg: str = INK) -> str:
    """SVG fragment: the mark in an s×s rounded square at (x, y)."""
    pts = _coil_points(x, y, s)
    back, front = [], []
    for (x1, y1, c1), (x2, y2, _) in zip(pts, pts[1:]):
        (front if c1 >= 0 else back).append(f"M{x1:.2f},{y1:.2f}L{x2:.2f},{y2:.2f}")
    w = s * 0.07
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * 0.22:.2f}" fill="{bg}"/>'
            f'<path d="{"".join(back)}" stroke="#6F8FBF" stroke-width="{w:.2f}" stroke-linecap="round" fill="none"/>'
            f'<path d="{"".join(front)}" stroke="#FFFFFF" stroke-width="{w:.2f}" stroke-linecap="round" fill="none"/>'
            f'<circle cx="{x + s * 0.80:.2f}" cy="{y + s * 0.24:.2f}" r="{s * 0.08:.2f}" fill="{ACCENT}"/>')


def logo_svg(height: int = 64) -> str:
    s = height
    width = int(s * 6.4)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{s}" viewBox="0 0 {width} {s}" '
            f'font-family="{FONT}">'
            f'{logo_mark(0, 0, s)}'
            f'<text x="{s * 1.22:.1f}" y="{s * 0.56:.1f}" font-size="{s * 0.44:.1f}" font-weight="700" fill="{INK}">{SITE_NAME}</text>'
            f'<text x="{s * 1.24:.1f}" y="{s * 0.86:.1f}" font-size="{s * 0.16:.1f}" letter-spacing="{s * 0.04:.1f}" '
            f'fill="{MUTED}">{SITE_NAME_EN} · β</text>'
            f'</svg>\n')


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
