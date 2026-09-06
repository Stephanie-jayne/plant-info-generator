#!/usr/bin/env python3
"""
wikimedia.py

Search Wikimedia Commons for images matching a plant name and return a best candidate
with URL and license metadata (extmetadata).

API reference:
https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=<term>&gsrnamespace=6&prop=imageinfo&iiprop=url|extmetadata&format=json
"""
from __future__ import annotations
import requests

USER_AGENT = "plant-post-generator/0.2 (+https://example.org/)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def _parse_extmeta(extmeta: dict) -> dict:
    # Safe extraction of common metadata fields
    def v(key):
        return extmeta.get(key, {}).get("value") if extmeta.get(key) else None

    return {
        "license_short": v("LicenseShortName"),
        "license_url": v("LicenseUrl"),
        "artist": v("Artist"),
        "credit": v("Credit"),
        "copyright": v("Copyright")
    }


def find_commons_image(plant_name: str, max_results: int = 6) -> dict | None:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": plant_name,
        "gsrnamespace": 6,  # files
        "gsrlimit": max_results,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata"
    }
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(COMMONS_API, params=params, headers=headers, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json().get("query", {}).get("pages", {})
    if not data:
        return None

    candidates = []
    for pid, p in data.items():
        ii = p.get("imageinfo", [{}])[0]
        url = ii.get("url")
        extmeta = ii.get("extmetadata", {})
        meta = _parse_extmeta(extmeta)
        licence = meta.get("license_short") or meta.get("license_url")
        # Build a concise attribution string
        attribution_parts = []
        if meta.get("artist"):
            attribution_parts.append(meta.get("artist"))
        if meta.get("credit"):
            attribution_parts.append(meta.get("credit"))
        if meta.get("copyright"):
            attribution_parts.append(meta.get("copyright"))
        attribution = " | ".join([p for p in attribution_parts if p])
        candidates.append({
            "title": p.get("title"),
            "url": url,
            "licence": licence,
            "licence_url": meta.get("license_url"),
            "attribution": attribution
        })

    # Prefer candidates with licence metadata (so we can attribute correctly)
    for c in candidates:
        if c.get("licence"):
            return c
    # Otherwise return the first candidate
    return candidates[0] if candidates else None
