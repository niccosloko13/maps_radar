# Relas Navigation V3 — Fase B

## Status

**INCOMPLETE / BLOCKED — NOT READY FOR PHYSICAL TEST.** Sessão encerrada no estado atual a pedido do usuário. A Fase B integral não está concluída. Foram implementados o núcleo operacional, integrações reais disponíveis e o fluxo de teste isolado. Não marcar como prontas fontes sem chave, endpoint real validado ou coordenada comprovada. Nenhum push ou deploy foi feito.

Branch local: `feat/navigation-v3-phase-b`. Checkpoint privado preserva o workspace anterior; baseline salvo antes de editar: 75 JS, 47 Python e selftest aprovados. Alterações anteriores da Fase A/Official Radar Finder permanecem preservadas e não foram publicadas. O banco pessoal e a branch Neon production não receberam mutações desta fase.

## Implementação

- Pacote `road_data`: migração aditiva explícita SQLite/Postgres, registry de nove fontes, adapters específicos ARTESP/SIBH/PRF/ANTT, contratos para feeds oficiais ainda pendentes, snapshots, histórico, evidências e candidatos conservadores multifonte.
- Coleta Admin/CLI request-bound; mapa nunca dispara coleta upstream. Gate/quota/lease no banco, inclusive chave ARTESP compartilhada. Último snapshot bom preservado em falha, schema inesperado ou paginação incompleta. Vazio válido encerra registros ausentes sem apagar histórico.
- APIs públicas por bbox/classe e corredor via POST; APIs Admin protegidas para saúde, eventos, infraestrutura, logs, catálogos, habilitação, sync, revisão e diagnóstico.
- MapLibre com clusters/pontos/linhas/regiões, presets persistidos, origem/freshness/detalhes, ícones e estados normal/selected/critical/stale. Radares permanecem acima das camadas auxiliares.
- Corredor CITY 1/10 km, ROAD 3/50 km e projeção/direção. AlertManager mantém P0 radar iminente; infraestrutura P5 sem voz. Chuva pontual não gera alegação/voz regional. Camadas desabilitadas não geram alertas auxiliares.
- Fontes & Operação no Admin: saúde, freshness, contagens, logs, payload normalizado, infraestrutura/revisão, eventos/filtros, mapa incorporado e diagnóstico agregado opcional sem localização persistida.
- Assets/service worker versionados; APIs e Admin continuam fora do cache privado do worker. Corrida de inicialização de rota/source corrigida, sem mudar filtro/matcher GPS.

Nenhuma dependência nova. Auth e Official Radar Finder não foram alterados. Precision Engine recebeu somente as alterações anteriores já existentes no workspace; esta fase mudou a versão dos smokes, não o algoritmo.

## Dados reais do ambiente isolado

| Fonte | Resultado real | Mapa real |
|---|---|---|
| ARTESP ocorrências | 0; chave ausente | 0 |
| ARTESP intervenções | 0; chave ausente | 0 |
| SIBH | primeira coleta 962 → 958 SP; atualização 958 → 954 SP; 961 IDs históricos, 954 ativos na última medição | Teste dedicado API/source/render 1/1/1 |
| PRF | 27: 17 operacionais, 9 delegacias, 1 superintendência | 0 coordenadas comprovadas; somente Admin |
| PMRv | 0 novos; cadastro atual não validado | 0 |
| ANTT pedágios | 277 nacionais → 73 SP; 73 ativos/coordenados | Teste Miracatu 1/1/1 e clique |
| ARTESP pedágios | 0 novos | 0 |
| Bases/SAU/apoio | 0 novos | 0 |
| Defesa Civil | 0; portal expirou e endpoint não validado | 0 |

`DATA_COUNTS.json` é o inventário por fonte, com timestamps e distinção histórico/ativo/mapa. `prf-live.json`, `antt-live.json` e `live-health.json` trazem evidência de coleta. Bancos reais de validação ficam em private e não contêm fixtures. As fixtures usam outro banco/servidor explicitamente TEST.

## Testes e evidências

- Suíte final: ver `test-javascript.txt`, `test-python.txt`, `test-selftest.txt` e `TEST_RESULTS.json`. Novos testes exercitam rate limits, 401/403/429, timeout, schema, vazio válido, snapshots, paginação, TTL, bbox, direção, estado de fonte, origem, tarifas, revisão e autorização ASGI.
- Branch Neon isolada `relas-phase-b-validation` (`br-royal-waterfall-b4fwbd1n`), com expiração em 29/10/2026: migração duas vezes, insert/update/upsert, rollback, delete controlado e reconexão passaram. Contagens das tabelas legadas permanecem iguais. Detalhes em `postgres-tests.json`. Nenhuma migração aplicada em production.
- Browser: quatro viewports 375x812, 390x844, 430x932 e 412x915, sem overflow ou botões principais abaixo de 44px; onze categorias TEST individualmente renderizadas/clicadas; cluster de 11; linhas/regiões e estados SVG carregados; fontes e subseções Admin acessíveis.
- E2E TEST separado: banco → APIs → mapa → corredor retornaram 11 registros (5 eventos, 2 clima/estações, 4 infraestrutura); 10 candidatos auxiliares, estação de chuva excluída da voz; radar TEST selecionado P0 acima do contexto. Nenhuma fixture foi inserida no banco pessoal/Neon production.
- Regressões mapa/navegação/GPS: semáforos reais em teste dedicado 198/198/198; oito tipos legados clicáveis; localização negada/ausente, follow/recenter, excesso de velocidade, direção oposta, previsão/LOST/recuperação/replay e fallback preservados. Service worker com atualização pendente durante condução foi exercitado.
- Rota real de API Praia Grande → São Bernardo: **56.036m, 26 passos, 1.256 coordenadas**, incluindo SP-160, SP-150/BR-050 e SPA-291/055. Corredor inicial ROAD: zero eventos reais coletados, uma estação, zero praças/bases. Isso não comprova via livre nem ausência de chuva/perigo.

