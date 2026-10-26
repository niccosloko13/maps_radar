"""One real collection; no fixtures, no production writes."""
import os,sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.update(DATABASE_BACKEND='sqlite',RELAS_ENV='development',VERCEL='0')
import db
from road_data import Service
from road_data.readiness import station_freshness
from collections import Counter
root=Path('artifacts/navigation-intelligence-v3-phase-b1')
s=Service(lambda:db.connect(root/'private/validation.sqlite'))
results={sid:s.sync(sid) for sid in ['artesp-occurrences','artesp-interventions','sp-aguas']}
rows=s.items(include_inactive=True,limit=10000)
stations=[r for r in rows if r['source_id']=='sp-aguas']
current=[r for r in stations if r['observation_freshness']['current']]
result={'collected_at':time.time(),'sync':results,'source_health':s.health(),'diagnostics':s.diagnostics(),
 'counts':dict(Counter(r['source_id'] for r in rows)),
 'sibh':{'inventory':len(stations),'current':len(current),'states':dict(Counter(r['freshness'] for r in stations)),
 'reasons':dict(Counter(r['observation_freshness']['reason'] for r in stations)),
 'cadences_seconds':dict(Counter(str(r['observation_freshness'].get('cadence_seconds')) for r in stations)),
 'eligible_map':sum(r['map_eligible'] for r in stations)},
 'public_features':len(s.features('-53.2,-25.4,-44,-19.7')['features'])}
(root/'real-data-results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'sync':results,'sibh':result['sibh'],'statuses':dict(Counter(r['status'] for r in result['source_health']))}))
