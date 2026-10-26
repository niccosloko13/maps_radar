"""Read-only deployed HTTP smoke; Vercel CLI handles protected URL access."""
import json,subprocess,sys,concurrent.futures,os
from pathlib import Path
A=Path('artifacts/navigation-intelligence-v3-phase-b2');url=sys.argv[1];label=sys.argv[2]
cached=Path(os.environ['LOCALAPPDATA'])/'npm-cache/_npx'
manifest=next(p for p in cached.glob('*/node_modules/vercel/package.json') if json.loads(p.read_text(encoding='utf-8'))['version']=='65.1.0')
cli=manifest.parent/'dist/vc.js'
assert url.startswith('https://mapsradar-') and url.endswith('.vercel.app')
route=json.loads((A/'private/real-route.json').read_text())
payload=A/'private/release-route-body.json';payload.write_text(json.dumps({'coordinates':route['geometry']['coordinates'],'along':0,'mode':'ROAD_MODE','speed':20}),encoding='utf-8')
checks=[('health','/api/health',200),('map','/',200),('admin','/admin',200),('boot','/boot.js?v=233',200),('phase-b','/navigation/phase-b.js?v=233',200),('radars','/api/radars',200),('road-objects','/api/road-objects',200),('map-features','/api/map/features?bbox=-46.5,-24,-46.3,-23.85&zoom=14',200),('source-health','/api/source-health',200),('aux-infra','/api/road-infrastructure?bbox=-53.2,-25.4,-44,-19.7&zoom=12',200),('weather','/api/weather?bbox=-53.2,-25.4,-44,-19.7',200),('admin-guard','/api/admin/layer-diagnostics',401),('route-corridor','/api/road-events/route',200)]
# The existing endpoint defaults to mapped-only, not all inventory records.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import db
with db.Postgres((A/'private/release-production-url.txt').read_text(encoding='utf-8-sig').strip()) as c:
 c.execute('SET TRANSACTION READ ONLY')
 mapped_objects=c.execute("SELECT count(*) FROM road_objects WHERE state='SP' AND latitude IS NOT NULL AND longitude IS NOT NULL").fetchone()[0]
def run(check):
 name,path,expected=check;out=A/('private/'+label+'-'+name+'.json')
 # Direct node avoids cmd.exe treating URL ampersands as shell operators.
 cmd=['node',str(cli),'curl',path,'--deployment',url,'--','--silent','--show-error','--max-time','90','--output',str(out),'--write-out','%{http_code}']
 if name=='route-corridor':cmd+=['--request','POST','--header','Content-Type: application/json','--data-binary','@'+str(payload)]
 p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=110)
 code=p.stdout.strip();result={'name':name,'path':path,'http':code,'expected':expected,'pass':p.returncode==0 and code==str(expected)}
 if out.exists():
  body=out.read_text(encoding='utf-8',errors='replace')
  if name=='map':result['asset233']='v=233' in body;result['pass']&=result['asset233']
  if name in ('health','radars','road-objects','map-features','source-health','aux-infra','weather','route-corridor'):
   try:j=json.loads(body)
   except ValueError:result['pass']=False;result['error']='NON_JSON_RESPONSE';return result
   if name=='health':result['health']=j;result['pass']&=j.get('ok') and j.get('engine')=='postgres'
   elif name=='source-health':result['sources']=j.get('items');result['pass']&=len(j.get('items',[]))==9
   elif name=='route-corridor':
    result['items']=[{k:r.get(k) for k in ('event_id','source_id','event_type','road','direction','navigation_eligible','distance_from_route_m')} for r in j.get('items',[])];result['counts']=j.get('counts');result['pass']&=any(r['event_id']=='official-support:4169' and r['navigation_eligible'] for r in result['items'])
   else:
    result['count']=len(j.get('items',j.get('features',[])))
    if name=='aux-infra':result['by_source']={sid:sum(f['properties']['source_id']==sid for f in j['features']) for sid in ('antt-tolls','prf-sp','artesp-tolls','official-support')};result['pass']&=result['count']==516
    if name=='radars':result['pass']&=result['count']==196
    if name=='road-objects':result['expected_mapped_objects']=mapped_objects;result['pass']&=result['count']==mapped_objects
    if name=='weather':result['pass']&=result['count']==0
 return result
only=sys.argv[3] if len(sys.argv)>3 else None
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,[c for c in checks if not only or c[0]==only]))
if only:
 prior=json.loads((A/(label+'-http-verification.json')).read_text(encoding='utf-8'))
 results=[next((new for new in results if new['name']==old['name']),old) for old in prior['checks']]
report={'deployment':url,'label':label,'app_commit':'ee5506c','checks':results,'passed':sum(bool(r['pass']) for r in results),'total':len(results)}
(A/(label+'-http-verification.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'total':report['total'],'failures':[r['name'] for r in results if not r['pass']]}))
sys.exit(0 if all(r['pass'] for r in results) else 1)
