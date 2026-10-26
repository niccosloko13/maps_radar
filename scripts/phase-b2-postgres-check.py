"""One final compatibility check on the explicitly isolated B.1 Neon branch."""
import sys,os,json,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import db
from road_data import Service
from road_data.schema import STATEMENTS
from road_data.adapters import make,iso
root=Path('artifacts/navigation-intelligence-v3-phase-b2');url=(root/'private/neon-url.txt').read_text(encoding='utf-8-sig').strip()
if 'ep-square-fog-b48vnmfc' not in url:raise RuntimeError('Unexpected endpoint; refusing mutation')
os.environ['DATABASE_BACKEND']='postgres';os.environ['DATABASE_URL']=url
connect=lambda:db.Postgres(url)
added={re.search(r'CREATE TABLE IF NOT EXISTS ([a-z_]+)',s)[1] for s in STATEMENTS if s.startswith('CREATE TABLE')}
def counts():
    with connect() as c:
        names=[r[0] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")]
        return {n:c.execute('SELECT count(*) FROM '+n).fetchone()[0] for n in names if re.fullmatch('[a-z_]+',n) and n not in added}
before=counts();s=Service(connect);s.initialize();s.initialize()
row=make('prf-sp','B2-TEST-ONLY','PRF_OPERATIONAL_UNIT','infrastructure',{'TEST':True},iso())
s.persist('prf-sp',[row],iso(),replace=False)
with connect() as c:
    c.execute('INSERT INTO road_source_reviews(source_id,license,terms_url,license_verified,endpoint_verified,reviewed_at) VALUES(?,?,?,?,?,?)',('prf-sp','TEST ONLY','https://example.invalid/TEST',1,1,iso()))
    c.execute('INSERT INTO road_location_reviews(event_id,lon,lat,coordinate_quality,confidence,coordinate_source,approval_status,evidence_json,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?)',(row['event_id'],-46.55,-23.7,'OFFICIAL_COORDINATE',.95,'TEST ONLY','APPROVED','{}',iso()))
assert len(s.features('-46.56,-23.71,-46.54,-23.69')['features'])==1
with connect() as c:
    c.execute("UPDATE road_location_reviews SET approval_status='BLOCKED' WHERE event_id=?",(row['event_id'],));c.rollback()
assert s.health();assert s.diagnostics()['counts'][0]['eligible_map']==1
with connect() as c:
    c.execute('DELETE FROM road_location_reviews WHERE event_id=?',(row['event_id'],));c.execute('DELETE FROM event_evidence WHERE event_id=?',(row['event_id'],));c.execute('DELETE FROM road_event WHERE event_id=?',(row['event_id'],));c.execute("DELETE FROM road_source_reviews WHERE source_id='prf-sp'")

# Explicitly isolated synthetic asset exercises the new persisted approval path.
from road_data.artesp_assets import normalize
raw={'ID':'B2-TEST-ASSET','Desc_Componente':'Base Operacional - SAU','Rodovia':'SP160','Localizacao':'km 010+000','Sentido':'Norte','Latitude':'-23.8','Longitude':'-46.7','Municipio':'TEST CITY','Cod_Status':'Ativo','Nome_Concessionaria':'TEST ONLY'}
asset=normalize([raw],'official-support',iso(),municipality_at=lambda *p:'TEST CITY')[0]
s.persist('official-support',[asset],iso(),replace=False)
with connect() as c:
 c.execute('INSERT INTO road_source_reviews(source_id,license,terms_url,license_verified,endpoint_verified,reviewed_at) VALUES(?,?,?,?,?,?)',('official-support','TEST ONLY','https://example.invalid/TEST',1,1,iso()))
assert len(s.features('-46.71,-23.81,-46.69,-23.79')['features'])==1
with connect() as c:
 c.execute('DELETE FROM road_location_reviews WHERE event_id=?',(asset['event_id'],));c.execute('DELETE FROM event_evidence WHERE event_id=?',(asset['event_id'],));c.execute('DELETE FROM road_event WHERE event_id=?',(asset['event_id'],));c.execute("DELETE FROM road_source_reviews WHERE source_id='official-support'")

after=counts();assert before==after
result={'status':'PASS','branch':'relas-phase-b1-validation','branch_id':'br-green-frost-b4ubujn6','production_modified':False,'readiness_evidence':False,'fixture_scope':'isolated database syntax/rollback test ONLY; not map readiness','checks':['additive migration twice','Postgres COALESCE viewport join','coordinate approval overlay','license policy query','diagnostics counts','rollback','controlled test cleanup'],'legacy_counts_before':before,'legacy_counts_after':after,'legacy_unchanged':True}
(root/'postgres-tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS: isolated PostgreSQL compatibility, legacy counts unchanged')
