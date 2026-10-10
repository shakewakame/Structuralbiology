"""Draw a structure as a cartoon (ribbon) SVG straight from PDB coordinates.

No image generation is involved. The backbone comes from the deposited mmCIF file
(alpha-carbon / phosphorus positions), the secondary structure from its own
_struct_conf / _struct_sheet_range records: helices are drawn as rounded tubes,
strands as arrows, loops as thin tubes and nucleic acids as a thin tube,
coloured by entity and shaded by depth, with the ligands of interest as dots.
"""

from __future__ import annotations

import gzip
import math
import re
from collections import defaultdict

PALETTE = ["#3B6FB6", "#E0A030", "#3E9E8F", "#9C5FB5", "#D0605E", "#6C8EBF",
           "#8DA94A", "#C17C4E", "#5AA9C8", "#B5869E"]
LIGAND_COLOR = "#E4572E"
SUBDIV = 3  # spline samples per residue
TOKEN = re.compile(r"""'(?:[^']|'(?=\S))*'|"(?:[^"]|"(?=\S))*"|\S+""")
MAX_TRACE_POINTS = 6000


def _unquote(v: str) -> str:
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"" else v


def parse_cif(text: str, categories=("_atom_site", "_entity", "_struct_ref", "_struct_conf", "_struct_sheet_range")) -> dict[str, list[dict]]:
    """Rows of the requested mmCIF categories, from both loop_ and single-row key-value form."""
    lines = text.splitlines()
    out: dict[str, list[dict]] = {c: [] for c in categories}
    single: dict[str, dict] = {}
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].strip()
        if line == "loop_":
            j = i + 1
            fields = []
            while j < n and lines[j].startswith("_"):
                fields.append(lines[j].strip())
                j += 1
            cat = fields[0].split(".")[0] if fields else ""
            if cat in out:
                names = [f.split(".", 1)[1] for f in fields]
                buf = []
                while j < n and not lines[j].startswith(("#", "loop_", "_")):
                    if lines[j].startswith(";"):  # multi-line text field, closed by a line starting with ';'
                        block = [lines[j][1:]]
                        while j + 1 < n and not lines[j + 1].startswith(";"):
                            j += 1
                            block.append(lines[j])
                        j += 1
                        buf.append("\n".join(block).strip())
                    else:
                        buf += TOKEN.findall(lines[j])
                    while len(buf) >= len(names):
                        out[cat].append(dict(zip(names, (_unquote(v) for v in buf[:len(names)]))))
                        buf = buf[len(names):]
                    j += 1
            i = j
            continue
        if line.startswith("_") and "." in line:
            key, _, rest = line.partition(" ")
            cat, item = key.split(".", 1)
            if cat in out:
                value = rest.strip()
                if not value and i + 1 < n:
                    i += 1
                    if lines[i].startswith(";"):
                        block = [lines[i][1:]]
                        while i + 1 < n and not lines[i + 1].startswith(";"):
                            i += 1
                            block.append(lines[i])
                        i += 1
                        value = " ".join(block).strip()
                    else:
                        value = lines[i].strip()
                single.setdefault(cat, {})[item] = _unquote(value)
        i += 1
    for cat, row in single.items():
        out[cat].append(row)
    return out


def _jacobi_eigen(a: list[list[float]]) -> list[list[float]]:
    """Eigenvectors (as columns, sorted by descending eigenvalue) of a symmetric 3x3 matrix."""
    a = [row[:] for row in a]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(50):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda pq: abs(a[pq[0]][pq[1]]))
        if abs(a[p][q]) < 1e-9:
            break
        theta = 0.5 * math.atan2(2 * a[p][q], a[q][q] - a[p][p])
        c, s = math.cos(theta), math.sin(theta)
        for k in range(3):
            akp, akq = a[k][p], a[k][q]
            a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
        for k in range(3):
            apk, aqk = a[p][k], a[q][k]
            a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
        for k in range(3):
            vkp, vkq = v[k][p], v[k][q]
            v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    order = sorted(range(3), key=lambda i: -a[i][i])
    return [[v[r][c] for c in order] for r in range(3)]


