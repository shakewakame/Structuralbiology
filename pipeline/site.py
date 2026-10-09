"""Build the static website from the built issues.

    python3 -m pipeline.site            # writes site/ (index + one page per issue, Qiita-like layout)

Reads every data/issues/<date>/ that has candidates.json and a picks/ folder, and produces
a browsable site under site/. Graphical abstracts and the logo are copied in so the pages are
self-contained and can be served by any static host (Cloudflare Pages, GitHub Pages, ...).
"""

from __future__ import annotations

import html
import shutil
import sys

from . import brand, render
from .common import ISSUES_DIR, ROOT, read_json

SITE_DIR = ROOT / "site"
TAGLINE = "毎日、新しいタンパク質の構造を、研究者の視点で。"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def slug(text: str) -> str:
    return "a-" + "".join(c if c.isalnum() else "-" for c in (text or "")).strip("-").lower()[:40]


CSS = f"""
:root {{
  --ink:{brand.INK}; --emerald:{brand.EMERALD}; --emerald-dark:{brand.EMERALD_DARK};
  --muted:{brand.MUTED}; --page:{brand.PAGE_BG}; --card:{brand.CARD_BG}; --hair:{brand.HAIRLINE};
  --panel:{brand.PANEL};
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin:0; background:var(--page); color:#1b2733;
  font-family:{brand.FONT}; font-size:16px; line-height:1.85;
  -webkit-font-smoothing:antialiased;
}}
a {{ color:var(--emerald-dark); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
img {{ max-width:100%; height:auto; }}

/* top bar */
.topbar {{ background:var(--ink); }}
.topbar .inner {{ max-width:1180px; margin:0 auto; padding:14px 20px; display:flex; align-items:center; gap:16px; }}
.topbar a.brand {{ display:flex; align-items:center; gap:12px; color:#fff; }}
.topbar .mark {{ width:34px; height:34px; }}
.topbar .name {{ font-weight:700; font-size:19px; color:#fff; }}
.topbar .en {{ font-size:12px; letter-spacing:1px; color:#AFC9BE; }}
.topbar .spacer {{ flex:1; }}
.topbar .tag {{ color:#CFE3DB; font-size:13px; }}

/* layout: content + right TOC rail */
.wrap {{ max-width:1180px; margin:0 auto; padding:28px 20px 80px; display:grid;
         grid-template-columns: minmax(0,1fr) 260px; gap:40px; }}
.main {{ min-width:0; }}
.rail {{ position:sticky; top:24px; align-self:start; font-size:14px; }}
.rail h4 {{ margin:0 0 10px; font-size:12px; letter-spacing:1px; color:var(--muted); font-weight:700; }}
.rail ol {{ list-style:none; margin:0; padding:0; border-left:2px solid var(--hair); }}
.rail li {{ margin:0; }}
.rail a {{ display:block; padding:6px 0 6px 14px; margin-left:-2px; border-left:2px solid transparent;
           color:#4a5a63; line-height:1.5; }}
.rail a:hover {{ border-left-color:var(--emerald); color:var(--ink); text-decoration:none; }}
@media (max-width:1000px) {{ .wrap {{ grid-template-columns:1fr; }} .rail {{ display:none; }} }}

/* issue header */
.issue-head {{ margin:4px 0 26px; }}
.issue-head .date {{ font-size:28px; font-weight:800; color:var(--ink); margin:0; }}
.issue-head .lead {{ color:#3a4a53; margin:10px 0 0; }}
.pill-count {{ display:inline-block; background:var(--emerald); color:#fff; font-weight:700;
               font-size:13px; padding:3px 12px; border-radius:999px; margin-right:8px; }}
.notice {{ background:#fff8ec; border:1px solid #f0dca8; color:#6b5a2a; font-size:13.5px;
           border-radius:10px; padding:10px 14px; margin:16px 0 0; }}

/* article card */
.card {{ background:var(--card); border:1px solid var(--hair); border-radius:14px;
         padding:26px 30px 10px; margin:0 0 26px; box-shadow:0 1px 2px rgba(22,50,79,.04); }}
.card .kicker {{ font-size:13px; color:var(--muted); margin:0 0 4px; }}
.card h2 {{ font-size:23px; line-height:1.45; color:var(--ink); margin:2px 0 14px;
            font-weight:800; scroll-margin-top:20px; }}
.ga {{ display:block; width:100%; border:1px solid var(--hair); border-radius:12px; margin:6px 0 6px; }}
.ga-cap {{ text-align:center; color:var(--muted); font-size:12.5px; margin:0 0 20px; }}
.meta {{ font-size:13.5px; color:var(--muted); margin:0 0 20px; }}
.meta a {{ color:var(--emerald-dark); }}

.card h3 {{ font-size:17px; color:var(--ink); font-weight:700; margin:26px 0 12px;
            padding-bottom:7px; border-bottom:1px solid var(--hair); position:relative; }}
.card h3::before {{ content:""; position:absolute; left:0; bottom:-1px; width:38px; height:3px;
                    background:var(--emerald); border-radius:2px; }}

.summary {{ margin:0; padding:0; list-style:none; }}
.summary li {{ padding:8px 0 8px 0; border-bottom:1px dashed var(--hair); }}
.summary li:last-child {{ border-bottom:none; }}
.summary .k {{ display:inline-block; min-width:5.5em; font-weight:700; color:var(--emerald-dark); }}

.hl {{ margin:0 0 16px; }}
.hl .chip {{ display:inline-block; background:var(--panel); color:var(--emerald-dark);
             border:1px solid var(--emerald); font-size:12px; font-weight:700;
             padding:2px 10px; border-radius:999px; margin:0 0 7px; }}
.hl p {{ margin:4px 0 0; }}
details {{ margin:8px 0 0; }}
details summary {{ cursor:pointer; color:var(--muted); font-size:13px; }}
details blockquote {{ margin:8px 0 0; padding:8px 14px; border-left:3px solid var(--emerald);
                      background:#f4faf7; color:#3a4a53; font-size:13.5px; border-radius:0 8px 8px 0; }}
details blockquote .src {{ display:block; color:var(--muted); font-size:12px; margin-top:4px; }}

table.struct {{ border-collapse:collapse; width:100%; font-size:13.5px; margin:4px 0 8px; }}
table.struct th, table.struct td {{ border:1px solid var(--hair); padding:6px 10px; text-align:left; }}
table.struct th {{ background:var(--panel); color:var(--ink); font-weight:700; }}
.proteins {{ list-style:none; padding:0; margin:8px 0 0; font-size:14px; }}
.proteins li {{ padding:3px 0; }}
.first {{ color:var(--emerald-dark); font-weight:700; }}
.labnotes {{ list-style:none; padding:0; margin:0; font-size:14.5px; }}
.labnotes li {{ padding:4px 0; }}
.labnotes .k {{ font-weight:700; color:var(--ink); }}

/* home feed */
.hero {{ max-width:1180px; margin:0 auto; padding:34px 20px 8px; }}
.hero h1 {{ font-size:26px; color:var(--ink); margin:0 0 6px; }}
.hero p {{ color:#3a4a53; margin:0; }}
.feed {{ max-width:860px; margin:0 auto; padding:14px 20px 80px; }}
.issue-card {{ display:block; background:var(--card); border:1px solid var(--hair); border-radius:14px;
               padding:20px 24px; margin:0 0 16px; color:inherit; box-shadow:0 1px 2px rgba(22,50,79,.04); }}
.issue-card:hover {{ border-color:var(--emerald); text-decoration:none; }}
.issue-card .d {{ font-size:19px; font-weight:800; color:var(--ink); }}
.issue-card .c {{ color:var(--muted); font-size:14px; margin:2px 0 10px; }}
.issue-card ul {{ margin:0; padding-left:18px; color:#2b3a43; font-size:14.5px; }}
.issue-card li {{ padding:2px 0; }}
footer {{ border-top:1px solid var(--hair); color:var(--muted); font-size:13px; text-align:center;
          padding:24px 20px 40px; }}
"""


