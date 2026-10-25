# Relas 2.2.0 — Vercel / Neon

## Status

**Producao validada no projeto Vercel atual: build cloud READY, PostgreSQL conectado, APIs publicas, busca/rota e Admin testados no endereco https://mapsradar-three.vercel.app. As secoes anteriores registram a auditoria e os bloqueios encontrados durante a preparacao; o encerramento abaixo registra sua resolucao.**

A CLI Vercel 65.2.0 respondeu `Logged out`; `vercel build --yes` falhou com `The specified token is not valid`. O login foi solicitado ao operador, sem abrir autenticacao automaticamente. Nao houve deployment, alteracao de dominio ou push que disparasse deploy automatico nesta etapa.

## Auditoria e arquitetura

O [mapa tecnico inicial](ARCHITECTURE.md) foi produzido antes das alteracoes de runtime. Inventariou 24 tabelas, 15.282 registros e 54 caminhos de API. Complementa a auditoria anterior em `artifacts/neon-migration/`, com DDL SQLite e chamadas SQL. Nomes reais incluem `source_registry`, `city_scan_jobs`, `operation_logs` e `update_queue`; nao foram inventadas tabelas substitutas para fontes/filas existentes.

Antes: servidor stdlib persistente, migrations/seeds no startup, SQLite WAL, senha em arquivo criada no import, sessoes em memoria, workers em threads e caches JSON locais. Frontend MapLibre/HTML/JS sem pipeline Node; package.json configura Neon, nao Next.js.

Agora:

- `server:app` FastAPI/ASGI, detectavel por Vercel. Adaptador `web_app.py` reutiliza os handlers e a logica de negocio existentes. StaticFiles preserva `/`, Admin, PWA e assets. Importar a aplicacao nao abre porta, cria SQLite, gera senha, aplica migration ou inicia threads.
- `python server.py` continua local/LAN, com os preloads e migrations SQLite historicos preservados. Em modo hospedado, abrir HTTPServer manualmente e recusado. Launchers Windows continuam disponiveis.
- `db/` centraliza conexao, parametros, introspeccao, conflitos/upserts, identities, transacoes e schemas. SQLite somente local; Vercel exige PostgreSQL e nunca faz fallback silencioso. Handles fecham deterministicamente nos dois engines.
- Runtime usa conexao pooled Neon; migracao usa conexao direta. Sockets ociosos podem ser reutilizados apenas dentro de uma requisicao; handles ativos permanecem separados e todos os sockets fecham ao terminar. Nao ha pool global com threads de manutencao.
- Jobs hospedados executam durante a requisicao, com status/lease no Neon, claim por transacao/advisory lock, prazo cooperativo de 45 segundos e falha registrada. Nao existe worker permanente. Limite da Function: 120 segundos, consultas: ate 25 segundos, conexao: 10 segundos. Lotes do Admin sao enviados um por vez.
- Caches importantes usam `runtime_state` em ambiente hospedado. Assets vendor sao empacotados, sem download/gravação no diretorio read-only da Function. Nenhum SQLite/WAL/SHM, marker ou log de arquivo e fonte persistente em producao.
- Admin exige usuario/hash/chave em Preview/Production. PBKDF2-SHA256, 600.000 iteracoes, tokens assinados HMAC com expiracao de 8 horas; cookie HttpOnly/Secure/SameSite=Lax. Sessao continua valida entre processos. Frontend deixou de guardar sessao em localStorage. Configuracao ausente falha fechada.
- Health consulta o banco real e informa engine, ambiente, versao e schema. Admin possui `database-status` e listagem de jobs. Mutacoes GET legadas exigem Admin localmente e sao recusadas na Vercel; georreferencia ganhou POST Admin.
- Cache PWA atualizado para v220, APIs/Admin continuam fora do cache e atualizacao durante direcao continua adiada. Pequena correcao de overflow do Admin; sem redesign da aplicacao nesta etapa.

## Neon e schema

Inspecao autenticada pela CLI confirmou org `org-weathered-leaf-68637248`, projeto `shy-art-03849128` (`radar`), PostgreSQL 18, database `neondb`, branch production `br-old-water-b4gz2ktq`. Antes da migracao nao havia tabelas de aplicacao. MCP nao foi usado porque nao esta exposto nesta sessao; OAuth/configuracoes existentes foram preservados. As duas skills locais foram atualizadas pela CLI.

Primeiro foi criada/migrada a branch isolada `relas-vercel-validation` (`br-tiny-queen-b481oqjo`), com expiracao em 31/10/2026 23:59:59 UTC. Depois dos testes, production recebeu a mesma migracao explicita.

