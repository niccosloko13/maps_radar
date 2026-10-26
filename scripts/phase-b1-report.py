"""Close B.1 from recorded real evidence. Does not call any upstream source."""
import os,json,re,hashlib,sqlite3,zipfile
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'artifacts/navigation-intelligence-v3-phase-b1'
def read(n):return json.loads((A/n).read_text(encoding='utf-8-sig'))
def write(n,t):(A/n).write_text(t.strip()+'\n',encoding='utf-8')
def table(rows,keys):
 def cell(v):return str(v if v is not None else 'NOT_AVAILABLE').replace('|','/').replace('\n',' ')
 return '| '+' | '.join(keys)+' |\n|'+'|'.join(['---']*len(keys))+'|\n'+'\n'.join('| '+' | '.join(cell(r.get(k)) for k in keys)+' |' for r in rows)
real=read('real-data-results.json');browser=read('browser-results.json');prf=read('prf-coordinate-review.json');toll=read('antt-coordinate-review.json');diag=read('admin-diagnostics-browser.json');prfb=read('prf-targeted-browser.json');pg=read('postgres-tests.json');exits=read('suite-exit-codes.json');health=real['source_health'];sibh=real['sibh'];now=datetime.now(timezone.utc).isoformat()
statuses=dict(Counter(s['status'] for s in health))
assert all(v==0 for v in exits.values())
assert diag['map']['rendered']==json.loads(diag['diagnostics']['clients'][0]['payload_json'])['rendered']==1
with sqlite3.connect(A/'private/validation.sqlite') as c:
 fixtures=c.execute("SELECT count(*) FROM road_event WHERE event_id LIKE '%TEST%' OR payload_json LIKE '%\"TEST\"%'").fetchone()[0]
 history=c.execute('SELECT count(*) FROM event_evidence').fetchone()[0]
