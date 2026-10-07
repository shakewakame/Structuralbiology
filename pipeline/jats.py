"""Parse JATS full-text XML into readable sections and extract PDB / EMDB identifiers."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

XLINK = "{http://www.w3.org/1999/xlink}href"

# Sections that never help summarise the science.
SKIP_TITLES = re.compile(
    r"acknowledg|author contribution|competing interest|conflict|funding|peer review|"
    r"reporting summary|supplementary|source data|footnote|references|associated data|"
    r"ethics|ethical|additional information|declaration|orcid", re.I)
SKIP_SEC_TYPES = {"ack", "ref-list", "fn-group", "supplementary-materials", "associated-data",
                  "history", "kwd-group", "COI-statement"}
DATA_TITLES = re.compile(r"data (and code )?availability|accession|data deposition", re.I)

PDB_HREF = re.compile(
    r"(?:10\.2210/pdb([0-9][a-z0-9]{3})/pdb|rcsb\.org/(?:structure|pdb/explore[^?]*\?structureId=)/?"
    r"([0-9][a-z0-9]{3})|pdbe/entry/pdb/([0-9][a-z0-9]{3})|pdbj\.org/mine/[a-z/]*([0-9][a-z0-9]{3}))",
    re.I)
EXTENDED_PDB = re.compile(r"\bpdb_0000([0-9][a-z0-9]{3})\b", re.I)
EMDB = re.compile(r"\bEMD-(\d{4,5})\b", re.I)
# A bare 4-character PDB code: digit 1-9 + 3 alphanumerics with at least one letter,
# letters all upper case (rejects "10mM", "2nd" and years).
PDB_TOKEN = re.compile(r"(?<![A-Za-z0-9-])([1-9][A-Z0-9]{3})(?![A-Za-z0-9])")
PDB_CONTEXT = re.compile(r"PDB|Protein Data Bank|accession|deposited|entry|entries|code", re.I)
# "Coordinates/maps have been deposited in the PDB/EMDB" — the paper reports its own structure,
# even when the accession codes only appear in a supplementary table. The auxiliary verb keeps out
# sentences about other people's entries ("structures deposited in the PDB include ...").
_REPO = r"(?:Protein Data Bank|\bPDB\b|\bwwPDB\b|\bEMDB\b|Electron Microscopy Data Bank)"
_DEPOSIT_VERB = r"\b(?:ha(?:ve|s) been|were|was|are|is|we(?: have)?)\s+(?:\w+\s+){0,2}?(?:deposited|submitted)\b"
DEPOSITED = re.compile(rf"{_DEPOSIT_VERB}[^.]{{0,200}}{_REPO}|{_REPO}[^.]{{0,200}}{_DEPOSIT_VERB}", re.I)
# "7 V3Q": a code split by typesetting. Only looked for inside deposition statements.
SPLIT_PDB = re.compile(r"(?<![A-Za-z0-9])([1-9]) ([A-Z0-9]{3})(?![A-Za-z0-9])")
PREPRINT_DOI_PREFIXES = ("10.1101/", "10.26434/", "10.21203/", "10.2139/", "10.20944/", "10.48550/")


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def _paragraph_text(sec) -> str:
    """Text of a section, excluding nested <sec> children, tables and figures."""
    parts = []
    for child in sec:
        tag = child.tag
        if tag in ("sec", "title", "label", "table-wrap", "fig"):
            continue
        parts.append(_text(child))
    return "\n\n".join(p for p in parts if p)


def _walk_sections(sec, depth, out):
    if sec.get("sec-type") in SKIP_SEC_TYPES:
        return
    title_el = sec.find("title")
    title = _text(title_el) if title_el is not None else ""
    # Data availability is collected separately in parse().
    if title and (SKIP_TITLES.search(title) or DATA_TITLES.search(title)):
        return
    body = _paragraph_text(sec)
    out.append({"title": title, "depth": depth, "text": body})
    for child in sec.findall("sec"):
        _walk_sections(child, depth + 1, out)


def parse(xml: str) -> dict:
    root = ET.fromstring(xml)
    title_el = root.find(".//article-meta/title-group/article-title")
    abstract_el = root.find(".//article-meta/abstract")

    sections = []
    body = root.find("body")
    if body is not None:
        intro_text = _paragraph_text(body)
        if intro_text:
            sections.append({"title": "", "depth": 1, "text": intro_text})
        for sec in body.findall("sec"):
            _walk_sections(sec, 1, sections)

    # Data availability lives in <back>, in notes, or in a sec-type statement.
    data_avail = []
    for sec in root.iter("sec"):
        t = sec.find("title")
        if (t is not None and DATA_TITLES.search(_text(t))) or \
                sec.get("sec-type") in ("data-availability", "data-availability-statement"):
            data_avail.append(_text(sec))
    for notes in root.iter("notes"):
        if notes.get("notes-type") in ("data-availability", "data-availability-statement"):
            data_avail.append(_text(notes))
    for cm in root.iter("custom-meta"):  # PLOS puts the statement in article-meta
        name, value = cm.find("meta-name"), cm.find("meta-value")
        if name is not None and value is not None and "data availability" in _text(name).lower():
            data_avail.append(_text(value))

    captions = []
    for fig in root.iter("fig"):
        label = fig.find("label")
        cap = fig.find("caption")
        if cap is not None:
            captions.append(f"{_text(label) if label is not None else 'Figure'}: {_text(cap)}")
    tables = []
    for tw in root.iter("table-wrap"):
        label = tw.find("label")
        cap = tw.find("caption")
        tables.append({"label": _text(label) if label is not None else "Table",
                       "caption": _text(cap) if cap is not None else "",
                       "text": _text(tw.find("table")) if tw.find("table") is not None else ""})

    ids = extract_ids(root, "\n".join(data_avail), sections)
    article_ids = {a.get("pub-id-type"): _text(a) for a in root.findall(".//article-meta/article-id")}
    all_text = "\n".join([*data_avail, *(s["text"] for s in sections)])
    return {
        "journal": _text(jt) if (jt := root.find(".//journal-meta//journal-title")) is not None else None,
        "doi": (article_ids.get("doi") or "").lower() or None,
        "pmid": article_ids.get("pmid"),
        "deposition_statement": bool(DEPOSITED.search(all_text)),
        "title": _text(title_el) if title_el is not None else "",
        "abstract": _text(abstract_el) if abstract_el is not None else "",
        "sections": sections,
        "data_availability": "\n\n".join(dict.fromkeys(data_avail)),
        "figure_captions": captions,
        "tables": tables,
        **ids,
    }


def extract_ids(root, data_availability: str, sections: list[dict]) -> dict:
    pdb, emdb = [], []

    def add(lst, x):
        if x not in lst:
            lst.append(x)

    for link in root.iter("ext-link"):
        href = link.get(XLINK, "") or ""
        text = _text(link)
        if link.get("ext-link-type", "").lower() == "pdb" and re.fullmatch(r"[1-9][A-Za-z0-9]{3}", text):
            add(pdb, text.upper())
        for m in PDB_HREF.finditer(href):
            add(pdb, next(g for g in m.groups() if g).upper())
        for m in EMDB.finditer(href + " " + text):
            add(emdb, f"EMD-{m.group(1)}")

    texts = [data_availability] + [s["text"] for s in sections]
    for t in texts:
        for m in EXTENDED_PDB.finditer(t):
            add(pdb, m.group(1).upper())
        for m in EMDB.finditer(t):
            add(emdb, f"EMD-{m.group(1)}")
    # Bare codes: only in the data-availability text, or in sentences that talk about the PDB.
    sentences = re.split(r"(?<=[.;])\s+", data_availability)
    for t in texts[1:]:
        sentences += [s for s in re.split(r"(?<=[.;])\s+", t) if PDB_CONTEXT.search(s)]
    for s in sentences:
        if not PDB_CONTEXT.search(s):
            continue
        for m in PDB_TOKEN.finditer(s):
            tok = m.group(1)
            if re.search(r"[A-Z]", tok):
                add(pdb, tok)

    # Deposition statements: the data-availability text plus body sentences saying the authors
    # deposited coordinates (and the sentence after, which often lists the codes).
    deposition = [data_availability]
    for t in texts[1:]:
        parts = re.split(r"(?<=[.;])\s+", t)
        for i, sent in enumerate(parts):
            if DEPOSITED.search(sent):
                deposition += parts[i:i + 2]
    deposition_text = "\n".join(deposition)
    own = set()
    for m in PDB_TOKEN.finditer(deposition_text):
        if re.search(r"[A-Z]", m.group(1)):
            add(pdb, m.group(1))
            own.add(m.group(1))
    for m in SPLIT_PDB.finditer(deposition_text):
        if re.search(r"[A-Z]", m.group(2)):
            add(pdb, m.group(1) + m.group(2))
            own.add(m.group(1) + m.group(2))
    for m in re.finditer(r"\bEMDB?[:\s]+(?:ID[:\s]+)?(\d{4,5})\b", deposition_text):
        add(emdb, f"EMD-{m.group(1)}")
    up = deposition_text.upper()
    own |= {p for p in pdb if p in up}
    return {"pdb_ids": pdb, "emdb_ids": emdb, "pdb_ids_in_deposition": sorted(own)}


def packet_text(parsed: dict, max_chars: int = 120_000) -> str:
    """Full text as Markdown for the article writer; also the corpus that evidence quotes are checked against."""
    out = [f"# {parsed['title']}", "", "## Abstract", parsed["abstract"], ""]
    for s in parsed["sections"]:
        if s["title"]:
            out.append("#" * min(s["depth"] + 1, 4) + " " + s["title"])
        if s["text"]:
            out.append(s["text"])
        out.append("")
    if parsed["figure_captions"]:
        out += ["## Figure legends", *parsed["figure_captions"], ""]
    for t in parsed["tables"]:
        out += [f"## {t['label']} {t['caption']}".rstrip(), t["text"][:4000], ""]
    if parsed["data_availability"]:
        out += ["## Data availability", parsed["data_availability"], ""]
    text = "\n".join(out)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... truncated ...]\n"
    return text
