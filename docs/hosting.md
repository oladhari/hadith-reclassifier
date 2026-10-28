# Research website hosting

## Library thumbnails

Run `python3 scripts/prepare_thumbnails.py` with Pillow (see
`scripts/requirements-thumbnails.txt`), Poppler, FFmpeg and LibreOffice installed.
The command reads and checksum-verifies local originals without changing them.
It makes bounded 640px WebP previews: images, the first PDF/document page, and a
video frame. Identical originals share a preview. Audio retains its type icon.
Outputs are `frontend/public/thumbnails/` and the source-controlled
`frontend/src/content/thumbnails.json`; both must accompany a website deployment.
These small derivatives are served by the website CDN independently of R2 originals.
The resumable command reuses verified existing previews and reports unsupported
or failed conversions in `data/research/thumbnail-report.json`. Run it again after
adding archive items. Change the filename version when changing rendering rules.
Library cards use lazy loading, an error fallback, full-page containment and a
play overlay for videos; the video detail player also uses the preview as its poster.

## Arabic catalogue and transcripts

The curated catalogue lives in the existing `research_catalogue_settings` row
`media_catalogue`. Its private editorial section retains evidence, confidence,
selection reasons and duplicate occurrences. Only its `public` section is exposed
through `website_catalogue`; full transcript text is separated into the restricted
`website_transcripts` read view so ordinary library pages do not load every transcript.
No hadith verdict, scholar approval or book acceptance is created by this workflow.

`scripts/enrich_media.py` preserves original bytes and reuses existing Arabic OCR,
album captions, PDF text and content-hash caches. Speech transcription follows the
AraClip word-timed Arabic cache pattern, using bounded Whisper API chunks. Generated
text remains unverified for quotation; literal name corrections do not rewrite a
speaker's claims. The cache is `data/research/enrichment`, linked to the data disk.
API processing is disabled by default in the initial tool. Use the capped
`scripts/finish_media_catalogue.py` continuation and preserve its spending ledger.
The guard reserves a conservative maximum before each request, settles using
returned token usage, and counts unknown network outcomes conservatively.

After metadata/source checks and manual overrides, run
`scripts/publish_media_catalogue.py --dry-run`, then its normal mode to save a
consistent local backup, descriptions, extracts, public JSON and WebVTT captions.
`--sync-cloud` deliberately synchronizes only this catalogue and its transcript
extracts to the dedicated Neon host, installs `media-catalogue-view.sql`, and verifies
the restricted reader. Existing raw provenance remains private. Install the optional
dependencies in `scripts/requirements-media-catalogue.txt`; PDF rendering also needs
Poppler and document conversion needs LibreOffice.

The public library has one listing per original content object, with duplicate IDs
redirecting to the canonical listing. Hidden or insufficiently identified material
does not appear in public browsing. Original source/media IDs remain preserved.
Arabic titles, descriptions, tags and transcripts are searchable. Theme and scope
filters separate complete books/volumes, excerpts, page scans and recordings.
Thematic chapters are bounded playback sections linked to their full original;
they are not newly encoded or context-free replacement videos.

Editorial PDF collections are registered in `frontend/src/content/media-collections.json`.
`scripts/merge_pdf_collection.py` compares all selected pages locally and copies
original PDF page objects into a versioned asset under `public/collections/`.
Near-identical covers require explicit operator confirmation with `--same-cover`;
different evidence pages are preserved. The registry records original checksums,
output checksum, omitted duplicate pages and a complete source-page map. Publication
consolidates the member listings and aliases, while original media endpoints remain
unchanged and accessible from the collection's provenance panel. The collection is
served directly by the website CDN; no paid AI processing or original R2 replacement
is involved.

The same registry supports `type: "images"` for related scans of the same work
and subject. These become one library card with a paired preview and an ordered
gallery. Each image keeps its own label, attribution, source endpoint and checksum;
the image bytes are never stitched, cropped or recompressed. Member library URLs
redirect to the canonical group, while source bundles deduplicate the group and
retain access to the originals.

Publish repository changes before deploying. Deploy the `frontend` directory as a Next.js application on Vercel. The feedback edition sends `X-Robots-Tag: noindex, nofollow`.

## Public assets

Run `scripts/publish_research_assets.py --credentials-file /absolute/path/to/existing/config` with the optional dependencies from `scripts/requirements-publish.txt`. Credentials are read at runtime, never copied into the frontend. Use `--dry-run` to inspect counts. The uploader uses the public R2 bucket only, with a separate `othmani` prefix; it never publishes the private archive bucket. Existing mismatched objects cause failure rather than overwrite. Local originals are preserved and uploads are verified by size and SHA metadata.

The seven Arabic corpus JSON files are uploaded under `othmani/corpus/`. Deduplicated original media use `othmani/originals/sha256/` keys. Upload progress is resumable; verified storage locations are recorded in the local research catalogue.

## Vercel configuration

