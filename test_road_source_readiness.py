"""B.1 policy unit tests; fixtures here are not production/readiness data."""
import unittest
from datetime import datetime,timezone
from road_data.readiness import station_freshness,source_readiness
from road_data.coordinate_review import official_prf_review,toll_review

NOW=datetime(2026,10,26,12,tzinfo=timezone.utc).timestamp()
def iso(age):return datetime.fromtimestamp(NOW-age,timezone.utc).isoformat()
def station(age,gap=10,cache_age=0,observed=True):return station_freshness({'max_date':iso(age),'measurement_gap':gap},NOW,iso(cache_age),observed=observed)

class SourceReadinessTests(unittest.TestCase):
    def test_ten_minute_nominal_station(self):
        self.assertEqual(station(1200)['state'],'FRESH');self.assertEqual(station(1201)['state'],'AGING');self.assertEqual(station(2401)['state'],'STALE')
    def test_hourly_is_not_ten_minute_station(self):
        self.assertEqual(station(3500,60)['state'],'FRESH');self.assertTrue(station(3500,60)['current']);self.assertFalse(station(4000,60)['current'])
    def test_cache_stopped_is_not_a_dead_station(self):
        self.assertEqual(station(200000,cache_age=200000)['state'],'STALE');self.assertEqual(station(200000,cache_age=200000)['reason'],'COLLECTOR_CACHE_STALE')
    def test_station_can_be_dead_only_with_fresh_provider_evidence(self):
        self.assertEqual(station(200000)['state'],'DEAD_STATION');self.assertEqual(station(200000,observed=False)['state'],'STALE')
    def test_missing_timestamp_cadence_and_future_are_unknown(self):
        self.assertEqual(station(1,None)['state'],'UNKNOWN');self.assertEqual(station(-301)['state'],'UNKNOWN')
        self.assertEqual(station_freshness({},NOW,iso(0))['state'],'UNKNOWN')
    def test_daily_reading_never_establishes_current_road_rain(self):
        self.assertEqual(station(30,1440)['state'],'FRESH');self.assertFalse(station(30,1440)['current'])
    def source(self,**changes):
        return dict(source_id='antt-tolls',auth_type='none',category='infrastructure',last_success_at=iso(60),last_source_timestamp=iso(100*86400),poll_interval_seconds=86400,enabled=1,last_error=None,**changes)
    def review(self,**changes):return dict(license_verified=1,endpoint_verified=1,license='TEST',attribution_required=1,**changes)
    def test_static_infrastructure_not_expired_by_old_content_timestamp(self):
        r=source_readiness(self.source(),self.review(),NOW,False,approved=73)
        self.assertEqual(r['freshness_status'],'FRESH');self.assertEqual(r['freshness_kind'],'INFRASTRUCTURE_FRESHNESS');self.assertEqual(r['status'],'HEALTHY');self.assertGreater(r['source_snapshot_age_seconds'],90*86400)
    def test_unknown_license_is_explicit_blocker(self):
        r=source_readiness(self.source(),{'endpoint_verified':1},NOW,False)
        self.assertEqual(r['status'],'BLOCKED_LICENSE');self.assertIn('LICENSE_NOT_VERIFIED',r['blockers']);self.assertIsNone(r['attribution_required'])
    def test_endpoint_coordinates_auth_disabled_have_explicit_reason(self):
        self.assertEqual(source_readiness(self.source(),{'license_verified':1},NOW,False)['status'],'BLOCKED_ENDPOINT')
        s=self.source();s['source_id']='prf-sp';self.assertEqual(source_readiness(s,self.review(),NOW,False)['status'],'BLOCKED_COORDINATES')
        s['auth_type']='api-key';self.assertEqual(source_readiness(s,self.review(),NOW,False)['status'],'AUTH_REQUIRED')
        s['enabled']=0;self.assertEqual(source_readiness(s,self.review(),NOW,False)['status'],'DISABLED')
    def test_partial_coordinate_coverage_is_degraded_and_not_hidden(self):
        r=source_readiness(self.source(),self.review(),NOW,False,66,7);self.assertEqual(r['status'],'DEGRADED');self.assertEqual(r['coordinate_blocked'],7)
    def row(self):return {'event_id':'TEST','event_type':'PRF_OPERATIONAL_UNIT','description':'TEST Miracatu','road':'BR-116','km_start':344,'payload_json':{'address':'BR-116 km 344 Miracatu/SP'}}
    def candidate(self):return {'uf':'SP','situacao':'Ativo','municipio':'Miracatu','rodovia':'BR-116','km_m':'344.0','latitude':'-24.03','longitude':'-47.17'}
    def test_official_join_requires_local_municipality_and_km(self):
        r=official_prf_review(self.row(),[self.candidate()],lambda x,y:'Miracatu');self.assertEqual(r['status'],'APPROVED');self.assertEqual(r['coordinate_quality'],'OFFICIAL_COORDINATE')
        bad=official_prf_review(self.row(),[self.candidate()],lambda x,y:'Ourinhos');self.assertEqual(bad['coordinate_quality'],'CONFLICT');self.assertIsNone(bad['lon'])
        c=self.candidate();c['km_m']='350';self.assertEqual(official_prf_review(self.row(),[c],lambda x,y:'Miracatu')['status'],'BLOCKED')
    def test_administrative_unit_not_promoted_from_operational_coordinate(self):
        r=self.row();r['event_type']='PRF_DELEGACY';self.assertEqual(official_prf_review(r,[self.candidate()],lambda x,y:'Miracatu')['status'],'BLOCKED')
    def test_unknown_coordinate_not_promoted_by_address(self):
        self.assertEqual(official_prf_review(self.row(),[],lambda x,y:None)['coordinate_quality'],'OFFICIAL_ROAD_KM')
    def test_toll_conflict_preserves_coordinate_for_review(self):
        r={'event_id':'TEST','description':'TEST','lon':-47.17,'lat':-24.03,'municipality':'Miracatu','road':'BR-116','km_start':344,'status':'active'}
        self.assertEqual(toll_review(r,lambda x,y:'Another city')['status'],'BLOCKED');self.assertEqual(toll_review(r,lambda x,y:'Miracatu')['status'],'APPROVED')

if __name__=='__main__':unittest.main()
