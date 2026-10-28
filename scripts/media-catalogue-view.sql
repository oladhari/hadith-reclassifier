-- Expose only the curated public metadata projection. No private selection
-- reasons, archive captions, raw provenance or original payloads are accessible.
CREATE OR REPLACE VIEW research.website_catalogue AS
SELECT entry.key AS id,
(CASE WHEN d.decision='keep' AND NOT coalesce((entry.value->>'visible')::boolean,false)
 THEN c.metadata || jsonb_build_object('id',entry.key::integer)
 ELSE entry.value-'transcript' END)
 || CASE WHEN d.decision='hide' THEN jsonb_build_object('visible',false,'manual_video_hidden',true)
         WHEN d.decision='keep' THEN jsonb_build_object('visible',true) ELSE '{}'::jsonb END AS metadata
FROM research.research_catalogue_settings setting
CROSS JOIN LATERAL jsonb_each(setting.value::jsonb->'public') entry
LEFT JOIN research.video_review_catalogue c ON c.id=(entry.value->>'canonical_id')::integer
LEFT JOIN research.video_review_decisions d ON d.id=c.id
WHERE setting.key='media_catalogue';
GRANT SELECT ON research.website_catalogue TO othmani_website_reader;

CREATE OR REPLACE VIEW research.website_transcripts AS
WITH base AS MATERIALIZED (
 SELECT e.key AS id,e.value->>'transcript' AS text
 FROM research.research_catalogue_settings s,
 LATERAL jsonb_each(s.value::jsonb->'public') e
 WHERE s.key='media_catalogue' AND (e.value->>'visible')::boolean
 AND e.key=e.value->>'canonical_id' AND e.value ? 'transcript'
)
SELECT b.id,b.text FROM base b
LEFT JOIN research.video_review_decisions d ON d.id=b.id::integer
WHERE d.decision IS DISTINCT FROM 'hide'
UNION ALL
SELECT d.id::text,t.text FROM research.video_review_decisions d
JOIN research.research_media m ON m.legacy_id=d.id
JOIN LATERAL (SELECT e.text FROM research.research_extracts e WHERE e.media_id=m.id
 AND e.kind='speech_transcript' ORDER BY e.ordinal LIMIT 1) t ON true
WHERE d.decision='keep' AND NOT EXISTS(SELECT 1 FROM base b WHERE b.id=d.id::text);
GRANT SELECT ON research.website_transcripts TO othmani_website_reader;

CREATE OR REPLACE FUNCTION research.website_normalize(value text) RETURNS text
LANGUAGE sql IMMUTABLE STRICT AS $$
SELECT lower(translate(regexp_replace(value,'[ً-ٰٟـ]','','g'),'أإآٱى','ااااي'));
$$;
GRANT EXECUTE ON FUNCTION research.website_normalize(text) TO othmani_website_reader;