def page(title: str, body: str, depth: int) -> str:
    up = "../" * depth
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(title)}</title>'
            f'<link rel="icon" href="{up}assets/logo-mark.svg">'
            f'<style>{CSS}</style></head><body>'
            f'<div class="topbar"><div class="inner">'
            f'<a class="brand" href="{up}index.html">'
            f'<img class="mark" src="{up}assets/logo-mark.svg" alt="">'
            f'<span><span class="name">{esc(brand.SITE_NAME)}</span> '
            f'<span class="en">{brand.SITE_NAME_EN} · β</span></span></a>'
            f'<span class="spacer"></span>'
            f'<span class="tag">{esc(TAGLINE)}</span>'
            f'</div></div>{body}'
            f'<footer>{esc(brand.SITE_NAME)}（ベータ版）・論文の要約は AI が作成した下書きです。'
            f'数値と ID は PDB / UniProt に基づきます。</footer></body></html>')


def doi_url(cand: dict) -> str:
    return f"https://doi.org/{cand['doi']}" if cand.get("doi") else \
        f"https://europepmc.org/article/PMC/{cand['pmcid']}"


def quote_html(evidence: list) -> str:
    if not evidence:
        return ""
    rows = "".join(f'<blockquote>{esc(e["quote"])}'
                   f'<span class="src">— {esc(e.get("section", ""))}</span></blockquote>'
                   for e in evidence)
    return f'<details><summary>根拠（論文本文）</summary>{rows}</details>'


