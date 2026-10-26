import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import db
from road_data import Service
from road_data import adapters as A
from road_data.geometry import corridor


class RoadDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.env=patch.dict(os.environ,{'DATABASE_BACKEND':'sqlite','RELAS_ENV':'development','VERCEL':'0','ARTESP_OCCURRENCES_API_KEY':'unit-secret-never-return','ARTESP_INTERVENTIONS_API_KEY':'unit-secret-never-return'})
        self.env.start();self.addCleanup(self.env.stop);self.now=1800000000.;self.path=Path(self.tmp.name)/'road.sqlite'
        self.calls=[];self.response=(200,{},json.dumps(self.payload()).encode())
        self.s=Service(lambda:db.connect(self.path),self.http,lambda:self.now);self.s.initialize()
        # Explicit TEST policies only. These unit grants are never readiness evidence.
        with self.s.connect() as c:
            for sid in ('artesp-occurrences','artesp-interventions','prf-sp','antt-tolls','sp-aguas','defesa-civil-sp','pmrv-sp','artesp-tolls','official-support'):
                c.execute('INSERT INTO road_source_reviews(source_id,license,terms_url,commercial_restrictions,attribution_required,last_terms_check,license_verified,endpoint_verified,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?)',(sid,'TEST ONLY','https://example.invalid/TEST','TEST ONLY',1,A.iso(),1,1,A.iso()))

    def http(self,url,headers):self.calls.append((url,headers));return self.response
    def payload(self,rows=None,**meta):
        return {'meta':{'versao':'1.0.0','timestamp':'2027-01-15T08:00:00+00:00',**meta},'results':rows if rows is not None else [{'slug':'test-only','classe':'Acidente','status':'ativa','lat':-23.7,'lng':-46.55,'rodovia':{'nome':'SP-160'},'municipios':[{'cod_ibge':'3548708','nome':'São Bernardo do Campo'}]}]}
    def reset_gate(self):
        with self.s.connect() as c:c.execute('UPDATE road_poll_budget SET next_at=0,lease_until=0');c.execute('UPDATE road_data_sources SET next_attempt_at=0,lease_until=0')

    def test_migration_idempotent_and_non_destructive(self):
        with self.s.connect() as c:c.execute('CREATE TABLE old_inventory(id TEXT PRIMARY KEY)');c.execute("INSERT INTO old_inventory VALUES('keep')")
        self.s.initialize()
        with self.s.connect() as c:self.assertEqual(c.execute('SELECT id FROM old_inventory').fetchone()[0],'keep');self.assertEqual(c.execute('SELECT count(*) FROM road_data_sources').fetchone()[0],9)

    def test_success_preserves_geometry_direction_provenance(self):
        self.assertTrue(self.s.sync('artesp-occurrences')['ok']);r=self.s.items(include_inactive=True)[0]
        self.assertEqual(r['geometry']['coordinates'],[-46.55,-23.7]);self.assertEqual(r['source_type'],'official');self.assertEqual(r['road'],'SP-160')
        self.assertNotIn('unit-secret',json.dumps(self.s.health()));self.assertNotIn('unit-secret',json.dumps(self.s.logs()))

    def test_http_errors_preserve_snapshot(self):
        self.s.sync('artesp-occurrences')
        for code in (401,403,429,500):
            self.reset_gate();self.response=(code,{'Retry-After':'600'},b'unit-secret-body')
            self.assertFalse(self.s.sync('artesp-occurrences')['ok']);self.assertEqual(len(self.s.items(include_inactive=True)),1)
            self.assertEqual(next(s for s in self.s.health() if s['source_id']=='artesp-occurrences')['freshness_status'],'STALE')
        self.assertNotIn('unit-secret',json.dumps(self.s.logs()))

    def test_timeout_preserves_snapshot(self):
        self.s.sync('artesp-occurrences');self.reset_gate()
        def fail(*args):raise TimeoutError('secret remote request')
        self.s.http=fail;self.assertFalse(self.s.sync('artesp-occurrences')['ok']);self.assertEqual(len(self.s.items(include_inactive=True)),1)

    def test_schema_change_does_not_clear_and_valid_empty_does(self):
        self.s.sync('artesp-occurrences');self.reset_gate();self.response=(200,{},b'{"changed":[]}')
        self.assertEqual(self.s.sync('artesp-occurrences')['error'],'PARSER_DEGRADED');self.assertEqual(self.s.items(include_inactive=True)[0]['status'],'active')
        self.reset_gate();self.response=(200,{},json.dumps(self.payload([])).encode());self.assertTrue(self.s.sync('artesp-occurrences')['ok']);self.assertEqual(self.s.items(include_inactive=True)[0]['status'],'ended')

    def test_rate_limit_shared_key_and_probe(self):
        self.s.sync('artesp-occurrences');self.assertEqual(self.s.sync('artesp-occurrences')['status'],'RATE_LIMITED');self.assertEqual(self.s.sync('artesp-interventions')['status'],'RATE_LIMITED');self.assertEqual(len(self.calls),1)
        self.now+=301;self.assertTrue(self.s.sync('artesp-interventions',True)['ok']);self.assertEqual(len(self.s.items(include_inactive=True)),1)

    def test_pagination_only_publishes_complete_snapshot(self):
        self.response=(200,{},json.dumps(self.payload(next_offset=100)).encode());r=self.s.sync('artesp-occurrences');self.assertFalse(r['snapshot_published']);self.assertEqual(len(self.s.items(include_inactive=True)),0)
        self.now+=301;self.response=(200,{},json.dumps(self.payload([])).encode());self.assertTrue(self.s.sync('artesp-occurrences')['snapshot_published']);self.assertEqual(len(self.s.items(include_inactive=True)),1)

    def test_missing_geometry_is_inventory_only(self):
        rows=self.payload()['results'];rows[0].pop('lat');rows[0].pop('lng');self.response=(200,{},json.dumps(self.payload(rows)).encode());self.s.sync('artesp-occurrences')
        self.assertEqual(len(self.s.items(include_inactive=True)),1);self.assertEqual(len(self.s.features('-47,-24,-46,-23')['features']),0)

    def test_expiry_bbox_and_freshness(self):
        row=A.make('prf-sp','unit','PRF_OPERATIONAL_UNIT','infrastructure',{},A.iso(),geometry={'type':'Point','coordinates':[-46.55,-23.7]});self.s.persist('prf-sp',[row],A.iso())
        self.assertEqual(len(self.s.features('-46.56,-23.71,-46.54,-23.69')['features']),0)
        with self.s.connect() as c:c.execute('INSERT INTO road_location_reviews(event_id,lon,lat,coordinate_quality,confidence,coordinate_source,approval_status,evidence_json,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?)',(row['event_id'],-46.55,-23.7,'OFFICIAL_COORDINATE',.97,'TEST ONLY','APPROVED','{}',A.iso()))
        self.assertEqual(len(self.s.features('-46.56,-23.71,-46.54,-23.69')['features']),1);self.assertEqual(len(self.s.features('-48,-24,-47,-23')['features']),0)
        with self.assertRaises(ValueError):self.s.features('nan,1,2,3')

    def test_corridor_parallel_direction_region_and_windows(self):
        def row(kind,p,direction=None):
            r=A.make('prf-sp',kind,kind,'event',{},A.iso(),geometry={'type':'Point','coordinates':p});r['direction']=direction;return r
        route=[[-46.55,-23.75],[-46.55,-23.65]]
        rows=[row('own',[-46.55,-23.7],'NORTE'),row('opposite',[-46.55,-23.7],'SUL'),row('parallel',[-46.552,-23.7])]
        self.assertEqual([r['event_type'] for r in corridor(rows,route)],['own'])
        self.assertEqual(corridor(rows,route,along=11000),[])

    def test_sibh_public_sp_readings_expiry_not_regional_rain(self):
        payload={'measurements':[{'station_prefix_id':'fixture','cod_ibge':'3550308','longitude':'-46.55','latitude':'-23.7','value':2,'max_date':'2026-10-25T12:00:00Z','station_name':'TEST'}]}
        rows=A.sibh(payload);self.assertEqual(rows[0]['event_type'],'RAIN_STATION');self.assertEqual(rows[0]['geometry']['type'],'Point');self.assertIsNotNone(rows[0]['expires_at'])
        payload['measurements'][0]['cod_ibge']='3125101';self.assertEqual(A.sibh(payload),[])
        with self.assertRaises(A.SchemaChanged):A.sibh({'changed':[]})

    def test_official_weather_requires_validity(self):
        p={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'id':'TEST','type':'HEAVY_RAIN'},'geometry':{'type':'Point','coordinates':[-46.5,-23.7]}}]}
        with self.assertRaises(A.SchemaChanged):A.official_geojson(p,'defesa-civil-sp')
        p['features'][0]['properties']['valid_until']='2026-10-26T12:00:00Z';self.assertEqual(A.official_geojson(p,'defesa-civil-sp')[0]['record_class'],'weather')

    def test_prf_administrative_never_operational_or_geocoded_automatically(self):
        r=A.prf('<h1>Delegacia em Teste</h1><p>Modificado em 20/10/2026 Endereço: BR 116 Km 10 Telefone: 191</p>','https://www.gov.br/prf/test')[0]
        self.assertEqual(r['event_type'],'PRF_DELEGACY');self.assertIsNone(r['geometry']);self.assertEqual(r['source_updated_at'],'2026-10-20T00:00:00-03:00')

    def test_disabled_source_cannot_sync(self):
        row=A.make('artesp-occurrences','TEST-disabled','ACCIDENT','event',{},A.iso(),geometry={'type':'Point','coordinates':[-46.55,-23.7]});self.s.persist('artesp-occurrences',[row],A.iso())
        with self.s.connect() as c:c.execute("UPDATE road_data_sources SET enabled=0 WHERE source_id='artesp-occurrences'")
        self.assertEqual(self.s.sync('artesp-occurrences')['status'],'RATE_LIMITED');self.assertEqual(len(self.calls),0)
        self.assertEqual(len(self.s.features('-47,-24,-46,-23')['features']),0);self.assertEqual(len(self.s.items(include_inactive=True)),1)
        self.assertEqual(self.s.diagnostics()['counts'][0]['eligible_map'],0)

    def test_diagnostics_do_not_persist_location(self):
        self.s.record_diagnostics({'rendered':4,'route':[[1,2]],'latitude':-23,'user':'private'})
        data=self.s.diagnostics()['clients'][0]['payload_json'];self.assertEqual(json.loads(data),{'rendered':4})

    def test_same_credential_hourly_cap(self):
        for i in range(12):
            self.now+=301;self.assertTrue(self.s.sync('artesp-occurrences')['ok'])
        self.reset_gate();self.assertEqual(self.s.sync('artesp-occurrences')['status'],'RATE_LIMITED')

    def test_response_remaining_zero_prevents_early_retry(self):
        self.response=(200,{'X-RateLimit-Remaining':'0'},json.dumps(self.payload()).encode());self.assertTrue(self.s.sync('artesp-occurrences')['ok']);self.now+=601;self.assertEqual(self.s.sync('artesp-occurrences')['status'],'RATE_LIMITED')

    def test_newest_tariff_only_and_expired_weather_excluded(self):
        p={'tariff':12,'tariff_valid_until':A.iso()};r=A.make('artesp-tolls','TEST','TOLL_PLAZA','infrastructure',p,A.iso(),geometry={'type':'Point','coordinates':[-46.55,-23.7]})
        self.s.persist('artesp-tolls',[r],A.iso());self.assertIsNone(self.s.items()[0]['tariff'])

    def test_asgi_endpoints_and_existing_admin_auth(self):
        import server
        from fastapi.testclient import TestClient
        with patch.object(server,'db',self.s.connect),TestClient(server.app) as client:
            self.assertEqual(client.get('/api/admin/road-sources').status_code,401)
            self.assertEqual(client.post('/api/admin/road-sources/prf-sp/sync',json={}).status_code,401)
            self.assertEqual(client.post('/api/road-events/diagnostics',json={'rendered':1}).status_code,401)
            self.assertEqual(client.get('/api/source-health').status_code,200)
            self.assertEqual(client.get('/api/road-events?bbox=-47,-24,-46,-23').status_code,200)
            self.assertEqual(client.get('/api/weather?bbox=nan,1,2,3').status_code,400)
            self.assertEqual(client.post('/api/road-events/route',json={'coordinates':[[0,0]]}).status_code,400)
            for name in ('navigation/phase-b.js','navigation/phase-b.css','road-admin.js','icons/gale.svg'):
                self.assertEqual(client.get('/'+name).status_code,200)

    def test_antt_tolls_are_sp_only_and_do_not_invent_tariffs(self):
        data={'praca-de-pedagio':[{'uf':'SP','concessionaria':'TEST','praca_de_pedagio':'TEST','rodovia':'BR-116','km_m':'12,3','situacao':'Ativo','latitude':'-23.7','longitude':'-46.55','sentido':'Crescente/Decrescente'},{'uf':'RJ'}]}
        rows=A.antt_tolls(data,'2026-07-28T11:00:00');self.assertEqual(len(rows),1);self.assertEqual(rows[0]['km_start'],12.3);self.assertEqual(rows[0]['status'],'active');self.assertNotIn('tariff',rows[0]['payload_json'])
        with self.assertRaises(A.SchemaChanged):A.antt_tolls({'changed':[]},A.iso())

    def test_review_does_not_publish_geocoded_proposal(self):
        row=A.make('prf-sp','TEST-review','PRF_OPERATIONAL_UNIT','infrastructure',{},A.iso());self.s.persist('prf-sp',[row],A.iso());r=self.s.review(row['event_id'],[{'longitude':-46.55,'latitude':-23.7}]);self.assertFalse(r['published_to_map']);self.assertIsNone(self.s.items(include_inactive=True)[0]['geometry'])

    def test_catalog_shares_budget_and_retains_old_on_error(self):
        self.response=(200,{},b'{"meta":{"next_offset":100},"results":[{"nome":"TEST"}]}')
        self.assertTrue(self.s.catalogs('artesp-occurrences','rodovias',True)['partial']);self.assertEqual(self.s.sync('artesp-occurrences')['status'],'RATE_LIMITED')
        self.now+=301;self.response=(429,{},b'private');self.assertFalse(self.s.catalogs('artesp-occurrences','rodovias',True)['ok']);self.assertEqual(len(self.s.catalogs('artesp-occurrences')['items']),1)

    def test_authenticated_admin_sources_logs_diagnostics_and_disable(self):
        import server
        from admin_auth import AdminAuth
        from fastapi.testclient import TestClient
        with patch.dict(os.environ,{'SESSION_SECRET':'unit-session-secret-long-enough-123456','ADMIN_USERNAME':'operator'}),patch.object(server,'AUTH',AdminAuth(self.tmp.name)),patch.object(server,'db',self.s.connect):
            headers={'Authorization':'Bearer '+server.AUTH.issue()}
            with TestClient(server.app) as client:
                for path in ('/api/admin/road-sources','/api/admin/layer-diagnostics','/api/admin/road-source-logs','/api/admin/road-events','/api/admin/road-infrastructure','/api/admin/road-sources/artesp-occurrences/catalogs'):
                    r=client.get(path,headers=headers);self.assertEqual(r.status_code,200,path);self.assertNotIn('unit-secret-never-return',r.text)
                self.assertEqual(client.post('/api/admin/road-sources/prf-sp/disable',json={},headers=headers).status_code,200)
                self.assertEqual(client.post('/api/road-events/diagnostics',json={'rendered':2,'route':'PRIVATE'},headers=headers).status_code,200)
                self.assertEqual(json.loads(self.s.diagnostics()['clients'][0]['payload_json']),{'rendered':2})

    def test_validity_is_utc_and_fresh_active_event_does_not_expire_from_old_edit(self):
        self.assertEqual(A.timestamp('2026-10-25T22:00:00-03:00'),'2026-10-26T01:00:00+00:00')
        p=self.payload();p['results'][0]['atualizado_em']='2025-01-01T00:00:00Z'
        row=A.artesp(p,'artesp-occurrences','2026-10-26T01:00:00+00:00')[0]
        self.assertEqual(row['source_updated_at'],'2025-01-01T00:00:00+00:00');self.assertEqual(row['expires_at'],'2026-10-26T01:30:00+00:00')


if __name__=='__main__':unittest.main()
