# Endpoint validation
| source | url | http | schema | status |
|---|---|---|---|---|
| artesp-interventions | https://ccm.artesp.sp.gov.br/rodovias/api/intervencoes/ | NOT_ATTEMPTED_AUTH_REQUIRED | BLOCKED: no authenticated/approved payload | AUTH_REQUIRED |
| artesp-occurrences | https://ccm.artesp.sp.gov.br/rodovias/api/ocorrencias/ | NOT_ATTEMPTED_AUTH_REQUIRED | BLOCKED: no authenticated/approved payload | AUTH_REQUIRED |
| antt-tolls | https://dados.antt.gov.br/api/3/action/package_show?id=praca-de-pedagio | 200 | validated real payload | DEGRADED |
| artesp-tolls | https://dadosabertos.artesp.sp.gov.br/ | Portal only / no approved data feed | BLOCKED: no authenticated/approved payload | BLOCKED_ENDPOINT |
| official-support | https://www.der.sp.gov.br/ | Portal only / no approved data feed | BLOCKED: no authenticated/approved payload | BLOCKED_LICENSE |
| pmrv-sp | https://www4.policiamilitar.sp.gov.br/unidades/cprv/ | Portal only / no approved data feed | BLOCKED: no authenticated/approved payload | BLOCKED_LICENSE |
| prf-sp | https://www.gov.br/prf/pt-br/canais-de-atendimento/unidades-prf/sao-paulo | 200 | validated real payload | DEGRADED |
| defesa-civil-sp | https://admin.defesacivil.sp.gov.br/previsaodotempo/sp/alertas | Portal only / no approved data feed | BLOCKED: no authenticated/approved payload | BLOCKED_LICENSE |
| sp-aguas | https://cth.daee.sp.gov.br/sibh/api/v2/measurements/now?station_type_id=2&show_all=false&serializer=complete&public=true&hours=1 | 200 | validated real payload | BLOCKED_LICENSE |

ANTT tolls: CKAN success/result/resources/license_id=cc-by, JSON praca-de-pedagio envelope; required id,coordinates,UF,rodovia/km,situacao; national277/SP73. Bulk snapshot, no pages; empty/schema drift fails closed. CKAN resource last_modified is content revision, not event time. No numeric rate header advertised in captured evidence; daily cache policy. ANTT PRF bulk JSON PRF172/SP26, CC BY; coordinates checked with local polygons.

PRF: official HTML index + bounded linked directory pages,27 normalized. Address/BR/km/name parsed; no official directory coordinates assumed. Published directory revision is not ingestion time. Once/day, <=30pages,1second spacing,90second bound. HTML drift preserves previous snapshot. ANTT coordinate join is a separate explicit review, not an unreviewed geocoder.

SIBH: HTTP200 real measurements list,1106 received/1094 normalized. Fields station_prefix_id,cod_ibge,longitude,latitude,value,max_date,measurement_gap; min_date/qtd support interval analysis. Single bulk hours=1 response, no pagination advertised. max_date is station reading, not server fetch time. Empty latest observation cannot create rain/clear-road assertions. Poll600seconds; current sample rate-limit headers absent. Source-specific license NOT VERIFIED.

ARTESP: authenticated real response NOT TESTED (keys absent); occurrences/interventions0 real. Documentation requires Api-Key,limit100,offset pagination,12requests/hour,>=300seconds; active filter filtro_finalizada=1. Required results/meta and object timestamp/geometry validation have isolated contract tests only. No real rate headers or empty/error payload observed; do not call operational. Missing-key tests perform no HTTP. 401/403/429/schema drift behavior is tested with clearly isolated unit inputs, not counted as live validation.

Public portals: SP Aguas200; DER200HTML; PMRv connection failure (separate web observation502); Defesa Civil bounded direct probe timed out, separate browser/search retrieval200HTML with 'SEM ALERTAS NO MOMENTO'. None proves a licensed machine feed. ARTESP public portal terms validated, geographic toll inventory endpoint still missing. No forced malformed requests to official services; errors/empty response behavior beyond observed traffic remains contract-test evidence only. Full safe probe metadata remains in private/portal-probes.json; no keys.
