"""Explain actual route eligibility, including zeros; no thresholds are changed."""
import os,sys,json,copy,time
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ.update(DATABASE_BACKEND='sqlite',RELAS_ENV='development',VERCEL='0')
import db
from road_data import Service
from road_data.geometry import project,vertices,corridor,distance
from road_data.adapters import iso
A=Path('artifacts/navigation-intelligence-v3-phase-b2');s=Service(lambda:db.connect(A/'private/validation.sqlite'))
route=json.loads((A/'private/real-route.json').read_text());coords=route['geometry']['coordinates'];rows=s.items(include_inactive=True,limit=10000);health=s.health()
segments=[];along=0
for a,b in zip(coords,coords[1:]):segments.append((a,b,along));along+=distance(a,b)
by_source=[];nearest={}
for h in health:
 sid=h['source_id'];group=[r for r in rows if r['source_id']==sid];approved=[r for r in group if r['geometry'] and (r['record_class']!='infrastructure' or r.get('approval_status')=='APPROVED')];map_rows=[r for r in group if r['map_eligible']]
 # No-direction diagnostic is a counterfactual EXPLANATION, never returned as eligible data.
 geom=corridor([dict(r,direction='') for r in map_rows],coords,0,'ROAD_MODE',0)
 direction=corridor(map_rows,coords,0,'ROAD_MODE',0);window=corridor(map_rows,coords,0,'ROAD_MODE',20)
 current=corridor([r for r in approved if r.get('observation_freshness',{}).get('current')],coords,0,'ROAD_MODE',0)
 minimum=None
 for r in approved:
  for p in vertices(r['geometry']):
   for a,b,start in segments:
    d,t=project(p,a,b)
    if minimum is None or d<minimum['distance_m']:minimum={'event_id':r['event_id'],'distance_m':round(d,2),'along_m':round(start+t*distance(a,b),2),'direction':r.get('direction')}
 if h['status']=='AUTH_REQUIRED':reason='NO_SOURCE_COVERAGE: AUTH_REQUIRED'
 elif h['status']=='BLOCKED_LICENSE':reason='LICENSE_BLOCK'+('; NO_SOURCE_COVERAGE' if not group else '')
 elif not group:reason='NO_SOURCE_COVERAGE'
 elif not geom and minimum and minimum['distance_m']>1000:reason='NO_SOURCE_COVERAGE: approved inventory geographically outside this route'
 elif not geom:reason='DISTANCE_BUFFER: no approved point within unchanged corridor' if minimum and minimum['distance_m']>35 else 'FRESHNESS_FILTER / KM_TO_COORDINATE_ERROR'
 elif not direction:reason='DIRECTION_FILTER'
 elif not window:reason='DISTANCE_BUFFER: outside initial speed-based ahead window'
 else:reason=None
 by_source.append({'source':sid,'status':h['status'],'records_statewide':len(group),'records_spatially_eligible':len(approved),'records_map_eligible':len(map_rows),'records_intersecting_corridor':len(geom),'records_direction_eligible':len(direction),'records_initial_window':len(window),'current_observations_in_corridor':len(current),'records_rendered':'BROWSER_MEASURED_SEPARATELY','records_alerted':0,'reason_for_zero':reason,'nearest_approved_or_raw_geometry':minimum})
output={'captured_at':iso(),'route_distance_m':route['distance_m'],'route_vertices':len(coords),'route_provider':route.get('provider'),'rows':by_source,'initial_route_result':s.route(coords,0,'ROAD_MODE',20),'radar_P0_unchanged':True,'counterfactual_direction_removed_is_diagnostics_only':True}
(A/'route-coverage.json').write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding='utf-8')
# Review original seven coordinate conflicts individually; do not silently merge entities.
old=json.loads(Path('artifacts/navigation-intelligence-v3-phase-b1/antt-coordinate-review.json').read_text(encoding='utf-8'));payload={r['event_id']:r['payload_json'] for r in rows if r['source_id']=='antt-tolls'};groups=defaultdict(list)
for r in rows:
 if r['source_id']=='antt-tolls':groups[(r['road'],r['km_start'],r['lat'],r['lon'])].append(r)
classification=[]
for r in old:
 if r['status']=='APPROVED':continue
 p=payload[r['event_id']];members=groups[(r['road'],r['km'],r['lat'],r['lon'])]
 cls='FREE_FLOW_MULTI_PORTAL' if 'free flow' in (r['name'] or '').lower() and len(members)>1 else 'SAME_SITE_DIFFERENT_DIRECTION' if len({m['direction'] for m in members})>1 else 'SAME_SITE_DIFFERENT_STRUCTURE' if len(members)>1 else 'CONFLICT_UNRESOLVED'
 classification.append(dict(r,classification=cls,direction=p.get('sentido'),concessionaire=p.get('concessionaria'),track=p.get('tipo_de_pista'),source_status=p.get('situacao'),spatial_resolution='CONFLICT_UNRESOLVED',evidence='https://dados.antt.gov.br/dataset/praca-de-pedagio',reason='Source names/directions preserved. Municipality polygon mismatch remains; official location text alone cannot correct coordinates.'))
(A/'antt-conflicts.json').write_text(json.dumps(classification,indent=2,ensure_ascii=False),encoding='utf-8')
stations=[r for r in rows if r['source_id']=='sp-aguas'];(A/'freshness-results.json').write_text(json.dumps({'captured_at':iso(),'sources':health,'sibh_states':dict(Counter(r['freshness'] for r in stations)),'sibh_current':sum(r['observation_freshness']['current'] for r in stations),'sibh_inventory':len(stations)},indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps([{k:r[k] for k in ['source','records_map_eligible','records_intersecting_corridor','records_direction_eligible','records_initial_window','reason_for_zero']} for r in by_source]))
