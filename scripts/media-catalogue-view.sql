-- Expose only the curated public metadata projection. No private selection
-- reasons, archive captions, raw provenance or original payloads are accessible.
CREATE OR REPLACE VIEW research.website_catalogue AS
SELECT entry.key AS id,(entry.value - 'transcript') AS metadata
FROM research.research_catalogue_settings setting,
LATERAL jsonb_each(setting.value::jsonb->'public') entry
WHERE setting.key='media_catalogue';
GRANT SELECT ON research.website_catalogue TO othmani_website_reader;

CREATE OR REPLACE VIEW research.website_transcripts AS
SELECT entry.key AS id,entry.value->>'transcript' AS text
FROM research.research_catalogue_settings setting,
LATERAL jsonb_each(setting.value::jsonb->'public') entry
WHERE setting.key='media_catalogue' AND (entry.value->>'visible')::boolean
AND entry.key=entry.value->>'canonical_id' AND entry.value ? 'transcript';
GRANT SELECT ON research.website_transcripts TO othmani_website_reader;

CREATE OR REPLACE FUNCTION research.website_normalize(value text) RETURNS text
LANGUAGE sql IMMUTABLE STRICT AS $$
SELECT lower(translate(regexp_replace(value,'[ً-ٰٟـ]','','g'),'أإآٱى','ااااي'));
$$;
GRANT EXECUTE ON FUNCTION research.website_normalize(text) TO othmani_website_reader;
