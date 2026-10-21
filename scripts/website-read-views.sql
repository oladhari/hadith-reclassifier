-- Public read models only. Website credentials receive SELECT on these views,
-- not on the underlying editorial/review tables.
CREATE OR REPLACE FUNCTION research.website_date(value text) RETURNS timestamptz
LANGUAGE plpgsql STABLE STRICT SET timezone = 'UTC' AS $$
BEGIN RETURN value::timestamptz; EXCEPTION WHEN OTHERS THEN RETURN NULL; END;
$$;

CREATE OR REPLACE VIEW research.website_hadiths AS
WITH runs AS (
 SELECT DISTINCT ON (r.hadith_id) r.*
 FROM research.research_filter_runs r JOIN research.research_filter_profiles p ON p.id=r.profile_id
 ORDER BY r.hadith_id,p.version DESC,research.website_date(r.created_at) DESC NULLS LAST,r.id DESC
), assessments AS (
 SELECT DISTINCT ON (a.hadith_id) a.* FROM research.research_assessments a
 ORDER BY a.hadith_id,research.website_date(COALESCE(NULLIF(a.reviewed_at,''),a.created_at)) DESC NULLS LAST,
 research.website_date(a.created_at) DESC NULLS LAST,a.id DESC
), base AS (
 SELECT h.id,c.slug,c.title,h.source_number,h.source_ordinal,t.text,t.normalized_text,t.original_data,
 a.id AS assessment_id,a.verdict,a.reasoning,a.reviewed_at,
 COALESCE(a.verdict IN ('accepted','rejected') AND length(trim(a.reviewer))>0 AND research.website_date(a.reviewed_at) IS NOT NULL,false) AS final,
 EXISTS(SELECT 1 FROM jsonb_array_elements(CASE WHEN jsonb_typeof(r.report::jsonb->'results')='array' THEN r.report::jsonb->'results' ELSE '[]'::jsonb END) e
 WHERE e->>'state' IN ('clear','flagged','disputed','not_applicable') AND jsonb_typeof(e->'observation_ids')='array' AND e->'observation_ids'<>'[]'::jsonb) AS filtered,
 a.id IS NOT NULL AS assessed,
 EXISTS(SELECT 1 FROM research.research_filter_routes fr WHERE fr.hadith_id=h.id)
 OR EXISTS(SELECT 1 FROM research.research_filter_observations fo WHERE fo.hadith_id=h.id) AS started
 FROM research.research_hadiths h JOIN research.research_collections c ON c.id=h.collection_id
 LEFT JOIN research.research_hadith_texts t ON t.hadith_id=h.id AND t.language='ar'
 LEFT JOIN runs r ON r.hadith_id=h.id LEFT JOIN assessments a ON a.hadith_id=h.id
), states AS (
 SELECT *,CASE WHEN final THEN verdict WHEN assessed OR filtered THEN 'needs_review' WHEN started THEN 'in_progress' ELSE 'unreviewed' END AS status,
 final AND verdict='accepted' AND EXISTS(SELECT 1 FROM research.research_book_entries b WHERE b.hadith_id=base.id AND b.assessment_id=base.assessment_id AND b.status='approved' AND length(b.reviewer)>0 AND length(b.reviewed_at)>0) AS in_book
 FROM base
)
SELECT id,slug,title,source_number,source_ordinal,text,normalized_text,original_data,status,filtered,in_book,
 CASE WHEN final THEN jsonb_build_object('verdict',verdict,'reasoning',COALESCE(reasoning,''),'reviewed_at',reviewed_at) ELSE NULL END AS review
FROM states;

CREATE OR REPLACE VIEW research.website_corpus_counts AS
SELECT slug,title,count(*)::int AS total,count(*) FILTER(WHERE length(trim(text))>0)::int AS with_text,
count(*) FILTER(WHERE filtered)::int AS filtered,count(*) FILTER(WHERE in_book)::int AS in_book,
count(*) FILTER(WHERE status='unreviewed')::int AS unreviewed,count(*) FILTER(WHERE status='in_progress')::int AS in_progress,
count(*) FILTER(WHERE status='needs_review')::int AS needs_review,count(*) FILTER(WHERE status='accepted')::int AS accepted,
count(*) FILTER(WHERE status='rejected')::int AS rejected
FROM research.website_hadiths GROUP BY slug,title;

CREATE OR REPLACE VIEW research.website_media AS
SELECT m.legacy_id AS id,m.source_date AS date,m.kind,m.mime_type AS mime,
COALESCE(m.archive_relative_path,'media/'||m.legacy_id||'/'||COALESCE(m.original_name,'original'||CASE m.kind WHEN 'image' THEN '.jpg' WHEN 'pdf' THEN '.pdf' WHEN 'video' THEN '.mp4' WHEN 'audio' THEN '.mp3' ELSE '.bin' END)) AS path,
o.byte_size AS size,m.original_name AS name,o.object_key,
COALESCE(l.state,'planned') AS storage_state
FROM research.research_media m JOIN research.research_objects o ON o.id=m.object_id
LEFT JOIN LATERAL(SELECT state FROM research.research_storage_locations WHERE object_id=o.id AND provider='r2' ORDER BY verified_at DESC NULLS LAST LIMIT 1) l ON true;

CREATE OR REPLACE VIEW research.website_sources AS
SELECT s.legacy_id AS id,s.source_date AS date,
COALESCE((SELECT jsonb_agg(m.legacy_id ORDER BY am.position)
 FROM research.research_album_members mine JOIN research.research_album_members am ON am.album_id=mine.album_id
 JOIN research.research_media m ON m.source_id=am.source_id WHERE mine.source_id=s.id),
 (SELECT jsonb_agg(m.legacy_id ORDER BY m.legacy_id) FROM research.research_media m WHERE m.source_id=s.id),'[]'::jsonb) AS files,
COALESCE((SELECT jsonb_agg(e.text ORDER BY e.ordinal) FROM research.research_extracts e WHERE e.source_id=s.id AND e.kind='collection_quote' AND e.review_state IN ('unverified','verified')),'[]'::jsonb) AS quotes
FROM research.research_sources s;

CREATE OR REPLACE VIEW research.website_bibliography AS
SELECT DISTINCT ON (s.legacy_id) s.legacy_id AS id,w.title,c.description AS detail,
COALESCE((SELECT e.text FROM research.research_extracts e WHERE e.source_id=s.id AND e.kind='manual_partial_quote' ORDER BY e.ordinal LIMIT 1),'') AS quote
FROM research.research_citations c JOIN research.research_sources s ON s.id=c.source_id
JOIN research.research_works w ON w.id=c.work_id ORDER BY s.legacy_id,c.id;
