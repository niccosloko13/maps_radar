# Diagnóstico de layers — UI V3

Checkpoint: `f23e22aa8a1bbdabfc1b9146701839dd0169755f`. Fonte da auditoria: API pública de produção antes desta publicação; testes da nova UI no proxy local, sem escrita em produção.

## Inventário e normalização

`/api/road-objects?mapped=0`: 6426 registros `traffic_signal`, 6419 com coordenadas, 7 sem coordenadas. `community.legacy()` normaliza `traffic_signal` -> `signal`, `radar_semaforo` -> `signal_radar`, `physical_bump`/`lombada_eletronica` -> `bump`. A API GeoJSON inclui somente registros mapeáveis e ativos; reconciliação pode suprimir duplicata comunitária confirmada. Os 7 registros sem coordenadas não podem ser desenhados e não foram geocodificados nem alterados.

`/api/radars`: 196 registros. `/api/map/features` estadual: 14769 features, combinando inventário antigo e comunitário. As contagens não são somáveis entre endpoints: os radares antigos já entram no GeoJSON.

| Tipo GeoJSON | API estadual |
| --- | ---: |
| bump | 1744 |
| toll | 390 |
| police | 266 |
| signal_radar | 788 |
| red_light | 364 |
| mobile | 1307 |
| fixed | 3491 |
| signal | 6419 |

## Prova de renderização

Viewport mobile 390x844; zoom 14. Cada linha usa seu próprio bbox, registrado em `browser-map.json`, com API 200, normalização sem descarte e ícone registrado. Elegíveis na source = coluna source; elegíveis na layer = pontos individuais sem `point_count`. Renderizados contam IDs únicos dentro dos IDs retornados pela API, evitando duplicação de tiles.

| Tipo | API do viewport | GeoJSON/source | Renderizados | Detalhe ao toque |
| --- | ---: | ---: | ---: | --- |
| signal | 202 | 202 | 202 | Semáforo |
| fixed | 1 | 1 | 1 | Radar fixo |
| signal_radar | 8 | 8 | 8 | Radar semafórico |
| red_light | 12 | 12 | 12 | Câmera de avanço |
| mobile | 4 | 4 | 4 | Radar móvel |
| police | 2 | 2 | 2 | Fiscalização |
| bump | 1 | 1 | 1 | Lombada |
| toll | 1 | 1 | 1 | Pedágio |

Teste dedicado Paulista: API 198; source `relas-signals` 198; layer `relas-signal-icons` 198 renderizados. Source separada, cluster até zoom 12, overview 13, individual 14+. Minzoom não exige 17. Filtro desligado esvazia source; preferência sobrevive a reload. Não foi encontrado mismatch `traffic_signal`/`signal` na API atual.

## Causas comprovadas e correções

1. Colisão de símbolos: fixture local com quatro equipamentos próximos produziu **1 renderizado** com `icon-allow-overlap=false` e **4** com a nova política. Ícones de segurança e de rota permitem overlap; labels de velocidade permanecem opcionais. Em densidade extrema, sobreposição ainda existe; clusters reduzem ruído até zoom 12.
2. Preferências persistidas: uma categoria desligada continua desligada. Não é perda no banco. Painel agora informa contagem visível, estado e botão “Mostrar todas”; chip informa filtros ativos. Novas categorias migram sem reativar as antigas escolhas.
3. Obras/acidentes: backend armazena `kind=other` e `report_kind=works/accident`. Nova normalização de apresentação gera `display_kind`/`display_icon`, preservando dados originais. Render, filtro e clique testados com fixture local; zero relatos ativos desses dois tipos na auditoria.
4. Relevância em rota antes reduzia demais a opacidade dos pontos de contexto (0.28); agora 0.48 e alertas na rota em layer destacada.
5. Cache: shell v222 inclui JS/CSS/SVG novos. APIs continuam fora do cache privado. Atualização durante direção continua adiada.

Não se atribui a dados faltantes um bug de CSS. Os dados atuais chegam; inventário sem coordenadas e filtros/colisões são situações distintas. Registro completo: `data-audit.json`, `browser-map.json`, `browser-navigation.json`, `browser-ui-v3.json`.
