"""Render an issue: graphical abstracts (SVG) and the issue page for review (README.md).

    python3 -m pipeline.render 2026-10-07
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata

from . import brand, pdb, structure_svg
from .common import issue_dir, read_json
from .schema import LAB_NOTE_FIELDS

SITE_NAME = brand.SITE_NAME
FONT = brand.FONT
INK, MUTED, PANEL, ACCENT = brand.INK, brand.MUTED, brand.PANEL, brand.EMERALD
W, H = 1200, 630

METHOD_JA = {
    "X-RAY DIFFRACTION": "X線結晶構造解析",
    "ELECTRON MICROSCOPY": "クライオ電顕",
    "SOLUTION NMR": "溶液NMR",
    "SOLID-STATE NMR": "固体NMR",
    "ELECTRON CRYSTALLOGRAPHY": "電子線結晶構造解析",
    "NEUTRON DIFFRACTION": "中性子回折",
}
KIND_JA = {
    "new_structure": "新しい構造",
    "new_structure_ids_unlisted": "新しい構造（ID は補足資料）",
    "new_map_only": "新しいマップ（EMDB）",
}


def method_ja(m: str | None) -> str:
    return ", ".join(METHOD_JA.get(x.strip(), x.strip()) for x in (m or "").split(",") if x.strip())


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


# ---------- text layout for SVG (no automatic wrapping in SVG) ----------

def char_width(ch: str) -> float:
    return 1.0 if unicodedata.east_asian_width(ch) in ("W", "F", "A") else 0.56


def wrap(text: str, size: float, max_width: float, max_lines: int) -> list[str]:
    units = re.findall(r"[A-Za-z0-9.,:;/+\-–()'%Åα-ωΑ-Ω]+ ?|.", text)
    lines, cur, cur_w = [], "", 0.0
    for u in units:
        uw = sum(char_width(c) for c in u) * size
        if cur and cur_w + uw > max_width:
            # Keep closing punctuation on the previous line.
            if u[0] in "、。）」』，．・":
                cur += u
                u, uw = "", 0.0
            lines.append(cur.rstrip())
            cur, cur_w = u.lstrip(), uw
        else:
            cur += u
            cur_w += uw
    if cur.strip():
        lines.append(cur.rstrip())
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…"
    return lines


def text_block(lines, x, y, size, color, weight=400, line_height=1.35) -> str:
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<text x="{x}" y="{y + i * size * line_height:.1f}" font-size="{size}" '
                   f'font-weight="{weight}" fill="{color}">{esc(ln)}</text>')
    return "".join(out)


# ---------- graphical abstract ----------

def pick_structure(cand: dict, pick: dict) -> dict | None:
    released = [s for s in cand["own_structures"] if s["status"] == "released"]
    if pick.get("ga_pdb_id"):
        for s in released:
            if s["pdb_id"] == pick["ga_pdb_id"].upper():
                return s
    with_res = [s for s in released if s.get("resolution")]
    if with_res:
        return min(with_res, key=lambda s: s["resolution"])
    return released[0] if released else None


def method_line(cand: dict) -> str:
    rel = [s for s in cand["own_structures"] if s["status"] == "released"]
    if not rel:
        return "PDB 公開待ち" if cand["own_structures"] else "—"
    methods = sorted({method_ja(s["method"]) for s in rel})
    res = [s["resolution"] for s in rel if s.get("resolution")]
    res_txt = (f"{min(res):.2f} Å" if len(res) == 1 or min(res) == max(res)
               else f"{min(res):.2f}–{max(res):.2f} Å") if res else ""
    n = f"（{len(rel)} 構造）" if len(rel) > 1 else ""
    return " / ".join(methods) + (f"・{res_txt}" if res_txt else "") + n


def ligand_line(cand: dict) -> str:
    seen = {}
    for s in cand["own_structures"]:
        for l in s.get("ligands") or []:
            seen.setdefault(l["id"], l.get("name") or l["id"])
    if not seen:
        return "なし（または未公開）"
    names = [f"{k}" for k in list(seen)[:4]]
    return ", ".join(names) + (" ほか" if len(seen) > 4 else "")


def _placeholder(cand: dict, s: dict | None) -> tuple[str, str]:
    if s:
        return "構造図は省略", f"PDB {s['pdb_id']}（座標ファイルが大きすぎるため）"
    if cand["own_structures"]:
        return "構造データは PDB 公開待ち", ", ".join(x["pdb_id"] for x in cand["own_structures"][:4])
    if cand["kind"] == "new_map_only":
        return "EMDB マップのみ（原子モデルなし）", ", ".join(cand.get("emdb_ids", [])[:4])
    return "PDB ID は論文の補足資料に記載", "（座標を自動取得できないため構造図なし）"


def graphical_abstract(cand: dict, pick: dict, issue_date: str, theme: brand.Theme | None = None) -> str:
    """Brand bar, the paper's own title, and the structure — nothing else (facts live in the page margin)."""
    th = theme or brand.THEMES[brand.DEFAULT_THEME]
    bar, pad = 52, 24
    title = cand["title"]
    rw = W - 2 * pad
    for size in (30, 28, 26, 24):
        tl = wrap(title, size, rw, 2)
        if tl and not tl[-1].endswith("…"):
            break
    else:
        size, tl = 22, wrap(title, 22, rw, 3)
    meta_y = bar + 32
    title_y = meta_y + 14 + size
    title_bottom = title_y + (len(tl) - 1) * size * 1.28
    px, py = pad, int(title_bottom + 18)
    pw, ph = rw, H - py - 22

    s = pick_structure(cand, pick)
    body, legend, pdb_note = "", [], ""
    if s:
        coords = pdb.coordinates(s["pdb_id"])
        if coords:
            lig_ids = {l["id"] for l in s.get("ligands") or []}
            genes = {p["uniprot"]: p["gene"] for p in cand.get("proteins", []) if p.get("gene")}
            body, legend = structure_svg.render(coords, lig_ids, px, py, pw, ph - 34, genes,
                                                margin=22, entity_colors=list(th.entities),
                                                ligand_color=th.ligand)
            if pick.get("legend_labels"):
                legend = [(col, lab) for (col, _), lab in zip(legend, pick["legend_labels"])]
            if len(legend) < 2:  # a single colour needs no key
                legend = []
            pdb_note = f"PDB {s['pdb_id']}"
    if not body:
        msg, sub = _placeholder(cand, s)
        body = "".join(text_block([t], px + pw / 2, py + ph / 2 + dy, size_, th.muted, wt)
                       .replace("<text ", '<text text-anchor="middle" ', 1)
                       for t, dy, size_, wt in ((msg, -10, 26, 600), (sub, 30, 18, 400)) if t)

    leg, lx, ly = [], px + 22, py + ph - 18
    for col, desc in legend[:3]:
        label = wrap(desc, 15, 250, 1)[0] if desc else ""
        leg.append(f'<rect x="{lx:.0f}" y="{ly - 11}" width="12" height="12" rx="6" fill="{col}"/>'
                   f'<text x="{lx + 18:.0f}" y="{ly}" font-size="15" fill="{th.ink2}">{esc(label)}</text>')
        lx += 18 + sum(char_width(c) for c in label) * 15 + 26
    if s and s.get("ligands") and body and pdb_note:
        leg.append(f'<circle cx="{lx + 6:.0f}" cy="{ly - 5}" r="6" fill="{th.ligand}" '
                   f'stroke="{structure_svg._shade(th.ligand, 0.45)}"/>'
                   f'<text x="{lx + 18:.0f}" y="{ly}" font-size="15" fill="{th.ink2}">リガンド</text>')
    note = (f'<text x="{px + pw - 22}" y="{ly}" font-size="14" fill="{th.muted}" text-anchor="end">{esc(pdb_note)}</text>'
            if pdb_note else "")

    head = (f'<rect width="{W}" height="{bar}" fill="{th.bar}"/>'
            f'{brand.logo_mark(24, 8, 36, bg=th.ink2, back=th.loop_back, front=th.loop_front, dot=th.ligand)}'
            f'<text x="72" y="33" font-size="21" font-weight="700" fill="{th.bar_text}">{esc(brand.SITE_NAME)}</text>'
            f'<text x="{72 + 21 * 5.6:.0f}" y="33" font-size="12" letter-spacing="2" fill="{th.bar_muted}">'
            f'{esc(brand.SITE_NAME_EN)}</text>'
            f'<text x="{W - 24}" y="33" font-size="16" fill="{th.bar_muted}" text-anchor="end">{esc(issue_date)}</text>')
    journal = f"{cand['journal'] or cand['journal_abbrev']}  ·  {cand['pub_date']}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{th.paper}"/>{head}'
            f'{text_block([journal], pad, meta_y, 15, th.muted)}'
            f'{text_block(tl, pad, title_y, size, th.ink, 700, 1.28)}'
            f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="{th.soft}"/>'
            f'{body}{"".join(leg)}{note}</svg>\n')


