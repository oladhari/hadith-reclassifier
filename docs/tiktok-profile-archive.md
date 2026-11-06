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

## Public catalogue publication

`prepare_tiktok_publication.py` assigns stable numeric IDs starting at 2000001
(sorted TikTok IDs), generates local thumbnails, and writes the existing public
read models. It requires a complete verified archive and explicit reviewed
`review/duplicate-decisions.json` before applying any merge. A dry run saves a
private title preview and publication report. Re-running replaces its own IDs
instead of adding a second import.

Titles use caption subjects and names, with conservative general titles when the
caption contains no specific subject; dates distinguish separate clips with the
same caption. `tiktok-title-overrides.json` holds manually edited titles, including
readable on-screen subjects from sampled frames of otherwise uncaptioned clips.
The script does not claim to have transcribed the recordings. The original
unabridged public caption and source link are retained on each detail page,
explicitly attributed to the publisher. Quotations are not scholarly verdicts by
the website. Topics are caption-based discovery tags.

`audit_tiktok_duplicates.py` compares SHA-256 identities against the existing
SQLite archive and uses duration plus five perceptual frame samples (10%, 30%,
50%, 70%, 90%) to propose re-encoded reposts for manual review. Candidate detection
is not proof that every possible crop, edit or partial excerpt was found.
Repeated captions, participants or hashtags alone never justify merging.

Confirmed repost: 7695172069994089742 → 7695177264484420878. Five sampled frames
match closely; full-length audio magnitude spectra correlate at 0.956, with
0.975 envelope correlation. The 720×1234 copy is kept over 576×984. Both captions
and TikTok source URLs appear on the canonical detail page; the duplicate URL
permanently redirects. Both physical originals remain in R2.

The media API permits only this profile's content-addressed object keys with a
fixed extension allowlist. Video/audio playback redirects directly to R2 with
byte-range support; it does not consume Neon network transfer. No write API or
reviewer endpoint is added. Existing 57 manual video exclusions remain effective.

Public verification: `npm --prefix frontend run check:tiktok` checks collection
counts, unique titles, source attribution, pagination, canonical redirects and
actual R2 range requests for video and audio. Run existing catalogue, research
and security regressions as well before deployment.

Final comparison covered **1,613 videos** (1,251 TikTok downloads and 362 existing
archive videos), all with five readable frame samples. There were 22 candidate
pairs; all were inspected visually and compared using full-length audio magnitude
spectra (correlations 0.935–0.999). Duplicate source groups account for repeated
pairs to existing aliases, not 22 separate new duplicate clips.

Final public projection:

- 1,232 genuinely new video listings.
- 12 existing public video pages retained, with their sharper TikTok copy selected
  for playback/download and their original captions/transcripts retained.
- 1 internal TikTok repost consolidated, plus 12 imported occurrences merged into
  the existing pages (13 duplicate import cards avoided).
- 1 duplicate between existing pages (1784 → 1289) also consolidated.
- 6 matches to previously excluded archive items remain unpublished; their R2
  originals are preserved. The 57 explicit manual exclusions remain unchanged.
- The profile collection therefore contains 1,244 distinct public videos and
  2 audio entries. No paid transcription or AI generation was used.

`source_posts` preserves all relevant public TikTok URLs and full captions for a
merged page. `preferred_media_id` selects the better physical copy while retaining
the stable page ID and canonical transcript track. Existing-entry changes are
saved in `tiktok-catalogue-overlay.json` for future catalogue refreshes. The import
is idempotent; its dry run never changes the website projections.
