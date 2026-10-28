# Research catalogue work

- Preserve original archive files, attachment occurrences, citations and review
  history. Consolidate duplicate public listings by content hash; never delete
  distinct pages or editions merely because their covers or titles match.
- User-facing catalogue titles, descriptions and search tags are Arabic. Keep
  source statements distinct from editorial interpretation and scholarly rulings.
- Reuse saved OCR, transcription and metadata caches before making any paid API
  call. Do not retranscribe an already completed content hash.
- Every new paid processing run needs an explicit spending ceiling enforced in
  code. For the ongoing October 2026 catalogue cleanup, the remaining additional
  ceiling is USD 2, tracked in `data/research/enrichment/budget-remaining.json`.
  Never reset that ledger or use `--allow-unbudgeted` to bypass the ceiling.
  `scripts/finish_media_catalogue.py` is the capped continuation entrypoint.
- Generated processing caches live under `/mnt/linuxdata/othmani-catalogue`,
  linked at `data/research/enrichment`. Keep private captions, selection reasons,
  credentials and raw provenance out of public projections and deployments.

- Manual video visibility is stored separately in Neon `video_review_decisions`
  with append-only `video_review_history`. Catalogue publication must preserve
  these decisions and apply `scripts/media-catalogue-view.sql`; never reset them
  from machine-generated selection metadata. Initial setup is
  `scripts/setup_video_review.py` (restricted role; credentials stay private).
- The private `/review/videos` page uses server-only reviewer credentials and a
  signed, expiring access-code session. Do not publish the access code, private
  review exports, or credentials as website assets. Originals stay in R2.