# ---------- issue page ----------

def structure_table(cand: dict) -> list[str]:
    own = cand["own_structures"]
    if not own:
        if cand["kind"] == "new_map_only" and cand.get("emdb_ids"):
            links = ", ".join(f"[{e}](https://www.ebi.ac.uk/emdb/{e})" for e in cand["emdb_ids"][:12])
            return [f"原子モデルのない cryo-EM マップ（EMDB）：{links}", ""]
        return ["寄託の記載はあるが、ID は補足資料にのみ記載されている。", ""]
    rows = ["| PDB | 手法 | 分解能 | 公開 | 生物種 | リガンド |", "|---|---|---|---|---|---|"]
    for s in own:
        if s["status"] != "released":
            rows.append(f"| {s['pdb_id']} | — | — | 公開待ち | — | — |")
            continue
        orgs = sorted({o for p in s.get("polymers", []) for o in p["organisms"]})
        ligs = ", ".join(l["id"] for l in s.get("ligands") or []) or "—"
        res = f"{s['resolution']:.2f} Å" if s.get("resolution") else "—"
        rows.append(f"| [{s['pdb_id']}](https://www.rcsb.org/structure/{s['pdb_id']}) | {method_ja(s['method'])} | "
                    f"{res} | {s.get('release_date') or '—'} | {', '.join(orgs) or '—'} | {ligs} |")
    return rows + [""]


