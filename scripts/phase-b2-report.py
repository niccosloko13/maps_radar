"""Close B.2 from actual recorded evidence, with an explicitly limited test gate."""
import json,sqlite3,subprocess,hashlib,zipfile
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'artifacts/navigation-intelligence-v3-phase-b2'
def read(n):return json.loads((A/n).read_text(encoding='utf-8-sig'))
def write(n,t):(A/n).write_text(t.strip()+'\n',encoding='utf-8')
def table(rows,keys):
 def fmt(v):return str(v if v is not None else 'NOT_AVAILABLE').replace('|','/').replace('\n',' ')
 return '| '+' | '.join(keys)+' |\n|'+'|'.join(['---']*len(keys))+'|\n'+'\n'.join('| '+' | '.join(fmt(r.get(k)) for k in keys)+' |' for r in rows)
now=datetime.now(timezone.utc).isoformat();collect=read('collection-results.json');coverage=read('route-coverage.json');fresh=read('freshness-results.json');browser=read('browser-results.json');security=read('security-results.json');pg=read('postgres-tests.json');exits=read('final-exits.json');prf=read('prf-resolution.json');conflicts=read('antt-conflicts.json');health=collect['health'];status=dict(Counter(s['status'] for s in health));checkpoint=read('CHECKPOINT.json')
assert all(v==0 for v in exits.values());assert len(browser['route']['eligible_items'])==1
assert browser['route']['eligible_items'][0]['navigation_eligible'] is True
assert not browser['errors'];assert security['public_matching_paths']==[];assert security['history_matching_blob_ids']==[]
assert pg['legacy_unchanged']
client=json.loads(browser['admin']['diagnostics']['clients'][0]['payload_json'])
assert client['sources']['official-support']['eligible_route']==client['sources']['official-support']['rendered']==1
with sqlite3.connect(A/'private/validation.sqlite') as c:
 fixtures=c.execute("SELECT count(*) FROM road_event WHERE event_id LIKE '%TEST%' OR payload_json LIKE '%\"TEST\"%'").fetchone()[0]
 assert fixtures==0
 tolls=[json.loads(r[0]) for r in c.execute("SELECT payload_json FROM road_event WHERE source_id='antt-tolls'")]
 exact_duplicates=len(tolls)-len({json.dumps(r,sort_keys=True) for r in tolls});sites=len({(r['rodovia'],r['km_m'],r['latitude'],r['longitude']) for r in tolls})
