"""Repeatable final audit; outputs contain counts and public/mock geometry only."""
import csv,json,math,sqlite3,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import server,community
out=root/'artifacts/road-test-review';out.mkdir(parents=True,exist_ok=True)
commands=[([sys.executable,'selftest.py'],'legacy'),([sys.executable,'-m','unittest','test_community','test_road_review','-v'],'python-tests'),(['node','--test','tests/navigation.test.cjs'],'navigation-tests'),([sys.executable,'-m','py_compile','server.py','community.py','import_community.py','test_road_review.py'],'python-compile')]
for file in ['app/app.js','app/boot.js','app/sw.js','app/navigation-core.js','app/community-admin.js','app/admin.js','scripts/run-road-browser.cjs']:commands.append((['node','--check',file],'syntax-'+Path(file).stem))
tests=[]
for command,name in commands:
 start=time.perf_counter();run=subprocess.run(command,cwd=root,capture_output=True,text=True);(out/(name+'.log')).write_text(run.stdout+run.stderr,encoding='utf8');tests.append(dict(name=name,command=command,returncode=run.returncode,seconds=round(time.perf_counter()-start,3)))
(out/'tests-summary.json').write_text(json.dumps(tests,indent=2),encoding='utf8')
if any(test['returncode'] for test in tests):raise SystemExit('TEST FAILURE — inspect ignored local logs')
summary=community.summary(server,{});full=community.features(server,{})
visible={}
for f in full['features']:visible[f['properties']['kind']]=visible.get(f['properties']['kind'],0)+1
with community.transaction(server) as c:
 by_type={str(r[0]):r[1] for r in c.execute('SELECT original_type,count(*) FROM map_points WHERE source="community_speedcam" GROUP BY original_type')}
 invalid=c.execute('SELECT count(*) FROM map_points WHERE longitude IS NULL OR latitude IS NULL OR direction<0 OR direction>360 OR direction_type NOT IN (0,1,2)').fetchone()[0]
 radar_total=c.execute('select count(*) from radars').fetchone()[0];mapped=c.execute('select count(*) from radars where latitude is not null and longitude is not null').fetchone()[0]
 signals=c.execute("select count(*) from road_objects where object_type='traffic_signal' and latitude is not null and longitude is not null").fetchone()[0]
 preservation={};backup=out/'backups/before.db'
 if backup.exists():
  b=sqlite3.connect(backup);b.row_factory=sqlite3.Row
  for table in ['radars','road_objects']:
   missing=[];changed=[];refreshed=0;rows=b.execute('select * from '+table).fetchall()
   for old in rows:
    current=c.execute('select * from '+table+' where id=?',(old['id'],)).fetchone()
    if current is None:missing.append(old['id']);continue
    diff=[key for key in old.keys() if old[key]!=current[key]]
    if diff==['last_seen']:refreshed+=1
    elif diff:changed.append({'id':old['id'],'fields':diff})
   preservation[table]={'before':len(rows),'after':c.execute('select count(*) from '+table).fetchone()[0],'missing':missing,'content_changes':changed,'last_seen_refresh':refreshed}
  b.close()
first=community.import_file(server);second=community.import_file(server)
proof=dict(community_total=summary['total'],by_original_type=by_type,visible_map_by_kind=visible,trust=summary['trust'],municipalities=len(summary['by_municipality']),radar_inventory=radar_total,radars_with_coordinates=mapped,signals_with_coordinates=signals,invalid_stored_coordinates_or_direction=invalid,reimport_cached=bool(first.get('cached') and second.get('cached')),preservation=preservation)
(out/'data-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf8')
with (out/'municipalities.csv').open('w',encoding='utf-8-sig',newline='') as stream:
 writer=csv.writer(stream);writer.writerow(['municipality',*community.TYPES.values(),'total'])
 for city,counts in sorted(summary['by_municipality'].items()):writer.writerow([city,*[counts.get(k,0) for k in community.TYPES.values()],sum(counts.values())])
assert invalid==0 and first['imported']==8259 and all(not v['missing'] and not v['content_changes'] for v in preservation.values())
print(json.dumps({'tests_passed':len(tests),'data':proof},ensure_ascii=True))
