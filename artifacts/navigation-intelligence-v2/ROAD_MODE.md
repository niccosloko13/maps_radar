# Modo Estrada — Fase A

Detector determinístico em `app/navigation/intelligence.js`, ativo durante navegação com rota. Saídas CITY_MODE/ROAD_MODE; override Auto/Cidade/Estrada em Camadas → Modo de via e voz, ou no botão de opções do HUD.

| Evidência do segmento atual | Pontos |
| --- | ---: |
| road_ref/nome com SP-nnn ou BR-nnn | .65 |
| road_class motorway/trunk e respectivos links | .65 |
| velocidade >=22m/s | .20 |
| duas ou mais faixas, se informadas | .05 |
| espaçamento entre cruzamentos >=1000m, se informado | .10 |

Score limitado a 1, sem alegação probabilística. Entra com >=.60 por oito segundos; sai com <=.30 por quinze segundos. Velocidade sozinha NÃO decide rodovia. Ausência de faixa/classe/acesso não é inventada. O adaptador de rota preserva ref/nome/tipo/modificador/bearing/geometria fornecidos. A resposta real SBC–Santos trouxe SP-150/BR-050, embora road_class estivesse ausente. Nenhuma decisão usa toda a rota para afirmar que o veículo já está na rodovia: usa o segmento/instrução corrente.

Modo Estrada oculta semáforos comuns das layers de contexto e do destaque na rota; não oculta radar semafórico. Não altera a preferência do filtro. Ao encerrar navegação, as layers comuns são restauradas. Perfil de veículo pesado ainda não existe.

Câmera: cidade usa zoom próximo e contexto lateral; estrada usa zoom 15.3–15.8 em velocidade e 16.4 perto de manobra, pitch 48°, padding superior ~40% e foco até 160m à frente. Cidade: look-ahead até 65m. A posição do marcador não é deslocada para esse foco. Animação de 450ms, heading circular e posição da câmera suavizados; arrastar suspende follow, Recentralizar restaura.

Progresso usa routeMatch.along quando o matcher V2 tem confiança suficiente; fallback é a projeção compartilhada. Avanço é monotônico, rejeita saltos incompatíveis com dt e fixa fora da rota >25m. Nova rota/recalculo/início de navegação reinicia progresso. O source GeoJSON usa lineMetrics; line-gradient deixa TRAVELED quase invisível e REMAINING destacado, sem reenviar 20 mil vértices a cada fix. Modelo splitRoute também é testado.

O detector não faz map matching de toda a rede viária fora de rota. Sem ref/classificação disponível, permanece conservador e oferece override manual. Não foi calibrado com viagem física nesta entrega.
