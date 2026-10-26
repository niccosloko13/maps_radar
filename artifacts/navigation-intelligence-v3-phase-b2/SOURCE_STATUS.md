# B.2 source status
Capture time2026-10-26T05:19:30.444330+00:00. All states are explicit; no generic 'not operational'. Collector sync success is not the same as source readiness.

| source_id | status | record_count | coordinate_approved | coordinate_blocked | freshness_status | freshness_kind | last_attempt_at | last_success_at | last_source_timestamp | blocker | next_action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| artesp-interventions | AUTH_REQUIRED | 0 | 0 | 0 | UNKNOWN | EVENT_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | MISSING_API_KEY; LAST_FETCH_ERROR; NO_VALID_SNAPSHOT | Configure backend intervention API credential |
| artesp-occurrences | AUTH_REQUIRED | 0 | 0 | 0 | UNKNOWN | EVENT_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | MISSING_API_KEY; LAST_FETCH_ERROR; NO_VALID_SNAPSHOT | Configure backend occurrence API credential |
| antt-tolls | DEGRADED | 73 | 66 | 7 | FRESH | INFRASTRUCTURE_FRESHNESS | 2026-10-26T01:37:36.472181+00:00 | 2026-10-26T01:37:36.476181+00:00 | 2026-07-28T11:00:43.601569+00:00 | PARTIAL_COORDINATE_REVIEW | Review conflicting coordinates; collect within daily cache interval |
| artesp-tolls | DEGRADED | 239 | 211 | 28 | FRESH | INFRASTRUCTURE_FRESHNESS | 2026-10-26T05:19:16.430104+00:00 | 2026-10-26T05:19:16.444102+00:00 | 2025-05-30T16:48:23.146389+00:00 | PARTIAL_COORDINATE_REVIEW | Daily backend cache; preserve snapshot and review coordinate conflicts |
| official-support | DEGRADED | 249 | 228 | 21 | FRESH | INFRASTRUCTURE_FRESHNESS | 2026-10-26T05:19:21.350101+00:00 | 2026-10-26T05:19:21.368101+00:00 | 2025-05-30T16:48:23.146389+00:00 | PARTIAL_COORDINATE_REVIEW | Daily backend cache; preserve snapshot and review coordinate conflicts |
| pmrv-sp | BLOCKED_LICENSE | 0 | 0 | 0 | UNKNOWN | INFRASTRUCTURE_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | LICENSE_NOT_VERIFIED; ENDPOINT_NOT_VALIDATED; NO_VALID_SNAPSHOT | Obtain current official dataset/endpoint and redistribution terms |
| prf-sp | DEGRADED | 27 | 14 | 13 | FRESH | INFRASTRUCTURE_FRESHNESS | 2026-10-26T01:30:16.568062+00:00 | 2026-10-26T01:30:16.571062+00:00 | 2026-09-15T00:00:00-03:00 | PARTIAL_COORDINATE_REVIEW | Resolve coordinate conflicts; do not geocode-promote administrative units |
| defesa-civil-sp | BLOCKED_LICENSE | 0 | 0 | 0 | UNKNOWN | OBSERVATION_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | LICENSE_NOT_VERIFIED; ENDPOINT_NOT_VALIDATED; NO_VALID_SNAPSHOT | Validate licensed machine-readable alert endpoint; HTML empty state is not a feed |
| sp-aguas | BLOCKED_LICENSE | 1120 | 0 | 0 | FRESH | OBSERVATION_FRESHNESS | 2026-10-26T05:19:28.710306+00:00 | 2026-10-26T05:19:28.719306+00:00 | 2026-10-26T05:15:00+00:00 | LICENSE_NOT_VERIFIED | Obtain source-specific data license; configure scheduled backend collection |

Totals:{"AUTH_REQUIRED": 2, "DEGRADED": 4, "BLOCKED_LICENSE": 3}. HEALTHY0; DEGRADED4; blocked/auth5. Operational source subsets: ANTT,PRF,ARTESP toll assets,ARTESP SAU assets; SIBH diagnostic collection only. No ARTESP CCM incident/intervention authentication occurred. No new source registry entries (still9).

| source_id | event_type | normalized | active | eligible_map | blocked_map |
|---|---|---|---|---|---|
| antt-tolls | TOLL_PLAZA | 73 | 73 | 66 | 7 |
| artesp-tolls | TOLL_PLAZA | 239 | 239 | 211 | 28 |
| official-support | SAU | 249 | 246 | 225 | 21 |
| prf-sp | PRF_DELEGACY | 9 | 9 | 0 | 9 |
| prf-sp | PRF_OPERATIONAL_UNIT | 17 | 17 | 14 | 3 |
| prf-sp | PRF_SUPERINTENDENCY | 1 | 1 | 0 | 1 |
| sp-aguas | RAIN_STATION | 1120 | 1011 | 0 | 1011 |

## Freshness/category contract
ANTT/PRF/ARTESP assets use INFRASTRUCTURE_FRESHNESS, daily collection cadence. Last content revision remains separate; no blanket age expiry for infrastructure. ARTESP assets latest resource revision2025-05-30, not a live operation guarantee, and no periodic update frequency stated. A recently checked old snapshot is not a claim of current field inspection. Content age is visible in details/Admin. All4 collectors FRESH at capture. Source remains DEGRADED for unapproved coordinates. ARTESP incident/intervention uses EVENT_FRESHNESS with real event termination/expiry; no live payload obtained. SIBH uses OBSERVATION_FRESHNESS from max_date/measurement_gap, never ingestion time. Existing B.1 thresholds unchanged.

Current SIBH capture:{"AGING": 20, "FRESH": 991, "STALE": 109}; current-road observations957; retained1120. These are later than the immediate collection counts and naturally age. No scheduler was installed. Collection does not grant publication rights.

Licensing:[ANTT toll](https://dados.antt.gov.br/dataset/praca-de-pedagio) CC BY; [ANTT PRF coordinates](https://dados.antt.gov.br/dataset/prf) CC BY; original PRF directory CC BY-ND3.0 retained unchanged. [ARTESP asset catalog](https://dadosabertos.artesp.sp.gov.br/dataset/cadastro-de-ativos) license_id=cc-by, version unspecified; [portal terms](https://dadosabertos.artesp.sp.gov.br/terms) allow attributed redistribution/integrity/no endorsement. API CCM license remains CC BY-NC4.0 and requires keys. SIBH,PMRv,Defesa Civil have no confirmed source-specific reuse grant and remain blocked. No portal footer was treated as a license for an unrelated dataset.
