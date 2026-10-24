# Relas 2.1.5 — revisão final para teste de rua

Data: 24/10/2026. Repositório: https://github.com/niccosloko13/maps_radar.git. Branch de trabalho: `main`.

## Status final

**READY FOR ROAD TEST — teste controlado em contexto HTTPS com localização permitida.**

Os itens críticos de software passaram: fontes/API, semáforos realmente renderizados, identificação e toque nos oito tipos, filtros persistentes, clusters expansíveis, rota real, HUD, GPS simulado, direção, follow/recentralização, contribuição e atualização de cache. O teste de rua é a próxima etapa de validação dos sensores físicos. O HTTP pelo IP da rede local não habilita GPS no telefone: use HTTPS confiável, conforme o README. Isso é pré-requisito de acesso, não uma promessa de que o aparelho já esteja configurado.

Não houve homologação em veículo, em Safari/iOS ou em sensores reais. Nenhuma conclusão de precisão física ou autonomia de bateria foi inferida da automação.

## Auditoria antes das alterações

Relatório escrito antes de editar frontend/backend: [INITIAL_AUDIT.md](INITIAL_AUDIT.md). Medições: [initial-audit.json](initial-audit.json).

O projeto recebido tinha Python/SQLite, MapLibre local, importação comunitária e fluxo de condução, mas faltavam source/layer exclusivas de semáforos, acompanhamento fora de rota, suspensão do follow, chevron, proteção de precisão GPS e registro do service worker. Havia textos corrompidos e alvos pequenos no HUD compacto.

Na região Paulista/Consolação, zoom 14 e viewport 390×844, **198 semáforos chegavam à API/source, mas apenas 77 IDs apareciam** na camada compartilhada. O problema foi medido, não presumido pela presença do código.

## Map — mudanças, layers e estilo

Foram mantidos o backend, os contratos das APIs, o inventário e a estrutura do Admin. As alterações concentram-se na operação do mapa e da condução:

- Source `relas-signals` exclusiva para semáforos comuns.
- `relas-signal-clusters` / `relas-signal-count`: agrupamento até zoom 12.
- `relas-signal-overview`: visão urbana no zoom 13, com prevenção de colisões.
- `relas-signal-icons`: individuais a partir do zoom 14, sem exigir zoom 17.
- `relas-points`, `relas-clusters`, `relas-count`, `relas-icons`: demais tipos, com prioridade de confiança e de equipamentos críticos. Foi corrigido um caso em que um radar fixo era encoberto por símbolos de pedágio/fiscalização próximos.
- `relas-route-case` e `relas-route-line`: contorno e rota ciano.
- `relas-route-alerts` / `relas-route-alert-icons`: pontos relevantes do corredor, acima das informações secundárias. Os demais símbolos perdem intensidade durante rota ativa.
- `relas-position` para parada/heading desconhecido e `relas-user-heading` para movimento.
- Nenhum HTML marker para o inventário: a automação encontrou **0 `.maplibregl-marker`**.

Os SVGs foram refeitos sem o pino/placa genéricos: câmera fixa, câmera com sinal, sinal com câmera anexada, tripé, barreira de fiscalização, lombada lateral, pórtico de pedágio e semáforo vertical escuro com três luzes. O veículo usa chevron próprio. Há contorno escuro de separação e cores moderadas. Não foram usados emojis nem ativos de produtos proprietários.

O mapa continua usando OpenFreeMap/liberty com hierarquia de vias, POIs secundários reduzidos e temas claro/escuro/automático. Na condução, extrusões são ocultadas e a composição prioriza manobra, próximo alerta, velocidade, ETA e distância. Atribuição foi compactada e seu alvo aumentado para 44 px.

## Dados — contagens reais

Inventário existente: **196 radares**, dos quais **183 possuem coordenadas**. Semáforos georreferenciados em `/api/road-objects`: **6.419**, com `object_type=traffic_signal`, `source=geosampa_signals` e `official=1`.

A API de mapa consolida pontos comunitários e oficiais e suprime duplicatas/compatíveis na exibição. Por isso seu total difere da soma bruta dos inventários:

| Tipo na API pública do mapa | Quantidade |
|---|---:|
| Radar fixo | 3.491 |
| Radar semafórico | 788 |
| Câmera de avanço | 364 |
| Radar móvel | 1.307 |
| Polícia/fiscalização | 266 |
| Lombada | 1.744 |
| Pedágio | 390 |
| Semáforo comum | 6.419 |

### Base comunitária auditada

Arquivo `pesquisaradar.txt`, cabeçalho `X,Y,TYPE,SPEED,DirType,Direction`.

| TYPE | Tipo | Armazenados |
|---|---|---:|
| 1 | Radar fixo | 3.395 |
| 2 | Radar semafórico | 794 |
| 3 | Câmera de avanço | 367 |
| 5 | Radar móvel | 1.309 |
| 7 | Fiscalização | 266 |
| 8 | Lombada | 1.737 |
| 14 | Pedágio | 391 |
| Total | | **8.259** |

São 424 municípios. A classificação usa polígonos locais do IBGE; não há consulta externa por linha. A revisão em banco temporário verificou todos os 8.259 pontos contra os polígonos. Coordenadas, azimute, DirType, tipo original, velocidade e origem foram auditados; não foram encontrados registros armazenados com coordenada/direção inválida.

A carga original leu 39.975 linhas: 31.715 fora de SP e uma inválida (`Direction=635`) ficaram fora. Permanecem 8.165 comunitários não reconciliados, 51 compatíveis com oficial, 41 possíveis duplicatas e 2 conflitos. Todas essas observações são preservadas; a camada pública evita duplicar alertas compatíveis.

A reimportação foi repetida e reconheceu o lote existente, sem multiplicar registros. Contagens de todas as cidades: [municipalities.csv](municipalities.csv). Prova: [data-verification.json](data-verification.json).

### Instalação limpa e preservação

Para não depender do banco pessoal deste computador, foi incluído apenas um **snapshot de coordenadas públicas do GeoSampa**, com origem e data, em `data/geosampa_signals_snapshot.json`. Ele contém 6.419 observações, equivalentes a **6.367 coordenadas únicas** na precisão de sete casas usada pela carga inicial. Uma instalação limpa recebe esses pontos e o TXT comunitário automaticamente. O teste repetiu a inicialização e confirmou idempotência e preservação de metadados oficiais melhores.

Bancos antigos não são deduplicados destrutivamente: nesta máquina continuam os 6.419 semáforos já existentes. Não foi incluído arquivo SQLite no Git.

Comparação com o backup desta revisão:

- Radares: 196 antes / 196 depois; nenhum ausente e nenhuma alteração de conteúdo. `last_seen` foi renovado pela rotina preexistente de seeds em 116 registros.
- Objetos viários: 6.426 antes / 6.426 depois; nenhum ausente e nenhum conteúdo anterior substituído. Sete registros sem coordenadas continuam no inventário.
- Backup consistente, logs e arquivos de execução ficaram locais e ignorados pelo Git.

## Renderização — teste por tipo

Os testes abaixo usaram zoom 14, ícone carregado, filtro habilitado e toque real em símbolo. `API` e `source` são quantidades daquele tipo no viewport; `renderizados` são IDs únicos retornados por `queryRenderedFeatures`, restritos aos IDs da API. As diferenças nas camadas gerais são de colisão/decluttering, não perda no banco. Cada tipo teve pelo menos um símbolo tocável e o detalhe correto aberto.

| Tipo | API | Source | Renderizados | Detalhe por toque |
|---|---:|---:|---:|---|
| Semáforo comum — amostra urbana | 200 | 200 | 200 | Semáforo |
| Radar fixo | 1 | 1 | 1 | Radar fixo |
| Radar semafórico | 8 | 8 | 4 | Radar semafórico |
| Câmera de avanço | 1 | 1 | 1 | Câmera de avanço |
| Radar móvel | 4 | 4 | 4 | Radar móvel |
| Fiscalização | 2 | 2 | 1 | Fiscalização |
| Lombada | 1 | 1 | 1 | Lombada |
| Pedágio | 3 | 3 | 2 | Pedágio |

### Semáforos — verificação crítica completa

Mesmo recorte da auditoria inicial, centro próximo de **[-46.655, -23.563]**, 390×844, zoom 14:

- API: **198**.
- Source exclusiva `relas-signals`: **198**.
- Layer `relas-signal-icons`, minzoom 14: **198 renderizados**.
- SVG registrado no MapLibre, três cores visíveis e corpo vertical identificável.
- Toque real abriu o bottom sheet “Semáforo”, origem oficial GeoSampa.
- Desativar “Semáforos” esvaziou a source visual; a preferência continuou desativada após reload; reativar restaurou os dados.
- No zoom 12 foram encontrados 139 clusters de sinais no recorte amplo. Um cluster de 13 pontos foi tocado e expandiu para zoom 13, onde 310 sinais apareceram na visão urbana desse novo recorte.

Bboxes e métricas exatas: [browser-rendering.json](browser-rendering.json), [cluster-smoke.json](cluster-smoke.json). Não se está afirmando que todos os pontos do estado são desenhados simultaneamente.

## Mobile

Testados em Chromium:

- 375×812.
- 390×844.
- 430×932.
- 412×915, viewport Android.
- Desktop 1440×1000.

Mapa e modo motorista passaram sem overflow horizontal. Nos testes de exploração e condução, nenhum botão visível ficou abaixo de **44×44 px**. O alerta ficou abaixo da manobra, o rodapé dentro da tela e o botão de reportar acessível. Filtros, busca, detalhes, localização e resumo da rota foram exercitados.

O CSS utiliza `env(safe-area-inset-*)`, `viewport-fit=cover`, limites em `dvh` e scroll contido nos sheets. Isso protege o layout previsto para barras/notches; a geometria física de Safari, notch e barra dinâmica não foi reproduzida por um aparelho real nesta sessão.

## GPS, heading e câmera

- `watchPosition` fora e dentro de rota; alta precisão, timeout e mensagens explícitas.
- Teste de abertura com geolocalização simulada: watch ativo e indicador “GPS ativo · ±8 m”.
- A 12 m/s e heading 270°, chevron renderizado e HUD em 43 km/h.
- Parado/heading desconhecido: ponto, sem fabricar direção do veículo.
- Fix com precisão de 250 m: rejeitado e posição anterior preservada.
- Fix antigo, inválido e transição angular 359°→1°: testes automáticos passaram.
- Heading deduzido por deslocamento quando há evidência suficiente, suavização angular e da câmera.
- Zoom/tilt variam moderadamente com velocidade; não há reposicionamento da câmera após arraste até Recentralizar.
- Teste de arraste real: follow suspenso, botão visível, próximo update não trouxe a câmera de volta; Recentralizar reativou o follow.
- GPS inexistente: “GPS indisponível neste navegador”; permissão negada: “Localização negada · toque em localizar”. O mapa continuou utilizável.
- Sinal sem atualização recente ganha indicação e não mantém velocidade/alerta como se fossem atuais.
- Saída de rota exige três fixes fora do corredor antes de recalcular, com cooldown; recálculo não faz fit da rota inteira durante condução.
- Simulação pausa o watch real para não disputar câmera/HUD.

HTTPS foi exercitado em servidor isolado na porta 9443, com banco novo, certificado de teste e verificação de cadeia e hostname **ativadas**. `/api/health` retornou 200, versão 2.1.5, e o bbox oficial retornou 1.682 sinais únicos dessa instalação. Prova: [tls-smoke.json](tls-smoke.json). Chave e certificado de teste permanecem ignorados/localmente.

## Rota e alertas

Busca real por São Bernardo do Campo: HTTP 200 e resultado encontrado. Rota real Valhalla: **2.153 m, 11 instruções e 2 alertas**, motor `relas-map-v2`.

O motor usa corredor geométrico de 35 m, proximidade da linha, direção cadastrada e bearing. O cliente volta a conferir compatibilidade angular com o heading atual. Testes excluíram equipamento no sentido oposto e ponto em rua paralela a aproximadamente 110 m; direção desconhecida mantém comportamento conservador.

Em rota controlada para testar distâncias:

| Distância | Intensidade observada |
|---|---|
| 1.000 m | discreta |
| 450 m | atenção |
| 200 m | destaque |
| 70 m | forte |

Exceder 60 km/h no cenário controlado ativou contraste de excesso de velocidade. A velocidade do radar é uma referência do equipamento; não foi inventado um limite atual da via.