def protein_lines(cand: dict) -> list[str]:
    out = []
    for p in cand.get("proteins", []):
        flag = "（PDB で初めての構造）" if p.get("first_structure") else f"（既存の PDB 構造 {p.get('prior_pdb_count', 0)} 件）"
        out.append(f"- [{p['uniprot']}](https://www.uniprot.org/uniprotkb/{p['uniprot']}) "
                   f"{p.get('gene') or ''} {p.get('name') or ''} — *{p.get('organism') or ''}* {flag}")
    return out + ([""] if out else [])


def quote_block(evidence: list) -> list[str]:
    out = ["<details><summary>根拠（論文本文）</summary>", ""]
    for e in evidence:
        out.append(f"> {e['quote']}  ")
        out.append(f"> — {e.get('section', '')}")
        out.append("")
    return out + ["</details>", ""]


def article_md(cand: dict, pick: dict, n: int) -> list[str]:
    doi = f"https://doi.org/{cand['doi']}" if cand.get("doi") else f"https://europepmc.org/article/PMC/{cand['pmcid']}"
    s = pick["summary"]
    out = [f"## {n}｜{pick['target_label']}", "",
           f"![グラフィカルアブストラクト：{cand['title']}](ga/{cand['pmcid']}.svg)", "",
           f"### {pick['headline']}", "",
           f"*{cand['journal']}*（{cand['pub_date']}） · [論文]({doi}) · ライセンス: {cand.get('license') or '不明'}  ",
           f"原題：{cand['title']}", "",
           "#### 3行要約", "",
           f"- **背景**：{s['background']}",
           f"- **やったこと**：{s['approach']}",
           f"- **分かったこと**：{s['findings']}", "",
           "#### ここが面白い", ""]
    for h in pick["highlights"]:
        out += [f"**［{h['tag']}］** {h['text']}", ""] + quote_block(h.get("evidence", []))
    out += ["#### 構造データ", ""] + structure_table(cand) + protein_lines(cand)
    notes = pick.get("lab_notes") or {}
    filled = [(LAB_NOTE_FIELDS[k], notes[k]) for k in LAB_NOTE_FIELDS if notes.get(k)]
    if filled:
        out += ["#### 実験メモ", ""] + [f"- **{label}**：{v}" for label, v in filled] + [""]
        if notes.get("evidence"):
            out += quote_block(notes["evidence"])
    if pick.get("editor_notes"):
        out += [f"> 📝 編集者への確認事項：{pick['editor_notes']}", ""]
    return out + ["---", ""]


