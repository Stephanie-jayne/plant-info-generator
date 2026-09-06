#!/usr/bin/env python3
"""
gbif_fetch.py
Simple GBIF species match + species info retrieval.
"""
from __future__ import annotations
import requests
from typing import Dict, Any

USER_AGENT = "plant-post-generator/0.2 (+https://example.org/)"
GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
GBIF_SPECIES_URL = "https://api.gbif.org/v1/species/{key}"


def fetch_gbif(name: str) -> Dict[str, Any]:
    try:
        r = requests.get(GBIF_MATCH_URL, params={"name": name}, headers={"User-Agent": USER_AGENT}, timeout=10)
        if r.status_code != 200:
            return {}
        match = r.json()
        species = {"match": match}
        if "usageKey" in match and match.get("usageKey"):
            key = match["usageKey"]
            sreq = requests.get(GBIF_SPECIES_URL.format(key=key), headers={"User-Agent": USER_AGENT}, timeout=10)
            if sreq.status_code == 200:
                species.update(sreq.json())
            species["gbif_url"] = f"https://www.gbif.org/species/{key}"
        return species
    except Exception:
        return {}