Testes de áudio usam síntese interceptada; não houve teste em rua ou aparelho físico. Erros encontrados/corrigidos e limites de contagem estão em LAYER_DIAGNOSTICS.md. Nenhuma falha foi apagada da análise por ter havido uma repetição aprovada.

## Respostas às 20 perguntas do documento

1. **Chaves ARTESP configuradas?** Não; usuário confirmou que não possui.
2. **Conexão real ARTESP funcionou?** Não comprovada, sem credencial. Não enviar chave fictícia ao serviço.
3. **Ocorrências ativas ARTESP?** Zero coletadas; total real upstream desconhecido.
4. **Intervenções ativas ARTESP?** Zero coletadas; total upstream desconhecido.
5. **Quantas ARTESP no mapa?** Zero reais. Tipos foram validados apenas com TEST isolado.
6. **Quantas relevantes à rota?** Zero eventos ARTESP coletados; uma estação real no corredor da rota de API.
7. **SIBH tem endpoint público?** Sim, encontrado no HTML oficial e testado com 200; WEATHER.md documenta URL/schema.
8. **Quantas leituras ingeridas?** 954 SP na atualização final; 961 IDs históricos após duas coletas. Primeira leitura tinha 958 SP.
9. **Defesa Civil integrada?** Não. Contrato preparado não equivale a endpoint real operacional.
10. **Alertas ativos Defesa Civil?** Zero coletados; total real desconhecido.
11. **Unidades PRF importadas?** 27 registros, 17 operacionais; zero coordenadas aprovadas.
12. **Bases PMRv?** Zero novas.
13. **Pedágios?** 73 ANTT SP reais/coordenados; zero ARTESP novos; sem tarifa presumida.
14. **Bases/SAU?** Zero novas reais.
15. **Road Mode correto?** Fluxos automatizados e E2E TEST passaram; teste físico não executado.
16. **Radar continua P0?** Sim, comprovado em unitários, navegação e E2E TEST com contexto auxiliar.
17. **Admin tem health/freshness/logs?** Sim, nove fontes visíveis, inclusive pendências e indisponibilidade.
18. **Chave apareceu no frontend?** Não. Retorno só indica configuração; valores ficam exclusivamente no backend.
19. **Alguma fonte stale?** Sim. No snapshot de encerramento, SIBH está STALE, preservando os dados da última coleta; ANTT e PRF estão AGING. Endereços PRF antigos também têm freshness individual. As seis fontes sem operação estão BROKEN/NOT_CONFIGURED ou AUTH_REQUIRED. A captura SIBH 1/1/1 ocorreu quando a leitura estava disponível; não representa coleta contínua nem ausência de chuva.
20. **Pronto para teste físico da Fase B inteira?** **Não.** Resolver pendências externas e critérios listados em KNOWN_LIMITATIONS.md, depois repetir as fontes reais ponta a ponta.

## Executar e retornar

Local continua `python server.py` / start.bat. A migração auxiliar é explícita, não executada ao importar o app:

```powershell
# Usar somente um caminho de teste inicialmente; faz backup se já existir.
$env:DATABASE_BACKEND='sqlite'
python tools/road_data.py migrate --sqlite artifacts/navigation-intelligence-v3-phase-b/private/local.sqlite
python tools/road_data.py sync --sqlite artifacts/navigation-intelligence-v3-phase-b/private/local.sqlite --source sp-aguas
python tools/road_data.py health --sqlite artifacts/navigation-intelligence-v3-phase-b/private/local.sqlite
```

Para Neon, usar branch isolada e DATABASE_URL direto em ambiente privado antes de `python tools/road_data.py migrate`; não imprimir a URL. Sync posterior usa o backend configurado. Aplicar em produção somente após revisão e autorização, não como efeito de boot/deploy. Configurações de exemplo sem segredo em .env.example.

Rollback de código: preservar o workspace atual e usar o checkpoint privado para restauração seletiva, se solicitada. Trocar de branch sozinho não desfaz alterações ainda não commitadas. Nenhum rollback foi executado neste encerramento. Tabelas novas são aditivas e podem permanecer sem serem usadas; não apagar SQLite, tabelas legadas ou histórico para fazer rollback. Nenhum domínio/configuração Vercel foi alterado.

