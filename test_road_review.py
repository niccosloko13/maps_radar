import json,tempfile,unittest,threading,urllib.request
from pathlib import Path
import server,community

class RoadReviewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=server.DATA_DIR,server.DB_PATH
  server.DATA_DIR=Path(self.temp.name);server.DB_PATH=server.DATA_DIR/'old.db'
  server.init_db();server.ensure_v18_tables()
 def tearDown(self):
  import gc
  server.DATA_DIR,server.DB_PATH=self.old;gc.collect();self.temp.cleanup()
 def test_public_bootstrap_and_repeat_preserve_official(self):
  community.init(server)
  snapshot=json.loads((server.ROOT/'data/geosampa_signals_snapshot.json').read_text(encoding='utf8'));lon,lat=snapshot['points'][0]
  with server.db() as c:
   server._upsert_road_object(c,dict(id='preserve-signal',external_id='manual-official',source='geosampa_signals',object_type='traffic_signal',name='Preserve official metadata',longitude=lon,latitude=lat,municipality='São Paulo',state='SP',official=1,status='active',confidence=99),server.now())
  first=community.bootstrap_public_data(server);second=community.bootstrap_public_data(server)
  self.assertEqual(first['official_signals_inserted'],len({tuple(round(v,7) for v in p) for p in snapshot['points']})-1);self.assertEqual(second['official_signals_inserted'],0)
  with server.db() as c:
   self.assertEqual(c.execute("select name from road_objects where id='preserve-signal'").fetchone()[0],'Preserve official metadata')
   self.assertEqual(c.execute('select count(*) from map_points').fetchone()[0],8259)
   rows=c.execute('select longitude,latitude,direction,direction_type,original_type from map_points').fetchall()
  geo=community.boundaries(str(server.ROOT))
  self.assertTrue(all(geo.city(r['longitude'],r['latitude']) for r in rows))
  self.assertTrue(all(r['direction_type'] in [0,1,2] and 0<=r['direction']<=360 and r['original_type'] in community.TYPES for r in rows))
 def test_old_schema_migration_and_cache_headers(self):
  community.init(server);community.init(server)
  http=server.ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(http.server_address[1])
  try:
   for path in ['/?v=215','/boot.js?v=215','/sw.js','/navigation-core.js?v=215']:
    response=urllib.request.urlopen(base+path);self.assertEqual(response.status,200);self.assertIn('no-cache',response.headers['Cache-Control'])
   for path in ['/api/radars','/api/road-objects','/api/map/features?bbox=-46.7,-23.7,-46.6,-23.5','/icons/signal.svg?v=215','/icons/user-chevron.svg?v=215']:
    self.assertEqual(urllib.request.urlopen(base+path).status,200)
  finally:http.shutdown();http.server_close();thread.join()

if __name__=='__main__':unittest.main(verbosity=2)
