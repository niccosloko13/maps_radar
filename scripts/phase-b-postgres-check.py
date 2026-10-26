"""Run only on the isolated phase-B Neon branch; no production URL accepted."""
import os
import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import db
from road_data import Service
from road_data import adapters as A

root=Path('artifacts/navigation-intelligence-v3-phase-b')
url=(root/'private/neon-url.txt').read_text(encoding='utf-8-sig').strip()
if 'ep-bitter-recipe-b45th2dz' not in url:raise RuntimeError('Refusing unexpected Neon endpoint')
os.environ['DATABASE_BACKEND']='postgres';os.environ['DATABASE_URL']=url
def connect():return db.Postgres(url)
def counts():
    import re
    from road_data.schema import STATEMENTS
    added={re.search(r'CREATE TABLE IF NOT EXISTS ([a-z_]+)',s)[1] for s in STATEMENTS if s.startswith('CREATE TABLE')}
    with connect() as c:
        names=[r[0] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")]
        return {n:c.execute('SELECT count(*) FROM '+n).fetchone()[0] for n in names if re.fullmatch('[a-z_]+',n) and n not in added}
before=counts();s=Service(connect);s.initialize();s.initialize()
row=A.make('prf-sp','TEST-PHASE-B','PRF_OPERATIONAL_UNIT','infrastructure',{'TEST':True},A.iso(),geometry={'type':'Point','coordinates':[-46.55,-23.7]})
s.persist('prf-sp',[row],A.iso(),replace=False);s.persist('prf-sp',[row],A.iso(),replace=False)
assert len(s.items('-46.56,-23.71,-46.54,-23.69'))==1
with connect() as c:
    c.execute("UPDATE road_event SET description='TEST rollback' WHERE external_id='TEST-PHASE-B'");c.rollback()
    assert c.execute("SELECT description FROM road_event WHERE external_id='TEST-PHASE-B'").fetchone()[0] is None
    c.execute("UPDATE road_event SET description='TEST update' WHERE external_id='TEST-PHASE-B'")
with connect() as c:
    assert c.execute("SELECT count(*) FROM road_event WHERE external_id='TEST-PHASE-B'").fetchone()[0]==1
    c.execute("DELETE FROM event_evidence WHERE external_id='TEST-PHASE-B'");c.execute("DELETE FROM road_event WHERE external_id='TEST-PHASE-B'")
after=counts();unchanged={n:after[n]==v for n,v in before.items()};assert all(unchanged.values())
result={'branch':'relas-phase-b-validation','branch_id':'br-royal-waterfall-b4fwbd1n','expires_at':'2026-10-29T23:59:59Z','production_modified':False,'legacy_counts_before':before,'legacy_counts_after':{n:after[n] for n in before},'legacy_unchanged':all(unchanged.values()),'checks':['explicit additive migration twice','insert','upsert idempotent','viewport filter','update','transaction rollback','controlled delete','reconnect persistence'],'source_health_count':len(s.health()),'status':'PASS'}
(root/'postgres-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: isolated Neon migration, CRUD, rollback, upsert, reconnect; legacy counts unchanged')
