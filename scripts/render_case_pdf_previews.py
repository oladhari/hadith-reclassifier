#!/usr/bin/env python3
"""Render the cited pages from the read-only local archive for inline previews."""

import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "frontend" / "src" / "content"
OUTPUT = ROOT / "frontend" / "public" / "evidence" / "cases"
ARCHIVE = ROOT.parent / "telegram-archive"


def main():
    media = {item["id"]: item for item in json.loads((CONTENT / "archive-index.json").read_text())}
    studies = json.loads((CONTENT / "case-studies.json").read_text())
    cited_pages = {
        (item["id"], item.get("page", 1))
        for study in studies.values()
        for section in study["sections"]
        for item in section.get("evidence", [])
        if media[item["id"]]["kind"] == "pdf"
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        preview = Path(directory) / "page"
        for media_id, page in sorted(cited_pages):
            path = Path(media[media_id]["path"])
            source = ARCHIVE / (path if path.parts[0] == "muawiya4n" else Path("kkee9938") / path)
            subprocess.run(
                ["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-scale-to",
                 "1900", "-png", str(source), str(preview)],
                check=True,
            )
            with Image.open(preview.with_suffix(".png")) as image:
                image.save(OUTPUT / f"{media_id}-{page}.webp", quality=87, method=6)
            preview.with_suffix(".png").unlink()
    print(f"Rendered {len(cited_pages)} cited PDF pages.")


if __name__ == "__main__":
    main()