Migration versionada: `001-vercel-neon`, em `db/schema.sql`/`db/migrations.py`. Mantem as 24 tabelas e acrescenta `schema_migrations`, `migration_imports`, `runtime_state`, `runtime_jobs`. PKs e a PK composta de municipality_sources foram preservadas. Rowids implicitos e AUTOINCREMENT viraram BIGINT identity; sequencias foram alinhadas ao maior ID. Sem DROP/reset/delete automatico.

JSON e datas legadas ficam em TEXT deliberadamente: ha source_date descritivo e JSON cuja representacao original precisa ser preservada. Flags permanecem inteiros, REAL vira DOUBLE PRECISION, mantendo contratos da API. ON CONFLICT usa alvos explicitos; INSERT OR REPLACE nao e convertido por regex no driver e nao apaga/recria linhas. Foram adicionados indices de bbox, latitude/longitude, municipio, fonte, tipo, status/confianca, lote, ator e atualizacao nos campos existentes. PostGIS nao e requisito desta versao.

## Dados antes/depois

**24/24 tabelas, 15.282/15.282 registros originais, todos os campos comparados por SHA-256 estavel.**

| Tabela | SQLite | Neon production apos migracao | Verificacao de conteudo |
| --- | ---: | ---: | --- |
| admin_events | 79 | 79 | igual |
| assistant_update_runs | 1 | 1 | igual |
| city_scan_jobs | 4 | 4 | igual |
| community_batches | 1 | 1 | igual |
| manual_entries | 0 | 0 | igual |
| map_audit | 0 | 0 | igual |
| map_feedback | 0 | 0 | igual |
| map_points | 8259 | 8259 | igual |
| municipalities | 0 | 0 | igual |
| municipality_profiles | 0 | 0 | igual |
| municipality_sources | 2 | 2 | igual |
| operation_logs | 53 | 53 | igual |
| radar_history | 224 | 224 | igual |
| radar_validations | 0 | 0 | igual |
| radars | 196 | 196 | igual |
| road_network_meta | 0 | 0 | igual |
| road_object_history | 0 | 0 | igual |
| road_objects | 6426 | 6426 | igual |
| signal_networks | 3 | 3 | igual |
| source_attempts | 6 | 6 | igual |
| source_gaps | 0 | 0 | igual |
| source_registry | 19 | 19 | igual |
| source_syncs | 5 | 5 | igual |
| update_queue | 4 | 4 | igual |

A segunda execucao na branch de validacao inseriu **zero** linhas nas tabelas originais. Registros de teste/auditoria da branch de validacao explicam extras no destino dessa branch; nao foram transportados a production. [Resultado production](production/migration-result.json), [primeira validacao](validation/migration-result.json), [idempotencia](idempotence/migration-result.json).

Comparacoes adicionais por fonte, municipio, tipo, lote e ingested_by sao iguais: [data-comparison.json](data-comparison.json). SQLite original foi aberto read-only e novamente comparado campo a campo ao snapshot: [sqlite-preservation.json](sqlite-preservation.json), todas as 24 tabelas inalteradas.

- Radares de inventario: 196, sendo 183 com coordenadas. Fontes atuais: ANTT 80, Santo Andre 75, Santos 31, Praia Grande 10. A fonte DER existe no catalogo, mas nao havia radares DER nessa fotografia da origem; nenhum total foi inventado.
- Semaforos/road_objects: 6.426, sendo 6.419 georreferenciados e 7 registros legados sem coordenadas.
- Base comunitaria: 8.259 pontos em 424 municipios. TYPE 1: 3.395; 2: 794; 3: 367; 5: 1.309; 7: 266; 8: 1.737; 14: 391. Velocidade, Direction, DirType, fonte, lote e proveniencia preservados pelo comparativo integral.
- Historico de radares: 224; fontes registradas: 19; fila: 4; lotes comunitarios: 1. As tabelas vazias existentes tambem foram criadas/migradas, sem preencher dados ficticios.
- Cache encontrado/migrado: geocode_cache.json, 36.313 bytes. Malha DER/bumps nao existiam como cache persistente nessa origem. Caches novos no Neon nao sao sobrescritos pelo migrador.

Backups consistentes SQLite foram criados antes das importacoes, dentro de pastas `backups/` ignoradas pelo Git. Incluem paginas WAL via SQLite backup API. O SQLite de origem nunca e aberto para escrita pelo migrador. Conflito com dados diferentes no destino aborta e reverte toda a transacao, testado explicitamente.

## Testes executados

