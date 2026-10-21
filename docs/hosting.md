# Research website hosting

Publish repository changes before deploying. Deploy the `frontend` directory as a Next.js application on Vercel. The feedback edition sends `X-Robots-Tag: noindex, nofollow`.

## Public assets

Run `scripts/publish_research_assets.py --credentials-file /absolute/path/to/existing/config` with the optional dependencies from `scripts/requirements-publish.txt`. Credentials are read at runtime, never copied into the frontend. Use `--dry-run` to inspect counts. The uploader uses the public R2 bucket only, with a separate `othmani` prefix; it never publishes the private archive bucket. Existing mismatched objects cause failure rather than overwrite. Local originals are preserved and uploads are verified by size and SHA metadata.

The seven Arabic corpus JSON files are uploaded under `othmani/corpus/`. Deduplicated original media use `othmani/originals/sha256/` keys. Upload progress is resumable; verified storage locations are recorded in the local research catalogue.

## Vercel configuration

Set `CORPUS_DATA_BASE_URL` to the public corpus directory for build-time preparation, and `MEDIA_PUBLIC_BASE_URL` to the public app prefix for runtime delivery. These are public URLs; no storage secret belongs on Vercel. Set both for production and preview deployments when applicable. The build bundles corpus files for server-side search. Large media are delivered directly by R2 rather than bundled or proxied through Vercel.

For local builds, `HADITH_DATA_DIR` can override corpus input. `TELEGRAM_ARCHIVE_DIR` selects the read-only local archive. Neither should reference account session folders.

After deployment, check anonymous access, the default collection inventory, explicit search, empty review states, source images, PDF downloads and video byte ranges. `RESEARCH_TEST_URL=https://deployment.example npm run check:research` runs the HTTP checks from `frontend/`.

## Database and text ownership

The authoritative research catalogue is currently the local SQLite database at `data/research/research.sqlite3`. The published website uses generated read-only JSON projections; publishing the website did not migrate the catalogue to a cloud database.

The selected next destination is a dedicated Supabase PostgreSQL project named `othmani`, separate from other applications. Store book metadata, source citations, OCR/transcripts, narration texts, narrator records, filter observations and human reviews there. Keep scans, PDFs, audio and video in R2, referenced by object key and checksum. Original text discussion/provenance is internal and is not automatically a public website projection. The seven Arabic corpus JSON files are already hosted in the public corpus prefix and bundled for search during builds.

The root `.env` contains server-only R2 configuration and public delivery URLs. The frontend `.env.local` contains public delivery URLs and local read-only input paths, without R2 keys. Both files are Git-ignored and owner-only. Reserved `RESEARCH_POSTGRES_URL`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY` must remain empty until the dedicated project exists; they do not activate a cloud connection. Preserve the existing experimental backend's `DATABASE_URL`. Do not reuse another application's Supabase project or keys.

Cloudflare folder creation is unnecessary: the uploader creates objects under the app prefix automatically. A separately scoped bucket can be introduced later without changing the scholarly database model.