def struct_html(cand: dict) -> str:
    own = cand["own_structures"]
    if not own:
        if cand["kind"] == "new_map_only" and cand.get("emdb_ids"):
            links = ", ".join(f'<a href="https://www.ebi.ac.uk/emdb/{e}">{e}</a>' for e in cand["emdb_ids"][:12])
            return f'<p>原子モデルのない cryo-EM マップ（EMDB）：{links}</p>'
        return "<p>寄託の記載はあるが、ID は補足資料にのみ記載されている。</p>"
    head = "<tr><th>PDB</th><th>手法</th><th>分解能</th><th>公開</th><th>生物種</th><th>リガンド</th></tr>"
    rows = []
    for s in own:
        if s["status"] != "released":
            rows.append(f'<tr><td>{esc(s["pdb_id"])}</td><td>—</td><td>—</td><td>公開待ち</td><td>—</td><td>—</td></tr>')
            continue
        orgs = esc(", ".join(sorted({o for p in s.get("polymers", []) for o in p["organisms"]})) or "—")
        ligs = esc(", ".join(l["id"] for l in s.get("ligands") or []) or "—")
        res = f"{s['resolution']:.2f} Å" if s.get("resolution") else "—"
        rows.append(
            f'<tr><td><a href="https://www.rcsb.org/structure/{esc(s["pdb_id"])}">{esc(s["pdb_id"])}</a></td>'
            f'<td>{esc(render.method_ja(s["method"]))}</td><td>{res}</td>'
            f'<td>{esc(s.get("release_date") or "—")}</td><td>{orgs}</td><td>{ligs}</td></tr>')
    table = f'<table class="struct">{head}{"".join(rows)}</table>'
    prots = []
    for p in cand.get("proteins", []):
        flag = ('<span class="first">PDB で初めての構造</span>' if p.get("first_structure")
                else f'既存の PDB 構造 {p.get("prior_pdb_count", 0)} 件')
        prots.append(f'<li><a href="https://www.uniprot.org/uniprotkb/{esc(p["uniprot"])}">{esc(p["uniprot"])}</a> '
                     f'{esc(p.get("gene") or "")} {esc(p.get("name") or "")} — <i>{esc(p.get("organism") or "")}</i>（{flag}）</li>')
    plist = f'<ul class="proteins">{"".join(prots)}</ul>' if prots else ""
    return table + plist


def article_html(cand: dict, pick: dict, date: str, n: int) -> str:
    anchor = slug(f"{n}-{pick['target_label']}")
    s = pick["summary"]
    summary = (f'<ul class="summary">'
               f'<li><span class="k">背景</span>{esc(s["background"])}</li>'
               f'<li><span class="k">やったこと</span>{esc(s["approach"])}</li>'
               f'<li><span class="k">分かったこと</span>{esc(s["findings"])}</li></ul>')
    hls = "".join(f'<div class="hl"><span class="chip">{esc(h["tag"])}</span>'
                  f'<p>{esc(h["text"])}</p>{quote_html(h.get("evidence", []))}</div>'
                  for h in pick["highlights"])
    notes = pick.get("lab_notes") or {}
    from .schema import LAB_NOTE_FIELDS
    filled = [(LAB_NOTE_FIELDS[k], notes[k]) for k in LAB_NOTE_FIELDS if notes.get(k)]
    labnotes = ""
    if filled:
        items = "".join(f'<li><span class="k">{esc(label)}</span>：{esc(v)}</li>' for label, v in filled)
        labnotes = f'<h3>実験メモ</h3><ul class="labnotes">{items}</ul>{quote_html(notes.get("evidence", []))}'
    lic = esc(cand.get("license") or "不明")
    return (f'<article class="card">'
            f'<p class="kicker">#{n} · {esc(pick["target_label"])}</p>'
            f'<h2 id="{anchor}">{esc(pick["headline"])}</h2>'
            f'<img class="ga" src="../ga/{date}/{esc(cand["pmcid"])}.svg" alt="グラフィカルアブストラクト">'
            f'<p class="ga-cap">グラフィカルアブストラクト（原題：{esc(cand["title"])}）</p>'
            f'<p class="meta"><a href="{doi_url(cand)}">{esc(cand["journal"] or cand["journal_abbrev"])}'
            f'（{esc(cand["pub_date"])}）</a> · ライセンス: {lic}</p>'
            f'<h3>3行要約</h3>{summary}'
            f'<h3>ここが面白い</h3>{hls}'
            f'<h3>構造データ</h3>{struct_html(cand)}'
            f'{labnotes}'
            f'</article>')