- Python 3.12 em venv isolada. `python -m py_compile server.py` e compileall dos modulos/ferramentas: passaram.
- `python selftest.py`: passou. Mensagem historica v1.8.2 do selftest foi preservada; o app/health sao 2.2.0.
- `python -m unittest test_vercel_runtime test_community test_road_review -q`: **15 testes passaram**, incluindo banco antigo, repeticao de importacao, schema, ASGI/static, limites de body, auth, cookie seguro, ausencia de inicializacao no import hospedado e recusa de SQLite na Vercel.
- `node --test tests/navigation.test.cjs`: **4 passaram**. Sintaxe dos JS principais e diff whitespace: passaram.
- `uv lock --check` / `uv pip check`: dependencias consistentes. Lockfile reproduzivel e requirements exportado; nao ha build frontend Node a inventar.
- Smoke Neon: **31 checks passaram**; conexao, SELECT, INSERT, UPDATE, DELETE de fixtures proprias, rollback, upsert, sessao entre instancias, cadastro manual radar/semaforo, bbox/tipos, alertas de rota, replay comunitario, cache persistente, job e limite de lote. [Resultados](postgres-tests.json). As fixtures de inventario sao removidas por seus IDs; dados reais nao sao removidos.
- O smoke de cidade utiliza descoberta de providers simulada para testar o fluxo real de Admin, fila e logs em Postgres de forma deterministica. Nao equivale a reexecutar uma expansao estadual nem comprova disponibilidade de todos os sites externos.
- Conexao pooled tambem testada com escrita persistente, rollback, timeout local, isolamento de handles e reuso ocioso: [pooled-tests.json](pooled-tests.json). Conflito de migracao revertido e job expirado registrado: [failure-tests.json](failure-tests.json).
- APIs production via pooled responderam 200: `/`, `/admin`, `/api/health`, `/api/radars`, `/api/road-objects`, `/api/stats`, `/api/map/features`. [Prova de runtime](production-runtime.json). Admin/dashboard/inventario/fontes/logs/fila/database-status foram testados na branch isolada: [api-probe.json](api-probe.json).
- Reinicio real do processo ASGI preservou dados, jobs e aceitou o cookie da instancia anterior: [restart-proof.json](restart-proof.json). Servidor de teste e encerrado ao finalizar.

## Navegador / mobile

Chrome/Playwright com ASGI e Neon: oito tipos renderizados/clicados, detalhe correto para radar fixo, radar semaforico, camera de avanco, movel, fiscalizacao, lombada, pedagio e semaforo. Camadas desligam/ligam e preferencia persiste. Nenhum DOM marker. No zoom 10 foram observados 9 clusters de pontos e 3 de semaforos, com zero DOM markers; [captura](clusters.png).

Regiao de semaforos no zoom 14: **API 198 / source 198 / renderizados 198**. Semaforos usam source/layer/icones proprios; clusters e expansao do mapa existente foram preservados. Capturas iniciais por tipo podem observar a source anterior enquanto a requisicao seguinte do viewport ainda carrega; a medida dedicada acima foi feita apos carregar.

Viewports: 375x812, 390x844, 430x932 e Android 412x915; sem overflow no mapa/modo motorista, controles verificados com minimo de 44px. Driver: GPS simulado, heading, parada, fix impreciso, permissao negada/indisponivel, suspensao de follow e recentralizar. Busca real encontrou Sao Bernardo; rota Valhalla retornou 2.153 m, 11 instrucoes e 2 alertas. Intensidades 1000/450/200/70 m, excesso de velocidade, direcao oposta, resumo e 13 tipos de reporte passaram. Reporte sintetico do navegador foi interceptado e nao publicado.

Zero erros JavaScript/HTTP no smoke do mapa; quatro warnings do estilo base MapLibre ja conhecidos. FPS local medido 127 / p95 13,5ms em computador, **nao benchmark de celular**. Latencia de viewport Windows-Neon ficou em segundos; desempenho no runtime/regiao Vercel ainda precisa medicao. Evidencias: [mapa](browser-map.json) e [navegacao](browser-navigation.json). Admin abriu usando cookie HttpOnly, sem sessao em localStorage; overflow horizontal encontrado foi corrigido e revalidado em 1440px.

## Falhas encontradas e corrigidas

