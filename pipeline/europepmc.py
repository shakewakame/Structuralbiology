"""Europe PMC: daily candidate search and full-text retrieval."""

from __future__ import annotations

import json

from .common import cached, fetch

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"

STRUCTURE_TERMS = (
    '"cryo-EM" OR "cryoEM" OR "cryo-electron microscopy" OR "cryo-electron tomography" OR '
    '"subtomogram" OR "crystal structure" OR "X-ray crystallography" OR "crystallographic" OR '
    '"NMR structure" OR "solution structure"'
)
DEPOSITION_TERMS = (
    '"Protein Data Bank" OR "PDB" OR "wwPDB" OR "EMDB" OR "accession code" OR "accession codes"'
)
# Article types that never report a new structure of their own.
EXCLUDED_PUB_TYPES = {"review", "systematic review", "editorial", "comment", "letter",
                      "erratum", "published erratum", "retraction of publication",
                      "retracted publication", "news"}


def build_query(index_date: str) -> str:
    return (f"({STRUCTURE_TERMS}) AND ({DEPOSITION_TERMS}) AND OPEN_ACCESS:y AND NOT SRC:PPR "
            f"AND FIRST_IDATE:[{index_date} TO {index_date}]")


def search(query: str, page_size: int = 500) -> list[dict]:
    results, cursor = [], "*"
    while True:
        d = json.loads(fetch(f"{BASE}/search", params={
            "query": query, "format": "json", "resultType": "core",
            "pageSize": page_size, "cursorMark": cursor}))
        batch = d["resultList"]["result"]
        results += batch
        nxt = d.get("nextCursorMark")
        if not batch or not nxt or nxt == cursor:
            return results
        cursor = nxt


def metadata(r: dict) -> dict:
    journal = r.get("journalInfo", {}).get("journal", {})
    pub_types = [t.lower() for t in r.get("pubTypeList", {}).get("pubType", [])]
    return {
        "pmcid": r.get("pmcid"),
        "pmid": r.get("pmid"),
        "doi": (r.get("doi") or "").lower() or None,
        "title": r.get("title", "").strip(),
        "journal": journal.get("title"),
        "journal_abbrev": journal.get("isoabbreviation") or journal.get("medlineAbbreviation"),
        "authors": r.get("authorString", ""),
        "pub_date": r.get("firstPublicationDate"),
        "index_date": r.get("firstIndexDate"),
        "license": r.get("license"),
        "pub_types": pub_types,
        "abstract": r.get("abstractText", ""),
    }


def is_excluded_type(meta: dict) -> bool:
    return any(t in EXCLUDED_PUB_TYPES for t in meta["pub_types"]) and \
        "research-article" not in meta["pub_types"]


def fulltext_xml(pmcid: str) -> str | None:
    path = cached("fulltext", pmcid, ".xml")
    if path.exists():
        return path.read_text(encoding="utf-8")
    body = fetch(f"{BASE}/{pmcid}/fullTextXML", ok_404=True)
    if body is None:
        return None
    text = body.decode("utf-8", "replace")
    path.write_text(text, encoding="utf-8")
    return text