new_files=[]
with zipfile.ZipFile(A/'private/checkpoint.zip') as z:
 old={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
 for base in ['app','road_data','scripts','tools']:
  for p in (ROOT/base).rglob('*'):
   if p.suffix not in ('.py','.js','.cjs','.html','.css','.svg'):continue
   n=p.relative_to(ROOT).as_posix()
   if hashlib.sha256(p.read_bytes()).hexdigest()!=old.get(n):new_files.append(n)
 for n in ['.gitignore','selftest.py','test_artesp_assets.py']:
  p=ROOT/n
  if hashlib.sha256(p.read_bytes()).hexdigest()!=old.get(n):new_files.append(n)
write('FILES_CHANGED.json',json.dumps(sorted(set(new_files)),indent=2))
write('SOURCE_STATUS.md',f'''# B.2 source status
Capture time{datetime.fromtimestamp(collect['at'],timezone.utc).isoformat()}. All states are explicit; no generic 'not operational'. Collector sync success is not the same as source readiness.

{table(health,['source_id','status','record_count','coordinate_approved','coordinate_blocked','freshness_status','freshness_kind','last_attempt_at','last_success_at','last_source_timestamp','blocker','next_action'])}

Totals:{json.dumps(status)}. HEALTHY0; DEGRADED4; blocked/auth5. Operational source subsets: ANTT,PRF,ARTESP toll assets,ARTESP SAU assets; SIBH diagnostic collection only. No ARTESP CCM incident/intervention authentication occurred. No new source registry entries (still9).

{table(browser['admin']['diagnostics']['counts'],['source_id','event_type','normalized','active','eligible_map','blocked_map'])}

## Freshness/category contract
ANTT/PRF/ARTESP assets use INFRASTRUCTURE_FRESHNESS, daily collection cadence. Last content revision remains separate; no blanket age expiry for infrastructure. ARTESP assets latest resource revision2025-05-30, not a live operation guarantee, and no periodic update frequency stated. A recently checked old snapshot is not a claim of current field inspection. Content age is visible in details/Admin. All4 collectors FRESH at capture. Source remains DEGRADED for unapproved coordinates. ARTESP incident/intervention uses EVENT_FRESHNESS with real event termination/expiry; no live payload obtained. SIBH uses OBSERVATION_FRESHNESS from max_date/measurement_gap, never ingestion time. Existing B.1 thresholds unchanged.

Current SIBH capture:{json.dumps(fresh['sibh_states'])}; current-road observations{fresh['sibh_current']}; retained{fresh['sibh_inventory']}. These are later than the immediate collection counts and naturally age. No scheduler was installed. Collection does not grant publication rights.

Licensing:[ANTT toll](https://dados.antt.gov.br/dataset/praca-de-pedagio) CC BY; [ANTT PRF coordinates](https://dados.antt.gov.br/dataset/prf) CC BY; original PRF directory CC BY-ND3.0 retained unchanged. [ARTESP asset catalog](https://dadosabertos.artesp.sp.gov.br/dataset/cadastro-de-ativos) license_id=cc-by, version unspecified; [portal terms](https://dadosabertos.artesp.sp.gov.br/terms) allow attributed redistribution/integrity/no endorsement. API CCM license remains CC BY-NC4.0 and requires keys. SIBH,PMRv,Defesa Civil have no confirmed source-specific reuse grant and remain blocked. No portal footer was treated as a license for an unrelated dataset.
''')
write('PRF_RESOLUTION_B2.md',f'''# PRF blocked-record review
All15 previously blocked records reviewed individually. Total27; approved14 (previous12); blocked13 (3 operational coordinate conflicts +10 administrative/unmapped records). Exactly2 resolutions, no change to global angular/distance/km tolerances.

{table(prf,['record','previous_status','new_status','road','km','municipality','lat','lon','evidence','reason'])}

Official engineering evidence: [ANTT monitoring report, December2024, pp11-12](https://www.gov.br/antt/pt-br/assuntos/rodovias/concessionarias/lista-de-concessoes/autopista-regis-bittencourt/relatorios/relatorios-de-monitoracao/2024/rt_06_116_sp_275_4_k12_517.pdf). It independently identifies Barra do Turvo BR116 km525.700 north and Miracatu km387.500 north, matching precise ANTT inventory coordinates and local municipality polygons. Coarse/conflicting PRF directory km525/km386 remains in original payload; published read model uses corroborated precise km. Neither coordinate was inferred from a geocoder.

BR153 candidate coordinates for Guaicara,Marilia,Ourinhos still disagree with municipal polygons; no source correction or calibrated authoritative coordinate was found. No speculative swapping. Administrative offices are not operational posts; address/road-km alone does not locate their buildings. Existing approved12 retained. JSON evidence prf-resolution.json; B.1 full original evidence retained privately and in its reports. Approved corrections are applied only to the B.2 clone through scripts/phase-b2-review.py; not production.
''')
write('ANTT_CONFLICT_RESOLUTION.md',f'''# ANTT seven-conflict review
73 source records preserved;66 spatial approvals;7 coordinate conflicts remain;0 coordinate conflicts resolved. Source rows describe distinct names/directions/structures: no automatic merge by equal coordinate/km/road.

{table(conflicts,['name','road','km','municipality','polygon_municipality','lat','lon','direction','track','concessionaire','source_status','classification','spatial_resolution','reason'])}

Three co-located records are classified FREE_FLOW_MULTI_PORTAL because official names identify separate portals; this resolves their semantic identity, NOT their coordinates. The other4 remain CONFLICT_UNRESOLVED spatially. Official concession tariff page confirms named Aruja/Guararema sites, but does not establish precise coordinates; no coordinate promotion from text. [ANTT source](https://dados.antt.gov.br/dataset/praca-de-pedagio), [RioSP tariff source](https://www.gov.br/antt/pt-br/assuntos/rodovias/concessionarias/lista-de-concessoes/ccr-rio-sp/tarifas-de-pedagio).

Exact raw duplicates{exact_duplicates};{sites} unique raw road/km/coordinate groups,44 additional co-located records. Some pairs are SAME_SITE_DIFFERENT_DIRECTION; differently named structures remain separate. Actual number of independently surveyed physical sites is NOT CONFIRMED:29 coordinate groups are not proof of29 physical plazas. Operational inventory has73 source entities, not73 certified distinct sites. All7 stay hidden from automatic map publication. TRUE_DUPLICATE was not asserted for any raw row.
''')
write('SIBH_LICENSE_REVIEW.md','''# SIBH license/publication
SIBH_PUBLICATION = BLOCKED_LICENSE

Owner: SP Aguas, technical portal CTH/Hidrologia. [Official hydrology portal](https://www.spaguas.sp.gov.br/site/hidrologia/), [SIBH](https://apps.spaguas.sp.gov.br/sibh/), [official FAQ](https://www.spaguas.sp.gov.br/site/perguntas-frequentes/). These establish public consultation and institutional ownership, not an explicit license to redistribute current station observations in Relas.

Terms/license: no source-specific grant tied to this live measurements endpoint was confirmed. Portal pages display reserved rights. Official open-data catalog probe for SIBH failed; a license on another dataset (e.g. UGRHI boundaries) cannot be transferred to live rain observations. No permission assumed from accessibility or absence of prohibition.

Attribution if later authorized: SP Aguas/CTH-Hidrologia, station identifier, observation time and measurement window. Reuse permission: NOT_CONFIRMED. Commercial restriction: UNKNOWN. Redistribution restriction: UNKNOWN; not approved. B.2 did not contact anyone, accept private terms, bypass access controls, or publish raw rain observations. Existing diagnostic capture retained internally for technical analysis; this does not certify unrestricted internal-use permission either.

New real request HTTP200:1021 received,1016 SP normalized;7 new IDs,1009 updated,90 expired;1120 retained IDs. Publication remains0 even when current readings exist. Public weather endpoint was actually checked and returned0 features with BLOCKED_LICENSE. An observation is never converted into a regional rain hazard. Need official written/data-catalog permission tied to these observations before changing the gate.
''')
for row in coverage['rows']:
 sid=row['source'];row['records_rendered']=browser['route']['diagnostics']['sources'][sid]['rendered'];row['records_alerted']=browser['route']['diagnostics']['sources'][sid]['alerted']
write('ROUTE_COVERAGE.md',f'''# Required real route
Praia Grande(-24.0058,-46.4028) -> Sao Bernardo do Campo(-23.6914,-46.5646). Application /api/route actually returned56,050m,1248 vertices; not a fixture, straight line, or manually redrawn route. Public start/end test landmarks only; no personal track stored.

{table(coverage['rows'],['source','records_statewide','records_spatially_eligible','records_map_eligible','records_intersecting_corridor','records_direction_eligible','records_initial_window','records_rendered','records_alerted','reason_for_zero'])}

Approved static geometries and public eligibility are different columns. Intersecting counts are geometry-only diagnostic counterfactuals with direction removed; NEVER published as eligible data. Buffer remains35m for infrastructure,120m weather; initial ROAD_MODE speed20m/s ahead window24km. No buffer/angle/progress threshold relaxed.

Actual route eligible result:1 SAU official-support:4169, SP160 km62.1 north, Cubatao. Distance to route20.8m; ahead11,161.1m. API -> DB -> source -> symbol -> correct detail -> corridor -> frontend auxiliary P5,voice_default=false. Actual viewport rendered1 and persisted Admin client received1/route1/rendered1. Alerted0: no field GPS or near-alert voice event simulated as live driving evidence.

ARTESP toll inventory has1 geometric intersection, then0 direction-eligible: Riacho Grande is southbound and the route is northbound. Correct DIRECTION_FILTER; not a geometry mismatch. Other plazas off this alignment not forced in. ANTT nearest approved asset18,073.49m off route; PRF nearest30,915.63m: NO_SOURCE_COVERAGE by geography, not a35m buffer bug. No evidence of KM_TO_COORDINATE_ERROR or ROAD_REFERENCE_MISMATCH in the actual SAU match. Road refs preserved; no exact road-ref equality test was invented where none exists in matcher.

ARTESP CCM0 = missing keys, not 'no incidents'. SIBH0public = license gate, not 'no rain'. PMRv/Defesa Civil0 = no licensed operational endpoint. Auxiliary zero has therefore been eliminated honestly for this route, without changing filters. Broader event/weather/full toll coverage remains uncertified.
''')
maprows=[]
for sid,v in browser['layers'].items():
 good=next((x for x in v['attempts'] if x.get('detail_correct')),None);last=good or v['attempts'][-1]
 maprows.append(dict(source=sid,statewide_eligible=v['statewide_eligible'],received=last['received'],normalized=last['normalized'],eligible=last['eligible'],rendered=max(x['rendered'] for x in v['attempts']),clicked=bool(good),detail_correct=bool(good),source_shown=bool(good and good['source_shown']),freshness_shown=bool(good and good['freshness_shown'])))
write('MAP_REAL_DATA_VALIDATION.md',f'''# Real-map validation
390x844 mobile;1440x900 Admin. Fresh browser context with service worker blocked to inspect actual current assets; cache version233 also bumped for normal updates. Legacy radar reads came from existing read-only public API; new auxiliary records came ONLY from isolated real B.2 database. No fixtures seeded.

{table(maprows,['source','statewide_eligible','received','normalized','eligible','rendered','clicked','detail_correct','source_shown','freshness_shown'])}

Real layers rendered and correctly clicked this round:2 (PRF and SAU support). Do not count4 just because4 sources return features. ANTT toll0 in three sampled viewports; ARTESP toll0 in three sampled viewports. Bounded targeted diagnosis confirmed road-toll icon loaded and eligible source features exist, but colocated legacy community toll symbols take collision placement. See toll-collision-diagnostics.json. No radar was hidden and no icon-allow-overlap workaround added. This is an unresolved visual integration limitation, not evidence that official toll data is absent. B.1 prior ANTT screenshot remains historical evidence, not a new B.2 pass.

Unavailable real layers: ARTESP CCM events/interventions0AUTH_REQUIRED; SIBH0BLOCKED_LICENSE; Defesa Civil0BLOCKED_LICENSE/endpoint. No fixture substitutes counted.

Screenshots: [PRF](prf-sp-real-mobile.png), [SAU detail](official-support-real-mobile.png), [real route SAU](real-route-sau.png), [Admin diagnostics](admin-real-diagnostics.png). Route plot/auxiliary eligibility tested, not actual GPS movement or a physical driver alert. Browser pageerrors0. No repeated full browser suite; one bounded targeted collision diagnosis after reproducible failures.
''')
write('ADMIN_VALIDATION.md',f'''# Admin validation
Existing login flow actually passed in local isolated server. Authentication code unchanged; dedicated test-process credential is not a production credential. All9 sources visible with explicit source state/freshness/blocker/next_action. Added map_eligible and route_eligible to existing source tables; route count explicitly scoped to last captured client corridor, NOT an all-roads global count. No generic 'not operational'.

Global counts: ANTT73/66eligible;PRF27/14eligible;ARTESP toll239/211eligible;SAU249retained,246active,225eligible;SIBH1120retained/0public. Source geographic approved totals may include3 inactive SAU entries; inactive records cannot publish. Raw ARTESP workbook34396 rows was filtered to existing toll and SAU components only; radar/equipment data was not ingested.

Captured client diagnostics POST200. SAU route_eligible1/rendered1, alert0; exact persisted client values agree with map. Other route-source rendered0 is accurate, not replaced by statewide/API totals. Source/log/diagnostic tabs actually opened. BLOCKED_COORDINATES exists in policy for no approved PRF coordinates; current partially approved sources correctly DEGRADED. Prior HTTP/schema failures keep last valid snapshots; new adapter fails closed on license/header/empty-subset/unknown-status changes.

Evidence browser-results.json:admin; collection-results.json; route-coverage.json. Latest source-review/ingestion/freshness dates shown independently. Admin event lists are bounded; use source filters rather than infer global totals from one paginated/bounded table. No production Admin changes deployed.
''')
write('SECURITY_REVIEW.md',f'''# Security - immediate credential review
CREDENTIAL_ROTATION_REQUIRED = YES

Backup remains private/Git-ignored and untracked. It was not printed, deleted or copied into any public report. Four stored PostgreSQL connection settings still passed read-only SELECT1. Corresponding credentials, full URLs AND extracted database passwords were searched in all{security['history_blobs_examined']} locally reachable historical blobs:0matches. Public examined artifact/frontend matches0. Scope cannot prove absence from deleted remote history, remote forks or unexamined binary files.

OIDC token's decoded exp is expired; signature/server validity not asserted. No authenticated Vercel mutation attempted. No external credential rotation performed. Rotation recommended/required as a security maintenance action because active credentials survive in an old backup: owner should rotate affected Neon role password(s), update authorized runtime environments, verify reads/writes, then decide backup retention. Do not paste values in chat/Git. Rotation is outside B.2 authorization; no attempt made.

Source APIs/metadata contain no keys. ARTESP key statuses NOT_CONFIGURED only. Query errors/logs use class/status and allowlisted rate/terms headers. .env/.env.local/private database/backups are ignored; .env.example remains placeholders. Temporary test-branch URL removed after tests. Isolated PostgreSQL fixture rows explicitly TEST and cleaned; real SQLite fixture rows{fixtures}. Reviewed point-detail/diagnostic screenshots show no credential fields. No push/deploy, no production writes. Exact scan scope/evidence security-results.json; values never serialized there.
''')
write('PHYSICAL_TEST_PLAN.md',r'''# Controlled physical-test plan - not executed
Status: READY_FOR_PHYSICAL_TEST_WITH_LIMITATIONS for the scope below, NOT a full Phase B or production release certification.

Scope: radar P0, GPS, route progress/camera behavior and the one real northbound SAU on Praia Grande -> Sao Bernardo. ARTESP live events, weather and official toll-symbol coexistence are NOT certified and must not be tested as if available. Read all source warnings; absence of alerts means no coverage, never a clear road. This plan itself starts no process, telemetry, location permission, push or deployment.

## Runtime and device preflight (stationary)
Use the B.2 isolated real dataset, not the old deployed code or fixture server. From project root:
```
.\.venv\Scripts\python.exe scripts/phase-b2-real-server.py
```
It binds127.0.0.1:8820, uses private/validation.sqlite and read-only legacy radar proxy; internet required. It does not import the new assets into your personal database. Local Admin credential is confined to that loopback review process. Do not expose this development server publicly.

For an Android test with laptop/USB and Android Platform Tools already available, run manually:
```
adb reverse tcp:8820 tcp:8820
```
Open http://localhost:8820 on the phone, grant GPS; verify window.isSecureContext === true and navigator.geolocation exists. Alternatively use the project's existing trusted HTTPS setup, with a certificate trusted by the device, after separately configuring the intended real-data runtime. Plain LAN HTTP on iPhone/Android is NOT an approved GPS test. The current isolated review script is loopback-only; an iPhone requires separately prepared trusted access and is NOT certified by this run. Do not bypass certificate checks or disable browser security.

Stop preflight if GPS denied/unavailable, API fails, latest bundle233 absent, actual source state is unclear, or the real SAU fails to load. Browser automation was not a physical-device GPS test. No test trip is automatically authorized by a passing unit test.

Set route using real search: Praia Grande -> Sao Bernardo do Campo; select Estrada auxiliary preset (default Essential hides SAU intentionally), preserve radar filters. Verify SAU at SP160 km62.1 north, Cubatao. Current snapshot is infrastructure updated2025-05-30; presence/accessibility on site is unverified. No obligation to stop on a motorway or enter an unsafe access. Never interact with the phone while driving; a passenger operates logging/UI or stop safely.

## Telemetry commands (stationary console only)
Existing APIs, no new telemetry feature:
```
relas.locationTelemetry.start();
relas.navigationTelemetry.start();
// Stop after safely parking:
relas.locationTelemetry.stop();
relas.navigationTelemetry.stop();
// Export locally; contains personal GPS/route data. Keep outside Git/repository.
const saved = JSON.stringify({location:JSON.parse(relas.locationTelemetry.exportJSON()),navigation:JSON.parse(relas.navigationTelemetry.exportJSON())});
const url = URL.createObjectURL(new Blob([saved],{type:'application/json'}));
const link=document.createElement('a');link.href=url;link.download='relas-private-field-session.json';link.click();URL.revokeObjectURL(url);
```
Verify APIs exist before starting. Do not enable simulation/replay or use fixture rows. Do not commit/export the personal trace into public artifacts. After collection, stop the server with Ctrl+C and remove USB forwarding with adb reverse --remove tcp:8820.

## Observe and record
- GPS accuracy, heading while walking/driving/stopped; permission errors and recovery.
- ROAD_MODE, route progress monotonicity, reroute behavior, camera lag/jumps and recenter.
- Radar alert stays P0, correct side/direction and optional audio; no auxiliary interruption.
- SAU known coordinate appears, correct source/date/detail; P5 and no default voice. A far-away eligible corridor item need not produce a near-driver alert.
- PRF does not occur on this route with current coverage; do not expect a fabricated post.
- Riacho Grande toll is southbound: no toll charge alert on northbound route. Official toll symbols have a documented collision limitation; do not count this as validated.
- Traffic/ARTESP incidents and rain/Defesa Civil are unavailable: visible source status must explain this; no stale/current weather inference.
- Audio starts only after an explicit user action; inspect overspeed/radar and wrong-direction suppression while stationary/replaying your private recording later.
- Stop for false positives, wrong-side alerts, GPS jumping to parallel roads, voice contention, or unreadable/blocked UI. Do not continue driving to diagnose.

Test result remains pending until actual device observations are reviewed. This plan does not certify live weather, full toll coverage, emergency information, iPhone support, deployed code, or FULL_PHASE_B_READY.
''')
state='READY_FOR_PHYSICAL_TEST_WITH_LIMITATIONS'
write('REPORT.md',f'''# RELAS Phase B.2 - coverage unlock
**{state}**

This is a narrowly scoped, controlled LOCAL physical-test candidate (radar/GPS/navigation + one real SAU), not FULL_PHASE_B_READY, not a production deployment, and not approval of all source integrations. Public deployed code was not changed. First test requires stationary device preflight from PHYSICAL_TEST_PLAN.md.

Closed{now}. Branch{checkpoint['branch']}; base{checkpoint['base_commit']}; checkpoint SHA256{checkpoint['checkpoint_sha256']}. Existing valid uncommitted work retained. B.1 clone backed up and copied to B.2; personal SQLite untouched. No push/deploy/commit. File changes FILES_CHANGED.json.

## What changed and what actually works
Resolved existing registered sources artesp-tolls and official-support through the licensed ARTESP Cadastro de Ativos, not the protected CCM incident API. Added bounded XLSX parsing/strict source-specific normalization, stable IDs, local municipality checks, active status, provenance/snapshot preservation, daily polling gate, additive existing location-review path, public-map and navigation integration. Only toll/SAU components included; radar and all other workbook equipment excluded. No new registry source, product feature or UI redesign.

Real HTTP200 workbook34396 rows ->239 toll records (211map-eligible) +249SAU records (246active,225map-eligible). Source content date2025-05-30 remains visible; latest official inventory is not a guarantee of present field operation. Both source subsets DEGRADED because some coordinates fail validation. Admin exposes map/last-client-route counts and blockers. Two PRF exact-km conflicts resolved through independent official engineering evidence without relaxing global tolerances. Cache233. No authentication/Finder/Precision/radar matcher/direction changes.

The required real56.05km route now returns1 eligible SAU, not0. Browser confirms actual source symbol, correct detail/attribution/freshness and frontend P5 auxiliary. API source/current map and Admin persisted client diagnostics all report SAU route1/rendered1. No field GPS/audio alert claimed; alerted0. One toll geometric intersection correctly rejected for opposite direction. Other zero results explained per-source in ROUTE_COVERAGE.md.

## Required answers
1. ARTESP keys configured? No; both NOT_CONFIGURED.
2. ARTESP tested really? Authenticated CCM NOT_TESTED/AUTH_REQUIRED. Public licensed ARTESP asset catalog/workbook YES HTTP200 through normalizer/DB/Admin/map/corridor (SAU); toll rendering has limitation below.
3. Real occurrences?0 collected; upstream count unknown.
4. Real interventions?0 collected; upstream count unknown.
5. PRF total?27.
6. PRF approved?14 OFFICIAL_COORDINATE (up from12).
7. PRF blocked?13 (3 operational conflicts,10 administrative/unmapped).
8. ANTT records?73, all preserved;66 approved spatially.
9. ANTT conflicts resolved?0 of7 spatially. Three free-flow rows semantically identified as separate portals, still coordinate-blocked.
10. Physical/operational entities?73 source entities,29 coordinate groups; exact duplicates0. Physical distinct-site count NOT_CONFIRMED. Do not present29 groups as a surveyed count.
11. SIBH license confirmed?No.
12. SIBH public?No, BLOCKED_LICENSE.
13. SIBH fresh?{fresh['sibh_states'].get('FRESH',0)} FRESH,{fresh['sibh_states'].get('AGING',0)}AGING,{fresh['sibh_states'].get('STALE',0)}STALE at{fresh['captured_at']};{fresh['sibh_current']}current-road observations. Counts age naturally.
14. HEALTHY?None (0).
15. DEGRADED?ANTT tolls,PRF,ARTESP toll assets,SAU support (4 partial sources).
16. BLOCKED?ARTESP occurrence+intervention AUTH_REQUIRED;SIBH,PMRv,Defesa Civil BLOCKED_LICENSE (5).
17. Objects intersecting target route?2 public-eligible geometry intersections before direction (1toll+1SAU);1 direction/window-eligible SAU. No rain/events counted as fixtures.
18. Map?PRF and SAU real symbols/details verified this round. ANTT/ARTESP official toll samples0rendered due legacy community symbol collision, not passed. In-route viewport has1SAU.
19. Admin?All9 sources, accurate global/viewport/route counts, logs and blockers. Actual collected records from5 sources; not9 operational integrations.
20. Why zeros?Geographic coverage forANTT/PRF;opposite direction forARTESP toll;missing auth forCCM;license/endpoint forweather/PMRv/Defesa Civil. Detailed measurements in ROUTE_COVERAGE.md.
21. Radar P0?Yes; priority tests pass; new layers remain below radar; matcher/direction/voice arbitration unchanged.
22. Public secret?No matches among examined public files or locally reachable history, including extracted DB passwords. Scan limitations documented.
23. Rotate old credentials?CREDENTIAL_ROTATION_REQUIRED=YES; active DB settings passed SELECT1. Owner action required; no external credentials changed.
24. Final state?{state}, only for the explicitly limited LOCAL test below. FULL_PHASE_B_READY is not claimed.

## Formal first-test limitations / gate decision
Nonessential to the selected northbound radar/GPS/SAU test: missing CCM keys; SIBH publication license; PMRv/Defesa Civil; other unmapped PRF/ANTT conflicts outside route; official toll-symbol coexistence (the intersecting charged plaza is opposite-direction, and toll coverage is excluded from the approved first-test scope). These remain unresolved, not silently waived for full Phase B. Source warnings and zero semantics remain explicit. Four source subsets are partial/DEGRADED, not fully operational HEALTHY.

Toll-symbol collision is a real unresolved visual integration: three ANTT and three ARTESP samples were hidden by colocated community toll symbols; a bounded diagnostic verified loaded SVG/source and identified collider layers. No overlap workaround or broad reconciliation redesign was attempted. Do not use this build to certify official toll alerts/details. Live weather/traffic must not be relied on. New source database reviews/records are in isolated validation runtime ONLY; personal/production database provisioning remains separate.

Stationary device preflight is mandatory; Android USB loopback method documented, no iPhone trusted-HTTPS setup certified here. If secure context/GPS/API/data checks fail, do NOT commence the field test. Credential rotation recommended before public deployment; no known public exposure found. These conditions do not authorize public release or claim a successful physical trip.

## Validation
Baseline83 JS +38 relevant Python PASS. Final single relevant round83 JS +92 Python PASS, selftest PASS, Python/JS syntax PASS, isolated PostgreSQL compatibility PASS (including new asset approval persistence), existing legacy counts unchanged. Compileall literal glob emitted 'cannot list' for a script glob; explicit py_compile on relevant scripts/modules subsequently PASS. No full suites repeated. One real browser run plus one bounded toll-collision diagnosis; pageerrors0. Failures documented rather than looped into green. No field GPS/voice trip executed. Fixture rows in real database0; compatibility fixtures explicitly isolated/cleaned and never coverage evidence.

## Artifacts
SOURCE_STATUS.md;PRF_RESOLUTION_B2.md;ANTT_CONFLICT_RESOLUTION.md;SIBH_LICENSE_REVIEW.md;ROUTE_COVERAGE.md;MAP_REAL_DATA_VALIDATION.md;ADMIN_VALIDATION.md;SECURITY_REVIEW.md;PHYSICAL_TEST_PLAN.md;TEST_RESULTS.json. Private snapshots/raw workbook/route/checkpoint stay Git-ignored. Temporary Neon URL removed and review server stopped at closure.
''')
results={'final_state':state,'full_phase_b_ready':False,'approved_scope':'controlled LOCAL radar/GPS/route/SAU test only; stationary device preflight required','baseline':{'javascript':83,'relevant_python':38},'final_tests':{'javascript':83,'python':92,'selftest':'PASS','syntax':'PASS','postgres':'PASS','exit_codes':exits,'browser_pageerrors':browser['errors']},'artesp_keys':read('ARTESP_ENVIRONMENT.json'),'artesp_ccm_live_tested':False,'occurrences':0,'interventions':0,'prf':{'total':27,'approved':14,'blocked':13,'resolved':2},'antt':{'retained':73,'approved':66,'coordinate_conflicts':7,'spatially_resolved':0,'exact_duplicates':exact_duplicates,'coordinate_groups':sites,'physical_site_count':None},'artesp_assets':{'workbook_rows':34396,'tolls':239,'toll_map_eligible':211,'sau':249,'sau_active':246,'sau_map_eligible':225,'latest_resource_revision':'2025-05-30'},'sibh':{'inventory':fresh['sibh_inventory'],'states':fresh['sibh_states'],'current':fresh['sibh_current'],'captured_at':fresh['captured_at'],'publication':'BLOCKED_LICENSE'},'source_status_counts':status,'route':coverage['rows'],'route_objects_eligible':1,'route_geometry_intersections_before_direction':2,'route_objects_rendered':1,'actual_field_alerts':0,'map_real_layers_rendered_this_round':2,'official_toll_map_smoke':'FAILED_COLLISION_WITH_LEGACY_COMMUNITY_TOLL_SYMBOLS','admin_sources':9,'admin_matches_map':True,'radar_P0':True,'security':security,'real_database_fixture_rows':fixtures,'production_modified':False,'push':False,'deploy':False,'field_test_executed':False,'known_limitations':['missing ARTESP CCM keys','SIBH license unconfirmed','PMRv/Defesa Civil source/license blocked','13 PRF and7 ANTT records blocked','official toll symbol collision unresolved','static ARTESP assets last revised2025-05-30','isolated runtime only; device secure-context preflight required','rotation of active backup credentials requires owner action']}
write('TEST_RESULTS.json',json.dumps(results,indent=2,ensure_ascii=False));print(state+';11 required artifacts generated')
