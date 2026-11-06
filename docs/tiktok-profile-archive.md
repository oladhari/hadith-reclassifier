# TikTok public profile archive

Requested source: https://www.tiktok.com/@brad2557wtn

On 2026-11-06, yt-dlp 2026.10.26 with curl-cffi discovered 1,253 video entries.
The previous installed version could not resolve this profile. This is the count
returned by the inventory, not a guarantee that every entry remains downloadable.

The initial three videos downloaded successfully and passed full R2 read-back
SHA-256 verification. The resumable batch runs as user service
`othmani-tiktok-brad2557wtn.service`, four workers, outside the request process.
No Neon queries or paid AI calls are used. Existing research SQLite is read-only
for matching known object hashes. No website entries or prior video visibility
decisions are changed by this archival step.

- Inventory: ignored `data/research/tiktok-brad2557wtn/profile.json`.
- Downloads, progress manifest and logs: `/mnt/linuxdata/othmani-tiktok/brad2557wtn`.
- R2 objects: `othmani/imports/tiktok/brad2557wtn/objects/<sha256>.<extension>`;
  an already catalogued identical object is reused instead.
- Per-video public provenance: `othmani/imports/tiktok/brad2557wtn/provenance/<id>.json`.
  Source link, caption, date, duration and checksum are retained. Raw downloader
  metadata stays local because it may contain expiring CDN addresses.
- Downloads are checked with ffprobe; every stored object is read back and hashed.
  Failed entries remain retryable. Originals are retained, and a low-space guard
  prevents consuming the final 2 GiB. One process lock prevents overlapping runs.

Monitor:

```sh
systemctl --user status othmani-tiktok-brad2557wtn --no-pager
 tail -n 12 /mnt/linuxdata/othmani-tiktok/brad2557wtn/batch.log
```

Resume/retry after completion with the same arguments:

```sh
.research-venv/bin/python scripts/archive_tiktok_profile.py \
  --inventory data/research/tiktok-brad2557wtn/profile.json \
  --directory /mnt/linuxdata/othmani-tiktok/brad2557wtn --workers 4
```

Verified records are skipped. Do not report the batch complete until the manifest
is reconciled against all discovered IDs and any failures are explicitly reported.
Website publication is a separate catalogue step: use Arabic titles and source
attribution, avoid duplicate cards, and preserve all 57 existing hidden decisions.
