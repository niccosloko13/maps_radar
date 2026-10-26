# Real map validation
Mobile390x844, desktop1440x900, isolated real SQLite, read-only legacy radar proxy. No fixture database used. State bbox:-53.2,-25.4,-44,-19.7; API eligible78 (66 tolls+12 PRF). SIBH eligible0/license; ARTESP0/auth.

| layer | received in viewport | normalized | eligible_map | viewport | rendered | selected | detail_opened |
|---|---:|---:|---:|---:|---:|---:|---|
| ANTT toll |1|1|1|1|1|1|true|
| PRF approved Atibaia |1|1|1|1|1|1|true|
| SIBH |0|0|0|0|0|0|false: license blocked|
| ARTESP occurrences/interventions |0|0|0|0|0|0|false: auth required|

ANTT clicked real point[-47.32628,-24.157869]. PRF Atibaia clicked[-46.585265,-23.19135], real ANTT label/source/license in detail. Two genuinely rendered layers, not three. Earlier Aparecida PRF candidate was collision-suppressed by another symbol (radar priority retained); initial clicked detail was a different community enforcement object and is NOT accepted as PRF success. Raw initial browser-results.json preserves that failed selection. A targeted official Atibaia selection provided valid evidence; prf-targeted-browser.json records both attempts. No overlap override was added to hide radars.

Route Praia Grande -> Sao Bernardo: REAL_ROUTE, distance56050m, vertices1248, corridor counts{"event": 0, "weather": 0, "infrastructure": 0}. Zero eligible auxiliary records on that actual route; federal ANTT/PRF coverage does not substitute for missing state ARTESP coverage. Zero weather/license blocked. No fixture or straight-line route counted. Road test route coverage remains blocked.

Layer Diagnostics uses actual rendered IDs, not API totals. Fixed asynchronous aggregate lag; final recorded PRF received1/rendered1 and same persisted client counters. Rain license gating prevents rain rendering even while Admin can audit real readings. Eight of eleven previously fixture-tested types still lack any real normalized evidence; nine lack approved public real-map evidence (RAIN_STATION collected but blocked). No claim that all registered product types have live coverage.

Screenshots: [ANTT](antt-tolls-real-mobile.png), [PRF approved](prf-approved-real-mobile.png), [Admin](admin-real-diagnostics.png). prf-sp-real-mobile.png is retained as FAILED selection evidence, not readiness proof.
