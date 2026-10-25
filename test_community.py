import unittest,tempfile,json,sqlite3,shutil
from pathlib import Path
import server,community
class CommunityTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.old=(server.DB_PATH,server.DATA_DIR);server.DATA_DIR=Path(self.temp.name);server.DB_PATH=server.DATA_DIR/'test.db';server.init_db();community.init(server)
 def tearDown(self):server.DB_PATH,server.DATA_DIR=self.old;self.temp.cleanup()
 def test_polygon_and_holes(self):
  geo=community.Municipalities(server.ROOT);self.assertEqual(geo.city(-46.633,-23.55),'São Paulo');self.assertIsNone(geo.city(-43.2,-22.9));self.assertFalse(geo.ring(2,2,[[0,0],[1,0],[1,1],[0,1]]))
 def test_import_and_replay(self):
  p=Path(self.temp.name)/'fixture.txt';p.write_text('X,Y,TYPE,SPEED,DirType,Direction\n-46.633,-23.55,1,60,1,90\n-46.633,-23.55,1,60,1,90\n-43.2,-22.9,1,60,0,0\nNaN,-23,1,50,1,0\n-46,-23,99,60,0,0\n',encoding='utf8');r=community.import_file(server,p);self.assertEqual(r['imported'],1);self.assertEqual(r['duplicates'],1);self.assertEqual(r['outside_sp'],1);self.assertEqual(r['invalid'],2);self.assertTrue(community.import_file(server,p)['cached']);self.assertEqual(community.summary(server,{})['total'],1)
  p.write_text('bad\n');self.assertRaises(ValueError,community.import_file,server,p)
 def test_reconcile_and_official_preserved(self):
  from selftest import mkitem
  with server.db() as c:server.upsert(c,mkitem('official',-46.633,-23.55,'Leste'),server.now())
  p=Path(self.temp.name)/'fixture.txt';p.write_text('X,Y,TYPE,SPEED,DirType,Direction\n-46.633,-23.55,1,60,1,90\n-46.6331,-23.55,1,50,1,90\n',encoding='utf8');r=community.import_file(server,p);self.assertEqual(r['reconciled'],1);self.assertEqual(r['conflicts'],1)
  with server.db() as c:self.assertEqual(c.execute('select speed_limit from radars where id="official"').fetchone()[0],60)
  fc=community.features(server,{});self.assertEqual(len(fc['features']),2)
 def test_direction_and_route_corridor(self):
  for dt in [0,None]:self.assertTrue(community.direction_matches({'direction_type':dt,'direction':270},90))
  self.assertFalse(community.direction_matches({'direction_type':1,'direction':270},90));self.assertTrue(community.direction_matches({'direction_type':2,'direction':270},90))
  with server.db() as c:
   for rid,y,d in [('east',-23.55,90),('west',-23.55,270),('parallel',-23.551,90)]:c.execute('INSERT INTO map_points(id,longitude,latitude,kind,direction,direction_type,trust) VALUES(?,?,?,?,?,?,?)',(rid,-46.633,y,'fixed',d,1,'community'))
  alerts=community.route_points(server,[[-46.64,-23.55],[-46.62,-23.55]]);self.assertEqual([x['id'] for x in alerts],['east'])
 def test_migration_repeat_and_bbox(self):
  community.init(server);community.init(server)
  self.assertRaises(ValueError,community.features,server,{'bbox':['nan,1,2,3']})
  with server.db() as c:self.assertIn('radars',{x[0] for x in c.execute('select name from sqlite_master')})
 def test_bulk_does_not_promote_source(self):
  with server.db() as c:c.execute("INSERT INTO map_points(id,longitude,latitude,kind,source_type,trust,hidden) VALUES('x',-46,-23,'fixed','community','community',1)")
  community.post(server,None,'/api/admin/community/bulk',{'ids':['x'],'action':'approve'})
  with server.db() as c:r=c.execute('select * from map_points').fetchone();self.assertEqual(r['hidden'],0);self.assertEqual(r['source_type'],'community');self.assertEqual(r['trust'],'community')
 def test_public_report_and_feedback(self):
  handler=type('Handler',(),{'client_address':('127.0.0.1',1000)})()
  payload={'kind':'accident','longitude':-46.633,'latitude':-23.55}
  first=community.post(server,handler,'/api/map/report',payload);again=community.post(server,handler,'/api/map/report',payload);self.assertEqual(first['id'],again['id'])
  community.post(server,handler,'/api/map/feedback',{'id':first['id'],'action':'confirm'})
  with server.db() as c:
   r=c.execute('select * from map_points').fetchone();self.assertEqual(r['source_type'],'recent');self.assertEqual(r['report_kind'],'accident');self.assertEqual(c.execute('select count(*) from map_feedback').fetchone()[0],1)
   c.execute('update map_points set expires_at=0')
  fc=community.features(server,{});self.assertEqual(fc['features'],[]);self.assertIn(first['id'],fc['removed_ids'])
 def test_http_auth_and_validation(self):
  import threading,urllib.request,urllib.error
  http=server.ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(http.server_address[1])
  try:
   with self.assertRaises(urllib.error.HTTPError) as denied:urllib.request.urlopen(base+'/api/admin/community')
   self.assertEqual(denied.exception.code,401)
   password=__import__('os').environ.get('RELAS_ADMIN_PASSWORD') or server.AUTH.local_value('admin_password.txt',lambda:'test-only-password')
   req=urllib.request.Request(base+'/api/admin/login',data=json.dumps({'username':'admin','password':password}).encode(),headers={'Content-Type':'application/json'})
   login=json.load(urllib.request.urlopen(req));token=login['token']
   req=urllib.request.Request(base+'/api/admin/community',headers={'Authorization':'Bearer '+token});self.assertEqual(json.load(urllib.request.urlopen(req))['total'],0)
   with self.assertRaises(urllib.error.HTTPError) as bad:urllib.request.urlopen(base+'/api/map/features?bbox=nan,1,2,3')
   self.assertEqual(bad.exception.code,400)
  finally:http.shutdown();http.server_close();thread.join()

if __name__=='__main__':unittest.main(verbosity=2)
