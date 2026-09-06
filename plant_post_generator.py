#!/usr/bin/env python3
"""
plant_post_generator.py

Generate a ready-to-post Facebook "Plant of the Week" message with:
 - Wikipedia summary (preferred southern-hemisphere wording can be edited in post)
 - GBIF taxonomy & links
 - A freely-licensed image from Wikimedia Commons (with attribution/license)
 - Optionally download the image

Usage:
  python plant_post_generator.py "Plant name" [--download-image] [--length short|medium|long] [--voice we|i]
"""
from __future__ import annotations
import argparse
import datetime
import os
import re
import urllib.parse
import logging
from typing import Optional, Dict, Any

import requests

from wiki_fetch import fetch_wikipedia_summary
from gbif_fetch import fetch_gbif
from wikimedia import find_commons_image

USER_AGENT = "plant-post-generator/0.2 (+https://example.org/)"
LOGGER = logging.getLogger("plant_post_generator")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def safe_filename(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name).strip('_')


def image_filename_from_url(filename_base: str, url: str) -> str:
    # Extract path and extension safely
    parsed = urllib.parse.urlparse(url)
    path = parsed.path  # e.g. /wiki/File:Rosella.jpg
    _, ext = os.path.splitext(path)
    # Default to .jpg if unknown or too long
    if not ext or len(ext) > 6:
        ext = ".jpg"
    return f"{filename_base}{ext}"


def make_facebook_post(plant_name: str,
                       wiki: Dict[str, Any],
                       gbif: Dict[str, Any],
                       image_info: Optional[Dict[str, Any]],
                       length: str = "medium",
                       voice: str = "we") -> str:
    # voice: "we" or "i"
    pronoun = "We" if voice == "we" else "I"
    title = wiki.get("title") or plant_name
    lines = []

    # Header
    lines.append(f"{title} — Plant of the Week 🌿")
    lines.append("")

    # One-liner / description if available
    if wiki.get("description"):
        lines.append(f"{wiki['description'].capitalize()}.")
        lines.append("")

    # Short summary paragraph from Wikipedia if present
    if wiki.get("extract"):
        # For "short" keep one sentence; for medium include extract; for long include extract + extra note
        if length == "short":
            first_sentence = wiki["extract"].split(".")[0] + "."
            lines.append(first_sentence)
        else:
            lines.append(wiki["extract"])
        lines.append("")

    # Growing & care — practical, Australian-focused prompts (editable)
    lines.append("How to grow & care (AU):")
    lines.append("- Best in: full sun to part shade. Well-drained soil; add compost to improve fertility.")
    lines.append("- Water: regular watering while establishing; reduce in cooler months. Mulch to conserve moisture.")
    lines.append("- Climate & zone notes: generally suited to warm-temperate and subtropical areas; in cooler temperate zones, give protection or grow in containers and move to a protected spot in winter.")
    lines.append("")
    # Propagation
    lines.append("How to propagate:")
    lines.append("- Many plants can be grown from seed or cuttings; timing varies. As a general Australian guide: sow in autumn/winter in mild zones, spring in cooler zones; take semi-ripe cuttings in summer for woody shrubs.")
    lines.append("")

    # Harvesting & uses
    lines.append("Harvesting & uses:")
    lines.append("- Harvest when flowers/fruits/leaves are at their peak flavour. Use fresh in salads, make cordials, jams or teas depending on the plant.")
    lines.append("")

    # GBIF / taxonomy
    if gbif:
        lines.append("Quick taxonomy & links:")
        match = gbif.get("match", {})
        sci = match.get("scientificName") or match.get("parsed") or ""
        if sci:
            lines.append(f"- Scientific name: **{sci}**")
        if gbif.get("gbif_url"):
            lines.append(f"- More (GBIF): {gbif['gbif_url']}")
        lines.append("")

    # Image & attribution
    if image_info:
        lines.append("Image & attribution:")
        if image_info.get("title"):
            lines.append(f"- {image_info.get('title')}")
        if image_info.get("url"):
            lines.append(f"- Image: {image_info.get('url')}")
        if image_info.get("licence"):
            lines.append(f"- Licence: {image_info.get('licence')}")
        if image_info.get("attribution"):
            lines.append(f"- Attribution: {image_info.get('attribution')}")
        lines.append("")

    # Cautions
    lines.append("Cautions:")
    lines.append("- Check species-specific toxicity for pets and livestock before planting where animals have access.")
    lines.append("- Traditional or folk medicinal use is not the same as clinical evidence. If using for health, consult a professional.")
    lines.append("")

    # Sources block (keeps post clean but provides links for verification)
    lines.append("Sources & further reading:")
    if wiki.get("page_url"):
        lines.append(f"- Wikipedia: {wiki['page_url']}")
    if gbif and gbif.get("gbif_url"):
        lines.append(f"- GBIF: {gbif['gbif_url']}")
    lines.append("- For Australia-specific advice, check state agriculture / university extension pages, CSIRO, and ABC Gardening Australia.")
    lines.append("")

    # Disclaimer
    lines.append("_General information only — not medical advice. Consult a professional before medicinal use._")

    return "\n".join(lines)


