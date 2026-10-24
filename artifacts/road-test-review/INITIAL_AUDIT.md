# Auditoria inicial — Relas / teste de rua

Estado observado antes de alterar frontend/backend nesta revisão: 24/10/2026.

## Estrutura e fluxo

- Frontend público: `app/index.html`, `app/boot.js`, `app/app.js`, `app/styles.css`.
- Backend Python/HTTP/SQLite: `server.py`; fonte comunitária, bbox, reconciliação e alertas da rota: `community.py`.
- MapLibre GL JS 5.24.0 local em `app/vendor/`, com fallback CDN; mapa-base OpenFreeMap liberty.
- Inventário oficial: `radars`, `road_objects`; comunitário: `map_points` e `community_batches`.
- Fonte visual `relas-points` recebe `/api/map/features?bbox=...&types=...`; inclui todos os tipos. Sem source/layer exclusiva de semáforos.
- Camadas: `relas-clusters`, `relas-count`, `relas-icons`, `relas-route-case`, `relas-route-line`, `relas-position`, `relas-route-alert-icons`.
- Rotas: `/api/route`; busca: `/api/autocomplete`; contribuições: `/api/map/report` e `/api/map/feedback`.
- Inventário original continua em `/api/radars` e `/api/road-objects`.
- Filtros individuais persistem em `localStorage`.
- CSS responsivo em `app/styles.css`; diálogo nativo como bottom sheet.
- `app/sw.js` existe na versão v200, mas **nenhum service worker estava registrado**, e o loader não o registrava.

## APIs verificadas

- `/api/radars`: HTTP 200, 196 registros de inventário.
- `/api/road-objects`: HTTP 200, 6.419 registros georreferenciados, todos `object_type=traffic_signal`, origem `geosampa_signals`, `official=1`.
- Amostra real: latitude -23.46870002, longitude -46.6974; nome Cruzamentos Semaforizados; timing desconhecido, sem inventar fase atual.
- `/api/map/features`: HTTP 200. No recorte da Paulista/Consolação foram recebidas 223 features, 198 semáforos, zoom 14, viewport 390×844.
- A source do mapa continha os 198 semáforos; apenas **77 IDs únicos de semáforo estavam renderizados**, devido a colisões/prioridades da camada compartilhada. O SVG estava carregado e o filtro permitia os sinais.
- Estado inteiro, features visíveis após reconciliação: fixos 3.491; semafóricos 788; avanço 364; móveis 1.307; fiscalização 266; lombadas 1.744; pedágios 390; semáforos 6.419. Isso difere das contagens brutas importadas, pois duplicatas e compatíveis oficiais são consolidados para exibição.
- Números e bbox exatos em `initial-audit.json`.

## Console/HTTP/renderização

- Sem erro JavaScript no carregamento inicial.
- Quatro avisos MapLibre: “Expected value to be of type number, but found null instead”. Origem em worker do estilo; exige isolar se é expressão própria ou mapa-base.
- As APIs exercitadas responderam 200; sem erro HTTP de asset observado nesse carregamento.
- Ícones já eram SVG, porém todos usavam a mesma placa/pino grande e havia pouco contraste de forma entre categorias.
- Cluster mostra texto corrompido `? R`; há textos com acentuação corrompida no fluxo de rota/voz.

## GPS e modo motorista — problemas encontrados por leitura e observação

- Ao abrir o mapa, nenhuma posição é solicitada/acompanhada; é necessário tocar em localização, que usa apenas `getCurrentPosition`.
- `watchPosition` existe apenas durante rota; não filtra precisão ruim nem sinal antigo.
- Posição é sempre círculo, sem heading/chevron.
- A câmera é movida a cada atualização, mesmo após arrastar. Não há Recentralizar nem suspensão de follow.
- Sem smoothing angular, dedução robusta de movimento ou aviso de sinal desatualizado.
- `navigator.geolocation` e `speechSynthesis` são usados em pontos sem verificar disponibilidade.
- Simulação não interrompe o watch real; os dois podem disputar câmera e HUD.
- Próximo alerta é selecionado pela rota sem conferir bearing atual do veículo.
- Radar acima da velocidade não aumenta o contraste por excesso de velocidade.

## Mobile

- 390×844 carregou sem overflow horizontal; botões visíveis de exploração tinham altura >=44 px.
- HUD compacto tem botões de 32–42 px em telas menores, abaixo do alvo de toque solicitado.
- Painéis e alertas possuem posições fixas sem acomodar completamente safe area no topo e rodapé.
- Atribuição expandida pode cruzar botão de reportar/GPS.
- Falta um indicador de erro/precisão GPS utilizável fora de rota.
- HTTP por IP da rede local não é contexto seguro para GPS em celulares. Precisamos deixar o motivo explícito e documentar acesso HTTPS; localhost do computador não equivale ao localhost do telefone.

## Testes existentes

`python selftest.py` passou. `python -m unittest test_community -v`: 8 passaram. Isso não substitui os testes visuais e de GPS desta revisão.

## Git e privacidade

A pasta recebida não tinha `.git`. O clone do remoto informado confirmou repositório vazio, sem histórico a preservar. Foi iniciada a branch `main` na pasta atual. Bancos, backups, logs e arquivos temporários serão excluídos do commit.

## Correções planejadas, sem redesign estrutural do Admin

Separar semáforos em source/layers próprias; melhorar a leitura dos SVGs; corrigir GPS, heading, follow e recenter; respeitar safe areas e alvos de 44 px; estabilizar atualização de cache; testar renderização por tipo, rota, fallback e viewports solicitados. Preservar as APIs, o inventário e a estrutura administrativa existentes.
