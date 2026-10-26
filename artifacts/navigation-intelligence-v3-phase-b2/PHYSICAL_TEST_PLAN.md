# Controlled physical-test plan - not executed
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
