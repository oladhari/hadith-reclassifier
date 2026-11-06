"""Check canonical routing, source preservation and publication boundaries locally."""
import json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/research/imports/muawiya4n'
plan=json.loads((OUT/'publication-plan.json').read_text());catalogue=json.loads((ROOT/'frontend/src/content/media-catalogue.json').read_text())
stage=sqlite3.connect(OUT/'filter.sqlite3');local=sqlite3.connect(ROOT/'data/research/research.sqlite3')
assert stage.execute('select count(*) from explanation_links').fetchone()[0]==1798
assert local.execute('select count(*) from research_sources where legacy_id between 1000000 and 1999999').fetchone()[0]==1686
assert local.execute('select count(*) from research_media where legacy_id between 1000000 and 1999999').fetchone()[0]==1428
assert local.execute("select count(*) from research_provenance where external_id like 'muawiya4n:%' and length(trim(original_text))>0").fetchone()[0]==834
assert not local.execute('pragma foreign_key_check').fetchall()
for b in plan['bundles']:
 assert b['explanation'] and b['items']
 for id in b['items']:
  assert catalogue[str(id)]['visible'] and catalogue[str(id)]['canonical_id']==id
for id,entry in plan['public'].items():
 assert str(entry['canonical_id']) in catalogue
 for field in ['original_text','original_payload','contexts','source_message_ids','selection_reason']:assert field not in entry
 if entry.get('explanations'):
  assert entry['visible']
  for paragraph in entry['explanations']:assert paragraph['kind']=='source_commentary_paraphrase'
for id in plan['documents']:assert catalogue[id]['visible'] and catalogue[id]['canonical_id']==int(id)
# Protection from accidental publication of new recordings and rejected existing videos.
archive={r['id']:r for r in plan['archive']}
for id,row in plan['public'].items():
 if int(id)>=1000000 and row['canonical_id']>=1000000 and archive[int(id)]['kind'] in ['audio','video']:assert not row['visible']
print(json.dumps({'source_posts':1686,'comment_posts_preserved':834,'attachments':1428,'explanation_links':1798,'theme_bundles':len(plan['bundles']),'integrity':'ok'}))
