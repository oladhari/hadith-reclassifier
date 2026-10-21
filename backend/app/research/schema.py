"""Portable research catalogue, independent of the legacy AI-classification schema."""

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Text,
    Integer,
    BigInteger,
    Boolean,
    JSON,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    CheckConstraint,
    Index,
    PrimaryKeyConstraint,
    false,
)

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


def identity():
    return Column("id", String(36), primary_key=True)


def fk(name, target, nullable=False):
    return Column(
        name,
        String(36),
        ForeignKey(target, ondelete="RESTRICT"),
        nullable=nullable,
        index=True,
    )


def stamp():
    return Column("created_at", String(40), nullable=False)


def table(name, *cols):
    return Table(name, metadata, *cols)


schema_versions = table(
    "research_schema_versions",
    Column("version", Integer, primary_key=True),
    Column("applied_at", String(40), nullable=False),
)
imports = table(
    "research_imports",
    identity(),
    Column("fingerprint", String(64), nullable=False, unique=True),
    Column("inputs", JSON, nullable=False),
    stamp(),
)
sources = table(
    "research_sources",
    identity(),
    Column("legacy_id", Integer, unique=True, nullable=False),
    Column("reference_code", String(32), nullable=False, unique=True),
    Column("source_date", String(40)),
    Column("kind", String(32), nullable=False),
    Column("review_state", String(32), nullable=False, server_default="imported"),
    Column("reviewed_by", String(200)),
    Column("reviewed_at", String(40)),
    Column("editorial_title", Text),
    stamp(),
    CheckConstraint(
        "review_state IN ('imported','extracted','source_checked','scholarly_reviewed','published')",
        name="review_state",
    ),
    CheckConstraint(
        "review_state NOT IN ('scholarly_reviewed','published') OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)",
        name="reviewer_required",
    ),
)
provenance = table(
    "research_provenance",
    identity(),
    fk("source_id", "research_sources.id"),
    fk("import_id", "research_imports.id"),
    Column("provider", String(32), nullable=False),
    Column("external_id", String(80), nullable=False),
    Column("content_sha256", String(64), nullable=False),
    Column("original_text", Text),
    Column("original_payload", JSON, nullable=False),
    stamp(),
    UniqueConstraint("source_id", "content_sha256"),
)
albums = table(
    "research_albums",
    identity(),
    Column("external_group_id", String(80), unique=True, nullable=False),
    stamp(),
)
album_members = table(
    "research_album_members",
    fk("album_id", "research_albums.id"),
    fk("source_id", "research_sources.id"),
    Column("position", Integer, nullable=False),
    UniqueConstraint("album_id", "source_id"),
    UniqueConstraint("album_id", "position"),
)
objects = table(
    "research_objects",
    identity(),
    Column("sha256", String(64), unique=True, nullable=False),
    Column("byte_size", BigInteger, nullable=False),
    Column("mime_type", String(200), nullable=False),
    Column("object_key", String(300), unique=True, nullable=False),
    stamp(),
    CheckConstraint("byte_size >= 0", name="nonnegative_size"),
)
locations = table(
    "research_storage_locations",
    identity(),
    fk("object_id", "research_objects.id"),
    Column("provider", String(32), nullable=False),
    Column("bucket", String(200), nullable=False, server_default=""),
    Column("key", Text, nullable=False),
    Column("state", String(32), nullable=False),
    Column("verified_at", String(40)),
    UniqueConstraint("object_id", "provider", "bucket", "key"),
    CheckConstraint("provider IN ('local','r2')", name="storage_provider"),
    CheckConstraint(
        "state IN ('available','planned','missing')", name="location_state"
    ),
)
media = table(
    "research_media",
    identity(),
    fk("source_id", "research_sources.id"),
    fk("object_id", "research_objects.id"),
    Column("legacy_id", Integer, unique=True, nullable=False),
    Column("kind", String(24), nullable=False),
    Column("original_name", Text),
    Column("mime_type", String(200), nullable=False),
    Column("archive_relative_path", Text, nullable=True),
    Column("source_date", String(40)),
    stamp(),
)
works = table(
    "research_works",
    identity(),
    Column("title", Text, nullable=False),
    Column("author_name", Text),
    Column(
        "verification_state",
        String(32),
        nullable=False,
        server_default="needs_verification",
    ),
    stamp(),
)
editions = table(
    "research_editions",
    identity(),
    fk("work_id", "research_works.id"),
    Column("editor_name", Text),
    Column("publisher", Text),
    Column("edition_label", Text),
    Column("publication_year", String(32)),
    Column(
        "verification_state",
        String(32),
        nullable=False,
        server_default="needs_verification",
    ),
    stamp(),
)
citations = table(
    "research_citations",
    identity(),
    fk("source_id", "research_sources.id"),
    fk("media_id", "research_media.id", True),
    fk("work_id", "research_works.id"),
    fk("edition_id", "research_editions.id", True),
    Column("volume_label", String(80)),
    Column("printed_page", String(80)),
    Column("pdf_page", Integer),
    Column("description", Text),
    Column(
        "verification_state",
        String(32),
        nullable=False,
        server_default="needs_verification",
    ),
    stamp(),
)
extracts = table(
    "research_extracts",
    identity(),
    fk("source_id", "research_sources.id"),
    fk("media_id", "research_media.id", True),
    Column("kind", String(40), nullable=False),
    Column("text", Text, nullable=False),
    Column("text_sha256", String(64), nullable=False),
    Column("ordinal", Integer, nullable=False),
    Column("language", String(16), nullable=False, server_default="ar"),
    Column("start_ms", BigInteger),
    Column("end_ms", BigInteger),
    Column("review_state", String(32), nullable=False, server_default="unverified"),
    Column("method", String(80), nullable=False),
    stamp(),
    UniqueConstraint("source_id", "kind", "text_sha256"),
    CheckConstraint("start_ms IS NULL OR start_ms >= 0", name="nonnegative_start"),
    CheckConstraint(
        "end_ms IS NULL OR (start_ms IS NOT NULL AND end_ms >= start_ms)",
        name="ordered_timestamps",
    ),
)
topics = table(
    "research_topics",
    identity(),
    Column("slug", String(100), nullable=False, unique=True),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("sort_order", Integer, nullable=False),
    Column("terms", JSON, nullable=False),
    Column("required_terms", JSON, nullable=False),
    stamp(),
)
cases = table(
    "research_cases",
    identity(),
    Column("slug", String(100), nullable=False, unique=True),
    Column("title", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("editorial_data", JSON, nullable=False),
    Column("review_state", String(32), nullable=False, server_default="draft"),
    stamp(),
)
topic_cases = table(
    "research_topic_cases",
    fk("topic_id", "research_topics.id"),
    fk("case_id", "research_cases.id"),
    Column("position", Integer, nullable=False),
    UniqueConstraint("topic_id", "case_id"),
)


def links(name, owner, target):
    return table(
        name,
        fk(owner, target),
        fk("source_id", "research_sources.id"),
        Column("matched_terms", JSON, nullable=False),
        Column("normalized_text_hash", String(64)),
        Column("selected_reference", Boolean, nullable=False, server_default=false()),
        Column("link_state", String(32), nullable=False, server_default="suggested"),
        UniqueConstraint(owner, "source_id"),
    )


topic_sources = links("research_topic_sources", "topic_id", "research_topics.id")
case_sources = links("research_case_sources", "case_id", "research_cases.id")
collections = table(
    "research_collections",
    identity(),
    Column("slug", String(80), unique=True, nullable=False),
    Column("title", Text, nullable=False),
    stamp(),
)
hadiths = table(
    "research_hadiths",
    identity(),
    fk("collection_id", "research_collections.id"),
    Column("source_number", String(80), nullable=False),
    Column("source_ordinal", Integer, nullable=False),
    Column("book_number", String(80)),
    Column("book_hadith_number", String(80)),
    Column("review_state", String(32), nullable=False, server_default="unreviewed"),
    stamp(),
    UniqueConstraint("collection_id", "source_number"),
)
hadith_texts = table(
    "research_hadith_texts",
    identity(),
    fk("hadith_id", "research_hadiths.id", True),
    fk("collection_id", "research_collections.id"),
    Column("language", String(16), nullable=False),
    Column("source_ordinal", Integer, nullable=False),
    Column("source_number", String(80), nullable=False),
    Column("text", Text, nullable=False),
    Column("normalized_text", Text, nullable=False),
    Column("original_data", JSON, nullable=False),
    Column("source_file", String(200), nullable=False),
    Column("source_file_sha256", String(64), nullable=False),
    stamp(),
    UniqueConstraint("collection_id", "language", "source_ordinal"),
)
Index(
    "ix_research_hadith_texts_language_collection",
    hadith_texts.c.language,
    hadith_texts.c.collection_id,
)
rules = table(
    "research_rules",
    identity(),
    Column("code", String(80), nullable=False, unique=True),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("version", Integer, nullable=False),
    Column("status", String(24), nullable=False, server_default="proposed"),
    stamp(),
)
narrators = table(
    "research_narrators",
    identity(),
    Column("name_arabic", Text, nullable=False),
    Column("aliases", JSON, nullable=False),
    Column("birth_year_ah", Integer),
    Column("death_year_ah", Integer),
    Column("review_state", String(32), nullable=False, server_default="unreviewed"),
    stamp(),
)
judgments = table(
    "research_narrator_judgments",
    identity(),
    fk("narrator_id", "research_narrators.id"),
    fk("citation_id", "research_citations.id"),
    Column("critic_name", Text, nullable=False),
    Column("exact_text", Text, nullable=False),
    Column("context", Text),
    Column("review_state", String(32), nullable=False, server_default="unreviewed"),
    stamp(),
)
assessments = table(
    "research_assessments",
    identity(),
    fk("hadith_id", "research_hadiths.id"),
    Column("methodology_version", String(80), nullable=False),
    Column("verdict", String(32), nullable=False, server_default="under_review"),
    Column("reasoning", Text),
    Column("reviewer", String(200)),
    Column("reviewed_at", String(40)),
    stamp(),
    CheckConstraint(
        "verdict IN ('under_review','accepted','rejected')", name="assessment_verdict"
    ),
    CheckConstraint(
        "verdict = 'under_review' OR (reviewer IS NOT NULL AND reviewed_at IS NOT NULL)",
        name="assessment_review_required",
    ),
)
assessment_evidence = table(
    "research_assessment_evidence",
    identity(),
    fk("assessment_id", "research_assessments.id"),
    fk("source_id", "research_sources.id"),
    fk("rule_id", "research_rules.id", True),
    Column("finding", Text, nullable=False),
    UniqueConstraint("assessment_id", "source_id", "rule_id"),
)
book_entries = table(
    "research_book_entries",
    identity(),
    fk("hadith_id", "research_hadiths.id"),
    fk("assessment_id", "research_assessments.id"),
    Column("edition", String(80), nullable=False),
    Column("entry_number", Integer),
    Column("status", String(32), nullable=False, server_default="draft"),
    Column("reviewer", String(200)),
    Column("reviewed_at", String(40)),
    stamp(),
    UniqueConstraint("edition", "entry_number"),
    UniqueConstraint("edition", "hadith_id"),
    CheckConstraint("status IN ('draft','approved')", name="book_status"),
    CheckConstraint(
        "status != 'approved' OR (reviewer IS NOT NULL AND reviewed_at IS NOT NULL)",
        name="book_review_required",
    ),
)
jobs = table(
    "research_processing_jobs",
    identity(),
    fk("object_id", "research_objects.id"),
    Column("kind", String(32), nullable=False),
    Column("status", String(24), nullable=False, server_default="pending"),
    Column("input_sha256", String(64), nullable=False),
    Column("parameters", JSON, nullable=False),
    Column("result_extract_ids", JSON),
    Column("error", Text),
    stamp(),
    UniqueConstraint("object_id", "kind", "input_sha256"),
    CheckConstraint(
        "kind IN ('ocr','pdf_text','transcription')", name="processing_kind"
    ),
)

# Junction records have real composite primary keys for reliable export and migration.
for name, columns in {
    "research_album_members": ("album_id", "source_id"),
    "research_topic_cases": ("topic_id", "case_id"),
    "research_topic_sources": ("topic_id", "source_id"),
    "research_case_sources": ("case_id", "source_id"),
}.items():
    metadata.tables[name].append_constraint(PrimaryKeyConstraint(*columns))
settings = table(
    "research_catalogue_settings",
    Column("key", String(100), primary_key=True),
    Column("value", JSON, nullable=False),
)
# A book entry can reference only an accepted assessment of the SAME hadith.

assessments.append_constraint(UniqueConstraint("id", "hadith_id", "verdict"))
book_entries.append_column(
    Column("required_verdict", String(32), nullable=False, server_default="accepted")
)
book_entries.append_constraint(
    CheckConstraint(
        "required_verdict = 'accepted'", name="accepted_assessment_required"
    )
)
book_entries.append_constraint(
    ForeignKeyConstraint(
        ["assessment_id", "hadith_id", "required_verdict"],
        [
            "research_assessments.id",
            "research_assessments.hadith_id",
            "research_assessments.verdict",
        ],
    )
)
corpus_files = table(
    "research_corpus_files",
    identity(),
    fk("collection_id", "research_collections.id"),
    Column("language", String(16), nullable=False),
    Column("filename", String(200), nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("metadata", JSON, nullable=False),
    Column("record_count", Integer, nullable=False),
    stamp(),
    UniqueConstraint("collection_id", "language", "sha256"),
)

# Versioned, evidence-led triage. No automatic accepted/rejected hadith verdicts.
filter_profiles = table(
    "research_filter_profiles", identity(),
    Column("profile_key", String(100), nullable=False),
    Column("version", Integer, nullable=False),
    Column("definition", JSON, nullable=False),
    Column("definition_sha256", String(64), nullable=False),
    Column("status", String(24), nullable=False), stamp(),
    UniqueConstraint("profile_key", "version"),
    CheckConstraint("status IN ('draft','active','retired')", name="profile_status"),
)
filter_routes = table(
    "research_filter_routes", identity(), fk("hadith_id", "research_hadiths.id"),
    Column("route_key", String(100), nullable=False),
    Column("isnad_text", Text, nullable=False), stamp(),
    UniqueConstraint("hadith_id", "route_key"), UniqueConstraint("id", "hadith_id"),
)
filter_observations = table(
    "research_filter_observations", identity(),
    fk("hadith_id", "research_hadiths.id"), fk("profile_id", "research_filter_profiles.id"),
    Column("route_id", String(36)), Column("scope", String(16), nullable=False),
    Column("layer_code", String(20), nullable=False),
    Column("finding", String(24), nullable=False),
    Column("facts", JSON, nullable=False), Column("evidence", JSON, nullable=False),
    Column("supersedes", JSON, nullable=False),
    Column("reasoning", Text, nullable=False),
    Column("review_state", String(24), nullable=False),
    Column("reviewer", String(200)), Column("reviewed_at", String(40)), stamp(),
    ForeignKeyConstraint(["route_id", "hadith_id"], ["research_filter_routes.id", "research_filter_routes.hadith_id"]),
    CheckConstraint("scope IN ('report','route')", name="observation_scope"),
    CheckConstraint("(scope='report' AND route_id IS NULL) OR (scope='route' AND route_id IS NOT NULL)", name="route_scope"),
    CheckConstraint("finding IN ('clear','concern','disputed','not_applicable')", name="finding_type"),
    CheckConstraint("review_state IN ('draft','reviewed')", name="observation_review"),
    CheckConstraint("review_state!='reviewed' OR (reviewer IS NOT NULL AND reviewed_at IS NOT NULL)", name="observation_reviewer"),
)
filter_runs = table(
    "research_filter_runs", identity(), fk("hadith_id", "research_hadiths.id"),
    fk("profile_id", "research_filter_profiles.id"),
    Column("input_sha256", String(64), nullable=False),
    Column("text_sha256", String(64), nullable=False),
    Column("snapshot", JSON, nullable=False), Column("report", JSON, nullable=False),
    Column("outcome", String(32), nullable=False), stamp(),
    UniqueConstraint("hadith_id", "profile_id", "input_sha256"),
    CheckConstraint("outcome IN ('needs_data','flagged','disputed','methodology_pending','ready_for_review')", name="triage_outcome"),
)
