Plant Post Generator

What this does:
- Generate a ready-to-post Facebook "Plant of the Week" post for a given plant name.
- Fetches a Wikipedia summary and a GBIF taxonomy match.
- Searches Wikimedia Commons for a freely-licensed image and extracts license/attribution metadata.
- Writes a Markdown file with the post and attribution; optionally downloads the image.

Quickstart:
1. Save the files into a directory (or commit them to this repo).
2. Create and activate a Python venv:
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows

3. Install dependencies:
   pip install -r requirements.txt

4. Run:
   python plant_post_generator.py "Hibiscus sabdariffa" --download-image

Output:
- <Plant_name>.md with the post and a "Sources & further reading" block.
- If --download-image is used and an image is found, the image file will be downloaded to the project folder.

Notes & next steps:
- The script uses Wikipedia and GBIF for quick, reliable reference data and Wikimedia Commons for free images. For Australia-specific authority (CSIRO, state agriculture/extension pages, ABC Gardening Australia, university pages), extend the script to link or add those pages per plant; adding them manually is recommended when preparing a post for your audience.
- Always check the Commons file page for exact attribution wording and license terms before publishing.
- This tool produces general gardening content — not medical advice.
