"""Integration checks against the isolated validation branch, never production.

Set NEON_VALIDATION_URL (pooled or direct). Test records have unique IDs and are
removed explicitly; the real SQLite is never opened. No secret is printed.
"""
import json
import os
import secrets
import sys
import time
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime_config import load_environment
load_environment()
if not os.environ.get('NEON_VALIDATION_URL'):raise SystemExit('NEON_VALIDATION_URL required')
os.environ.update(DATABASE_BACKEND='postgres',DATABASE_URL=os.environ['NEON_VALIDATION_URL'],RELAS_ENV='preview')
from admin_auth import hash_password
password=secrets.token_urlsafe(24);marker='relas-test-'+secrets.token_hex(6)
os.environ.update(ADMIN_USERNAME='relas-validation',ADMIN_PASSWORD_HASH=hash_password(password),SESSION_SECRET=secrets.token_urlsafe(48))
import server
import db
import runtime_jobs
from fastapi.testclient import TestClient


def main():
    results={};ids=[]
    def record(name, value=True):
        if value is False:raise AssertionError(name)
        results[name]=value
    try:
        try:
            with server.db() as c:
                c.execute('INSERT INTO runtime_state(key,value_json,updated_at) VALUES(?,?,?)',(marker,'{}',server.now()))
                c.execute('UPDATE runtime_state SET value_json=? WHERE key=?',('{"ok":true}',marker))
                record('insert_update_select',c.execute('SELECT value_json FROM runtime_state WHERE key=?',(marker,)).fetchone()[0]=='{"ok":true}')
                raise ValueError('rollback-test')
        except ValueError:pass
        with server.db() as c:
            record('rollback',c.execute('SELECT key FROM runtime_state WHERE key=?',(marker,)).fetchone() is None)
            sql=db.upsert_statement('INSERT INTO source_gaps(municipality,status) VALUES(?,?)')
            c.execute(sql,(marker,'needs_source'));c.execute(sql,(marker,'checked'))
            record('upsert',c.execute('SELECT status FROM source_gaps WHERE municipality=?',(marker,)).fetchone()[0]=='checked')
            c.execute('DELETE FROM source_gaps WHERE municipality=?',(marker,))
            record('delete_controlled',c.execute('SELECT status FROM source_gaps WHERE municipality=?',(marker,)).fetchone() is None)
        with TestClient(server.app,base_url='https://relas.test') as client:
            login=client.post('/api/admin/login',json={'username':'relas-validation','password':password})
            record('admin_login',login.status_code==200)
            token=login.json()['token']
            # A distinct transport instance accepts the same signed cookie/token.
            with TestClient(server.app,base_url='https://relas.test') as second:
                record('distributed_session',second.get('/api/admin/inventory',headers={'Authorization':'Bearer '+token}).status_code==200)
            for path in ['/api/health','/api/radars','/api/road-objects','/api/stats','/api/admin/database-status','/api/admin/dashboard','/api/admin/inventory','/api/admin/sources','/api/admin/logs','/api/admin/update-queue','/api/map/features?bbox=-46.67,-23.58,-46.64,-23.55']:
                response=client.get(path);record(path,response.status_code==200)
            for kind in ['radar','signal']:
                response=client.post('/api/admin/manual/'+kind,json={'municipality':'São Paulo','name':marker+kind,'latitude':-23.55,'longitude':-46.633,'speed_limit':60,'direction':'Leste'})
                record('manual_'+kind,response.status_code==200 and response.json().get('ok'))
                ids.append(response.json()['id'])
            filtered=client.get('/api/map/features?bbox=-46.64,-23.56,-46.62,-23.54&types=signal').json()
            record('bbox_type_filter',all(f['properties']['kind']=='signal' for f in filtered['features']))
            response=client.post('/api/map/route-alerts',json={'coordinates':[[-46.64,-23.55],[-46.62,-23.55]]})
            record('route_alerts',response.status_code==200)
            record('community_import_replay',server.community.import_file(server)['cached'])
            server._save_json(Path(marker),{'persistent':True})
            record('durable_cache',server._load_json(Path(marker),{})=={'persistent':True})
            # Execute a real bounded Admin job with no external network dependencies.
            real_sync=server.sync_municipalities_ibge
            server.sync_municipalities_ibge=lambda:{'ok':True,'cached':True,'test':marker}
            try:
                response=client.post('/api/admin/sync/municipalities',json={})
                record('request_bound_job',response.status_code==200 and response.json()['status']=='completed')
            finally:server.sync_municipalities_ibge=real_sync
            record('job_persisted',runtime_jobs.state(server,'municipalities')['status']=='completed')
            # Exercise city/queue/log SQL end to end; provider discovery is mocked
            # so this verifies our integration rather than external availability.
            with patch.object(server,'_probe_backbones',lambda city:[]),patch.object(server,'_known_connector_probe',lambda *args:None),patch.object(server,'_official_open_data_scout',lambda city:[{'source_id':marker,'name':marker}]):
                response=client.post('/api/admin/update-city',json={'municipality':marker,'mode':'radars','include_osm':False})
                record('city_update_with_mock_providers',response.status_code==200 and response.json()['status']=='completed')
            with server.db() as c:
                record('city_queue_and_logs',c.execute('SELECT count(*) FROM update_queue WHERE municipality=?',(marker,)).fetchone()[0]>0 and c.execute('SELECT count(*) FROM operation_logs WHERE municipality=?',(marker,)).fetchone()[0]>0)
            response=client.post('/api/admin/batch-scan',json={'municipalities':['São Paulo','Santos']})
            record('oversized_job_rejected',response.status_code==400)
        record('opposite_direction',not server.community.direction_matches({'direction_type':1,'direction':270},90))
        record('bidirectional',server.community.direction_matches({'direction_type':2,'direction':270},90))
        # Reconnect after closing every prior handle: data persists in Neon.
        with server.db() as c:record('reconnect_persistence',c.execute('SELECT value_json FROM runtime_state WHERE key=?',(marker,)).fetchone() is not None)
    finally:
        with server.db() as c:
            for rid in ids:
                c.execute('DELETE FROM manual_entries WHERE entity_id=?',(rid,))
                c.execute('DELETE FROM radar_history WHERE radar_id=?',(rid,))
                c.execute('DELETE FROM road_object_history WHERE object_id=?',(rid,))
                c.execute('DELETE FROM radars WHERE id=?',(rid,))
                c.execute('DELETE FROM road_objects WHERE id=?',(rid,))
            c.execute('DELETE FROM admin_events WHERE message LIKE ?',('%'+marker+'%',))
            c.execute('DELETE FROM runtime_state WHERE key=?',(marker,))
            for table in ('operation_logs','update_queue','source_attempts','source_gaps','municipality_sources','municipality_profiles'):
                c.execute('DELETE FROM '+table+' WHERE municipality=?',(marker,))
        Path('artifacts/vercel-neon/postgres-tests.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print(json.dumps({'checks':len(results),'passed':all(results.values())}))


if __name__=='__main__':main()