def download_image(url: str, outpath: str) -> None:
    headers = {"User-Agent": USER_AGENT}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(outpath, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
    except Exception as exc:
        LOGGER.warning("Failed to download image %s: %s", url, exc)
        raise


def build_post(plant_query: str, download_image_flag: bool, length: str, voice: str) -> str:
    LOGGER.info("Looking up: %s", plant_query)
    wiki = fetch_wikipedia_summary(plant_query)
    if wiki:
        LOGGER.info("Found Wikipedia: %s", wiki.get("title"))
    else:
        LOGGER.info("No Wikipedia summary found for %s", plant_query)

    gbif = fetch_gbif(plant_query)
    if gbif:
        LOGGER.info("GBIF lookup complete")

    image_info = None
    # 1) Prefer the Wikipedia thumbnail if it exists (useful quick fallback)
    if wiki and wiki.get("thumbnail"):
        image_info = {
            "title": f"Wikipedia thumbnail for {wiki.get('title') or plant_query}",
            "url": wiki.get("thumbnail"),
            "licence": None,
            "attribution": f"Wikipedia page: {wiki.get('page_url')}" if wiki.get('page_url') else ""
        }

    # 2) Try searching Commons for a better-quality image / license metadata
    try:
        commons = find_commons_image(plant_query)
        if commons:
            # Prefer Commons candidate with explicit licence metadata
            if commons.get("licence") or not image_info:
                image_info = commons
    except Exception as exc:
        LOGGER.warning("Commons image search failed: %s", exc)

    # Compose post
    post_text = make_facebook_post(plant_query, wiki or {}, gbif or {}, image_info, length=length, voice=voice)
    filename_base = safe_filename(plant_query)
    md_name = f"{filename_base}.md"

    with open(md_name, "w", encoding="utf-8") as f:
        f.write(post_text)
    LOGGER.info("Wrote %s", md_name)

    if download_image_flag and image_info and image_info.get("url"):
        try:
            img_name = image_filename_from_url(filename_base, image_info["url"])
            download_image(image_info["url"], img_name)
            LOGGER.info("Downloaded image to %s", img_name)
        except Exception:
            LOGGER.warning("Image download failed; generated post still saved without image file.")

    # Print short attribution summary to console for quick copy/paste
    if image_info:
        LOGGER.info("Image chosen: %s", image_info.get("title"))
        LOGGER.info("Image URL: %s", image_info.get("url"))
        LOGGER.info("Licence: %s", image_info.get("licence"))
        LOGGER.info("Attribution: %s", image_info.get("attribution"))
    else:
        LOGGER.info("No suitable Commons image found automatically. You can add one manually.")

    return md_name


def main():
    parser = argparse.ArgumentParser(description="Generate Facebook-ready Plant of the Week post")
    parser.add_argument("plant", help="Plant scientific or common name, e.g. 'Rosella' or 'Hibiscus sabdariffa'")
    parser.add_argument("--download-image", action="store_true", help="Download the selected image")
    parser.add_argument("--length", choices=["short", "medium", "long"], default="medium", help="Post length")
    parser.add_argument("--voice", choices=["we", "i"], default="we", help="Write as 'we' or 'I'")
    args = parser.parse_args()
    build_post(args.plant, args.download_image, args.length, args.voice)


if __name__ == "__main__":
    main()
