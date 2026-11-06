-- Read only unverified OCR for visible canonical documents, without expanding catalogue JSON.
CREATE OR REPLACE VIEW research.website_document_texts AS
SELECT e.id,e.text FROM research.research_public_document_entries e
JOIN research.website_catalogue c ON c.id=e.id
WHERE (c.metadata->>'visible')::boolean AND (c.metadata->>'canonical_id')=e.id;
GRANT SELECT ON research.website_document_texts TO othmani_website_reader;
