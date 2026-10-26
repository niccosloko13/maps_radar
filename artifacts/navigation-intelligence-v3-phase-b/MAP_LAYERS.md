# Camadas e navegação

## Sources

`road-events`: GeoJSON de pontos, clustering MapLibre com raio 45 e max zoom 12. `road-event-geometries`: linhas e regiões oficiais. Sem DOM markers para os novos registros.

Camadas: road-events, road-events-clusters, road-traffic-events, road-traffic-lines, road-weather-regions, roadworks, closures, floods, weather, prf-posts, pmrv-bases, toll-plazas, support-bases, rain-stations e administrative. Radares ficam acima das camadas auxiliares na ordem de renderização.

Críticos têm elegibilidade desde zoom 7, demais eventos/pedágios/postos desde 11; apoio, pluviômetros e unidades administrativas desde 14. Clusters representam pontos afastados. Há redução por colisão de símbolos: contagem da source não é contagem renderizada.

Camadas → Dados de estrada reúne presets Essencial/Estrada/Completo e seleção individual persistida. A escolha explícita é preservada; Road Mode prepara sugestão de Estrada, sem trocar automaticamente o preset. Filtros dos radares existentes são independentes. Camadas desabilitadas não geram alertas auxiliares.

## Corredor

CITY: 1 km atrás / até 10 km à frente; ROAD: 3 km atrás / até 50 km à frente, janela adaptada por velocidade. Bbox no banco e projeção posterior; distância lateral 20m para eventos, 35m infraestrutura e 120m para estação/região climática. Sentido cardinal conhecido incompatível é excluído. Linhas e polígonos usam sua geometria real; km não é convertido em coordenada presumida.

Resumo Na rota mostra contexto distante; card/voz usam a janela curta do AlertManager. GPS perdido/predito não autoriza voz. P0 radar iminente, P1 crítico sustentado por gravidade/bloqueio total, P2 manobra, P3 obra/interdição, P4 trânsito/clima, P5 infraestrutura. Postos/pedágios/apoio sem voz por padrão. Estação de chuva nunca vira alerta regional ou voz.

## Evidências reais

- ANTT Miracatu: API 1 / source 1 / renderizado 1; clique abriu detalhe, atualização julho/2026 e tarifa ausente.
- SIBH São Bernardo: API 1 / source 1 / renderizado 1; leitura/acumulado de estação, sem alegação de chuva forte.
- PRF: 27 no inventário, zero pins por ausência de coordenada comprovada.
- ARTESP CCM, PMRv, Defesa Civil e apoio: zero registros reais novos no mapa. Não confundir os screenshots TEST com essas fontes.

## Evidências TEST isoladas

Onze tipos testados individualmente: acidente, obra, interdição, alagamento, PRF, PMRv, pedágio, SAU, pluviômetro, chuva e congestionamento. Cada um renderizou e abriu detalhe por clique real. Source conjunta 11 pontos + 2 geometrias; colisão inicial mostrou três símbolos, sem fingir que todos estavam renderizados ao mesmo tempo. Cluster de 11 verificado. Fluxo completo em outro banco TEST: 11 eventos API/corredor, 10 candidatos auxiliares após excluir estação de chuva, radar mantido P0.

## Limitações

Sem overlay meteorológico regional validado, sem trânsito real ARTESP por falta de chaves, sem coordenadas PRF aprovadas. Estados normal/selected/critical/stale possuem molduras SVG próprias: selecionado ciano, crítico vermelho e stale tracejado com opacidade reduzida. Isso não torna feeds ausentes operacionais.


## Classificação final

Camadas com dados reais verificadas durante os testes: toll-plazas e rain-stations. Onze tipos TEST renderizados/clicados não equivalem a onze fontes operacionais. Duas geometrias TEST carregadas não são eventos reais. No encerramento, as leituras SIBH expiraram: zero elegíveis, snapshot preservado e fonte STALE. Nenhum teste físico executado; INCOMPLETE/BLOCKED permanece.
