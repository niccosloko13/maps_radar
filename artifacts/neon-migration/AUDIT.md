# Relas — auditoria prévia à integração Neon PostgreSQL

Data: 24/10/2026. Base do código: commit `03a2dab6250af5a58a5a2adba628ea8d21c4550a`, branch `main`.

## Escopo e método

Auditoria realizada **antes de instalar a CLI ou editar o runtime**. `server.py` foi lido junto com `community.py`, importador, scripts de inicialização e testes. O SQLite existente foi aberto com URI `mode=ro`; não se chamou `init_db`, seeds, checkpoint ou importação nesta inspeção. Nenhum servidor Relas estava ouvindo na porta 8815.

A inspeção de schema, contagens, constraints e chamadas SQL está em [sqlite-inspection.json](sqlite-inspection.json); o DDL original, em [schema-sqlite.sql](schema-sqlite.sql). Esses arquivos não contêm registros nem credenciais. A listagem AST registra cada chamada com arquivo, função, linha e expressão, incluindo consultas montadas dinamicamente. Foram encontradas **118 chamadas execute/executescript em server.py e 21 em community.py**. Os testes/scripts também acessam SQLite diretamente.

## Arquitetura encontrada

- Backend Python síncrono, `http.server.ThreadingHTTPServer` e `SimpleHTTPRequestHandler`, porta padrão 8815. Não é Next.js, não há `package.json`, bundler de frontend ou build npm obrigatório.
- Frontend estático MapLibre em `app/`; API e Admin compartilham o servidor Python.
- `server.db()` (`server.py:205`) cria uma conexão SQLite por chamada com `sqlite3.Row`, timeout de 30 s, WAL, synchronous NORMAL e foreign_keys ON.
- Grande parte das funções controla `commit()`/`close()` manualmente. `community.transaction()` centraliza commit/rollback e fecha a conexão explicitamente.
- `sqlite3.Row` é usado simultaneamente como sequência (`row[0]`, `row[1]`) e mapa (`row['id']`, `dict(row)`). Essa compatibilidade precisa ser mantida por qualquer driver novo.
- `server.init_db()`, `ensure_v18_tables()` e `community.init()` fazem a evolução aditiva do schema. Não existe Alembic, ORM ou tabela central de versões.
- Instalação atual usa a biblioteca padrão Python. Node é usado para testes auxiliares e, futuramente, para a CLI Neon; isso não muda a arquitetura do servidor.
- Não foi encontrado skill Neon no catálogo de skills habilitados, em ferramentas conectadas ou no diretório local de skills pessoais inspecionado.

## Caminhos e arquivos persistentes

Prioridade do banco local:

1. `RADAR_DATA_DIR`, se informado.
2. `%LOCALAPPDATA%\RadarSP\data\radar.db` no Windows.
3. `user-data/radar.db` na ausência de LOCALAPPDATA.

`BUNDLED_DB_PATH` aponta para `data/radar.db`, usado somente para copiar uma instalação portátil antiga se o destino ainda não existir. `ensure_user_data()` também preserva caches JSON de malha DER, geocoding e lombadas. Esses caches são distintos do banco relacional e não devem ser removidos durante a integração.

`admin_password.txt` fica no diretório persistente; sessões de Admin estão em memória e não fazem parte de uma migração de dados. Não foi lido nem incluído o conteúdo da senha.

## Tabelas e contagens antes de qualquer migração

| Tabela | Registros | Chave primária |
|---|---:|---|
| admin_events | 79 | id |
| assistant_update_runs | 1 | batch_id |
| city_scan_jobs | 4 | id |
| community_batches | 1 | batch_id |
| manual_entries | 0 | id |
| map_audit | 0 | id |
| map_feedback | 0 | id |
| map_points | 8259 | id |
| municipalities | 0 | ibge_id |
| municipality_profiles | 0 | municipality |
| municipality_sources | 2 | municipality, source_id |
| operation_logs | 53 | id |
| radar_history | 224 | history_id |
| radar_validations | 0 | id |
| radars | 196 | id |
| road_network_meta | 0 | id |
| road_object_history | 0 | history_id |
| road_objects | 6426 | id |
| signal_networks | 3 | id |
| source_attempts | 6 | id |
| source_gaps | 0 | municipality |
| source_registry | 19 | source_id |
| source_syncs | 5 | source_id |
| update_queue | 4 | id |

