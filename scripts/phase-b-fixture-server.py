"""Explicit isolated TEST server. Never writes personal SQLite or Neon."""
import os
import sys
import sqlite3
from pathlib import Path
if os.environ.get('RELAS_ENABLE_TEST_FIXTURES')!='1':raise RuntimeError('Set RELAS_ENABLE_TEST_FIXTURES=1 explicitly for isolated tests')
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
os.environ.update(DATABASE_BACKEND='sqlite',RELAS_ENV='development',VERCEL='0',ARTESP_OCCURRENCES_API_KEY='TEST-NOT-LIVE',ARTESP_INTERVENTIONS_API_KEY='TEST-NOT-LIVE')
import server
from road_data import Service
from road_data.adapters import make,iso
private=root/'artifacts/navigation-intelligence-v3-phase-b/private/fixtures';private.mkdir(parents=True,exist_ok=True)
server.DATA_DIR=private;server.DB_PATH=private/'TEST.sqlite';sqlite3.connect(server.DB_PATH).close()
server.init_db();server.ensure_v18_tables();server.community.init(server)
s=Service(server.db);s.initialize()
types=['ACCIDENT','ROADWORK','CLOSURE','FLOOD','CONGESTION','PRF_OPERATIONAL_UNIT','PMRV_POST','TOLL_PLAZA','SAU','HEAVY_RAIN','RAIN_STATION']
rows=[]
from datetime import datetime,timezone,timedelta
for i,kind in enumerate(types):
    sid='artesp-occurrences' if i<5 else {'PRF_OPERATIONAL_UNIT':'prf-sp','PMRV_POST':'pmrv-sp','TOLL_PLAZA':'antt-tolls','SAU':'official-support','HEAVY_RAIN':'defesa-civil-sp','RAIN_STATION':'sp-aguas'}[kind]
    cls='event' if i<5 else 'weather' if i>=9 else 'infrastructure'
    row=make(sid,'TEST-'+kind,kind,cls,{'TEST':True},iso(),geometry={'type':'Point','coordinates':[-46.55,-23.7+i*.0005]})
    row.update(description='TEST ONLY · '+kind,road='SP-160',direction='NORTE',source_updated_at=iso(),expires_at=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat() if cls!='infrastructure' else None)
    rows.append(row)
for sid in {r['source_id'] for r in rows}:s.persist(sid,[r for r in rows if r['source_id']==sid],iso())
with server.db() as c:c.execute("UPDATE road_data_sources SET status='HEALTHY',last_success_at=?,last_source_timestamp=?,name='TEST fixture source',authority='TEST ONLY',attribution='TEST fixture, not a live official feed',license='TEST ONLY'",(iso(),iso()))
os.environ.pop('ADMIN_PASSWORD_HASH',None);os.environ['ADMIN_USERNAME']='admin';os.environ['RELAS_ADMIN_PASSWORD']='123';os.environ['SESSION_SECRET']='isolated-phase-b-test-session-not-production';server.AUTH=server.AdminAuth(private);server.ADMIN_USER='admin'
class H(server.H):
    def log_message(self,*a):pass
    def end_headers(self):self.send_header('X-Relas-Test-Fixtures','1');super().end_headers()
    def do_POST(self):
        if self.path.startswith('/api/admin/road-sources/'):return self.js({'error':'TEST server does not call official upstream sources'},409)
        return super().do_POST()
server.ThreadingHTTPServer(('127.0.0.1',8818),H).serve_forever()