O resumo da rota mostra os pontos conhecidos no corredor e as próximas lombadas, semáforos e pedágios. O botão Alertar ofereceu as 13 opções e enviou tipo/coordenadas em dois toques. **O envio do smoke foi interceptado**: nenhum incidente sintético foi inserido na base real. Backend, feedback e expiração foram exercitados em bancos temporários.

Prova detalhada: [browser-navigation.json](browser-navigation.json).

## Cache e atualização

- Shell `relas-v215-road-test` e assets com `v=215`.
- HTML, bootstrap e service worker recebem política de revalidação; navegação é network-first.
- Ícones versionados também nos detalhes e alertas, corrigindo reaparecimento de SVG antigo no cache HTTP.
- Instalação do shell é atômica: só ativa após os assets essenciais terem sido cacheados.
- APIs e autenticação não são armazenadas pelo worker.
- Caches antigos são removidos apenas no namespace `relas-`.
- A URL de lançamento com `?v=215` evita o HTML que versões anteriores já haviam deixado fresco no cache do navegador.
- Atualização não reinicia condução ativa: o evento de troca de controller foi simulado, o app manteve o HUD e registrou atualização pendente, aplicada ao encerrar a navegação. O teste passou.

Não foi prometido mapa offline completo: tiles, busca e cálculo de rota continuam externos.

## Performance

Queries por bbox/tipos, índices SQLite, cache pequeno de viewports, atualização incremental comunitária e sources GeoJSON foram preservados. As conexões abertas pelas consultas comunitárias agora são fechadas explicitamente após commit/rollback.

As consultas de viewport no smoke final ficaram aproximadamente entre **14 e 43 ms**, incluindo ida/volta HTTP local e leitura do dado da source. Isso não é benchmark de rede móvel.

Na medição final de dois segundos durante animação do mapa, foram observados 146 callbacks `requestAnimationFrame`, aproximadamente 73/s, com p95 de intervalo de 27,7 ms. É uma medição do navegador de automação e do agendamento de frames, não uma garantia de FPS da GPU ou de desempenho em celular. A variação entre execuções ficou registrada na sessão; o relatório usa o resultado da execução final.

## Admin

Nenhum redesign amplo. O painel e suas operações foram mantidos. Foi corrigido o envio indevido de `Authorization: Bearer null` na seção comunitária quando uma sessão válida usa cookie.

Smoke autenticado: seção Base comunitária SP abriu; filtro São Bernardo do Campo retornou **192**; logout concluído. [admin-smoke.json](admin-smoke.json), [screenshot](admin-smoke.png).

A senha demonstrativa foi retirada do código e do formulário. Agora vem de `RELAS_ADMIN_PASSWORD` ou de um arquivo local aleatório no diretório persistente, sem publicar valor no Git. O README explica o acesso.

## Bugs corrigidos

1. Sinais competindo com todos os tipos na mesma source/layer e ficando ocultos.
2. Radar fixo encoberto por símbolos comunitários de menor prioridade próximos.
3. SVG antigo reaparecendo nos detalhes/alertas por URL sem versão.
4. Falta de watch de localização fora de rota, chevron e Recentralizar.
5. Atualização de câmera mesmo após arraste; heading sem suavização e fix ruim aceito.
6. Watch real disputando câmera com a simulação.
7. Uso de GPS/voz sem proteção suficiente para API indisponível.
8. Alvos pequenos e desalinhamentos do HUD/safe areas; atribuição repetindo quatro símbolos de informação ao aumentar o alvo.
9. Texto corrompido em rota/voz e cluster.
10. Service worker existente mas sem registro; HTML de lançamento com query sem política de revalidação.
11. Reload de atualização capaz de interromper condução; agora adiado até encerrar.
12. Conexões de consultas comunitárias não fechadas pelo simples uso do contexto SQLite.
13. Header de autenticação vazio na seção comunitária do Admin.
14. Traceback por cliente fechar conexão HTTP durante troca de viewport/reload; erros esperados de socket são tratados sem esconder falhas de banco.
15. Instalação nova dependendo de dados que só existiam no banco desta máquina; snapshot público e bootstrap idempotente foram adicionados.

## Problemas ainda conhecidos