São **24 tabelas de aplicação**, além de `sqlite_sequence`, interno do SQLite. Não há PK nula nos registros existentes. O inventário inclui 196 radares, 6.426 objetos viários, 8.259 pontos comunitários, 224 versões de radares, 79 eventos Admin, 53 logs operacionais, 4 jobs, 4 propostas e os demais registros da tabela acima. Tabelas vazias também precisam ser criadas e comparadas, não omitidas da migração.

### Índices

Oito índices explícitos, além dos índices automáticos de PK/UNIQUE do SQLite:

- `CREATE INDEX idx_operation_logs_op ON operation_logs(operation_id,id)`
- `CREATE INDEX idx_update_queue_status ON update_queue(status,id)`
- `CREATE INDEX map_bbox ON map_points(longitude,latitude)`
- `CREATE INDEX map_city_type ON map_points(municipality,kind)`
- `CREATE INDEX map_source_trust ON map_points(source,trust)`
- `CREATE INDEX map_updated ON map_points(updated_at)`
- `CREATE INDEX object_viewport ON road_objects(longitude,latitude)`
- `CREATE INDEX radar_viewport ON radars(longitude,latitude)`

Definições e índices automáticos por tabela constam na inspeção JSON.

### Constraints e relacionamentos

- Todas as 24 tabelas possuem PK; `municipality_sources` tem PK composta `(municipality, source_id)`.
- Há NOT NULL, defaults e `CHECK(id=1)` em `road_network_meta`. O DDL completo preserva os detalhes por coluna.
- **Não há foreign keys declaradas**, apesar do PRAGMA foreign_keys ON. Relacionamentos são lógicos: radar_history/radar_validations → radars; road_object_history → road_objects; fontes → source_registry; map_points.batch_id → community_batches; feedback/audit → entidades; logs → operation_id; jobs/fila → operação e município.
- Não se deve adicionar FK nova e descartar órfãos para fazê-la passar. A migração deve primeiro preservar e auditar a situação existente.
- PK TEXT no SQLite pode aceitar NULL se não vier acompanhada de NOT NULL; o Postgres é mais estrito. O caso foi verificado: nenhum NULL de PK no snapshot atual.
- AUTOINCREMENT aparece em históricos, eventos, jobs, tentativas, validações, cadastros manuais, operation_logs e update_queue.
- `map_feedback.id` e `map_audit.id` usam INTEGER PRIMARY KEY **sem AUTOINCREMENT**, mas ainda recebem IDs implícitos pelo rowid. Também necessitam identidade no Postgres. `road_network_meta.id=1` é uma chave explícita/singleton, não uma sequência comum.

## Migrações e inicialização existentes

- `init_db()` cria 17 tabelas iniciais e acrescenta colunas de radares por `PRAGMA table_info` + `ALTER TABLE`.
- `ensure_v18_tables()` cria `operation_logs`, `update_queue`, `assistant_update_runs`; inclui índices e colunas de jobs, road_objects e radars, inclusive proveniência (`ingested_by`, lote e nota).
- `community.init()` cria `map_points`, `community_batches`, `map_feedback`, `map_audit`, índices espaciais simples e acrescenta `name`/`report_kind`.
- `PRAGMA user_version=0`; `schema_version=43` é um contador interno SQLite, não uma versão de migração da aplicação. Journal atual: WAL. Encoding: UTF-8.
- `main()` chama init, migração aditiva, seeds municipais/redes, bootstrap público, refresh de physical IDs e checkpoint antes de iniciar HTTP; depois programa cache de vendor e lote de semáforos em background.
- `init_db()` muda jobs queued/running para interrupted ao iniciar. Em Postgres compartilhado, isso pode marcar trabalho de outro processo como interrompido: precisa revisão explícita.
- `checkpoint_db()` executa `PRAGMA wal_checkpoint(TRUNCATE)`. Deve permanecer restrito ao backend SQLite.

## Escritas, upserts e APIs SQLite especiais

