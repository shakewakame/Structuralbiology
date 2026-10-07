"""RCSB PDB / PDBe lookups: entry facts, release status, prior structures, coordinates."""

from __future__ import annotations

import json

from .common import cached, fetch, fetch_json

GRAPHQL = "https://data.rcsb.org/graphql"
HOLDINGS = "https://data.rcsb.org/rest/v1/holdings/status/{}"
PDBE_BEST = "https://www.ebi.ac.uk/pdbe/api/mappings/best_structures/{}"
COORDS = "https://files.rcsb.org/download/{}.cif.gz"

# Buffer components, cryoprotectants, detergents, common ions and glycans that are rarely the story.
COMMON_ADDITIVES = {
    "HOH", "DOD", "SO4", "PO4", "GOL", "EDO", "PEG", "PG4", "PGE", "1PE", "P6G", "MPD", "DMS",
    "ACT", "ACY", "FMT", "TRS", "EPE", "MES", "BME", "DTT", "CIT", "IMD", "NA", "CL", "K", "BR",
    "IOD", "NO3", "SCN", "CA", "MG", "ZN", "MN", "NI", "CO", "CD", "CU", "FE", "FE2", "UNX", "UNL",
    "NAG", "NDG", "BMA", "MAN", "FUC", "GAL", "GLC", "BOG", "LMT", "LMN", "DDM", "CLR", "Y01",
    "PCW", "POV", "PEE", "PLM", "OLA", "OLC", "MYR", "STE", "D10", "HEX", "LDA", "UNK", "AZI",
    "MLI", "TAR", "SIN", "MAL", "SUC", "TLA", "BCT", "CO3", "NH4", "OXY", "PEO", "CXS", "B3P",
    # lipids and lipid-like detergents modelled around membrane proteins
    "PC1", "PCF", "PEF", "PEV", "PGV", "PGW", "LHG", "LMG", "DGD", "SQD", "CDL", "3PE", "6PL",
    "PTY", "PLX", "P5S", "LPP", "8PE", "PEK", "D12", "OCT", "HP6", "LNK", "UND", "R16", "C14",
    "PX4", "POV", "PSF", "CHD", "CPQ", "AJP", "DU0", "NKP", "LBN", "PIO", "9Z9", "A1L",
}

ENTRY_QUERY = """
query($ids: [String!]!) {
  entries(entry_ids: $ids) {
    rcsb_id
    struct { title }
    exptl { method }
    rcsb_entry_info { resolution_combined }
    rcsb_accession_info { initial_release_date deposit_date }
    rcsb_primary_citation { pdbx_database_id_DOI pdbx_database_id_PubMed title }
    polymer_entities {
      rcsb_polymer_entity { pdbx_description }
      entity_poly { rcsb_entity_polymer_type }
      rcsb_polymer_entity_container_identifiers { uniprot_ids }
      rcsb_entity_source_organism { scientific_name }
    }
    nonpolymer_entities {
      nonpolymer_comp { chem_comp { id name type } }
    }
  }
}
"""


def entries(ids: list[str]) -> dict[str, dict]:
    """Released entries keyed by upper-case ID. IDs that are unknown or unreleased are absent."""
    out = {}
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        body = fetch(GRAPHQL, data=json.dumps({"query": ENTRY_QUERY, "variables": {"ids": chunk}}).encode(),
                     headers={"Content-Type": "application/json"})
        for e in (json.loads(body).get("data") or {}).get("entries") or []:
            if e:
                out[e["rcsb_id"].upper()] = _entry_facts(e)
    return out


def _entry_facts(e: dict) -> dict:
    cit = e.get("rcsb_primary_citation") or {}
    acc = e.get("rcsb_accession_info") or {}
    res = (e.get("rcsb_entry_info") or {}).get("resolution_combined") or []
    polymers = []
    for p in e.get("polymer_entities") or []:
        polymers.append({
            "description": (p.get("rcsb_polymer_entity") or {}).get("pdbx_description"),
            "type": (p.get("entity_poly") or {}).get("rcsb_entity_polymer_type"),
            "uniprot_ids": (p.get("rcsb_polymer_entity_container_identifiers") or {}).get("uniprot_ids") or [],
            "organisms": sorted({o["scientific_name"] for o in p.get("rcsb_entity_source_organism") or []
                                 if o.get("scientific_name")}),
        })
    ligands = []
    for n in e.get("nonpolymer_entities") or []:
        cc = ((n.get("nonpolymer_comp") or {}).get("chem_comp")) or {}
        if cc.get("id") and cc["id"] not in COMMON_ADDITIVES:
            ligands.append({"id": cc["id"], "name": cc.get("name")})
    return {
        "pdb_id": e["rcsb_id"].upper(),
        "status": "released",
        "title": (e.get("struct") or {}).get("title"),
        "method": ", ".join(x["method"] for x in e.get("exptl") or []),
        "resolution": res[0] if res else None,
        "release_date": (acc.get("initial_release_date") or "")[:10] or None,
        "deposit_date": (acc.get("deposit_date") or "")[:10] or None,
        "citation_doi": (cit.get("pdbx_database_id_DOI") or "").lower() or None,
        "citation_pmid": str(cit["pdbx_database_id_PubMed"]) if cit.get("pdbx_database_id_PubMed") else None,
        "citation_title": cit.get("title"),
        "polymers": polymers,
        "ligands": ligands,
    }


def holding_status(pdb_id: str) -> str | None:
    """'unreleased', 'removed', or None when the ID does not exist."""
    d = fetch_json(HOLDINGS.format(pdb_id), ok_404=True)
    if not d:
        return None
    status = (d.get("rcsb_repository_holdings_combined") or {}).get("status", "").upper()
    return {"UNRELEASED": "unreleased", "REMOVED": "removed", "CURRENT": "released"}.get(status, status.lower() or None)


def structures_for_uniprot(acc: str) -> set[str]:
    """All PDB IDs that SIFTS maps to this UniProt accession (upper case). SIFTS lags new releases by days."""
    d = fetch_json(PDBE_BEST.format(acc), ok_404=True)
    if not d:
        return set()
    return {x["pdb_id"].upper() for x in d.get(acc, [])}


def coordinates(pdb_id: str, max_bytes: int = 20_000_000) -> bytes | None:
    path = cached("coords", pdb_id, ".cif.gz")
    if path.exists():
        return path.read_bytes()
    body = fetch(COORDS.format(pdb_id), ok_404=True, timeout=180)
    if body is None or len(body) > max_bytes:
        return None
    path.write_bytes(body)
    return body
