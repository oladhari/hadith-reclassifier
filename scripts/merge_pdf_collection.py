#!/usr/bin/env python3
"""Merge explicitly selected source PDFs, retaining their original page objects.

Exact raster duplicates are omitted. --same-cover additionally permits omission
of later first pages only after the operator has visually confirmed the covers.
No original, database record or cloud object is overwritten.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT.parent / "telegram-archive/kkee9938"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", type=int, nargs="+", required=True)
    parser.add_argument("--same-cover", action="store_true")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()
    if len(set(args.ids)) != len(args.ids) or len(args.ids) < 2:
        raise ValueError("Select at least two distinct original IDs")
    archive = {row["id"]: row for row in json.loads((ROOT / "frontend/src/content/archive-index.json").read_text())}
    object_keys = json.loads((ROOT / "frontend/src/content/media-objects.json").read_text())
    work = ROOT / "data/research/enrichment/pdf-comparison"
    writer = PdfWriter()
    seen, page_map, omitted, originals = {}, [], [], []
    first_cover = None
    readers = []
    for id in args.ids:
        item = archive[id]
        if item["kind"] != "pdf":
            raise ValueError("Only PDF originals can be merged")
        source = (ARCHIVE / item["path"]).resolve()
        if not source.is_relative_to(ARCHIVE.resolve()):
            raise ValueError("Invalid source path")
        with source.open("rb") as stream:
            sha = hashlib.file_digest(stream, "sha256").hexdigest()
        if sha != object_keys[str(id)].split("/")[-1]:
            raise ValueError("Original checksum differs")
        rendered = work / str(id)
        rendered.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftoppm", "-scale-to", "1300", "-png", str(source), str(rendered / "page")],
                       check=True, capture_output=True)
        reader = PdfReader(source)
        readers.append(reader)
        images = sorted(rendered.glob("page-*.png"))
        if len(images) != len(reader.pages):
            raise ValueError("Rendered and original page counts differ")
        originals.append({"id": id, "page_count": len(reader.pages), "sha256": sha})
        bookmark = None
        for number, (page, raster) in enumerate(zip(reader.pages, images), 1):
            with Image.open(raster) as image:
                image = image.convert("RGB")
                digest = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
                cover = ImageOps.fit(image.convert("L"), (256, 360))
            duplicate_of = seen.get(digest)
            reason = "identical_render"
            if not page_map:
                first_cover = cover
            elif number == 1 and args.same_cover and first_cover is not None:
                error = ImageStat.Stat(ImageChops.difference(first_cover, cover)).mean[0]
                if error < .1:
                    duplicate_of = 1
                    reason = "visually_confirmed_same_cover"
            if duplicate_of is not None:
                omitted.append({"source_id": id, "source_page": number, "duplicate_of": duplicate_of, "reason": reason})
                continue
            writer.add_page(page)
            output_number = len(writer.pages)
            seen[digest] = output_number
            page_map.append({"page": output_number, "source_id": id, "source_page": number, "render_sha256": digest})
            if bookmark is None:
                bookmark = writer.add_outline_item(f"الملف الأصلي {id}", output_number - 1)
        if bookmark is None:
            raise ValueError("A member contributes no distinct pages; review the collection selection")
    writer.add_metadata({"/Title": args.title, "/Subject": "جمع تحريري للملفات الأصلية؛ حُذفت الصفحات المكررة فقط، ولم تتغير النصوص أو صور الأدلة."})
    output = ROOT / "output/pdf"
    output.mkdir(parents=True, exist_ok=True)
    pdf = output / f"ghadir-sources-{args.ids[0]}.pdf"
    with pdf.open("wb") as stream:
        writer.write(stream)
    with pdf.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    if len(PdfReader(pdf).pages) != len(page_map):
        raise ValueError("Merged PDF page count differs")
    public = ROOT / "frontend/public/collections"
    public.mkdir(parents=True, exist_ok=True)
    asset = public / f"ghadir-sources-{sha[:20]}.pdf"
    asset.write_bytes(pdf.read_bytes())
    registry_path = ROOT / "frontend/src/content/media-collections.json"
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    registry[str(args.ids[0])] = {"canonical_id": args.ids[0], "members": args.ids,
        "title": args.title, "description": args.description, "asset_url": "/collections/" + asset.name,
        "asset_sha256": sha, "asset_size": asset.stat().st_size, "page_count": len(page_map),
        "originals": originals, "page_map": page_map, "omitted": omitted}
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"pages": len(page_map), "original_pages": sum(row["page_count"] for row in originals),
        "omitted": omitted, "bytes": asset.stat().st_size, "output": str(pdf)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
