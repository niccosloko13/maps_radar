# Relas B.2 production publication

Published at the user's explicit request on 2026-10-26. Earlier B/B.1/B.2 reports are historical snapshots of their no-deploy sessions; this release record supersedes only their deployment status, not their known limitations or physical-test results.

- Application commit: `ee5506c` on `feat/navigation-v3-phase-b1`, pushed to `niccosloko13/maps_radar`.
- Project: `nexus-a534/maps_radar`, ID `prj_3eXFTKDsAxx8GMMyGVU3Wgg1EJ36`.
- Production: https://mapsradar-three.vercel.app/
- Exact deployed build: https://mapsradar-ptp0sjuxh-nexus-a534.vercel.app
- Deployment ID: `dpl_7amRrsPHRHkpd1VpgNDKHGFETQt6`.
- Release method: production build staged without assigning domains, 13 HTTP checks passed, then the same build promoted. Deployment Protection was preserved; authenticated Vercel CLI was used for the protected staged URL.
- Vercel build: READY, FastAPI/Python function, approximately 15.51MB. Input dry run: 165 files / 8,978,443bytes, no artifacts/private databases/environment files included.
- Assets: cache/bundle version233.

## Persistent data

Additive auxiliary schema `003-road-data-source-readiness` explicitly applied to Neon project `shy-art-03849128`, production branch `br-old-water-b4gz2ktq`, database `neondb`. The target was inspected before mutation and had no existing auxiliary tables. Reviewed real auxiliary tables were imported in one transaction using COPY; counts compared before commit. No legacy or authentication table writes, no reset, no fixture import, no personal SQLite deletion. Client viewport diagnostics were not copied as production observations.

Checkpoint branch before mutation: `relas-pre-b2-release-checkpoint`, ID `br-floral-haze-b4ey5j8q`, expires2026-11-02T23:59:59Z. It was created without a compute. Existing SQLite/checkpoints/backups were preserved. Temporary release connection file was removed after verification; no secret values are in this report.

Transferred: **1,708 real auxiliary records**, nine sources and nine reviewed source policies, provenance/evidence/history/location reviews. Public eligible infrastructure: **516** records:66ANTT tolls +14PRF +211ARTESP toll assets +225SAU. Source terms/coordinate gates remain enforced. SIBH observations remain diagnostic-only and naturally age; no current-rain assertion or publication license invented. This release does not install a recurring collector.

Legacy counts preserved:

| Table | Before | After |
|---|---:|---:|
| radars |196|196|
| radar_history |224|224|
| road_objects |6426|6426|
| source_registry |19|19|
| operation_logs |53|53|
| update_queue |4|4|
| manual_entries |0|0|
| community_batches |1|1|

The legacy `/api/road-objects` defaults to **mapped-only** and correctly returns6,419; seven inventory records lack coordinates. An initial smoke assertion incorrectly expected the entire6,426 inventory; it was corrected after reading the existing endpoint and independently querying PostgreSQL. Only that assertion/request was rechecked, not the full unit suites. No data was deleted to make counts agree.

## Verification

- Previous complete code suites:83JavaScript +92Python PASS; selftest/syntax/PostgreSQL compatibility PASS. No application code changed during release except the CLI migration output now reports the actual schema version.
- Staged deploy:13/13 HTTP checks passed: map, Admin page, assets, PostgreSQL health, radars, road objects, viewport features, source health, auxiliary infrastructure, weather license block, Admin API authentication guard, real route corridor.
- Verification helper's first Windows run had encoding and cmd.exe ampersand argument issues; fixed by invoking the cached Vercel Node entrypoint directly with UTF-8 decoding. These were test instrumentation failures, not application fixes.
- Public production alias: HTML200 with assets233; health200/PostgreSQL and expected legacy counts.
- Public production browser: no pageerrors or unexpected API failures. Real SAU `official-support:4169` received1/rendered1; clicked detail showed ARTESP source, north direction, Cubatao/SP160km62.1, static source revision and freshness. Screenshot: [production-sau-mobile.png](production-sau-mobile.png).
- Public production route: actual `/api/route` returned56,050m/1,248vertices; `/api/road-events/route` returned the real northbound SAU, navigation_eligible=true,20.8m from route.
- Admin login page visible; unauthenticated diagnostics API returned401. A production password login was not attempted or claimed: no credentials were guessed or exposed.
- Index security review:300files/~18.4MB initially examined; no actual known secret values/passwords or forbidden private/database paths. Follow-up evidence files also reviewed before their documentation commit.

Machine evidence: `staged-http-verification.json`, `production-browser-verification.json`, `production-data-publish.json`, `production-final-counts.json`, `release-index-security.json`.

## Limits and rollback

The first-test status remains **READY_FOR_PHYSICAL_TEST_WITH_LIMITATIONS**, not full Phase B readiness. ARTESP CCM keys are absent; SIBH/PMRv/Defesa Civil licensing/endpoints remain blocked; coordinate conflicts and official toll-symbol collisions remain documented. Static ARTESP content revision is2025-05-30; a successful recent fetch is not a fresh field inspection. No physical trip/GPS/audio test was performed by this release.

**CREDENTIAL_ROTATION_REQUIRED=YES** remains an owner action: active credentials survive in a private ignored backup. Nothing was rotated externally during publication and no matching public exposure was detected within the audited scope.

Application rollback: promote the previous production build `https://mapsradar-dfajlmzxa-nexus-a534.vercel.app` using the linked project's authenticated Vercel CLI. The auxiliary migration is additive and the previous application ignores those tables, so application rollback does not require dropping them. Do not restore a database branch or drop source tables automatically; inspect any subsequent writes first. The database checkpoint is available only until its documented expiry.
