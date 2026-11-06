# Public reads and Neon transfer limits

Public browsing uses publication snapshots by default. A database URL alone never
enables live reads. `RESEARCH_DATA_SOURCE=neon` explicitly enables the optional
live corpus path; `queryNeon` fails closed otherwise. Do not enable live mode
while Neon transfer is exhausted. No plan, billing, database records, assessment
history or archived originals are changed by this deployment.

The catalogue (~3 MB), archive, bibliography, source records, transcripts and OCR
read models are read from their existing server-only JSON publications. The old
minute-by-minute whole-view exports are removed, including transcript/document
search exports. Text search indexes normalize lazily once per server process.
HTML remains dynamic/private for CSP nonces; this is not a shared HTML cache.

All 17 public Arabic corpus collections are gzip-compressed into immutable R2
objects by `scripts/publish_site_corpus_snapshot.py`. Only public corpus data is
uploaded. `frontend/src/content/corpus-assets.json` records source/compressed
SHA256, byte lengths and expected counts. The build verifies and unpacks these
objects into ignored `.corpus` files, traced into corpus and main-search routes.
Visitors search/read the packaged copies; they do not trigger database exports
or R2 downloads of the full corpus. Missing/corrupt snapshots fail the build.

The 200 already-generated Bukhari reports are projected by
`scripts/export_public_hadith_drafts.py`, which validates the existing source and
profile hashes and publishes only approved report fields. It makes no API or
DB calls and publishes no raw responses, private provenance or new rulings.

For a future publication: update the public read-model JSON, validate counts and
review decisions, regenerate the corpus manifest/draft projection when their
contents change, and deploy. Neon remains the research store; the website shows
the last published snapshot rather than arbitrary unpublished database changes.
Keep 57 hidden-video decisions and all original/citation URLs intact.

## Explicit Telegram catalogue selections

`telegram-catalogue-overrides.json` preserves individual public selections across
catalogue refreshes. On 2026-11-06 the user highlighted muawiya4n/1769, already
stored in R2 but absent from the public projection. Library ID 1001769 is now
published with a neutral Arabic title, its full attributed channel caption,
Telegram source link, and a generated preview. Three sampled frames show tables
of Bukhari's teachers and quotations about narrators described as Shi'i. Duration:
429.732 seconds. No duplicate candidate appeared against the saved five-frame
fingerprints of 1,613 archived videos. This selection does not alter the 57
manual exclusions, make a scholarly ruling, or claim a completed transcription.
