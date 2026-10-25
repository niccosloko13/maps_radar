# Mapa tecnico antes da migracao

Auditoria realizada antes de editar o runtime. Complementa artifacts/neon-migration/AUDIT.md e sqlite-inspection.json.

## Arquitetura atual
server.py e um monolito Python stdlib: H(SimpleHTTPRequestHandler), do_GET/do_POST e ThreadingHTTPServer. main inicializa/migra SQLite, aplica seeds e dispara threads/Timers antes de serve_forever. app/ contem HTML/CSS/JS MapLibre e Admin, sem build Node. package.json configura apenas Neon. start.bat/start.ps1 chamam selftest e python server.py.

SQLite persistente no diretorio local RadarSP/data. db() aplica WAL/busy_timeout/foreign_keys. init_db/ensure_v18_tables/community.init fazem migracoes incrementais. 24 tabelas, oito indices explicitos, sem FKs declaradas. Schema completo e chamadas SQL inventariados no auditor anterior. Historicos, JSON e timestamps sao TEXT; preservar representacao para evitar perdas.

## Dependencias de processo e disco
ADMIN_SESSIONS em memoria; senha gerada em arquivo no import; LOCK/DB_WRITE_LOCK/CITY_SCAN_LOCK/CITY_BATCH_LOCK; SYNC/BAIXADA_SYNC/DEPENDENCY_STATE globais. Threads executam DER, lotes de cidades, descoberta direcionada, pacote assistant e georreferencia. Startup marca jobs interrompidos indiscriminadamente. Caches JSON de malha DER, geocode, bumps; assets vendor podem ser baixados no diretorio da aplicacao. Tudo isso exige separacao de modo local e Function.

## Plano de compatibilidade
1. Manter handlers e logica de negocio, encapsulados por FastAPI/ASGI, sem abrir porta na importacao. StaticFiles serve app; main local continua disponivel.
2. Centralizar conexao/dialeto/upserts/introspeccao em camada db. PostgreSQL obrigatorio na Vercel, SQLite permitido local. Schema SQL versionado explicito, identities e indices; datas/JSON legados em TEXT por fidelidade.
3. Ferramenta explicita faz backup SQLite consistente, valida todas as tabelas/colunas, importa em transacao, recusa conflitos e compara cada linha/contagem. Testar em branch Neon isolada antes de production. Nunca semear no cold start.
4. Sessao assinada e verificavel entre instancias; credenciais e chave via env, autenticacao production falha fechada. Cookies Secure/HttpOnly/SameSite.
5. Estado de jobs e caches importantes no Postgres. Operacoes Admin sincronas com prazo e status persistido; nenhuma thread de trabalho em Function. Lotes grandes limitados por requisicao; retomada explicita, sem worker ficticio.
6. Health e database-status verificam banco real. Assets versionados, API/Admin fora do cache. Build real e testes SQLite/Postgres/ASGI antes de qualquer Preview.

## Acesso cloud antes de mutacoes
CLI autenticada confirmou projeto shy-art-03849128 (radar), org org-weathered-leaf-68637248, PostgreSQL 18, branch production br-old-water-b4gz2ktq. MCP nao exposto nesta sessao. Nenhuma mutacao cloud executada nesta auditoria. Inspecionar databases/tabelas antes de criar branch/schema.

## Tabelas e contagens antes
- radars: 196
- radar_history: 224
- source_syncs: 5
- road_network_meta: 0
- municipalities: 0
- source_registry: 19
- admin_events: 79
- road_objects: 6426
- road_object_history: 0
- signal_networks: 3
- municipality_sources: 2
- source_gaps: 0
- city_scan_jobs: 4
- source_attempts: 6
- municipality_profiles: 0
- radar_validations: 0
- manual_entries: 0
- operation_logs: 53
- update_queue: 4
- assistant_update_runs: 1
- map_points: 8259
- community_batches: 1
- map_feedback: 0
- map_audit: 0

## Rotas identificadas
- `/api/access`
- `/api/admin`
- `/api/admin/`
- `/api/admin/apply-updates`
- `/api/admin/assistant-pack`
- `/api/admin/assistant-pack/run`
- `/api/admin/batch-scan`
- `/api/admin/community`
- `/api/admin/community/`
- `/api/admin/community/export`
- `/api/admin/coverage`
- `/api/admin/dashboard`
- `/api/admin/inventory`
- `/api/admin/login`
- `/api/admin/logout`
- `/api/admin/logs`
- `/api/admin/manual/radar`
- `/api/admin/manual/signal`
- `/api/admin/me`
- `/api/admin/ops`
- `/api/admin/queue-state-updates`
- `/api/admin/sources`
- `/api/admin/sync/antt`
- `/api/admin/sync/der`
- `/api/admin/sync/municipalities`
- `/api/admin/sync/osm-city`
- `/api/admin/sync/praia-grande`
- `/api/admin/sync/santo-andre`
- `/api/admin/sync/santos`
- `/api/admin/update-city`
- `/api/admin/update-queue`
- `/api/autocomplete`
- `/api/der/diagnostic`
- `/api/diagnostics`
- `/api/geocode`
- `/api/georef/der/start`
- `/api/health`
- `/api/map/`
- `/api/map/features`
- `/api/radars`
- `/api/radars/mapped`
- `/api/road-objects`
- `/api/roads/status`
- `/api/route`
- `/api/signal-networks`
- `/api/sources`
- `/api/stats`
- `/api/sync/baixada/state`
- `/api/sync/der/start`
- `/api/sync/praia-grande`
- `/api/sync/santo-andre`
- `/api/sync/santos`
- `/api/sync/state`
- `/api/vendor/status`