Set `CORPUS_DATA_BASE_URL` to the public corpus directory for build-time preparation, and `MEDIA_PUBLIC_BASE_URL` to the public app prefix for runtime delivery. These are public URLs; no storage secret belongs on Vercel. Set both for production and preview deployments when applicable. The build bundles corpus files for server-side search. Large media are delivered directly by R2 rather than bundled or proxied through Vercel.

For local builds, `HADITH_DATA_DIR` can override corpus input. `TELEGRAM_ARCHIVE_DIR` selects the read-only local archive. Neither should reference account session folders.

After deployment, check anonymous access, the default collection inventory, explicit search, empty review states, source images, PDF downloads and video byte ranges. `RESEARCH_TEST_URL=https://deployment.example npm run check:research` runs the HTTP checks from `frontend/`.

## Database and text ownership

The local editorial catalogue remains at `data/research/research.sqlite3`. Its portable catalogue is hosted in the dedicated Neon project, under the private `research` schema. The website reads hadith search, review statistics, media metadata and source bundles from Neon through restricted website views. Statistics and source metadata have a 60-second cache; hadith searches query current records with pagination. Editorial page copy and curated argument/image selections remain source-controlled. Local catalogue changes must still be synchronized deliberately.

The hosted destination is a dedicated Neon PostgreSQL project named `othmani`, separate from other applications. Store book metadata, source citations, OCR/transcripts, narration texts, narrator records, filter observations and human reviews there. Keep scans, PDFs, audio and video in R2, referenced by object key and checksum. Original text discussion/provenance is internal and is not automatically a public website projection. The seven Arabic corpus JSON files are already hosted in the public corpus prefix and bundled for search during builds.

The root `.env` contains server-only R2 configuration and public delivery URLs. The frontend `.env.local` contains public delivery URLs and local read-only input paths, without R2 keys. Both files are Git-ignored and owner-only. `RESEARCH_DATABASE_PROVIDER=neon` records the selected destination. `RESEARCH_POSTGRES_URL`, `NEON_PROJECT_ID`, and `NEON_DATABASE_HOST` identify the dedicated connection; selecting a provider alone does not activate a cloud connection. Preserve the existing experimental backend's `DATABASE_URL`. Do not reuse another application's database or credentials.

Cloudflare folder creation is unnecessary: the uploader creates objects under the app prefix automatically. A separately scoped bucket can be introduced later without changing the scholarly database model.

## Neon authentication and provisioning

Authenticate with `npx --yes neonctl@latest auth` on this workstation. Credentials belong to the CLI's private configuration and must not be copied into source files. Once authenticated, create the dedicated `othmani` project on the Free plan and obtain its PostgreSQL connection string without logging the password. Store the connection string only as `RESEARCH_POSTGRES_URL` in the root private `.env`; keep the legacy backend's `DATABASE_URL` unchanged. The administrator connection remains local. The website receives only the restricted reader connection as `RESEARCH_READ_DATABASE_URL` in Vercel production and preview environments.

Before migration, retain a consistent local backup and validate the exported table checksums and row counts. The migration uses a single transaction, checks every table by row count and an order-independent content fingerprint, enables RLS, and revokes PUBLIC access to the schema. Private discussion provenance and import payloads remain in the original local archive; they are excluded from this portable catalogue. File uploads to R2 are independent and continue during this setup.

## Catalogue migration and storage synchronization

Install `scripts/requirements-database-publish.txt` along with the research requirements. `scripts/publish_research_database.py --dry-run` verifies export checksums without contacting a database. Initial migration refuses to overwrite an existing `research` schema and checks the connection against `NEON_DATABASE_HOST`. Use `--verify-only` for a later read-only content comparison against the same export snapshot. After any intentional cloud synchronization, generate a fresh snapshot before comparing it.

`--sync-storage` updates only locally verified R2 storage locations in Neon. It does not publish discussion payloads, alter scholarly reviews, or make database tables public. The local upload completion hook runs this synchronization after the media upload finishes. Credentials belong only in the root private `.env`; only the restricted reader connection belongs on Vercel; the administrator connection does not.

## Active website reader

Run `scripts/configure_website_reader.py` after initial migration to install `scripts/website-read-views.sql` and provision the restricted login. It grants SELECT only on the website views, denies editing privileges, and leaves original provenance inaccessible. Run `scripts/check_neon_website.py` to verify permissions and review-state transitions. Its synthetic changes use a transaction that is always rolled back.

Set the server-only `RESEARCH_READ_DATABASE_URL` in the frontend environment. A configured Neon connection never silently falls back to stale JSON on database errors; readers see a retry message. Offline snapshot mode remains available only when this connection is absent. Database credentials are never NEXT_PUBLIC variables. Hosted builds skip corpus JSON preparation when the reader is configured; original JSON files remain preserved in R2.

The HTTP integration suite was also run against the Neon-connected server with `HADITH_DATA_DIR` pointing to a nonexistent directory, verifying that search results came from the database. Media bytes continue to come from R2. On local networks with slow IPv4 connections and unavailable IPv6, Node's `--network-family-autoselection-attempt-timeout=2000` option may be needed for the local preview; this is not a Vercel requirement.