def issue_page(date: str) -> tuple[str, dict]:
    d = ISSUES_DIR / date
    meta = read_json(d / "candidates.json")
    cands = {c["pmcid"]: c for c in meta["candidates"]}
    picks = []
    for path in sorted((d / "picks").glob("*.json")):
        pk = read_json(path)
        picks.append((cands[pk["pmcid"]], pk))
    picks.sort(key=lambda cp: cp[1].get("rank", 99))
    c = meta["counts"]
    new_total = c["new_structure"] + c.get("new_structure_ids_unlisted", 0) + c.get("new_map_only", 0)

    toc_items = []
    for n, (_, pk) in enumerate(picks, 1):
        a = slug(f"{n}-{pk['target_label']}")
        toc_items.append(f'<li><a href="#{a}">{n}. {esc(pk["target_label"])}</a></li>')
    toc = "".join(toc_items)
    rail = f'<nav class="rail"><h4>この号の記事</h4><ol>{toc}</ol></nav>'
    articles = "".join(article_html(cand, pk, date, n) for n, (cand, pk) in enumerate(picks, 1))
    head = (f'<div class="issue-head"><p class="date">{esc(date)} 号</p>'
            f'<p class="lead"><span class="pill-count">新しい構造 {new_total} 本</span>'
            f'Europe PMC に {esc(meta["index_date"])} に登録されたオープンアクセス論文 {c["parsed"]} 本から。</p>'
            f'<p class="notice">この号は AI が論文本文から作成したレビュー用の下書きです。'
            f'数値・ID・リガンドは PDB / UniProt から取得し、記述には本文からの引用を付けています。</p></div>')
    body = f'<div class="wrap"><div class="main">{head}{articles}</div>{rail}</div>'
    summary = {"date": date, "new_total": new_total,
               "targets": [pk["target_label"] for _, pk in picks]}
    return page(f"{date} 号 · {brand.SITE_NAME}", body, depth=1), summary


def home(summaries: list[dict]) -> str:
    cards = []
    for s in summaries:
        items = "".join(f"<li>{esc(t)}</li>" for t in s["targets"])
        cards.append(f'<a class="issue-card" href="issues/{s["date"]}.html">'
                     f'<div class="d">{esc(s["date"])} 号</div>'
                     f'<div class="c">新しい構造 {s["new_total"]} 本</div>'
                     f'<ul>{items}</ul></a>')
    body = (f'<div class="hero"><h1>{esc(brand.SITE_NAME)} '
            f'<span style="font-size:16px;color:{brand.MUTED};font-weight:400">{esc(brand.SITE_NAME_EN)}</span></h1>'
            f'<p>{esc(TAGLINE)}</p></div>'
            f'<div class="feed">{"".join(cards)}</div>')
    return page(brand.SITE_NAME, body, depth=0)


def build() -> int:
    issues = sorted([d.name for d in ISSUES_DIR.iterdir()
                     if (d / "candidates.json").exists() and (d / "picks").exists()], reverse=True)
    if not issues:
        print("no built issues found")
        return 1
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    (SITE_DIR / "assets").mkdir(parents=True)
    (SITE_DIR / "issues").mkdir()
    for name in ("logo.svg", "logo-mark.svg"):
        shutil.copy(ROOT / "assets" / name, SITE_DIR / "assets" / name)
    summaries = []
    for date in issues:
        html_text, summary = issue_page(date)
        (SITE_DIR / "issues" / f"{date}.html").write_text(html_text, encoding="utf-8")
        ga_src = ISSUES_DIR / date / "ga"
        if ga_src.exists():
            shutil.copytree(ga_src, SITE_DIR / "ga" / date)
        summaries.append(summary)
    (SITE_DIR / "index.html").write_text(home(summaries), encoding="utf-8")
    print(f"built site/ with {len(issues)} issue(s): {', '.join(issues)}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
