"""UniProt: gene names, protein names and organisms for accessions."""

from __future__ import annotations

from .common import fetch_json

ACCESSIONS = "https://rest.uniprot.org/uniprotkb/accessions"


def lookup(accessions: list[str]) -> dict[str, dict]:
    out = {}
    accs = sorted(set(accessions))
    for i in range(0, len(accs), 100):
        d = fetch_json(ACCESSIONS, params={
            "accessions": ",".join(accs[i:i + 100]),
            "fields": "accession,gene_primary,gene_synonym,protein_name,organism_name",
            "format": "json"})
        for r in (d or {}).get("results", []):
            desc = r.get("proteinDescription", {})
            name = (desc.get("recommendedName") or (desc.get("submissionNames") or [{}])[0]).get("fullName", {})
            genes = r.get("genes") or [{}]
            out[r["primaryAccession"]] = {
                "uniprot": r["primaryAccession"],
                "gene": (genes[0].get("geneName") or {}).get("value"),
                "synonyms": [s["value"] for s in genes[0].get("synonyms", [])],
                "name": name.get("value"),
                "organism": r.get("organism", {}).get("scientificName"),
            }
    return out