1. Row factory psycopg precisava lidar com DDL sem cursor.description; tentativa inicial foi revertida e o adaptador foi corrigido.
2. Pooler Neon rejeitou statement_timeout nos parametros de abertura. Foi substituido por set_config local a transacao, comprovado em conexao pooled.
3. Context manager SQLite nao fechava handles; Python 3.12/Windows revelou WinError 32. Camada central e fechamento do migrador em falhas foram corrigidos e retestados.
4. Sessoes em memoria e criacao de senha no import nao serviam a multiplas instancias. Foram substituidas por configuracao explicita e tokens assinados verificaveis entre processos.
5. Rotas GET legadas podiam disparar mutacoes sem Admin; foram protegidas e bloqueadas no modo hospedado.
6. Jobs em threads podiam morrer apos resposta. Hospedado executa durante request e registra resultado/falha/lease no banco.
7. Respostas de job preservam campos do contrato Admin; cidades/decisoes sao particionadas pelo cliente em requisicoes limitadas.
8. Overflow horizontal no Admin e fallback de API desconhecida para arquivo foram corrigidos.

## Limites e pendencias reais

- **Bloqueio atual: autenticacao Vercel e variaveis seguras ainda nao configuradas/verificadas na plataforma. Build, bundle Linux, framework detection do projeto conectado e Preview nao foram aprovados por um build real.** Nao ha credenciais de producao Admin inventadas no repo nem senha fixa como fallback.
- Importadores preservam sua logica e SQL portavel; nao foram reexecutadas sincronizacoes completas DER/ANTT/WFS/OSM/municipais contra todos os provedores externos. Lotes longos precisam CLI; requests interrompidos nao continuam magicamente em background. Revise logs/contagens de uma sincronizacao parcial antes de repetir.
- Branch de validacao expira; para Preview duradouro usar uma branch propria sem essa expiracao e segredo distinto de production.
- Logout remove cookie/local token; tokens assinados emitidos continuam criptograficamente validos ate expirar (8h) ou rotacionar SESSION_SECRET. Nao ha tabela de revogacao individual nesta versao.
- Escritas futuras no Neon nao sao replicadas para SQLite. Rollback local mantem a fotografia original, nao incorpora mudancas cloud automaticamente.
- Rotas externas ainda usam os provedores do projeto, inclusive endpoint demo Valhalla observado no teste. Nenhuma infraestrutura de fila/cron ou novo provedor foi provisionado.

## Operacao, arquivos e configuracao

[Variaveis exatas por ambiente](ENVIRONMENT_VARIABLES.md), [comandos de deploy/rollback](DEPLOYMENT.md), [lista de arquivos](FILES.md). Novas dependencias: FastAPI/Starlette/Pydantic, psycopg3 binary, python-dotenv e uvicorn local, com transitivas fixadas. httpx somente para testes. uv usado na venv para gerar/verificar lock; Vercel CLI executada via npx, sem mudar Node global.

O `.env.local` ignorado recebeu URLs diretas/pooled de production e validacao, sem imprimi-las. Nenhuma credencial foi colocada em relatorio, README ou commit. `.gitignore`, `.vercelignore` e excludeFiles protegem bancos, backups, env, configuracao do agente, testes e caches. `.codex/config.toml`, trust, configuracao OAuth, `neon.ts`, org/projeto e servicos existentes foram preservados.

A proxima validacao e: concluir `npx vercel login`, conectar **o projeto Vercel existente**, configurar variaveis de Preview, executar `vercel pull` e `vercel build`, inspecionar bundle e testar um Preview isolado. Somente depois revisar Production. O rollback detalhado permanece no guia; nao executar DROP ou trocar Neon por SQLite na Vercel.


## Screenshots

- [admin-postgres.png](admin-postgres.png)
- [alert.png](alert.png)
- [clusters.png](clusters.png)
- [desktop-map.png](desktop-map.png)
- [detail-bump.png](detail-bump.png)
- [detail-fixed.png](detail-fixed.png)
- [detail-signal.png](detail-signal.png)
- [filters.png](filters.png)
- [mobile-375.png](mobile-375.png)
- [mobile-390.png](mobile-390.png)
- [mobile-412.png](mobile-412.png)
- [mobile-430.png](mobile-430.png)
- [mobile-driver.png](mobile-driver.png)
- [mobile-map.png](mobile-map.png)
- [semaforos-map.png](semaforos-map.png)


## Publicacao Git posterior

Apos a revisao, o usuario autorizou explicitamente commit e push das alteracoes para main. Essa publicacao nao valida o build da Vercel nem resolve as variaveis/autenticacao pendentes descritas acima. O push pode acionar a integracao automatica GitHub/Vercel.


## Correcao do build unused_function

O primeiro build cloud do commit c8cb51b falhou antes de instalar dependencias: `server.py` era interpretado como pattern de funcao legada em api/. Inspecao posterior confirmou que o framework do projeto Vercel estava indefinido. A configuracao agora fixa `framework: fastapi` em vercel.json, preservando server:app e os limites/exclusoes existentes.