- Quatro avisos numéricos do estilo OpenFreeMap/liberty. Foram reproduzidos em um mapa isolado, com o mesmo MapLibre e **sem código/camadas do Relas**. Não houve erro JavaScript da aplicação nem erro HTTP no smoke final do mapa.
- Convenção de `DirType` e interpretação do azimute seguem 0=desconhecido/todos, 1=um sentido, 2=dois sentidos. Falta documentação do fornecedor; os originais foram preservados.
- Corredor geométrico não garante exclusão em vias paralelas muito próximas, viadutos e níveis diferentes; não há map matching topológico por segmento.
- Nem todo radar do inventário possui coordenadas. O app não inventa posição para os 13 radares não mapeados e para objetos antigos sem coordenadas.
- Semáforos oficiais deste snapshot são da capital. O ícone não informa a fase atual das luzes nem o tempo de abertura.
- Cadastro comunitário/móvel não é confirmação de equipamento operando naquele instante.
- Desempenho físico, precisão em caminhada, bateria, voz audível, Safari/WebKit e GPS em segundo plano devem ser observados no primeiro teste de rua. Layouts de viewport não substituem esses testes.
- Moderação/reputação e proteção distribuída contra abuso de relatos não foram expandidas nesta revisão de estabilidade.

## Testes executados

- `python selftest.py`: passou, preservando a suíte funcional existente.
- `python -m unittest test_community test_road_review -v`: **10 testes passaram**, incluindo instalação limpa, migração, idempotência, preservação oficial, autenticação, cache/headers, coordenadas e direção.
- `node --test tests/navigation.test.cjs`: **4 testes passaram**.
- Python compile e syntax checks de app, boot, SW, navegação, Admin e runner: passaram.
- Dez endpoints/assets do servidor final retornaram 200, incluindo radares, road_objects, features, health, shell e ícones: [api-smoke.json](api-smoke.json).
- Smokes de renderização, todos os tipos, toque, filtros, persistência, cluster, mobile, rota, GPS, follow, relato e update: passaram.
- Comparação com backup e reimportação repetida: passou.
- TLS com verificação de certificado/hostname, em instalação limpa: passou.

Resumos: [tests-summary.json](tests-summary.json), [data-verification.json](data-verification.json). Logs detalhados ficam locais e ignorados pelo Git. Scripts reproduzíveis: `scripts/road_audit.py`, `scripts/road-browser-smoke.js`, `scripts/road-navigation-smoke.js` e `scripts/run-road-browser.cjs`.

Alguns primeiros testes de automação precisaram de ajuste: aguardar o fim da inércia de um arraste, esperar um diálogo fechado como elemento oculto e aguardar a ativação/reload do service worker. Esses casos foram separados de falhas do produto; os resultados acima são das execuções finais com asserções ativas.

## Screenshots

- [Antes da revisão, mobile](before-mobile.png)
- [Desktop — mapa](desktop-map.png)
- [Mobile 375×812](mobile-375.png)
- [Mobile 390×844](mobile-390.png)
- [Mobile 430×932](mobile-430.png)
- [Android 412×915](mobile-412.png)
- [Modo motorista](mobile-driver.png)
- [Filtros](filters.png)
- [Detalhe de radar](detail-fixed.png)
- [Semáforos no mapa](semaforos-map.png)
- [Detalhe de semáforo](detail-signal.png)
- [Lombada](detail-bump.png)
- [Alerta com excesso de velocidade](alert.png)
- [Admin — regressão](admin-smoke.png)

## Arquivos e versionamento

Alterações focadas em `app/app.js`, `app/navigation-core.js`, `app/index.html`, `app/styles.css`, `app/boot.js`, `app/sw.js`, `app/icons/`, `community.py`, `server.py`, testes e documentação. Admin recebeu somente ajuste de credencial/formulário e correção de autenticação comunitária.

O remoto informado estava vazio e a pasta recebida não era um checkout. Foi iniciada `main`, preservando a base recebida e reunindo projeto, correções, dados públicos e evidências neste primeiro commit. Não há histórico anterior a reescrever; não se usa force push.

Bancos, backups, arquivos de senha, chaves, `.env`, logs, `.playwright-mcp`, dependências e temporários são ignorados. O commit é revisado com `git diff`/`git diff --check` e inspeção dos arquivos staged; o hash e o resultado do push são informados na entrega.