As funções de escrita/DDL identificadas abaixo são pontos de revisão; a inspeção JSON contém também as consultas de leitura e as expressões SQL originais.

### server.py

- `db` — linhas 207, 208, 209, 210.
- `checkpoint_db` — linhas 215.
- `init_db` — linhas 219, 239, 241, 242, 242, 244, 246.
- `upsert` — linhas 298, 298, 300, 300, 300, 301.
- `ensure_road_network` — linhas 552.
- `seed_santo_andre` — linhas 596.
- `do_sync` — linhas 651, 660.
- `_seed_praia_grande_impl` — linhas 973.
- `_seed_santos_impl` — linhas 1003.
- `_admin_event` — linhas 1170.
- `sync_municipalities_ibge` — linhas 1184.
- `sync_antt_sp` — linhas 1257.
- `seed_signal_networks` — linhas 1295.
- `_upsert_road_object` — linhas 1311, 1312, 1314.
- `_sync_official_signal_wfs` — linhas 1445.
- `sync_osm_objects_city` — linhas 1498.
- `_record_source_attempt` — linhas 1533.
- `_save_municipality_source` — linhas 1539.
- `_set_gap` — linhas 1545.
- `_clear_gap` — linhas 1551.
- `_run_city_batch_worker` — linhas 1641, 1647, 1654.
- `start_city_batch` — linhas 1662.
- `_manual_radar` — linhas 1699.
- `_manual_signal` — linhas 1714.
- `update_city_scope` — linhas 1733.
- `ensure_v18_tables` — linhas 1758, 1760, 1761, 1763, 1764, 1766.
- `_oplog` — linhas 1780.
- `_queue_update` — linhas 1786, 1787.
- `_run_city_batch_worker_v17` — linhas 1861, 1868, 1872.
- `start_city_batch_v17` — linhas 1877.
- `apply_update_decisions` — linhas 1947, 1951, 1955.
- `assistant_pack_state` — linhas 1979.
- `run_assistant_signal_pack` — linhas 1985, 1988, 2006.
### community.py

- `init` — linhas 20, 31, 33.
- `import_file` — linhas 110, 114.
- `features` — linhas 127.
- `post` — linhas 182, 183, 187, 199, 200, 201.

### Incompatibilidades concretas

1. Placeholders `?` em SQL parametrizado; psycopg usa `%s` e parâmetros separados, sem interpolar dados.
2. `INSERT OR REPLACE` em source_syncs, road_network_meta, signal_networks, road_objects, municipality_sources, source_gaps e assistant_update_runs. REPLACE pode apagar/recriar uma linha no SQLite; Postgres exige upserts definidos por tabela/chave e colunas, sem uma troca textual genérica.
3. `INSERT OR IGNORE` em relatos comunitários; em Postgres precisa ON CONFLICT adequado e sem mascarar erros de dados.
4. Alguns upserts já usam ON CONFLICT e são próximos do SQL portátil, mas dependem dos parâmetros e tipos corretos.
5. `lastrowid` é consumido na criação de jobs. No Postgres deve ser usado `RETURNING id`, preservando explicitamente esse contrato.
6. `total_changes` é usado na marcação de proveniência do lote; precisa contagem equivalente explícita, não uma propriedade SQLite fictícia.
7. `sqlite_master` é consultado para detectar `map_points` na conclusão de rota; deve virar introspecção central por backend.
8. `PRAGMA table_info`, WAL e busy_timeout não podem chegar ao Postgres.
9. Existem valores SQL entre aspas duplas, por exemplo `status="pending"` e `source_type="community"`; no Postgres aspas duplas são identificadores. Os casos devem ser corrigidos deliberadamente.
10. Fechamento de conexão/contexto não tem semântica idêntica entre sqlite3 e psycopg3. Falhas no Postgres abortam a transação até rollback; não se pode simplesmente continuar e gravar erro na mesma transação quebrada.
11. REAL SQLite conserva doubles; usar REAL Postgres reduziria precisão. Coordenadas, distâncias e tempos fracionários precisam DOUBLE PRECISION.
12. Flags são inteiros 0/1, com valores/defaults e APIs existentes. Conversão para boolean deve ser deliberada, sem mudar JSON retornado silenciosamente.
13. JSON está em TEXT (`raw_json`, `details`, `summary_json`, `result_json`, `targets_json`, `municipalities_json`). Timestamps também são TEXT, e `source_date` mistura datas, descrições e períodos. Não converter tudo automaticamente para JSONB/TIMESTAMPTZ: preservar o conteúdo original, incluindo strings não normalizadas, é prioridade.
14. IDs explícitos na cópia precisam de GENERATED BY DEFAULT AS IDENTITY/OVERRIDING apropriado e avanço de sequência depois da importação.
15. A ordem de NULL em ORDER BY difere; revisar queries de histórico/fontes sem perder a ordenação esperada do Admin.

