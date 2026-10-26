# RELAS Phase B.2 - coverage unlock
**READY_FOR_PHYSICAL_TEST_WITH_LIMITATIONS**

This is a narrowly scoped, controlled LOCAL physical-test candidate (radar/GPS/navigation + one real SAU), not FULL_PHASE_B_READY, not a production deployment, and not approval of all source integrations. Public deployed code was not changed. First test requires stationary device preflight from PHYSICAL_TEST_PLAN.md.

Closed2026-10-26T05:31:57.584231+00:00. Branchfeat/navigation-v3-phase-b1; base4943cd4f4be8db6817222433e995974bd8305a37; checkpoint SHA256dfc92e13f9fcfa57dc53b49dd47e73455ef54d136e67ac549f245d558b37f159. Existing valid uncommitted work retained. B.1 clone backed up and copied to B.2; personal SQLite untouched. No push/deploy/commit. File changes FILES_CHANGED.json.

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
13. SIBH fresh?991 FRESH,20AGING,109STALE at2026-10-26T05:25:33.610487+00:00;957current-road observations. Counts age naturally.
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
24. Final state?READY_FOR_PHYSICAL_TEST_WITH_LIMITATIONS, only for the explicitly limited LOCAL test below. FULL_PHASE_B_READY is not claimed.

## Formal first-test limitations / gate decision
Nonessential to the selected northbound radar/GPS/SAU test: missing CCM keys; SIBH publication license; PMRv/Defesa Civil; other unmapped PRF/ANTT conflicts outside route; official toll-symbol coexistence (the intersecting charged plaza is opposite-direction, and toll coverage is excluded from the approved first-test scope). These remain unresolved, not silently waived for full Phase B. Source warnings and zero semantics remain explicit. Four source subsets are partial/DEGRADED, not fully operational HEALTHY.

Toll-symbol collision is a real unresolved visual integration: three ANTT and three ARTESP samples were hidden by colocated community toll symbols; a bounded diagnostic verified loaded SVG/source and identified collider layers. No overlap workaround or broad reconciliation redesign was attempted. Do not use this build to certify official toll alerts/details. Live weather/traffic must not be relied on. New source database reviews/records are in isolated validation runtime ONLY; personal/production database provisioning remains separate.

Stationary device preflight is mandatory; Android USB loopback method documented, no iPhone trusted-HTTPS setup certified here. If secure context/GPS/API/data checks fail, do NOT commence the field test. Credential rotation recommended before public deployment; no known public exposure found. These conditions do not authorize public release or claim a successful physical trip.

## Validation
Baseline83 JS +38 relevant Python PASS. Final single relevant round83 JS +92 Python PASS, selftest PASS, Python/JS syntax PASS, isolated PostgreSQL compatibility PASS (including new asset approval persistence), existing legacy counts unchanged. Compileall literal glob emitted 'cannot list' for a script glob; explicit py_compile on relevant scripts/modules subsequently PASS. No full suites repeated. One real browser run plus one bounded toll-collision diagnosis; pageerrors0. Failures documented rather than looped into green. No field GPS/voice trip executed. Fixture rows in real database0; compatibility fixtures explicitly isolated/cleaned and never coverage evidence.

## Artifacts
SOURCE_STATUS.md;PRF_RESOLUTION_B2.md;ANTT_CONFLICT_RESOLUTION.md;SIBH_LICENSE_REVIEW.md;ROUTE_COVERAGE.md;MAP_REAL_DATA_VALIDATION.md;ADMIN_VALIDATION.md;SECURITY_REVIEW.md;PHYSICAL_TEST_PLAN.md;TEST_RESULTS.json. Private snapshots/raw workbook/route/checkpoint stay Git-ignored. Temporary Neon URL removed and review server stopped at closure.