assert fixtures==0
# Compare checkpoint inventory: preserve all existing paths; report only changed/new code.
changes=[]
with zipfile.ZipFile(A/'private/checkpoint.zip') as z:
 prior={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
 for base in ['app','road_data','scripts','tools']:
  for p in (ROOT/base).rglob('*'):
   if p.suffix not in ('.py','.js','.cjs','.html','.css','.svg'):continue
   n=p.relative_to(ROOT).as_posix()
   if hashlib.sha256(p.read_bytes()).hexdigest()!=prior.get(n):changes.append(n)
for n in ['test_road_data.py','test_road_source_readiness.py','tests/phase-b.test.cjs','selftest.py','.gitignore']:
 if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=prior.get(n):changes.append(n)
write('FILES_CHANGED.json',json.dumps(sorted(set(changes)),indent=2))
write('SOURCE_STATUS.md',f'''# Source status - B.1
Recorded at collection {datetime.fromtimestamp(real['collected_at'],timezone.utc).isoformat()}; time-sensitive, not a permanent health claim.

{table(health,['source_id','status','record_count','coordinate_approved','coordinate_blocked','freshness_status','freshness_kind','last_success_at','last_attempt_at','blocker','next_action'])}

Status totals: {json.dumps(statuses)}. HEALTHY=0; DEGRADED=2; blocked/auth=7. Three sources have real collection evidence; only two have partially approved public map data. Zero integrations are declared fully production-ready.

## License/terms review

{table(health,['source_id','license','terms_url','commercial_restrictions','attribution_required','last_terms_check','license_verified','endpoint_verified'])}

Unknown terms are a blocker, not an implied public-domain grant. ARTESP public portal data terms and authenticated CCM API terms are separate. PRF directory original text is retained as evidence; published coordinates/label come from the separately licensed ANTT inventory. Recheck terms before changing use/distribution.
''')
write('PRF_COORDINATE_REVIEW.md',f'''# PRF coordinate review
27 directory records: 17 operational, 9 delegacies, 1 superintendence. Approved:12; blocked:15 (5 operational conflicts +10 administrative/unresolved). No common geocoding was promoted to official.

Evidence: [PRF directory](https://www.gov.br/prf/pt-br/canais-de-atendimento/unidades-prf/sao-paulo), [ANTT PRF inventory](https://dados.antt.gov.br/dataset/prf). ANTT national inventory172, SP26. Local municipal polygons check coordinates without external per-record lookup. Match requires same BR, municipality, active post, km difference <=0.5km, unambiguous candidate and polygon agreement. Original directory facts/IDs and all conflicts are preserved.

{table(prf,['name','road','km','municipality','lat','lon','coordinate_source','coordinate_quality','confidence','status','notes'])}

No calibrated local BR road-km network was available. Administrative addresses are not operational posts. OFFICIAL_ROAD_KM without an approved coordinate is blocked. BR153 source records have municipality/coordinate discrepancies (including Ourinhos/Sao Jose do Rio Preto and Marilia/Guaicara); coordinates were not silently swapped. Full evidence in prf-coordinate-review.json. Published official coordinates are candidates with conservative validation, not field-survey guarantees.
''')
sample=json.loads((A/'private/sibh-current.json').read_text(encoding='utf-8'))['measurements']
ratios=[]
for r in sample:
 try:
  count=int(r['qtd']);span=(datetime.fromisoformat(r['max_date'].replace('Z','+00:00'))-datetime.fromisoformat(r['min_date'].replace('Z','+00:00'))).total_seconds()/60
  if count>1:ratios.append(round(span/(count-1),2))
 except (KeyError,ValueError,TypeError):pass
write('SIBH_FRESHNESS_ANALYSIS.md',f'''# SIBH freshness analysis
Real new GET succeeded. Received1106; SP normalized1094; IDs retained1113; current at collection1091. States: {json.dumps(sibh['states'])}. Reasons: {json.dumps(sibh['reasons'])}. DEAD_STATION=0, UNKNOWN=0. One fresh daily record is not evidence of current road rainfall.

The old954 snapshot became stale because the collector stopped after approximately01:44UTC; closure happened later. The unchanged max_date observation timestamps legitimately aged. Re-fetch returned new observations; there was no evidence requiring timezone correction. ISO offsets are respected; ingestion time is stored separately and never substituted for station time. This is not proof that every old station died.

Nominal cadence comes from provider measurement_gap (minutes). Cadences in retained SP inventory: {json.dumps(sibh['cadences_seconds'])}. In a separate real provider sample, {len(ratios)} records had multiple samples; observed average cadence examples: {dict(Counter(ratios).most_common(8))}. Variable sampling/count coverage is preserved; no one-size ten-minute assumption.

FRESH <=2 nominal samples; AGING <=4; STALE beyond4. Current eligibility additionally requires reading <=1hour and cadence <=1hour, matching the requested hours=1 window. A stale collector (>2poll intervals) means STALE cache, not DEAD_STATION. Only an explicitly observed provider reading older than max(24hours,12cadences) in a fresh collection can be DEAD_STATION. Missing cadence/time or future timestamp >5minutes is UNKNOWN and cannot alert. Missing latest observations stay historical/STALE. Snapshot is preserved on schema/network/auth errors.

The new collection created152 IDs, updated942, expired18; duplicates0. Historical inventory1113 includes19 IDs absent from the latest response; two returned readings were old. No silent deletion.

Source collection freshness FRESH at capture; public eligibility0: BLOCKED_LICENSE. [Portal](https://apps.spaguas.sp.gov.br/sibh/) reserves rights; no source-specific redistribution license was confirmed. Need license and scheduled backend collection before public use. Counts above describe capture time and naturally age; no recurring scheduler was installed or claimed.
''')
write('ANTT_REVIEW.md',f'''# ANTT toll review
Real inventory73 SP; approved66; conflict7; all73 retained. [Catalog](https://dados.antt.gov.br/dataset/praca-de-pedagio) license CC BY, unspecified version. B.1 catalog check HTTP200. Resource modified2026-07-28; catalog modified2026-07-29. Latest successful local data collection2026-10-26.

Old AGING was caused by applying a blanket30-day content timestamp rule to infrastructure. Infrastructure is persistent: source content age remains visible but does not expire the plaza like a5-minute event. INFRASTRUCTURE_FRESHNESS reflects daily collector health separately; it was FRESH at capture. Operational flag is the source assertion, not a live booth availability guarantee. No tariff is fabricated. Event expiry rules were not relaxed.

{table(toll,['name','road','km','municipality','polygon_municipality','lat','lon','coordinate_quality','status','notes'])}

Coordinate conflicts stay in inventory, blocked from public rendering. No duplicates were silently removed; original identifiers and payloads retained. Concessionaire/situation remain in raw official payload, including unknown fields. Full evidence in antt-coordinate-review.json. No fresh resource download was forced within the daily polling window; recent real snapshot and new official catalog metadata were reviewed separately.
''')
endpoint_rows=[]
for s in health:
 sid=s['source_id'];status='NOT_ATTEMPTED_AUTH_REQUIRED' if sid.startswith('artesp-') and sid!='artesp-tolls' else '200' if sid in ('antt-tolls','prf-sp','sp-aguas') else 'Portal only / no approved data feed'
 endpoint_rows.append(dict(source=sid,url=s['base_url'],http=status,schema='validated real payload' if sid in ('antt-tolls','prf-sp','sp-aguas') else 'BLOCKED: no authenticated/approved payload',status=s['status']))
write('SOURCE_ENDPOINT_VALIDATION.md',f'''# Endpoint validation
{table(endpoint_rows,['source','url','http','schema','status'])}

ANTT tolls: CKAN success/result/resources/license_id=cc-by, JSON praca-de-pedagio envelope; required id,coordinates,UF,rodovia/km,situacao; national277/SP73. Bulk snapshot, no pages; empty/schema drift fails closed. CKAN resource last_modified is content revision, not event time. No numeric rate header advertised in captured evidence; daily cache policy. ANTT PRF bulk JSON PRF172/SP26, CC BY; coordinates checked with local polygons.

PRF: official HTML index + bounded linked directory pages,27 normalized. Address/BR/km/name parsed; no official directory coordinates assumed. Published directory revision is not ingestion time. Once/day, <=30pages,1second spacing,90second bound. HTML drift preserves previous snapshot. ANTT coordinate join is a separate explicit review, not an unreviewed geocoder.

SIBH: HTTP200 real measurements list,1106 received/1094 normalized. Fields station_prefix_id,cod_ibge,longitude,latitude,value,max_date,measurement_gap; min_date/qtd support interval analysis. Single bulk hours=1 response, no pagination advertised. max_date is station reading, not server fetch time. Empty latest observation cannot create rain/clear-road assertions. Poll600seconds; current sample rate-limit headers absent. Source-specific license NOT VERIFIED.

ARTESP: authenticated real response NOT TESTED (keys absent); occurrences/interventions0 real. Documentation requires Api-Key,limit100,offset pagination,12requests/hour,>=300seconds; active filter filtro_finalizada=1. Required results/meta and object timestamp/geometry validation have isolated contract tests only. No real rate headers or empty/error payload observed; do not call operational. Missing-key tests perform no HTTP. 401/403/429/schema drift behavior is tested with clearly isolated unit inputs, not counted as live validation.

Public portals: SP Aguas200; DER200HTML; PMRv connection failure (separate web observation502); Defesa Civil bounded direct probe timed out, separate browser/search retrieval200HTML with 'SEM ALERTAS NO MOMENTO'. None proves a licensed machine feed. ARTESP public portal terms validated, geographic toll inventory endpoint still missing. No forced malformed requests to official services; errors/empty response behavior beyond observed traffic remains contract-test evidence only. Full safe probe metadata remains in private/portal-probes.json; no keys.
''')
write('MAP_REAL_DATA_VALIDATION.md',f'''# Real map validation
Mobile390x844, desktop1440x900, isolated real SQLite, read-only legacy radar proxy. No fixture database used. State bbox:-53.2,-25.4,-44,-19.7; API eligible78 (66 tolls+12 PRF). SIBH eligible0/license; ARTESP0/auth.

| layer | received in viewport | normalized | eligible_map | viewport | rendered | selected | detail_opened |
|---|---:|---:|---:|---:|---:|---:|---|
| ANTT toll |1|1|1|1|1|1|true|
| PRF approved Atibaia |1|1|1|1|1|1|true|
| SIBH |0|0|0|0|0|0|false: license blocked|
| ARTESP occurrences/interventions |0|0|0|0|0|0|false: auth required|

ANTT clicked real point[-47.32628,-24.157869]. PRF Atibaia clicked[-46.585265,-23.19135], real ANTT label/source/license in detail. Two genuinely rendered layers, not three. Earlier Aparecida PRF candidate was collision-suppressed by another symbol (radar priority retained); initial clicked detail was a different community enforcement object and is NOT accepted as PRF success. Raw initial browser-results.json preserves that failed selection. A targeted official Atibaia selection provided valid evidence; prf-targeted-browser.json records both attempts. No overlap override was added to hide radars.

Route Praia Grande -> Sao Bernardo: REAL_ROUTE, distance{browser['route'].get('distance_m')}m, vertices{browser['route'].get('vertices')}, corridor counts{json.dumps(browser['route'].get('counts'))}. Zero eligible auxiliary records on that actual route; federal ANTT/PRF coverage does not substitute for missing state ARTESP coverage. Zero weather/license blocked. No fixture or straight-line route counted. Road test route coverage remains blocked.

Layer Diagnostics uses actual rendered IDs, not API totals. Fixed asynchronous aggregate lag; final recorded PRF received1/rendered1 and same persisted client counters. Rain license gating prevents rain rendering even while Admin can audit real readings. Eight of eleven previously fixture-tested types still lack any real normalized evidence; nine lack approved public real-map evidence (RAIN_STATION collected but blocked). No claim that all registered product types have live coverage.

Screenshots: [ANTT](antt-tolls-real-mobile.png), [PRF approved](prf-approved-real-mobile.png), [Admin](admin-real-diagnostics.png). prf-sp-real-mobile.png is retained as FAILED selection evidence, not readiness proof.
''')
write('ADMIN_REAL_DATA_VALIDATION.md',f'''# Admin real-data validation
Existing local Admin auth flow used unchanged; test-only credentials confined to isolated server process. Nine sources visible; no redesign. Source Health shows status,last_attempt,last_success,record_count,freshness kind,approved/blocked coordinates,license/terms,blocker,next_action. SIBH BLOCKED_LICENSE/FRESH is intentional: collection health is different from permission to publish.

{table(diag['diagnostics']['counts'],['source_id','event_type','normalized','active','eligible_map','blocked_map'])}

Counters time-sensitive at capture. PRF received27 / approved12 / blocked15; ANTT73/66/7. SIBH received1106 / normalized1094 latest, retained1113; public map0. Logs contain actual collection results, errors are bounded and secrets excluded. Layer Diagnostics aggregate write returned200; final viewport PRF received1/rendered1, persisted exact1. Counts agree with observed map and approved-source policy; global78 eligibility is not the viewport render count. Admin source tabs/logs/diagnostics opened with real records. Browser harness failures (navigation wait, wrong hidden-class assertion, initial field overwrite) were corrected only in test instrumentation; not counted as app failures or test passes. Final evidence admin-diagnostics-browser.json.
''')
blockers='''1. ARTESP occurrences/interventions AUTH_REQUIRED: both keys absent; real authenticated schema/pagination/map/corridor cannot be certified. ARTESP was not authorized as an optional test requirement.
2. SIBH BLOCKED_LICENSE: fresh real readings exist, redistribution terms unconfirmed. Public rain layer intentionally blocked. Collector scheduling/production rollout not performed.
3. ARTESP toll geographic endpoint BLOCKED_ENDPOINT; state route has no eligible toll records with current approved inventory.
4. Defesa Civil, PMRv and support inventory BLOCKED_LICENSE + endpoint validation outstanding. Public portal HTML is not a data API.
5. PRF15 blocked (5 operational conflicts,10 administrative/unresolved);7 toll conflicts. No calibrated BR network to resolve conflicts; official source corrections/manual evidence needed.
6. Full real-data corridor coverage Praia Grande -> Sao Bernardo not demonstrated: zero eligible auxiliary objects; no absence-of-hazards inference.
7. Only isolated validation databases modified; production migrations/reviews/scheduled collection deliberately not installed. No deploy/push. Physical field validation not performed.
8. PRF symbol can be suppressed by map collision to preserve radar visibility. This is reported; no global overlap override or broader redesign added.'''
write('KNOWN_BLOCKERS.md','# NOT_READY_FOR_PHYSICAL_TEST\n\n'+blockers)
write('REPORT.md',f'''# RELAS Phase B.1 - SOURCE UNBLOCK & PRODUCTION READINESS
**NOT_READY_FOR_PHYSICAL_TEST**

Closed{now}. No push, commit or deploy. No new product scope. Base4943cd4f4be8db6817222433e995974bd8305a37; branch feat/navigation-v3-phase-b1. Initial checkpoint archive and SQLite backup retained privately; SHA25674df297a7324931394eec3e1cedd079de3513ce83304c2c0cde0db20e16d598f. Prior valid work was preserved.

## Actual changes
Additive schema003 source/license/location reviews; explicit source-readiness policy; conservative official-coordinate approval overlay; observation cadence/cache freshness; licensed public-map gating; Admin blocker visibility; live render diagnostic count fix; asset cache232; isolated review/collection/test/report tools. No changes to authentication, Official Radar Finder, Precision Engine or radar matcher/direction. File inventory: FILES_CHANGED.json (compared with checkpoint).

Two partial public integrations (ANTT+PRF), one actual but license-blocked collector(SIBH), six sources with no operational live collection. Zero sources certified fully production-ready. All nine now have explicit states/actions. Schema changes validated on isolated SQLite and expiring Neon branch only; no production or personal database migration. Legacy PostgreSQL counts unchanged; full comparison postgres-tests.json. All SQLite snapshots/history preserved, {history} evidence rows in isolated real database.

## Required answers
1. ARTESP configured? No; both environment variables NOT_CONFIGURED.
2. ARTESP real authentication passed? NOT_TESTED/AUTH_REQUIRED.
3. Real occurrences?0 collected; upstream volume unknown.
4. Real interventions?0 collected; upstream volume unknown.
5. PRF records?27.
6. PRF approved coordinates?12 OFFICIAL_COORDINATE.
7. PRF blocked?15 (5 conflicts,10 administrative/unresolved).
8. SIBH current?1091 at collection; latest normalized1094; retained1113.
9. SIBH stale?21 at collection; FRESH1085,AGING7,DEAD0,UNKNOWN0. One fresh daily record not current-road eligible.
10. Why previously stale? Stopped collection and genuinely aged max_date readings; new real fetch proves updates. No timezone fudge/threshold inflation.
11. ANTT valid?73 retained official SP assets;66 spatially approved,7 conflicts.
12. ANTT AGING? Old blanket30-day content-age rule caused it; corrected infrastructure classification FRESH collector, July snapshot age still explicit.
13. HEALTHY sources?0.
14. DEGRADED?2.
15. Blocked/auth?7 (AUTH_REQUIRED2,BLOCKED_LICENSE4,BLOCKED_ENDPOINT1).
16. Real map layers?2: ANTT toll and approved PRF.
17. Fixtures?8 of11 previously fixture-tested types lack any real normalized evidence;9 lack approved real-map evidence. No fixtures counted here.
18. Admin coherent? Yes,9sources with explicit blockers; global counts distinguish received/retained/eligible/viewport.
19. Layer Diagnostics matches? Yes, final PRF viewport received1/rendered1 and persisted1. Initial async aggregate discrepancy corrected.
20. Radar P0? Yes; JS radar-vs-aux priority tests pass, map layers remain below radar; matcher/direction unchanged.
21. Secret exposed? No new/public exposure detected. One pre-existing Git-ignored private environment backup contains a secret match; preserved privately without printing values. See SECURITY_REVIEW.md; this is not a claim of zero secrets anywhere on disk.
22. READY? No: NOT_READY_FOR_PHYSICAL_TEST.

## Validation
Baseline81 JS/71 Python+selftest PASS. Final single full round83 JS/85 Python, selftest, compile, PostgreSQL compatibility all PASS. Only targeted browser rechecks followed reproducible selection/diagnostic/instrumentation failures; suites not looped. Test mocks are policy tests only. PostgreSQL controlled fixture rows removed from isolated branch, not readiness evidence. Final UI static counter correction checked through actual map->Admin persistence, without rerunning already-passed suites. No field GPS/voice test performed.

## Remaining blockers
{blockers}

Evidence and source-specific terms are documented in SOURCE_STATUS.md, SOURCE_ENDPOINT_VALIDATION.md, PRF_COORDINATE_REVIEW.md, SIBH_FRESHNESS_ANALYSIS.md, ANTT_REVIEW.md, MAP_REAL_DATA_VALIDATION.md, ADMIN_REAL_DATA_VALIDATION.md, SECURITY_REVIEW.md and TEST_RESULTS.json. Freshness metrics are capture-time snapshots and naturally expire; this report does not keep a collector running.
''')
results={'readiness':'NOT_READY_FOR_PHYSICAL_TEST','closed_at':now,'baseline':{'javascript':81,'python':71,'selftest':'PASS'},'final':{'javascript':83,'python':85,'exit_codes':exits,'postgres':'PASS','radar_P0':True},'source_status_counts':statuses,'real_collections':3,'partially_public_integrations':2,'fully_production_ready':0,'real_events':0,'prf':{'total':27,'approved':12,'blocked':15,'conflicts':5},'antt':{'retained':73,'approved':66,'conflicts':7},'sibh':sibh,'map':{'real_layers':2,'eligible_statewide':78,'toll_viewport_rendered':1,'prf_viewport_rendered':1,'first_prf_candidate_collision_suppressed':True},'route':browser['route'],'admin':{'sources':9,'counts_match':True,'client_rendered':1},'fixtures':{'real_database_rows':fixtures,'policy_test_only':True,'prior_11_types_without_real_evidence':8,'prior_11_types_without_approved_map_evidence':9},'production_modified':False,'push':False,'deploy':False,'postgres_branch':'br-green-frost-b4ubujn6','screenshots':['antt-tolls-real-mobile.png','prf-approved-real-mobile.png','admin-real-diagnostics.png']}
write('TEST_RESULTS.json',json.dumps(results,indent=2,ensure_ascii=False))
print('Reports written; readiness NOT_READY_FOR_PHYSICAL_TEST')
