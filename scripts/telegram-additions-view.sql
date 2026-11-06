-- Expose only OCR for visible canonical documents. Source commentary/provenance stays private.
CREATE OR REPLACE VIEW research.website_document_texts AS
SELECT e.key AS id,e.value->>'text' AS text
FROM research.research_catalogue_settings s
CROSS JOIN LATERAL jsonb_each(s.value::jsonb->'documents') e
JOIN research.website_catalogue c ON c.id=e.key
WHERE s.key='telegram_additions' AND (c.metadata->>'visible')::boolean
AND (c.metadata->>'canonical_id')=e.key;
GRANT SELECT ON research.website_document_texts TO othmani_website_reader;