## Locks, threads e transações

- `DB_WRITE_LOCK`: threading.RLock global, usado em imports, seeds, logs, fila, jobs e cadastros. É uma proteção de escritor SQLite dentro de um processo; não é um lock distribuído.
- `LOCK`: guarda sincronização DER/estado operacional. `CITY_SCAN_LOCK` e `CITY_BATCH_LOCK` serializam certos jobs e impedem duplicar trabalhos; têm responsabilidade distinta de serializar o banco.
- `ThreadingHTTPServer` atende várias requisições; há workers de sync DER/Baixada, city scan legado/v17, discovery direcionado, lote ChatGPT/OpenAI e Timer de startup.
- Algumas conexões permanecem abertas durante loops de fontes/redes e há conexões abertas antes da aquisição do lock. No Postgres isso precisa ser delimitado em transações curtas, evitando idle in transaction durante HTTP externo.
- No backend SQLite, preservar WAL, timeout e proteção de escrita. No Postgres, não copiar um lock global de DB para todas as operações: usar transações, constraints, upserts e locking específico por job/recurso quando necessário.
- Verificação de fila antes de INSERT hoje não tem UNIQUE correspondente: processo concorrente pode duplicar proposta. Precisa análise de idempotência sem introduzir constraint que rejeite o histórico já existente.

## Importadores e preloads que precisam continuar funcionando

- DER: parser HTML/bulletins, malha KMZ e georreferenciamento; grava radars, radar_history, source_syncs e road_network_meta.
- ANTT: CSV/CKAN, filtros SP e upsert em radars/histórico/source_syncs.
- Santo André: snapshot oficial JSON e seed com preservação de coordenadas melhores.
- Santos e Praia Grande: seeds oficiais e geocoding com cache; inventário/histórico/source_syncs.
- GeoSampa e SIGSantos: WFS, IDs estáveis/reutilização por coordenada, road_objects, histórico e source_syncs.
- OSM/Overpass: comunidade e objetos, proveniência e diagnóstico da fonte; não deve ser promovido a oficial.
- TXT comunitário: arquivo atual `pesquisaradar.txt`, autodetecção por cabeçalho, filtro local IBGE, lote SHA, deduplicação e reconciliação. `speedcam.txt` será válido se mantiver o formato esperado, mas não há esse nome no diretório atual.
- ChatGPT/OpenAI: cruzamentos publicados, execução por cidades, assistant_update_runs, proveniência, fila e operation_logs.
- Bootstrap estadual/público: `data/geosampa_signals_snapshot.json`, `data/santo_andre_official_2026.json`, demais JSONs, polígonos municipais e TXT. Não apagar esses recursos para trocar o banco.
- `import_community.py` usa as funções do servidor e precisa selecionar o mesmo backend da aplicação.

## Endpoints dependentes do banco

Leituras públicas: `/api/radars`, `/api/radars/mapped`, `/api/road-objects`, `/api/signal-networks`, `/api/stats`, `/api/sources`, `/api/diagnostics`, `/api/map/features`. `/api/route` e `/api/map/route-alerts` também consultam inventário/direção e não são só proxies externos.

Escritas públicas: `/api/map/report`, `/api/map/feedback`; rotas legadas de sync/georef também podem escrever dados oficiais.

Admin: dashboard, coverage, sources, ops, inventory, update-queue, logs, assistant-pack e importação comunitária. Escritas incluem manual/radar, manual/signal, scan/update-city, apply-updates, queue-state-updates, sync municipal/estadual/OSM/WFS e community/bulk/import. Login/logout usam sessão em memória, mas os eventos de autenticação são persistidos.

