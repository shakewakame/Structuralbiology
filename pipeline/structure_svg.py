"""Draw a structure as an SVG backbone trace straight from PDB coordinates.

No image generation is involved: every line is an alpha-carbon (or phosphorus) trace
from the deposited mmCIF file, coloured by entity, with the ligands of interest as dots.
"""

from __future__ import annotations

import gzip
import math
import re
from collections import defaultdict

PALETTE = ["#3B6FB6", "#E0A030", "#3E9E8F", "#9C5FB5", "#D0605E", "#6C8EBF",
           "#8DA94A", "#C17C4E", "#5AA9C8", "#B5869E"]
LIGAND_COLOR = "#E4572E"
TOKEN = re.compile(r"""'(?:[^']|'(?=\S))*'|"(?:[^"]|"(?=\S))*"|\S+""")
MAX_TRACE_POINTS = 6000


def _unquote(v: str) -> str:
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"" else v


def parse_cif(text: str, categories=("_atom_site", "_entity", "_struct_ref")) -> dict[str, list[dict]]:
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


def render(cif_gz: bytes, ligand_ids: set[str], x0: float, y0: float, w: float, h: float,
           gene_names: dict[str, str] | None = None, margin: float = 28) -> tuple[str, list[tuple[str, str]]]:
    """SVG fragment for the box (x0, y0, w, h) and a legend [(colour, label)] per polymer entity.

    Labels are UniProt gene names (gene_names: accession -> gene) when the entity maps to one,
    otherwise the entity description.
    """
    cif = parse_cif(gzip.decompress(cif_gz).decode("utf-8", "replace"))
    atoms = cif["_atom_site"]
    entities = {e.get("id", ""): e.get("pdbx_description", "") for e in cif["_entity"]}
    for ref in cif["_struct_ref"]:
        gene = (gene_names or {}).get(ref.get("pdbx_db_accession", ""))
        if ref.get("db_name") == "UNP" and gene:
            entities[ref.get("entity_id", "")] = gene
    model = next((a.get("pdbx_PDB_model_num") for a in atoms), "1")
    chains: dict[str, list] = defaultdict(list)
    chain_entity: dict[str, str] = {}
    lig_atoms = []
    for a in atoms:
        if a.get("pdbx_PDB_model_num", "1") != model:
            continue
        xyz = (float(a["Cartn_x"]), float(a["Cartn_y"]), float(a["Cartn_z"]))
        if a.get("group_PDB") == "ATOM" and a.get("label_atom_id") in ("CA", "P"):
            key = a.get("label_asym_id", "?")
            chains[key].append((xyz, a["label_atom_id"]))
            chain_entity[key] = a.get("label_entity_id", "?")
        elif a.get("group_PDB") == "HETATM" and a.get("label_comp_id") in ligand_ids and \
                a.get("type_symbol") not in ("H", "D"):
            lig_atoms.append(xyz)
    pts = [p for c in chains.values() for p, _ in c]
    if not pts:
        return "", []

    step = max(1, math.ceil(len(pts) / MAX_TRACE_POINTS))
    cx, cy, cz = (sum(p[i] for p in pts) / len(pts) for i in range(3))
    cov = [[sum((p[i] - (cx, cy, cz)[i]) * (p[j] - (cx, cy, cz)[j]) for p in pts[::step]) for j in range(3)]
           for i in range(3)]
    ev = _jacobi_eigen(cov)

    def proj(p):
        d = (p[0] - cx, p[1] - cy, p[2] - cz)
        return tuple(sum(d[k] * ev[k][c] for k in range(3)) for c in range(3))

    # Wider than tall: put the longest axis horizontally if the box is wide, vertically otherwise.
    swap = h > w

    def xy(q):
        return (q[1], q[0], q[2]) if swap else q

    projected = {k: [(xy(proj(p)), at) for p, at in v[::step]] for k, v in chains.items()}
    allq = [q for v in projected.values() for q, _ in v]
    ligq = [xy(proj(p)) for p in lig_atoms]
    xs, ys, zs = [q[0] for q in allq + ligq], [q[1] for q in allq + ligq], [q[2] for q in allq]
    span_x, span_y = max(xs) - min(xs) or 1, max(ys) - min(ys) or 1
    scale = min((w - 2 * margin) / span_x, (h - 2 * margin) / span_y)
    ox = x0 + w / 2 - (min(xs) + max(xs)) / 2 * scale
    oy = y0 + h / 2 + (min(ys) + max(ys)) / 2 * scale
    zmin, zmax = min(zs), max(zs)

    def sx(q):
        return ox + q[0] * scale, oy - q[1] * scale

    entity_order = []
    for k in chains:
        if chain_entity[k] not in entity_order:
            entity_order.append(chain_entity[k])
    color = {e: PALETTE[i % len(PALETTE)] for i, e in enumerate(entity_order)}
    width = max(1.2, min(4.5, scale * 1.9))

    segments = []
    for k, v in projected.items():
        seg = []
        for idx, (q, at) in enumerate(v):
            if seg:
                prev = seg[-1]
                gap = math.dist(prev, q) / step
                if gap > (8.5 if at == "P" else 4.6) * 1.15:
                    if len(seg) > 1:
                        segments.append((k, seg))
                    seg = []
            seg.append(q)
            if len(seg) == 7:
                segments.append((k, seg))
                seg = [q]
        if len(seg) > 1:
            segments.append((k, seg))
    segments.sort(key=lambda s: sum(q[2] for q in s[1]) / len(s[1]))

    out = []
    for k, seg in segments:
        z = sum(q[2] for q in seg) / len(seg)
        depth = (z - zmin) / ((zmax - zmin) or 1)  # 0 = far, 1 = near
        col = _mix(color[chain_entity[k]], 0.6 * (1 - depth))
        pts_s = " ".join(f"{a:.1f},{b:.1f}" for a, b in (sx(q) for q in seg))
        out.append(f'<polyline points="{pts_s}" stroke="{col}" stroke-width="{width * (0.75 + 0.5 * depth):.2f}"/>')
    r = max(2.0, min(5.5, scale * 0.9))
    for q in ligq:
        a, b = sx(q)
        out.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{r:.1f}"/>')

    lig_group = (f'<g fill="{LIGAND_COLOR}" stroke="#ffffff" stroke-width="0.8">' +
                 "".join(x for x in out if x.startswith("<circle")) + "</g>") if ligq else ""
    trace = ('<g fill="none" stroke-linecap="round" stroke-linejoin="round">' +
             "".join(x for x in out if x.startswith("<polyline")) + "</g>")
    legend = [(color[e], entities.get(e, f"entity {e}")) for e in entity_order]
    return trace + lig_group, legend