def _mix(hex_color: str, white: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(x + (255 - x) * white) for x in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _shade(hex_color: str, dark: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"#{round(r * (1 - dark)):02x}{round(g * (1 - dark)):02x}{round(b * (1 - dark)):02x}"


def _spline(pts: list[tuple], sub: int) -> list[tuple]:
    """Catmull-Rom curve through pts with `sub` samples per interval; sample i*sub is pts[i]."""
    n = len(pts)
    if n < 3 or sub < 2:
        return list(pts)
    out = []
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[c] + (p2[c] - p0[c]) * t
                                    + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (3 * p1[c] - p0[c] - 3 * p2[c] + p3[c]) * t3) for c in range(3)))
    out.append(pts[-1])
    return out


def _secondary_structure(cif: dict) -> dict[tuple[str, int], str]:
    """(asym id, seq id) -> 'H' or 'E' from the entry's own annotation."""
    ss: dict[tuple[str, int], str] = {}

    def mark(rows, kind, ok=lambda r: True):
        for r in rows:
            if not ok(r):
                continue
            try:
                asym, a, b = r["beg_label_asym_id"], int(r["beg_label_seq_id"]), int(r["end_label_seq_id"])
            except (KeyError, ValueError):
                continue
            for i in range(a, b + 1):
                ss[(asym, i)] = kind

    mark(cif["_struct_sheet_range"], "E")
    mark(cif["_struct_conf"], "H", lambda r: r.get("conf_type_id", "HELX_P").startswith("HELX"))
    return ss


def _elements(res: list[dict]) -> list[tuple[str, int, int]]:
    """Consecutive residues of one secondary-structure type as (type, first, last) index ranges.

    Helices shorter than 4 residues and strands shorter than 3 are drawn as loop.
    """
    groups: list[list] = []
    for i, r in enumerate(res):
        kind = r["ss"]
        if groups and groups[-1][0] == kind:
            groups[-1][2] = i
        else:
            groups.append([kind, i, i])
    for g in groups:
        n = g[2] - g[1] + 1
        if (g[0] == "H" and n < 4) or (g[0] == "E" and n < 3):
            g[0] = "C"
    merged: list[list] = []
    for g in groups:
        if merged and merged[-1][0] == g[0] and g[0] in ("C", "N"):
            merged[-1][2] = g[2]
        else:
            merged.append(g)
    return [tuple(g) for g in merged]


def _points(pts: list[tuple[float, float]]) -> str:
    return " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)


