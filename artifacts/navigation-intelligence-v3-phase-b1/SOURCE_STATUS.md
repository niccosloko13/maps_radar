# Source status - B.1
Recorded at collection 2026-10-26T04:59:48.864630+00:00; time-sensitive, not a permanent health claim.

| source_id | status | record_count | coordinate_approved | coordinate_blocked | freshness_status | freshness_kind | last_success_at | last_attempt_at | blocker | next_action |
|---|---|---|---|---|---|---|---|---|---|---|
| artesp-interventions | AUTH_REQUIRED | 0 | 0 | 0 | UNKNOWN | EVENT_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | MISSING_API_KEY; LAST_FETCH_ERROR; NO_VALID_SNAPSHOT | Configure backend intervention API credential |
| artesp-occurrences | AUTH_REQUIRED | 0 | 0 | 0 | UNKNOWN | EVENT_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | MISSING_API_KEY; LAST_FETCH_ERROR; NO_VALID_SNAPSHOT | Configure backend occurrence API credential |
| antt-tolls | DEGRADED | 73 | 66 | 7 | FRESH | INFRASTRUCTURE_FRESHNESS | 2026-10-26T01:37:36.476181+00:00 | 2026-10-26T01:37:36.472181+00:00 | PARTIAL_COORDINATE_REVIEW | Review conflicting coordinates; collect within daily cache interval |
| artesp-tolls | BLOCKED_ENDPOINT | 0 | 0 | 0 | UNKNOWN | INFRASTRUCTURE_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | ENDPOINT_NOT_VALIDATED; NO_VALID_SNAPSHOT | Locate current geographic plaza inventory, not traffic statistics |
| official-support | BLOCKED_LICENSE | 0 | 0 | 0 | UNKNOWN | INFRASTRUCTURE_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | LICENSE_NOT_VERIFIED; ENDPOINT_NOT_VALIDATED; NO_VALID_SNAPSHOT | Validate official support inventory, coordinates and license |
| pmrv-sp | BLOCKED_LICENSE | 0 | 0 | 0 | UNKNOWN | INFRASTRUCTURE_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | LICENSE_NOT_VERIFIED; ENDPOINT_NOT_VALIDATED; NO_VALID_SNAPSHOT | Obtain current official dataset/endpoint and redistribution terms |
| prf-sp | DEGRADED | 27 | 12 | 15 | FRESH | INFRASTRUCTURE_FRESHNESS | 2026-10-26T01:30:16.571062+00:00 | 2026-10-26T01:30:16.568062+00:00 | PARTIAL_COORDINATE_REVIEW | Resolve coordinate conflicts; do not geocode-promote administrative units |
| defesa-civil-sp | BLOCKED_LICENSE | 0 | 0 | 0 | UNKNOWN | OBSERVATION_FRESHNESS | NOT_AVAILABLE | NOT_AVAILABLE | LICENSE_NOT_VERIFIED; ENDPOINT_NOT_VALIDATED; NO_VALID_SNAPSHOT | Validate licensed machine-readable alert endpoint; HTML empty state is not a feed |
| sp-aguas | BLOCKED_LICENSE | 1113 | 0 | 0 | FRESH | OBSERVATION_FRESHNESS | 2026-10-26T04:59:47.805631+00:00 | 2026-10-26T04:59:47.801633+00:00 | LICENSE_NOT_VERIFIED | Obtain source-specific data license; configure scheduled backend collection |

Status totals: {"AUTH_REQUIRED": 2, "DEGRADED": 2, "BLOCKED_ENDPOINT": 1, "BLOCKED_LICENSE": 4}. HEALTHY=0; DEGRADED=2; blocked/auth=7. Three sources have real collection evidence; only two have partially approved public map data. Zero integrations are declared fully production-ready.

## License/terms review

| source_id | license | terms_url | commercial_restrictions | attribution_required | last_terms_check | license_verified | endpoint_verified |
|---|---|---|---|---|---|---|---|
| artesp-interventions | CC BY-NC 4.0 | https://ccm.artesp.sp.gov.br/rodovias/api/docs/ | Non-commercial; attribution; portal terms acceptance required | True | 2026-10-26T04:41:24.345004+00:00 | True | True |
| artesp-occurrences | CC BY-NC 4.0 | https://ccm.artesp.sp.gov.br/rodovias/api/docs/ | Non-commercial; attribution; portal terms acceptance required | True | 2026-10-26T04:41:24.345004+00:00 | True | True |
| antt-tolls | CC BY (catalog does not specify version) | https://dados.antt.gov.br/dataset/praca-de-pedagio | Attribution required; current catalog snapshot is not a real-time operation guarantee | True | 2026-10-26T04:41:24.346004+00:00 | True | True |
| artesp-tolls | ARTESP portal data terms (June 2025) | https://dadosabertos.artesp.sp.gov.br/terms | Attribution, integrity, no endorsement; dataset-specific restrictions prevail | True | 2026-10-26T04:41:24.346004+00:00 | True | False |
| official-support | UNVERIFIED | https://www.der.sp.gov.br/ | No source-specific data license/feed confirmed | NOT_AVAILABLE | 2026-10-26T04:41:24.346004+00:00 | False | False |
| pmrv-sp | UNVERIFIED | https://www4.policiamilitar.sp.gov.br/unidades/cprv/ | Current source and data license not confirmed | NOT_AVAILABLE | 2026-10-26T04:41:24.346004+00:00 | False | False |
| prf-sp | CC BY (ANTT coordinates); CC BY-ND 3.0 (original PRF directory) | https://dados.antt.gov.br/dataset/prf | Map uses ANTT coordinate facts and label; original PRF text retained unchanged in inventory; attribution required | True | 2026-10-26T04:41:24.346004+00:00 | True | True |
| defesa-civil-sp | UNVERIFIED | https://admin.defesacivil.sp.gov.br/previsaodotempo/sp/alertas | No explicit reusable data license or machine-readable alert contract confirmed | NOT_AVAILABLE | 2026-10-26T04:41:24.346004+00:00 | False | False |
| sp-aguas | UNVERIFIED | https://apps.spaguas.sp.gov.br/sibh/ | Public endpoint; footer reserves rights; no source-specific redistribution grant confirmed | NOT_AVAILABLE | 2026-10-26T04:41:24.346004+00:00 | False | True |

Unknown terms are a blocker, not an implied public-domain grant. ARTESP public portal data terms and authenticated CCM API terms are separate. PRF directory original text is retained as evidence; published coordinates/label come from the separately licensed ANTT inventory. Recheck terms before changing use/distribution.
