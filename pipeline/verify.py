"""Check every pick of an issue before it is rendered.

    python3 -m pipeline.verify 2026-10-07

Errors (exit code 1):
  - missing or over-long fields, unknown tags
  - an evidence quote that does not appear verbatim in the paper's full text
  - "初構造" on a paper whose proteins already had PDB structures
  - a resolution (… Å) or PDB ID in the Japanese text that the paper / PDB does not support
Warnings: picks that are not classified as new structures, missing evidence for lab notes.
"""

from __future__ import annotations

import re
import sys
import unicodedata

from .common import cached, issue_dir, read_json
from .schema import LAB_NOTE_FIELDS, LIMITS, TAGS

ANGSTROM = re.compile(r"(\d+(?:\.\d+)?)\s*(?:Å|Å|オングストローム)")
PDB_ID_JA = re.compile(r"(?<![A-Za-z0-9])([1-9][A-Z0-9]{3})(?![A-Za-z0-9])")


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[‐‑‒–—−]", "-", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def japanese_fields(pick: dict) -> list[str]:
    out = [pick.get(k, "") or "" for k in ("headline", "takeaway", "target_label", "method_label", "ligand_label")]
    out += list((pick.get("summary") or {}).values())
    out += [h.get("text", "") for h in pick.get("highlights", [])]
    out += [v for k, v in (pick.get("lab_notes") or {}).items() if k in LAB_NOTE_FIELDS and v]
    return [x for x in out if isinstance(x, str)]


def check_pick(pick: dict, cand: dict | None, corpus: str | None) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if cand is None:
        return [f"{pick.get('pmcid')} is not in candidates.json"], []
    if cand["kind"] not in ("new_structure", "new_structure_ids_unlisted", "new_map_only"):
        warnings.append(f"classified as {cand['kind']}, not a new structure")

    def length(name, value, key):
        required, limit = LIMITS[key]
        if not value:
            if required:
                errors.append(f"{name} is missing")
            return
        if len(value) > limit:
            errors.append(f"{name} is {len(value)} characters (limit {limit})")

    for f in ("headline", "takeaway", "target_label"):
        length(f, pick.get(f), f)
    for f in ("background", "approach", "findings"):
        length(f"summary.{f}", (pick.get("summary") or {}).get(f), f"summary.{f}")

    hs = pick.get("highlights") or []
    if not 1 <= len(hs) <= 3:
        errors.append(f"highlights must have 1-3 items, has {len(hs)}")
    first = any(p.get("first_structure") for p in cand.get("proteins", []))
    quotes = []
    for i, h in enumerate(hs, 1):
        if h.get("tag") not in TAGS:
            errors.append(f"highlight {i}: unknown tag {h.get('tag')!r} (allowed: {', '.join(TAGS)})")
        if h.get("tag") == "初構造" and not first:
            errors.append(f"highlight {i}: tagged 初構造 but no protein is flagged first_structure in the PDB")
        length(f"highlight {i} text", h.get("text"), "highlight.text")
        if not h.get("evidence"):
            errors.append(f"highlight {i}: needs at least one evidence quote")
        quotes += [(f"highlight {i}", e) for e in h.get("evidence") or []]

    notes = pick.get("lab_notes") or {}
    for k in LAB_NOTE_FIELDS:
        if notes.get(k):
            length(f"lab_notes.{k}", notes[k], "lab_note")
    if any(notes.get(k) for k in LAB_NOTE_FIELDS) and not notes.get("evidence"):
        warnings.append("lab_notes has content but no evidence quotes")
    quotes += [("lab_notes", e) for e in notes.get("evidence") or []]

    if corpus is None:
        errors.append("full-text packet missing; run pipeline.collect first")
    else:
        norm = normalize(corpus)
        for where, e in quotes:
            q = e.get("quote", "") if isinstance(e, dict) else str(e)
            if len(q) < 20:
                errors.append(f"{where}: quote too short to verify: {q!r}")
            elif normalize(q) not in norm:
                errors.append(f"{where}: quote not found in the paper: {q[:90]!r}")

    known_res = {round(s["resolution"], 2) for s in cand["own_structures"] if s.get("resolution")}
    known_ids = {s["pdb_id"] for s in cand["own_structures"]} | set(cand.get("cited_pdb_ids", []))
    for text in japanese_fields(pick):
        for m in ANGSTROM.finditer(text):
            v = float(m.group(1))
            in_text = corpus is not None and re.search(rf"{re.escape(m.group(1))}\s*(?:Å|Å|angstrom)", corpus, re.I)
            if round(v, 2) not in known_res and not in_text:
                errors.append(f"resolution {m.group(0)} is not in the PDB entries or the paper")
        for m in PDB_ID_JA.finditer(text):
            tok = m.group(1)
            if re.search(r"[A-Z]", tok) and tok not in known_ids:
                errors.append(f"PDB ID {tok} is not among this paper's entries")
    return errors, warnings


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    d = issue_dir(argv[0])
    cands = {c["pmcid"]: c for c in read_json(d / "candidates.json")["candidates"]}
    picks = sorted((d / "picks").glob("*.json"))
    if not picks:
        print(f"no picks in {d / 'picks'}")
        return 1
    failed = False
    for path in picks:
        pick = read_json(path)
        packet = cached("packets", pick.get("pmcid", ""), ".md")
        corpus = packet.read_text(encoding="utf-8") if packet.exists() else None
        errors, warnings = check_pick(pick, cands.get(pick.get("pmcid")), corpus)
        status = "NG" if errors else "OK"
        print(f"[{status}] {path.name}")
        for e in errors:
            print(f"   error: {e}")
        for w in warnings:
            print(f"   warning: {w}")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