def contents_table(picks: list[tuple[dict, dict]]) -> list[str]:
    rows = ["| # | 標的 | 手法・分解能 | 見出し |", "|---|---|---|---|"]
    for n, (cand, pick) in enumerate(picks, 1):
        method = method_line(cand)
        if pick.get("method_label") and not any(x["status"] == "released" for x in cand["own_structures"]):
            method = pick["method_label"]
        tags = " ".join(f"`{h['tag']}`" for h in pick["highlights"])
        rows.append(f"| {n} | {pick['target_label']} | {method} | {pick['headline']} {tags} |")
    return rows + [""]


def issue_md(meta: dict, picks: list[tuple[dict, dict]]) -> str:
    c = meta["counts"]
    new_total = c["new_structure"] + c.get("new_structure_ids_unlisted", 0) + c.get("new_map_only", 0)
    picked = {p["pmcid"] for _, p in picks}
    rest = [x for x in meta["candidates"] if x["kind"] in KIND_JA and x["pmcid"] not in picked]
    covered = "すべて紹介する。" if not rest else f"うち {len(picks)} 本を紹介する（残りは末尾に一覧）。"
    out = ['<p align="center"><img src="../../../assets/logo.svg" alt="構造生物学デイリー" height="56"></p>', "",
           f"# {meta['issue_date']} 号", "",
           f"**今日の新しい構造：{new_total} 本**　Europe PMC に {meta['index_date']} に登録された"
           f"オープンアクセス論文 {c['parsed']} 本のうち、新しい構造を報告した論文は {new_total} 本。{covered}", ""]
    if picks:
        out += contents_table(picks)
    out += ["> この号は AI が論文本文から作成した**レビュー用の下書き**です。"
            "数値・ID・リガンドは PDB / UniProt から取得し、AI の記述には本文からの引用を付けています。", "", "---", ""]
    for n, (cand, pick) in enumerate(picks, 1):
        out += article_md(cand, pick, n)
    if rest:
        out += ["## 記事にしていない新しい構造", ""]
        for x in rest:
            doi = f"https://doi.org/{x['doi']}" if x.get("doi") else f"https://europepmc.org/article/PMC/{x['pmcid']}"
            ids = ", ".join(s["pdb_id"] for s in x["own_structures"][:4])
            out.append(f"- [{x['title']}]({doi}) — *{x['journal_abbrev'] or x['journal']}*"
                       f"（{KIND_JA[x['kind']]}{'：' + ids if ids else ''}）")
        out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    d = issue_dir(argv[0])
    meta = read_json(d / "candidates.json")
    cands = {c["pmcid"]: c for c in meta["candidates"]}
    picks = []
    for path in sorted((d / "picks").glob("*.json")):
        pick = read_json(path)
        picks.append((cands[pick["pmcid"]], pick))
    picks.sort(key=lambda cp: cp[1].get("rank", 99))
    (d / "ga").mkdir(exist_ok=True)
    for cand, pick in picks:
        (d / "ga" / f"{cand['pmcid']}.svg").write_text(graphical_abstract(cand, pick, meta["issue_date"]),
                                                       encoding="utf-8")
    (d / "README.md").write_text(issue_md(meta, picks), encoding="utf-8")
    print(f"Rendered {len(picks)} articles to {d / 'README.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
