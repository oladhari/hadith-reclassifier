# Hadith Reclassifier

A research application for browsing hadith collections and generating AI-assisted classifications with OpenAI. It combines a Next.js interface, a FastAPI backend, and PostgreSQL to organize narrations, analysis, and accepted entries in the Sahih Othmani collection.

AI-generated assessments require scholarly review; they are not authoritative authentication rulings.

## Features

- Import Arabic and English collection data from local JSON files.
- Browse and search narrations, inspect individual hadiths, and view classification statistics.
- Generate classification JSON covering transmission chains, narrator reliability, Quranic consistency, historical consistency, and other criteria.
- Store classifications and assign collection numbers to accepted narrations.
- Generate accepted or rejected book-entry text through the backend AI service.
- Reject incomplete or empty OpenAI responses before using their output.

## Stack and layout

- `frontend/`: Next.js 16, React 19, TypeScript, and Tailwind CSS.
- `backend/`: FastAPI, SQLAlchemy, Pydantic, and the OpenAI Python SDK.
- `scripts/`: collection download utility.
- `docker-compose.yml`: frontend, backend, and PostgreSQL services.
- `data/hadiths/`: local collection files, excluded from Git.

## Run with Docker

1. Copy the environment template only for a new setup. Preserve an existing `.env`:

   ```sh
   cp -n .env.example .env
   chmod 600 .env
   ```

2. Edit `.env` locally and set `OPENAI_API_KEY`. `OPENAI_TEXT_MODEL` defaults to `gpt-5-mini`. Keep the key private and never place it in frontend code. `SUNNAH_API_KEY` is optional; local-file ingestion does not require it.
3. Start the application:

   ```sh
   docker compose up --build -d
   ```

- Frontend: http://localhost:3000
- Backend API documentation: http://localhost:8000/api/v1/docs
- Health endpoint: http://localhost:8000/health

Compose uses the PostgreSQL connection configured for its `db` service. Its bundled database credentials are development defaults; configure secure credentials before deploying publicly.

## Collection data

To download collection files for a new installation:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python scripts/download_hadiths.py
```

The downloader preserves existing files. Use the dashboard or ingestion API to import selected collections into PostgreSQL. Importing or classifying records changes the database; live AI calls may incur OpenAI API charges.

## Validation

Run the service tests from the project root:

```sh
DEBUG=false PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
.venv/bin/python -m pip check
docker compose config --quiet
```

The automated service tests use mocked responses and synthetic data without API calls or database writes. They cover JSON parsing, invalid classifications, incomplete or empty responses, missing credentials, and both book-entry branches.

For frontend development, run `npm ci` and `npm run dev` in `frontend/`. `npm run lint` and `npm run build` provide frontend checks.

## Secrets and existing data

`.env`, environment variants, virtual environments, dependencies, build output, local data, and database artifacts are ignored by Git. `.env.example` contains configuration names without a real API key. The backend Docker build excludes environment files.

PostgreSQL data persists in the `pg_data` Docker volume. Use `docker compose stop` or `docker compose down` to stop services while retaining that volume. Do not use `docker compose down -v` when preserving records. Back up your database before schema or deployment changes.

## Arabic research website

The public Arabic RTL edition provides topic dossiers, source scans, PDFs and video, a searchable library, and a reviewed-book workflow. It uses navy, ivory and copper with IBM Plex Sans Arabic and Noto Naskh Arabic. Public references open within the website.

`/corpus` starts with collection inventory and actual review statistics. Narrations appear after an explicit search or status selection. Seven structured Arabic collections contain 36,390 records including repeated transmission routes. Musnad Ahmad scans are available, but a complete structured collection is not yet imported. Imported source grades are separate from project decisions; acceptance and book inclusion require recorded human review.

The public research pages require no OpenAI key or backend service. The legacy experimental AI backend is separate. The 22-layer draft framework supports evidence-backed examination and a Quran-comparison gate; it does not automatically authenticate narrations. See [filter documentation](docs/hadith-filter-layers.md).

The normalized local catalogue preserves originals and provenance, deduplicates objects, and generates public JSON projections. OCR text remains subject to verification. Video transcription and the editorial review interface remain future work. See [database documentation](docs/research-database.md).

For local development, run `npm ci` and `npm run dev` in `frontend/`. Production builds prepare seven corpus files in the ignored `.corpus/` directory. Media can be served from the local archive or public object storage. See [hosting instructions](docs/hosting.md).

Run `npm run lint`, `npm run build`, and, against a running edition, `npm run check:research` in `frontend/`. Set `RESEARCH_TEST_URL` to test another deployment. These checks do not call AI or mutate scholarly assessments.
