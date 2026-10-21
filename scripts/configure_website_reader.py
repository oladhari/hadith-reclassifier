"""Install website read views and a restricted login; never print credentials."""

import re
import secrets
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

import psycopg
from psycopg import sql
from publish_research_database import configuration

ROOT = Path(__file__).resolve().parents[1]
config = configuration(ROOT / ".env")
admin = config["RESEARCH_POSTGRES_URL"]
target = urlparse(admin)
if target.hostname != config["NEON_DATABASE_HOST"] or not target.hostname.endswith(
    ".neon.tech"
):
    raise ValueError("Expected dedicated Neon project connection")
role = "othmani_website_reader"
existing = config.get("RESEARCH_READ_DATABASE_URL")
if existing and urlparse(existing).username != role:
    raise ValueError("Unexpected reader identity")
password = urlparse(existing).password if existing else secrets.token_urlsafe(36)
with psycopg.connect(admin, connect_timeout=30) as conn:
    conn.execute((ROOT / "scripts/website-read-views.sql").read_text())
    exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone()
    if exists and not existing:
        raise ValueError(
            "Existing reader needs its saved credentials; refusing password reset"
        )
    if not exists:
        conn.execute(
            sql.SQL(
                "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS"
            ).format(sql.Identifier(role), sql.Literal(password))
        )
    conn.execute(
        sql.SQL("GRANT USAGE ON SCHEMA research TO {}").format(sql.Identifier(role))
    )
    for view in [
        "website_hadiths",
        "website_corpus_counts",
        "website_media",
        "website_sources",
        "website_bibliography",
    ]:
        conn.execute(
            sql.SQL("GRANT SELECT ON research.{} TO {}").format(
                sql.Identifier(view), sql.Identifier(role)
            )
        )
    conn.execute(
        sql.SQL("ALTER ROLE {} SET default_transaction_read_only=on").format(
            sql.Identifier(role)
        )
    )
    conn.execute(
        sql.SQL("ALTER ROLE {} SET statement_timeout='15s'").format(
            sql.Identifier(role)
        )
    )
url = existing or urlunparse(
    target._replace(
        netloc=f"{role}:{quote(password, safe='')}@{target.hostname}:{target.port or 5432}"
    )
)
for path in [ROOT / ".env", ROOT / "frontend/.env.local"]:
    text = path.read_text() if path.exists() else ""
    if re.search(r"^RESEARCH_READ_DATABASE_URL=", text, re.MULTILINE):
        text = re.sub(
            r"^RESEARCH_READ_DATABASE_URL=.*$",
            lambda _: "RESEARCH_READ_DATABASE_URL=" + url,
            text,
            flags=re.MULTILINE,
        )
    else:
        text += (
            "\n# Server-only restricted Neon reader\nRESEARCH_READ_DATABASE_URL="
            + url
            + "\n"
        )
    path.write_text(text)
    path.chmod(0o600)
print(
    "Website views and restricted reader configured; private environment files updated."
)