`/api/health` atualmente apenas retorna metadados do runtime; **não prova que houve conexão com banco**. A validação Neon terá que comprovar a origem dos dados e persistência após restart, sem expor URL de conexão.

## Driver e integração recomendados

A arquitetura é síncrona e usa threads. A recomendação é **psycopg3 síncrono**, sem ORM, em uma camada `db.py` que centralize conexão, backend, contexto transacional, linhas compatíveis, introspecção e operações específicas de upsert/identidade. Nenhuma dependência foi instalada nesta fase.

Padrão inicial deve continuar `DATABASE_BACKEND=sqlite`. A simples presença de DATABASE_URL criada pela CLI não deve ligar Postgres nem disparar migração automaticamente. `DATABASE_BACKEND=postgres` deve ser uma escolha explícita. Se esse modo falhar, informar o erro; não trocar silenciosamente para SQLite e criar bases divergentes.

Usar `.env.local`/`.env` sem publicar valores reais; hoje o servidor lê apenas `os.environ`, sem loader dotenv. `.gitignore` já protege `.env` e `.env.*`, com exceção de `.env.example`.

A documentação oficial indica conexão síncrona para aplicações clássicas com threads, commit/rollback explícitos e conexão direta para migrações administrativas; a URL pooled pode ser apropriada para runtime, respeitando as limitações de sessão do pool. A implementação deve revisar transações por request/importador e evitar estado de sessão dependente de um processo global.

Referências consultadas:

- [Psycopg3 — conexão síncrona e contexto](https://www.psycopg.org/psycopg3/docs/api/connections.html)
- [Psycopg3 — transações e rollback](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)
- [Neon — conexão direta para migrações e pooler](https://github.com/neondatabase/website/blob/main/content/docs/connect/connection-errors.md)
- [Neon — CLI init/link/env/deploy](https://neon.com/blog/just-landed-in-the-neon-cli)

Não foram encontradas skills Neon instaladas no catálogo/local consultado. Se a CLI instalar documentação/skills durante init, ler antes de concluir a implementação. A CLI Node configura Neon; não transforma este projeto em Next.js nem exige npm run build.

## Plano seguro de migração e validação

1. Concluir CLI/autenticação e identificar o destino sem imprimir credenciais. Parar se a CLI abrir login no navegador, conforme instrução do usuário.
2. Inspecionar schema/dados existentes no Neon antes de criar qualquer objeto; não resetar production.
3. Adicionar abstração central e schema PostgreSQL explícito/versionado, com SQLite ainda funcional e padrão.
4. Criar `tools/migrate_sqlite_to_postgres.py`, que faça backup consistente via sqlite3.backup antes de copiar e leia esse snapshot. Não copiar o arquivo SQLite bruto enquanto WAL pode estar ativo.
5. Migrar todas as tabelas, inclusive vazias, preservando PKs, valores, JSON, datas, fontes, direção, proveniência, lote, jobs, fila e histórico. Resolver colisões como conflito explícito; não sobrescrever linhas diferentes existentes silenciosamente.
6. Usar importação idempotente com política clara por PK, transação e ledger/checksums; ajustar sequências após preservar IDs.
7. Comparar contagem por tabela e por fonte/município e conteúdo/hash por PK. Contagem sozinha não detecta alteração de histórico/JSON.
8. Exercitar CRUD, rollback, upsert, concorrência, importadores, Admin, mapa, servidor em Postgres e restart. Escritas de smoke devem ser controladas/isoladas e não poluir dados reais.
9. Manter retorno operacional explícito com DATABASE_BACKEND=sqlite e o arquivo original intacto. Não fazer uma troca definitiva antes dessas provas.

## Estado ao concluir esta auditoria

**Nenhum dado migrado, nenhum schema PostgreSQL criado, nenhum arquivo SQLite apagado/substituído e nenhum runtime alterado.** O próximo passo autorizado é instalar/tentar a CLI Neon e executar a inicialização solicitada. PostgreSQL ainda não está declarado pronto.
