# Required real route
Praia Grande(-24.0058,-46.4028) -> Sao Bernardo do Campo(-23.6914,-46.5646). Application /api/route actually returned56,050m,1248 vertices; not a fixture, straight line, or manually redrawn route. Public start/end test landmarks only; no personal track stored.

| source | records_statewide | records_spatially_eligible | records_map_eligible | records_intersecting_corridor | records_direction_eligible | records_initial_window | records_rendered | records_alerted | reason_for_zero |
|---|---|---|---|---|---|---|---|---|---|
| artesp-interventions | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | NO_SOURCE_COVERAGE: AUTH_REQUIRED |
| artesp-occurrences | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | NO_SOURCE_COVERAGE: AUTH_REQUIRED |
| antt-tolls | 73 | 66 | 66 | 0 | 0 | 0 | 0 | 0 | NO_SOURCE_COVERAGE: approved inventory geographically outside this route |
| artesp-tolls | 239 | 211 | 211 | 1 | 0 | 0 | 0 | 0 | DIRECTION_FILTER |
| official-support | 249 | 228 | 225 | 1 | 1 | 1 | 1 | 0 | NOT_AVAILABLE |
| pmrv-sp | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | LICENSE_BLOCK; NO_SOURCE_COVERAGE |
| prf-sp | 27 | 14 | 14 | 0 | 0 | 0 | 0 | 0 | NO_SOURCE_COVERAGE: approved inventory geographically outside this route |
| defesa-civil-sp | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | LICENSE_BLOCK; NO_SOURCE_COVERAGE |
| sp-aguas | 1120 | 1120 | 0 | 0 | 0 | 0 | 0 | 0 | LICENSE_BLOCK |

Approved static geometries and public eligibility are different columns. Intersecting counts are geometry-only diagnostic counterfactuals with direction removed; NEVER published as eligible data. Buffer remains35m for infrastructure,120m weather; initial ROAD_MODE speed20m/s ahead window24km. No buffer/angle/progress threshold relaxed.

Actual route eligible result:1 SAU official-support:4169, SP160 km62.1 north, Cubatao. Distance to route20.8m; ahead11,161.1m. API -> DB -> source -> symbol -> correct detail -> corridor -> frontend auxiliary P5,voice_default=false. Actual viewport rendered1 and persisted Admin client received1/route1/rendered1. Alerted0: no field GPS or near-alert voice event simulated as live driving evidence.

ARTESP toll inventory has1 geometric intersection, then0 direction-eligible: Riacho Grande is southbound and the route is northbound. Correct DIRECTION_FILTER; not a geometry mismatch. Other plazas off this alignment not forced in. ANTT nearest approved asset18,073.49m off route; PRF nearest30,915.63m: NO_SOURCE_COVERAGE by geography, not a35m buffer bug. No evidence of KM_TO_COORDINATE_ERROR or ROAD_REFERENCE_MISMATCH in the actual SAU match. Road refs preserved; no exact road-ref equality test was invented where none exists in matcher.

ARTESP CCM0 = missing keys, not 'no incidents'. SIBH0public = license gate, not 'no rain'. PMRv/Defesa Civil0 = no licensed operational endpoint. Auxiliary zero has therefore been eliminated honestly for this route, without changing filters. Broader event/weather/full toll coverage remains uncertified.
