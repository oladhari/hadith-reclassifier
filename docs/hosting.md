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

The local editorial catalogue remains at `data/research/research.sqlite3`. Its portable catalogue is hosted in the dedicated Neon project, under the private `research` schema. The published website uses generated read-only JSON projections; it does not query Neon on every page view. Until an editorial database adapter is introduced, make catalogue changes locally and synchronize deliberately.

The hosted destination is a dedicated Neon PostgreSQL project named `othmani`, separate from other applications. Store book metadata, source citations, OCR/transcripts, narration texts, narrator records, filter observations and human reviews there. Keep scans, PDFs, audio and video in R2, referenced by object key and checksum. Original text discussion/provenance is internal and is not automatically a public website projection. The seven Arabic corpus JSON files are already hosted in the public corpus prefix and bundled for search during builds.

The root `.env` contains server-only R2 configuration and public delivery URLs. The frontend `.env.local` contains public delivery URLs and local read-only input paths, without R2 keys. Both files are Git-ignored and owner-only. `RESEARCH_DATABASE_PROVIDER=neon` records the selected destination. `RESEARCH_POSTGRES_URL`, `NEON_PROJECT_ID`, and `NEON_DATABASE_HOST` identify the dedicated connection; selecting a provider alone does not activate a cloud connection. Preserve the existing experimental backend's `DATABASE_URL`. Do not reuse another application's database or credentials.

Cloudflare folder creation is unnecessary: the uploader creates objects under the app prefix automatically. A separately scoped bucket can be introduced later without changing the scholarly database model.

## Neon authentication and provisioning

Authenticate with `npx --yes neonctl@latest auth` on this workstation. Credentials belong to the CLI's private configuration and must not be copied into source files. Once authenticated, create the dedicated `othmani` project on the Free plan and obtain its PostgreSQL connection string without logging the password. Store the connection string only as `RESEARCH_POSTGRES_URL` in the root private `.env`; keep the legacy backend's `DATABASE_URL` unchanged. The current website continues using its published read-only snapshots until a database adapter is explicitly connected and verified.

Before migration, retain a consistent local backup and validate the exported table checksums and row counts. The migration uses a single transaction, checks every table by row count and an order-independent content fingerprint, enables RLS, and revokes PUBLIC access to the schema. Private discussion provenance and import payloads remain in the original local archive; they are excluded from this portable catalogue. File uploads to R2 are independent and continue during this setup.

## Catalogue migration and storage synchronization

Install `scripts/requirements-database-publish.txt` along with the research requirements. `scripts/publish_research_database.py --dry-run` verifies export checksums without contacting a database. Initial migration refuses to overwrite an existing `research` schema and checks the connection against `NEON_DATABASE_HOST`. Use `--verify-only` for a later read-only content comparison against the same export snapshot. After any intentional cloud synchronization, generate a fresh snapshot before comparing it.

`--sync-storage` updates only locally verified R2 storage locations in Neon. It does not publish discussion payloads, alter scholarly reviews, or make database tables public. The local upload completion hook runs this synchronization after the media upload finishes. Credentials belong only in the root private `.env`; the current frontend does not require database credentials on Vercel.
