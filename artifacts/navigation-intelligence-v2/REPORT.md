# Relas Navigation Intelligence V2 — Fase A

## Status e escopo

**Fase A implementada e validada localmente.** Não declarar todas as fases B/C/D prontas. Sem deploy/push nesta missão. Branch `feat/navigation-intelligence-v2`, criada a partir de `4943cd4`. O trabalho local anterior do Official Radar Finder foi preservado, sem publicação ou migração automática de dados.

## O que mudou

- Busca estruturada de rua/número/cidade e CEP, fallback full-text e ranking real por número/cidade/proximidade. Formulário envia busca por Enter/botão, cancela requisições obsoletas e identifica aproximação.
- Correção funcional: Photon público devolvia HTTP 400 para lang=pt. Agora usa default, mantendo nomes brasileiros. CEP é conferido no ViaCEP e resultados com cidade/CEP incompatíveis são descartados; um resultado errado em Nazaré Paulista foi reproduzido e corrigido no teste.
- Rota separada em percorrida/restante por lineMetrics + line-gradient, com progresso compartilhado e reset no recálculo. Sem reconstruir a geometria inteira a cada GPS.
- Instruções construídas integralmente em PT-BR a partir de tipo/modificador, sem concatenar termos ingleses. A próxima manobra é a instrução do passo seguinte; o modo de via usa o contexto do passo corrente.
- CITY_MODE/ROAD_MODE com score, histerese e override Auto/Cidade/Estrada; câmera por velocidade/manobra, usuário mais abaixo e foco à frente sem deslocar o marcador.
- AlertManager e fila de voz: radar independente do mute de navegação, críticos independentes, cooldown/dedupe, prioridade P0/P1 acima da manobra, estados e indicadores de proveniência.
- Corredor de radar mais conservador, índice/bearing do segmento e supressão de sentido oposto/paralela/branch ambíguo tanto no card quanto no destaque da rota. GPS perdido/indisponível suspende destaque e voz; retorno readquire dados pelo fluxo existente.
- HUD compacto; quinze reportes na cidade, nove rodoviários ordenados, incluindo animal e interdição. Novos reportes permanecem comunidade, sem alegação de base policial oficial.
- Família SVG ampliada para estrada e contratos futuros. Sem criar um feed fictício de PRF/DER/concessionárias/chuva/trânsito.
- Métricas de GPS/engine/matching/render/câmera e registro local opt-in com exportação e replay determinístico. Cache/assets v224, incluindo novos módulos e ícones.

## Arquivos

`navigation_backend.py`; alterações pontuais em `server.py` e `community.py`; `app/navigation/{intelligence.js,road-runtime.js,road-mode.css,source-contracts.js}`; integração em `app/app.js`, `boot.js`, `index.html`, `sw.js`, `ui/map-ui.js`; 18 SVGs em app/icons; medição opcional no `app/location/location-engine.js` e tratamento de duração não medida em debug-view.js, sem alterar filtro/matcher; `tests/navigation-intelligence.test.cjs`, `tests/road-source-contracts.test.cjs`, `test_navigation_intelligence.py`; scripts de smoke/benchmark e runner; selftest/versão; .gitignore e estes artefatos.

Nenhuma migração de schema, alteração de autenticação, importação de radares ou escrita na base pessoal/Neon. O cache de busca reutiliza runtime_state em produção e arquivo local existente no modo local. Os comandos de teste usaram um banco isolado, não o banco do usuário.

## Evidência funcional

| Fluxo | Resultado |
| --- | --- |
| Busca real Paulista 1578 | MASP, número 1578, São Paulo, via Photon structured |
| Busca CEP 01310-200 | ViaCEP + geocodificação: São Paulo/CEP compatível; área aproximada rotulada |
| Bairro/cidade | Centro, São Bernardo do Campo |
| Rua Frei Caneca 569 | Número 569 em São Paulo, não rótulo com qualquer dígito |
| Rota urbana real | Valhalla, 2153m, 11 instruções, sem híbridos inglês/português |
| Rota rodoviária real | Valhalla, 54350m; refs SP-150/BR-050 preservadas |
| Auto estrada com contexto de teste | CITY -> ROAD, score .85 após nove segundos; override de ambos os modos aprovado |
| Radar-first | Card e destaque somente fixture-radar; oposto/paralela não selecionados |
| Voz | “Radar a 500 metros. Limite 60.” com Navigation=false/Radar=true, sintetizador interceptado |
| Progresso | ~400m percorridos, fração ~.1333 discreta; recálculo reinicia em zero |
| Registro e exportação UI | Um registro navegação + um GPS exportados, ambos parados após exportação |
| Replay | Duas execuções idênticas; decisões iguais às gravadas ao vivo |
| Semáforos | Teste dedicado API/source/render 198/198/198; filtro e clique aprovados |
| Tipos do mapa | Oito tipos clicáveis; zero DOM markers; zero pageerrors/HTTP errors no smoke do mapa |
| Precision V2 | Aquisição/tracking/previsão/LOST/recuperação/replay/fallback preservados |