def render(cif_gz: bytes, ligand_ids: set[str], x0: float, y0: float, w: float, h: float,
           gene_names: dict[str, str] | None = None, margin: float = 28,
           entity_colors: list[str] | None = None, ligand_color: str | None = None,
           ) -> tuple[str, list[tuple[str, str]]]:
    """SVG fragment for the box (x0, y0, w, h) and a legend [(colour, label)] per polymer entity.

    Labels are UniProt gene names (gene_names: accession -> gene) when the entity maps to one,
    otherwise the entity description.
    """
    palette = entity_colors or PALETTE
    lig_col = ligand_color or LIGAND_COLOR
    cif = parse_cif(gzip.decompress(cif_gz).decode("utf-8", "replace"))
    atoms = cif["_atom_site"]
    entities = {e.get("id", ""): e.get("pdbx_description", "") for e in cif["_entity"]}
    for ref in cif["_struct_ref"]:
        gene = (gene_names or {}).get(ref.get("pdbx_db_accession", ""))
        if ref.get("db_name") == "UNP" and gene:
            entities[ref.get("entity_id", "")] = gene
    ss_map = _secondary_structure(cif)
    model = next((a.get("pdbx_PDB_model_num") for a in atoms), "1")
    chains: dict[str, list[dict]] = defaultdict(list)
    chain_entity: dict[str, str] = {}
    seen: set[tuple] = set()
    lig_atoms = []
    for a in atoms:
        if a.get("pdbx_PDB_model_num", "1") != model:
            continue
        xyz = (float(a["Cartn_x"]), float(a["Cartn_y"]), float(a["Cartn_z"]))
        if a.get("group_PDB") == "ATOM" and a.get("label_atom_id") in ("CA", "P"):
            key = a.get("label_asym_id", "?")
            try:
                seq = int(a.get("label_seq_id", ""))
            except ValueError:
                continue
            if (key, seq) in seen:  # alternate locations
                continue
            seen.add((key, seq))
            at = a["label_atom_id"]
            chains[key].append({"seq": seq, "xyz": xyz, "at": at,
                                "ss": "N" if at == "P" else ss_map.get((key, seq), "C")})
            chain_entity[key] = a.get("label_entity_id", "?")
        elif a.get("group_PDB") == "HETATM" and a.get("label_comp_id") in ligand_ids and \
                a.get("type_symbol") not in ("H", "D"):
            lig_atoms.append(xyz)
    pts = [r["xyz"] for c in chains.values() for r in c]
    if not pts:
        return "", []

    # Break chains into continuous runs, then thin very large models.
    runs: list[tuple[str, list[dict]]] = []
    for k, v in chains.items():
        cur: list[dict] = []
        for r in v:
            if cur:
                limit = 9.5 if r["at"] == "P" else 5.6
                if r["seq"] - cur[-1]["seq"] != 1 or math.dist(cur[-1]["xyz"], r["xyz"]) > limit:
                    runs.append((k, cur))
                    cur = []
            cur.append(r)
        runs.append((k, cur))
    runs = [(k, v) for k, v in runs if len(v) > 1]
    step = max(1, math.ceil(len(pts) / MAX_TRACE_POINTS))
    if step > 1:
        runs = [(k, v[::step] + ([v[-1]] if (len(v) - 1) % step else [])) for k, v in runs]

    cx, cy, cz = (sum(p[i] for p in pts) / len(pts) for i in range(3))
    sample = pts[::step]
    cov = [[sum((p[i] - (cx, cy, cz)[i]) * (p[j] - (cx, cy, cz)[j]) for p in sample) for j in range(3)]
           for i in range(3)]
    ev = _jacobi_eigen(cov)

    def proj(p):
        d = (p[0] - cx, p[1] - cy, p[2] - cz)
        return tuple(sum(d[k] * ev[k][c] for k in range(3)) for c in range(3))

    # Wider than tall: put the longest axis horizontally if the box is wide, vertically otherwise.
    swap = h > w

    def xy(q):
        return (q[1], q[0], q[2]) if swap else q

    runs3 = [(k, [dict(r, q=xy(proj(r["xyz"]))) for r in v]) for k, v in runs]
    ligq = [xy(proj(p)) for p in lig_atoms]
    allq = [r["q"] for _, v in runs3 for r in v]
    xs, ys, zs = [q[0] for q in allq + ligq], [q[1] for q in allq + ligq], [q[2] for q in allq]
    span_x, span_y = max(xs) - min(xs) or 1, max(ys) - min(ys) or 1
    scale = min((w - 2 * margin) / span_x, (h - 2 * margin) / span_y)
    ox = x0 + w / 2 - (min(xs) + max(xs)) / 2 * scale
    oy = y0 + h / 2 + (min(ys) + max(ys)) / 2 * scale
    zmin, zmax = min(zs), max(zs)

    def sx(q):
        return ox + q[0] * scale, oy - q[1] * scale

    def tint(col, z):
        depth = (z - zmin) / ((zmax - zmin) or 1)  # 0 = far, 1 = near
        return _mix(col, 0.42 * (1 - depth))

    entity_order = []
    for k, _ in runs3:
        if chain_entity[k] not in entity_order:
            entity_order.append(chain_entity[k])
    color = {e: palette[i % len(palette)] for i, e in enumerate(entity_order)}

    tube = max(4.0, min(17.0, 2.2 * scale))   # helix tube diameter in px
    coil_w = max(1.4, 0.36 * tube)
    nuc_w = max(2.0, 0.5 * tube)
    arrow_hw = 0.5 * tube
    edge = 1.2 if tube > 8 else 0.8             # outline width

    parts: list[tuple[float, str]] = []         # (depth, svg) painted far to near

    for k, v in runs3:
        base = color[chain_entity[k]]
        for kind, a, b in _elements(v):
            if kind == "H":
                win = []
                for i in range(a, b + 1):
                    lo, hi = max(a, i - 1), min(b, i + 2)
                    n = hi - lo + 1
                    win.append(tuple(sum(v[j]["q"][c] for j in range(lo, hi + 1)) / n for c in range(3)))
                path = _spline(win, 2)
                z = sum(q[2] for q in path) / len(path)
                col = tint(base, z)
                sp = [sx(q) for q in path]
                pl = _points(sp)
                hl = _points([(px - 0.17 * tube, py - 0.2 * tube) for px, py in sp])
                parts.append((z, f'<g stroke-linecap="round" stroke-linejoin="round" fill="none">'
                                 f'<polyline points="{pl}" stroke="{_shade(col, 0.3)}" stroke-width="{tube + 2 * edge:.1f}"/>'
                                 f'<polyline points="{pl}" stroke="{col}" stroke-width="{tube:.1f}"/>'
                                 f'<polyline points="{hl}" stroke="{_mix(col, 0.5)}" stroke-width="{0.26 * tube:.1f}"/></g>'))
            elif kind == "E":
                path = _spline([r["q"] for r in v[a:b + 1]], SUBDIV)
                z = sum(q[2] for q in path) / len(path)
                col = tint(base, z)
                sp = [sx(q) for q in path]
                m = len(sp)
                head = min(m - 1, int(1.6 * SUBDIV))
                left, right = [], []
                for i, (px, py) in enumerate(sp):
                    ax, ay = sp[min(i + 1, m - 1)]
                    bx, by = sp[max(i - 1, 0)]
                    tx, ty = ax - bx, ay - by
                    norm = math.hypot(tx, ty) or 1
                    nx, ny = -ty / norm, tx / norm
                    if i < m - head:
                        hw = arrow_hw
                    else:
                        hw = arrow_hw * 1.75 * (m - 1 - i) / head if i < m - 1 else 0
                    if i == m - head:  # flare at the arrowhead base
                        left.append((px + nx * arrow_hw * 1.75, py + ny * arrow_hw * 1.75))
                        right.append((px - nx * arrow_hw * 1.75, py - ny * arrow_hw * 1.75))
                        continue
                    left.append((px + nx * hw, py + ny * hw))
                    right.append((px - nx * hw, py - ny * hw))
                parts.append((z, f'<polygon points="{_points(left + right[::-1])}" fill="{col}" '
                                 f'stroke="{_shade(col, 0.3)}" stroke-width="{edge}" stroke-linejoin="round"/>'))
            else:
                lo, hi = max(0, a - 1), min(len(v) - 1, b + 1)
                path = _spline([r["q"] for r in v[lo:hi + 1]], SUBDIV)
                width = nuc_w if kind == "N" else coil_w
                if kind == "N":
                    piece = 6
                else:
                    piece = 7
                i = 0
                while i < len(path) - 1:
                    seg = path[i:i + piece]
                    z = sum(q[2] for q in seg) / len(seg)
                    col = tint(_shade(base, 0.12), z)
                    parts.append((z, f'<polyline points="{_points([sx(q) for q in seg])}" '
                                     f'stroke="{col}" stroke-width="{width:.1f}" fill="none" '
                                     f'stroke-linecap="round" stroke-linejoin="round"/>'))
                    i += piece - 1

    parts.sort(key=lambda p: p[0])
    out = ["".join(s for _, s in parts)]
    r = max(2.2, min(6.5, scale * 0.85))
    if ligq:
        out.append(f'<g fill="{lig_col}" stroke="{_shade(lig_col, 0.45)}" stroke-width="1">' +
                   "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{r:.1f}"/>' for a, b in map(sx, ligq)) + "</g>")
    legend = [(color[e], entities.get(e, f"entity {e}")) for e in entity_order]
    return "".join(out), legend
