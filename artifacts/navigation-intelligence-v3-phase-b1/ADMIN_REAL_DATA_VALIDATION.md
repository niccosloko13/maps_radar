# Admin real-data validation
Existing local Admin auth flow used unchanged; test-only credentials confined to isolated server process. Nine sources visible; no redesign. Source Health shows status,last_attempt,last_success,record_count,freshness kind,approved/blocked coordinates,license/terms,blocker,next_action. SIBH BLOCKED_LICENSE/FRESH is intentional: collection health is different from permission to publish.

| source_id | event_type | normalized | active | eligible_map | blocked_map |
|---|---|---|---|---|---|
| antt-tolls | TOLL_PLAZA | 73 | 73 | 66 | 7 |
| prf-sp | PRF_DELEGACY | 9 | 9 | 0 | 9 |
| prf-sp | PRF_OPERATIONAL_UNIT | 17 | 17 | 12 | 5 |
| prf-sp | PRF_SUPERINTENDENCY | 1 | 1 | 0 | 1 |
| sp-aguas | RAIN_STATION | 1113 | 1091 | 0 | 1091 |

Counters time-sensitive at capture. PRF received27 / approved12 / blocked15; ANTT73/66/7. SIBH received1106 / normalized1094 latest, retained1113; public map0. Logs contain actual collection results, errors are bounded and secrets excluded. Layer Diagnostics aggregate write returned200; final viewport PRF received1/rendered1, persisted exact1. Counts agree with observed map and approved-source policy; global78 eligibility is not the viewport render count. Admin source tabs/logs/diagnostics opened with real records. Browser harness failures (navigation wait, wrong hidden-class assertion, initial field overwrite) were corrected only in test instrumentation; not counted as app failures or test passes. Final evidence admin-diagnostics-browser.json.