O backend HTTP isolado tem inventário vazio para route-alerts; isso explica zero alertas na rota real de teste. O mapa usa dados públicos via proxy somente leitura. Alertas controlados e reportes interceptados são fixtures, não inserções no banco de produção.

Mobile 375x812, 390x844, 430x932 e Android 412x915: sem overflow, controles >=44px, radar acima da manobra quando prioritário, HUD dentro do viewport. Busca, rota, GPS ausente/negado, follow/recenter, quatro intensidades, excesso de velocidade, sentido oposto, filtros persistidos e atualização segura do service worker foram exercitados.

## Testes e desempenho

- `node --test tests/*.test.cjs`: **75 PASS** (22 novos + 53 existentes).
- `python -m unittest discover -p "test_*.py"`: **47 PASS** (incluindo 21 do piloto oficial anterior e nove desta fase). Assets e contrato HTTP de busca também aprovados no app ASGI/FastAPI.
- `selftest.py`, py_compile e checks de sintaxe/diff: PASS.
- Browser de navegação anterior, novo Modo Estrada, mapa e Precision V2: PASS. Uma falha intencional esperada no teste de fallback V2.
- Benchmark sintético Node: 600 fixes e 200 alertas, p95 ~.0363ms sem gravação e ~.0203ms com gravação; diferença de JIT/ordem não significa que gravar é mais rápido. Replay igual ao live. Não mede celular físico.
- Mapa desktop em foreground: 141 FPS, p95 frame ~7.1ms no smoke. Uma primeira leitura de semáforos ainda carregando mostrou 54/202; o teste dedicado após estabilização confirmou 198/198, sem perda na source.
- Exemplo final de latência sintética: gpsFixAgeMs 4, engine/matching ~.1ms, markerRenderLagMs ~8.2, cameraLagMs ~454.3, incluindo animação de 450ms. Não é erro físico do GPS nem garantia de dispositivo móvel.

Dados brutos: `search-live.json`, `route-live.json`, `performance.json`, `browser-navigation.json`, `browser-map.json`, `browser-road-mode.json`, `browser-precision.json`.

Regressão encontrada no teste final e corrigida: debug V2 chamava toFixed em duração null durante previsão. Agora mostra “não medido”, sem inventar 0ms; teste unitário e repetição do fluxo de perda de sinal/replay validam a correção.

## Screenshots

[Busca](address.png), [Modo Estrada/radar](road-mode.png), [vozes e override](voice-settings.png), [reportes de estrada](road-reports.png), [mapa desktop](desktop-map.png), [semáforo](detail-signal.png), [lombada](detail-bump.png), [GPS/replay V2](replay-mobile.png).

## Registro e replay

Camadas → Modo de via e voz, ou opções do HUD → Registrar teste local → Parar → Exportar. JSON baixado contém navigation e location, sem upload. Não gravar trajetos reais fora de private/ se forem colocados no repositório.

```js
relas.navigationTelemetry.start();
relas.navigationTelemetry.stop();
const session = relas.navigationTelemetry.exportJSON();
const decisions = relas.navigationTelemetry.replay(session);
// O replay também aceita o bundle exportado pela UI.
```

O bundle.location pode ser carregado no replay GPS existente. Replay de navegação recalcula decisões; não emite áudio nem finge reproduzir a latência física. Limites e semântica em KNOWN_LIMITATIONS.md.

## Próximas fases

Fase B: adaptar fontes oficiais de postos/bases/trânsito/chuva e Route Event Corridor, validar licença/freshness, depois alimentar as camadas. Fase C: eventos estruturados/dedupe multievidência/rerouting. Fase D: presença anônima opt-in/avatares/confirmações. Official Radar Finder continua obrigatório para “Verificado”. Nenhum requisito dessas fases foi marcado como concluído por existir somente um contrato ou SVG.
