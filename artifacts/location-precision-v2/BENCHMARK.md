# Baseline x V2 — resultados objetivos

Mesmos dez traces sinteticos permanentes, sem ground truth medido. O baseline usa regras GPS do checkpoint e projecao geometrica legada; nao possuia state machine, confianca ou dead reckoning. Portanto zero nessas colunas do baseline significa ausencia do recurso, nao superioridade.

Execucao reproduzivel: `node scripts/location-benchmark.cjs`. JSON: [baseline](baseline.json), [V2](new-engine.json). O tempo de construcao do indice e separado da distribuicao de processamento. Nao foram usados Date.now/Math.random para gerar os inputs. Medicoes de CPU naturalmente variam entre execucoes.

| Trace | Rejeitados B/V2 | Trocas B/V2 | Distancia media a rota B/V2 (m) | Taxa match V2 | p95 V2 (ms, Node) |
| --- | ---: | ---: | ---: | ---: | ---: |
| straight-clean | 0 / 0 | 0 / 0 | 0.00 / 0.00 | 1.00 | 0.1114 |
| straight-noisy | 0 / 0 | 0 / 0 | 7.74 / 3.53 | 1.00 | 0.0138 |
| parallel-road | 0 / 0 | 124 / 0 | 4.20 / 10.00 | 1.00 | 0.0205 |
| intersection | 0 / 0 | 2 / 0 | 2.51 / 1.40 | 1.00 | 0.0212 |
| turn | 0 / 0 | 1 / 1 | 0.00 / 0.02 | 1.00 | 0.0186 |
| gps-dropout | 0 / 0 | 0 / 0 | 0.00 / 0.00 | 0.99 | 0.0296 |
| outlier | 1 / 1 | 0 / 0 | 0.00 / 0.00 | 1.00 | 0.0134 |
| accuracy-degradation | 0 / 0 | 0 / 0 | 5.69 / 1.10 | 1.00 | 0.0115 |
| heading-wrap | 0 / 0 | 0 / 0 | 2.80 / 2.80 | 1.00 | 0.0093 |
| route-departure | 0 / 0 | 0 / 0 | 92.88 / 1.08 | 0.51 | 0.0181 |

## Como interpretar

- No trace de paralelas houve 124 trocas de projecao no baseline e zero no V2. O V2 usa heading e historico. Isso mostra estabilidade nesse cenario sintetico, nao prova que escolheu a via real numa viagem.
- A distancia a rota pode aumentar ao manter uma escolha coerente, como nas paralelas. Menor distancia geometrica isolada nao e o objetivo.
- Em route-departure, a distancia media V2 e calculada somente nos matches validos: os pontos afastados foram devolvidos unmatched. Comparar essa media com o baseline sem a taxa de match produziria uma conclusao enganosa.
- A accuracy original continua identica entre variantes. Nao houve medicao de erro fisico, heading real ou acuracia centimetrica. Campos de ground truth permanecem null.
- Modelos gravados no meio de uma sessao e rings truncados usam checkpoint inicial no replay V2. O baseline contrafactual usa o estado baseline gravado quando disponivel, ou a ultima observacao do checkpoint V2; nao reconstrui uma historia baseline nunca gravada.

## Chrome com CPU reduzida (4x)

Rota sintetica de 20.000 segmentos, 600 fixes por caso. Hardware do computador via CDP, **nao um iPhone/Android real**. [Resultado bruto](browser-performance.json).

| Telemetria | Mediana (ms) | p95 (ms) | Primeiro fix (ms) | Segmentos examinados no ultimo fix |
| --- | ---: | ---: | ---: | ---: |
| Desligada | 0.30 | 1.00 | 4.20 | 263 |
| Ligada | 0.50 | 1.00 | 10.20 | 263 |

Construcao do indice: **35.60 ms** com CPU 4x. O custo e unico por geometria/recálculo; no app ele e feito ao receber a rota. Pode causar pausa curta em rotas enormes e nao deve ser confundido com processamento sustentado por fix. Medianas <5ms e p95 <15ms foram atingidos nesses testes. Nenhum Web Worker foi introduzido.

## Sessao real exportada

```powershell
node scripts/location-benchmark.cjs --session artifacts/location-precision-v2/private/trip.json
```

Resultados vao para private/ por padrao e nao sao versionados. Para um diretorio de saida explicito, use --output. Um replay pode manter seu proprio snapshot de parametros, em vez de assumir defaults posteriores. Nenhuma sessao real estava disponivel nesta tarefa.
