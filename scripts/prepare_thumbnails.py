#!/usr/bin/env python3
"""Create small, deduplicated library previews without modifying originals.

Requires Pillow, Poppler, FFmpeg and LibreOffice. Run with system python3.
The generated files are static assets served by the website CDN.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def run(command):
    subprocess.run(command, check=True, capture_output=True, timeout=120)


def render(source, kind, destination):
    with tempfile.TemporaryDirectory(prefix="othmani-preview-") as directory:
        temp = Path(directory)
        image = source
        if kind == "video":
            image = temp / "frame.jpg"
            # Seek shortly after the opening frame, without decoding the whole video.
            run(["ffmpeg", "-v", "error", "-threads", "1", "-ss", "1", "-i", str(source),
                 "-frames:v", "1", "-vf", "scale=640:640:force_original_aspect_ratio=decrease",
                 "-threads", "1", str(image)])
            if not image.exists():
                run(["ffmpeg", "-v", "error", "-i", str(source), "-frames:v", "1", "-threads", "1", str(image)])
        elif kind in {"pdf", "document"}:
            pdf = source
            if kind == "document":
                # Use a separate office profile so concurrent conversions cannot interfere.
                run(["libreoffice", f"-env:UserInstallation={(temp / 'profile').as_uri()}",
                     "--headless", "--convert-to", "pdf", "--outdir", str(temp), str(source)])
                pdf = temp / (source.stem + ".pdf")
            run(["pdftoppm", "-f", "1", "-singlefile", "-scale-to", "640", "-png",
                 str(pdf), str(temp / "page")])
            image = temp / "page.png"
        with Image.open(image) as original:
            preview = ImageOps.exif_transpose(original).convert("RGB")
            preview.thumbnail((640, 640), Image.Resampling.LANCZOS)
            staging = destination.with_suffix(".tmp")
            preview.save(staging, "WEBP", quality=78, method=6)
            staging.replace(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT.parent / "telegram-archive/kkee9938")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    archive = args.archive.resolve()
    output = ROOT / "frontend/public/thumbnails"
    output.mkdir(parents=True, exist_ok=True)
    items = json.loads((ROOT / "frontend/src/content/archive-index.json").read_text())
    keys = json.loads((ROOT / "frontend/src/content/media-objects.json").read_text())
    groups = {}
    for item in items:
        if item["kind"] in {"image", "pdf", "document", "video"}:
            sha = keys[str(item["id"])].split("/")[-1]
            groups.setdefault(sha, []).append(item)
    manifest, failures = {}, []

    def prepare(pair):
        sha, members = pair
        item = members[0]
        source = (archive / item["path"]).resolve()
        destination = output / f"{sha}-v1.webp"
        try:
            if not source.is_relative_to(archive):
                raise ValueError("Source outside archive")
            if not destination.exists():
                with source.open("rb") as stream:
                    if hashlib.file_digest(stream, "sha256").hexdigest() != sha:
                        raise ValueError("Original checksum differs")
                render(source, item["kind"], destination)
            with Image.open(destination) as image:
                image.verify()
            return members, destination.name, None
        except Exception as error:
            return members, None, type(error).__name__

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for index, (members, name, error) in enumerate(pool.map(prepare, groups.items()), 1):
            if name:
                for item in members:
                    manifest[str(item["id"])] = f"/thumbnails/{name}"
            else:
                failures.append({"ids": [item["id"] for item in members], "error": error})
            if index % 100 == 0:
                print(json.dumps({"processed": index, "objects": len(groups), "failed": len(failures)}), flush=True)
    (ROOT / "frontend/src/content/thumbnails.json").write_text(json.dumps(manifest, indent=2) + "\n")
    report = {"previews": len(manifest), "unique": len(set(manifest.values())),
              "by_kind": dict(Counter(item["kind"] for item in items if str(item["id"]) in manifest)),
              "failures": failures}
    (ROOT / "data/research/thumbnail-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
