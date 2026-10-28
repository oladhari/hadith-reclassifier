-- Private manual website visibility decisions. Original media and research rows stay intact.
CREATE TABLE IF NOT EXISTS research.video_review_catalogue (
 id integer PRIMARY KEY, metadata jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS research.video_review_decisions (
 id integer PRIMARY KEY REFERENCES research.video_review_catalogue(id),
 decision text NOT NULL CHECK (decision IN ('pending','keep','hide')),
 platform text NOT NULL CHECK (platform IN ('unknown','tiktok','youtube','other')),
 note text NOT NULL DEFAULT '' CHECK(length(note)<=1000), revision integer NOT NULL,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS research.video_review_history (
 event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 id integer NOT NULL REFERENCES research.video_review_catalogue(id),
 previous jsonb, current jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO research.video_review_catalogue(id,metadata)
SELECT e.key::integer,e.value-'transcript'
FROM research.research_catalogue_settings s,
LATERAL jsonb_each(s.value::jsonb->'public') e
JOIN research.research_media m ON m.legacy_id=e.key::integer AND m.kind='video'
WHERE s.key='media_catalogue' AND (e.value->>'visible')::boolean
AND e.key=e.value->>'canonical_id'
ON CONFLICT(id) DO NOTHING;

CREATE OR REPLACE VIEW research.video_review_items AS
SELECT c.id,c.metadata->>'title' AS title,c.metadata->>'description' AS description,
(c.metadata->>'duration')::numeric AS duration,m.source_date AS date,o.byte_size AS size,
coalesce(d.decision,'pending') AS decision,coalesce(d.platform,'unknown') AS platform,
coalesce(d.note,'') AS note,coalesce(d.revision,0) AS revision,d.updated_at,
coalesce(d.decision,'pending')<>'hide' AND (coalesce(d.decision,'pending')='keep' OR coalesce((e.value->>'visible')::boolean,false)) AS visible
FROM research.video_review_catalogue c
JOIN research.research_media m ON m.legacy_id=c.id AND m.kind='video'
JOIN research.research_objects o ON o.id=m.object_id
LEFT JOIN research.video_review_decisions d ON d.id=c.id
LEFT JOIN research.research_catalogue_settings s ON s.key='media_catalogue'
LEFT JOIN LATERAL (SELECT s.value::jsonb->'public'->c.id::text AS value) e ON true;

CREATE OR REPLACE FUNCTION research.set_video_review(p_id integer,p_decision text,p_platform text,p_note text,p_revision integer)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE oldrow research.video_review_decisions; newrow research.video_review_decisions;
BEGIN
 IF p_decision NOT IN ('pending','keep','hide') OR p_platform NOT IN ('unknown','tiktok','youtube','other') OR length(p_note)>1000 OR p_note IS NULL THEN
  RAISE EXCEPTION 'Invalid video review' USING ERRCODE='22023';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM research.video_review_catalogue WHERE id=p_id) THEN
  RAISE EXCEPTION 'Video not reviewable' USING ERRCODE='22023';
 END IF;
 PERFORM pg_advisory_xact_lock(742001,p_id);
 SELECT * INTO oldrow FROM research.video_review_decisions WHERE id=p_id;
 IF coalesce(oldrow.revision,0)<>p_revision THEN
  RAISE EXCEPTION 'Review changed; reload' USING ERRCODE='40001';
 END IF;
 INSERT INTO research.video_review_decisions(id,decision,platform,note,revision)
 VALUES(p_id,p_decision,p_platform,p_note,p_revision+1)
 ON CONFLICT(id) DO UPDATE SET decision=excluded.decision,platform=excluded.platform,
 note=excluded.note,revision=excluded.revision,updated_at=now() RETURNING * INTO newrow;
 INSERT INTO research.video_review_history(id,previous,current) VALUES(p_id,to_jsonb(oldrow),to_jsonb(newrow));
 RETURN to_jsonb(newrow);
END $$;
REVOKE ALL ON FUNCTION research.set_video_review(integer,text,text,text,integer) FROM PUBLIC;
GRANT USAGE ON SCHEMA research TO othmani_video_reviewer;
GRANT SELECT ON research.video_review_items,research.video_review_history TO othmani_video_reviewer;
GRANT EXECUTE ON FUNCTION research.set_video_review(integer,text,text,text,integer) TO othmani_video_reviewer;
REVOKE ALL ON research.video_review_catalogue,research.video_review_decisions,research.video_review_history FROM othmani_website_reader;
