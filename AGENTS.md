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
