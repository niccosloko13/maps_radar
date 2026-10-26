"""Apply documented official evidence ONLY to the B.2 clone."""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.update(DATABASE_BACKEND='sqlite',RELAS_ENV='development',VERCEL='0')
import db
from road_data import Service
from road_data.adapters import iso
from road_data.registry import BY_ID
A=Path('artifacts/navigation-intelligence-v3-phase-b2');s=Service(lambda:db.connect(A/'private/validation.sqlite'));s.initialize()
pdf='https://www.gov.br/antt/pt-br/assuntos/rodovias/concessionarias/lista-de-concessoes/autopista-regis-bittencourt/relatorios/relatorios-de-monitoracao/2024/rt_06_116_sp_275_4_k12_517.pdf'
old=json.loads(Path('artifacts/navigation-intelligence-v3-phase-b1/prf-coordinate-review.json').read_text(encoding='utf-8'));review=[]
with s.connect() as c:
 for r in old:
  if r['status']=='APPROVED':continue
  v=dict(record=r['name'],event_id=r['event_id'],previous_status=r['coordinate_quality'],new_status=r['coordinate_quality'],road=r['road'],km=r['km'],municipality=r['municipality'],lat=None,lon=None,evidence='PRF directory / ANTT PRF inventory / local municipality polygons',reason=r['notes'])
  if r['event_id'] in ('prf-sp:74c68daaa9c6b47cef89','prf-sp:ab38c25cc750a0811678'):
   candidate=r['official_candidate'];assert candidate['km_m'] in ('525.7','387.5')
   # Exact official engineering table corroborates ANTT's precise km; no wider threshold.
   e=dict(r,published_name=candidate['nome_do_prf'],published_km=float(candidate['km_m']),published_direction='NORTE',evidence_url=pdf,evidence_pages='11-12',resolution='Independent ANTT monitoring table matches exact BR/km/direction/municipality; directory km is coarse/conflicting; original retained')
   c.execute('UPDATE road_location_reviews SET lon=?,lat=?,coordinate_quality=?,confidence=?,approval_status=?,evidence_json=?,reviewed_at=? WHERE event_id=?',(float(candidate['longitude']),float(candidate['latitude']),'OFFICIAL_COORDINATE',.97,'APPROVED',json.dumps(e,ensure_ascii=False),iso(),r['event_id']))
   v.update(new_status='OFFICIAL_COORDINATE',km=e['published_km'],lat=float(candidate['latitude']),lon=float(candidate['longitude']),evidence=pdf,reason=e['resolution'])
  elif r['coordinate_quality']=='UNRESOLVED':v['reason']='Official textual address only; no calibrated official spatial evidence. Administrative location must not inherit operational-post coordinates.'
  review.append(v)
 for sid in ('artesp-tolls','official-support'):
  d=BY_ID[sid]
  c.execute('UPDATE road_data_sources SET base_url=?,authority=?,attribution=? WHERE source_id=?',(d['base_url'],d['authority'],d['attribution'],sid))
  c.execute('UPDATE road_source_reviews SET license=?,terms_url=?,license_verified=1,endpoint_verified=1,commercial_restrictions=?,attribution_required=1,last_terms_check=?,next_action=?,reviewed_at=? WHERE source_id=?',('CC BY (catalog version unspecified)','https://dadosabertos.artesp.sp.gov.br/dataset/cadastro-de-ativos','ARTESP attribution, integrity, no endorsement; static inventory not live operation status',iso(),'Daily backend cache; preserve snapshot and review coordinate conflicts',iso(),sid))
(A/'prf-resolution.json').write_text(json.dumps(review,indent=2,ensure_ascii=False),encoding='utf-8')
print('PRF official evidence resolves 2 conflicts; original source facts retained. Two existing ARTESP asset contracts reviewed.')
