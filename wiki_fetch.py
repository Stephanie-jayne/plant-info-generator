#!/usr/bin/env python3
"""
wiki_fetch.py
Fetch a Wikipedia summary using the REST summary endpoint.
"""
from __future__ import annotations
import urllib.parse
import requests
from typing import Dict, Any

USER_AGENT = "plant-post-generator/0.2 (+https://example.org/)"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


def fetch_wikipedia_summary(name: str) -> Dict[str, Any]:
    try:
        title = urllib.parse.quote(name.replace(" ", "_"))
        url = WIKI_SUMMARY_URL.format(title=title)
        headers = {"User-Agent": USER_AGENT}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return {}
        data = r.json()
        return {
            "title": data.get("title"),
            "description": data.get("description"),
            "extract": data.get("extract"),
            "page_url": data.get("content_urls", {}).get("desktop", {}).get("page"),
            "thumbnail": data.get("thumbnail", {}).get("source") if data.get("thumbnail") else None
        }
    except Exception:
        return {}