A CLI ja estava autenticada nesta etapa. Foi vinculado localmente o projeto existente maps_radar e feito pull de configuracoes Preview, sem alterar dominio ou definir variaveis secretas no remoto. As URLs privadas Neon foram preservadas; arquivos .vercel e env continuam ignorados. Uma variavel sensivel de Preview nao pode ser baixada e veio como placeholder; o build nao comprova valores de runtime.

`vercel build` passou com CLI 65.2.0, Python 3.12, dependencias instaladas de uv.lock. O manifest contem server.py e app/app.js no filePathMap, sem .env.local, radar.db ou arquivos de senha/sessao. Cinco testes de runtime passaram. O builder local Windows exigiu uv no PATH sem espacos; foi usada copia auxiliar em LOCALAPPDATA/RelasBuildTools, sem alterar PATH global. Isso nao exige mudanca no Linux da Vercel.

[Prova da correcao](build-fix.json). O push da correcao permite novo build pela integracao GitHub. Nenhum deploy manual de producao foi executado. Confirmar o novo build cloud e as variaveis de runtime antes de marcar o deployment pronto.


## Correcao de runtime no projeto Vercel recriado

O deployment e8d797jaq pertence ao projeto recriado prj_3eXFTKDsAxx8GMMyGVU3Wgg1EJ36. O vinculo local ainda apontava ao projeto anterior. Foi corrigido o vinculo local, preservando URLs Neon e configuracao existente. A unica variavel encontrada no novo projeto era DATABASE_BACKEND. Foram configurados backend postgres, DATABASE_URL pooled e credenciais Admin/SESSION_SECRET fortes, sem colocar valores em logs ou Git. Credenciais iniciais foram guardadas apenas em arquivo privado no diretorio local RadarSP/secrets; nao foi redefinida nenhuma credencial Admin existente na Vercel (nao havia).

Health agora diagnostica backend invalido/URL ausente sem mostrar o valor recebido. Erros internos registram apenas classe e rota, sem URL de conexao, corpo ou senha. Dois testes de regressao foram adicionados; 17 testes Python, selftest e 4 testes Node passaram. O cache do builder local Windows apresentou falha de permissao; isso nao foi tratado como build aprovado. A validacao final sera feita no novo deployment cloud, com as variaveis completas. [Registro](production-incident.json).


## Encerramento — validacao real do deployment

Deployment verificado: mapsradar-a00ksksn1-nexus-a534.vercel.app, commit de codigo d7a4b15, build cloud READY. Endereco estavel publico: https://mapsradar-three.vercel.app. O endereco e8d797jaq enviado durante o incidente e um deployment anterior, com variaveis antigas imutaveis; nao e o endereco a usar para acompanhar atualizacoes.

Health publico retorna HTTP 200, ok=true, database=ok, engine=postgres, environment=production, schema 001-vercel-neon. APIs publicas e Admin retornaram 200: 196 radares, 6.419 objetos georreferenciados, 8.259 pontos comunitarios, 19 fontes; viewport 375 features; filtro de semaforos 198. Frontend real mobile exibiu 198 semaforos, sem erros JS ou HTTP, com dados vindos do Postgres. Admin real abriu autenticado, sem sessao em localStorage ou overflow. Login com credencial criada e logout foram testados por HTTPS com cookie Secure/HttpOnly. Nenhum ponto sintetico foi inserido no inventario de producao.

Busca real retornou resultado e Valhalla calculou rota de 2.153m com 2 alertas. Medicoes do deployment: features de viewport 0,78s, semaforos 0,52s, health 0,44s, dashboard 0,64s nessa execucao. Esses tempos nao sao garantia de SLA. [Resultados HTTP](production-live-api.json), [navegador](production-live-browser.json), [mapa mobile](production-live-mobile.png), [Admin](production-live-admin.png).

Credencial inicial do Admin guardada em arquivo privado local RadarSP/secrets/Relas-Admin-Vercel.txt; senha/hash/session secret nunca foram publicados. O vinculo local Vercel foi atualizado para o projeto recriado. As variaveis Production foram configuradas; a configuracao Preview completa continua separada e nao foi apontada ao banco de producao. O token de acesso de protecao gerado pela CLI foi usado somente para verificar o deployment protegido; o dominio publico foi testado diretamente.

O ultimo build local foi prejudicado por permissoes do cache Windows/OneDrive; o build Linux na Vercel e o runtime real passaram. Nao houve reset nem nova importacao destrutiva do Neon. Os registros originais foram mantidos e a unica escrita funcional de teste foi a auditoria normal dos logins Admin.
