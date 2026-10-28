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
- Video review was completed by the user: 129 kept, 57 hidden. The review page
  and APIs were removed, and the reviewer role disabled. Preserve the final
  `frontend/src/content/video-visibility.json` fallback and all database decisions.
  Do not re-enable review access without a new user request. Private review
  backups and credentials must never enter public assets. Originals stay in R2.