## Artefatos e arquivos

Código principal desta fase: `road_data/{schema,registry,adapters,geometry,service,api}.py`, `tools/road_data.py`, dispatch em server.py, `app/navigation/phase-b.js`, `phase-b.css`, `app/road-admin.js`, integração app/boot/index/admin/sw, SVGs de erosão/deslizamento/incêndio/vendaval e estados; testes Python/JS e scripts de browser/Neon/fixtures. .env.example e .gitignore atualizados sem segredo.

Relatórios: SOURCE_MATRIX.md, ADMIN.md, MAP_LAYERS.md, ARTESP.md, WEATHER.md, ROAD_INFRASTRUCTURE.md, LAYER_DIAGNOSTICS.md, KNOWN_LIMITATIONS.md, AUDIT.md e BASELINE.md.

Screenshots: [camadas mobile](mobile-layers.png), [mapa TEST](mobile-map-test.png), [detalhe TEST](event-detail-test.png), [modo motorista E2E TEST](road-mode-e2e-TEST.png), [praça ANTT real](real-antt-toll.png), [detalhe ANTT real](real-antt-detail.png), [estação SIBH real](real-sibh-station.png), [desktop real](desktop-real-map.png), [Admin](admin-overview.png), [ARTESP sem chave](admin-artesp.png), [diagnóstico](admin-diagnostics-desktop.png).


## Encerramento solicitado pelo usuário

**INCOMPLETE / BLOCKED — NOT READY FOR PHYSICAL TEST.** Trabalho congelado no estado atual, sem novos refinamentos, tentativas externas, push ou deploy.

| Medida | Resultado comprovado |
|---|---|
| Fontes com coleta real | 3: ANTT, SIBH, PRF |
| Fontes sem operação | 6: duas ARTESP sem chave; Defesa Civil, PMRv, pedágios ARTESP e apoio sem feed validado |
| Fontes presentes no Admin | 9 |
| Integrações declaradas prontas em produção | 0 |
| Ocorrências/intervenções reais obtidas | 0; volume upstream desconhecido |
| Alertas meteorológicos regionais reais | 0 |
| SIBH: última coleta SP | 954 observações; 961 IDs históricos preservados |
| SIBH: elegibilidade no encerramento | 0 leituras não expiradas; snapshot preservado, fonte STALE |
| PRF | 27 registros: 17 operacionais, 9 delegacias, 1 superintendência; 0 coordenadas aprovadas |
| ANTT | 73 praças SP ativas/coordenadas, sem tarifa presumida |
| Novas camadas reais comprovadas | toll-plazas e rain-stations; teste dedicado API/source/render 1/1/1 durante a validação |
| Tipos TEST renderizados/clicados | 11 isolados; não representam 11 feeds reais |

O snapshot final foi lido localmente em **26/10/2026 04:03:24 UTC**, sem coleta externa. ANTT e PRF: HEALTHY/AGING. SIBH: STALE, com observações expiradas pelo TTL de 2h. As seis fontes sem operação permanecem AUTH_REQUIRED ou NOT_CONFIGURED, freshness BROKEN. A captura SIBH 1/1/1 é evidência histórica do teste; não representa disponibilidade atual nem ausência de chuva. Datas e contagens em DATA_COUNTS.json e source-health-final.json.

Três coletas reais não equivalem a três integrações integralmente prontas: PRF precisa de coordenadas aprovadas; SIBH precisa de integração regional/licença validada; ANTT foi validada apenas em ambiente isolado. Dependências externas e limitações internas permanecem em KNOWN_LIMITATIONS.md e SOURCE_MATRIX.md.

**Validação final:** 81 JavaScript aprovados e selftest/compilação/syntax aprovados, mantidos sem repetição injustificada. A única rodada Python de fechamento aprovou **71 testes, zero falhas** (final-closure-python.txt), incluindo as últimas correções de freshness e fontes desabilitadas. Browsers já aprovados não foram repetidos após o pedido de congelamento; a repetição interrompida pelo usuário não foi contada como nova aprovação. **Radar P0 confirmado** em unitários, navegação e E2E TEST. Teste físico não executado.

**Segredos/fixtures:** zero correspondências de valores secretos reais nos 199 arquivos publicáveis examinados. Zero registros TEST no banco com coletas reais; onze no banco separado private/fixtures/TEST.sqlite, ignorado pelo Git. O servidor TEST exige flag explícita e bloqueia sync upstream. A URL temporária de conexão Neon foi removida; configurações existentes e dados válidos foram preservados. Servidores de teste 8815/8816/8818 encerrados. Nenhum rollback foi executado.

### Contagens legadas na branch Neon isolada

| Tabela | Antes | Depois |
|---|---:|---:|
| radars | 196 | 196 |
| radar_history | 224 | 224 |
| road_objects | 6426 | 6426 |
| source_registry | 19 | 19 |
| operation_logs | 53 | 53 |
| update_queue | 4 | 4 |
| community_batches | 1 | 1 |
| manual_entries | 0 | 0 |

Comparação completa em postgres-tests.json. Production não foi migrada. Nenhum push/deploy foi realizado.
