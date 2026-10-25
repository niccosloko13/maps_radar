# Relas Precision Engine V2

## Status

Implementado e validado com testes automatizados, traces sinteticos e navegador. **Rollout opt-in; baseline continua padrao.** Nao houve teste de rua nem medicao de precisao fisica. Nenhum deploy ou push desta branch foi feito.

Checkpoint anterior: `e2481d5154cb344ac79004145edd1777c80f5d8e`. Branch: `feat/location-precision-v2`. Os snapshots `baseline-app.txt` e `baseline-navigation-core.cjs` preservam a referencia comparativa anterior.

## Arquitetura e alteracoes

- `app/location/`: parametros centralizados, geometria compartilhada, validacao de fixes, maquina de estados, filtro Kalman CV de quatro estados em metros locais, heading circular, corredor dinamico, matcher top-K com custos e histerese, confianca/blending, previsao limitada, telemetria, replay, metricas e debug opcional.
- `app/navigation-core.js`: kernel de projecao compartilhado entre navegacao e matcher, evitando algoritmos divergentes.
- `app/app.js`: selecao baseline/V2, integracao GPS e camera, fallback seguro, estados de sinal, supressao de alertas/voz durante previsao, APIs locais de gravacao/replay. A simulacao existente permanece disponivel.
- `app/boot.js`, `app/sw.js`, `app/index.html`: carregamento sem bundler, fallback em falha de modulo e assets/cache v221.
- `scripts/location-*.cjs` e `scripts/location-browser-*.js`: fixtures, benchmark comparativo, testes de integracao e performance.
- Sete `tests/location-*.test.cjs` e dez traces permanentes em `tests/fixtures/location/`.
- Scripts de smoke existentes e `selftest.py`: versao de assets atualizada; runner inclui smoke V2. `.gitignore` exclui sessoes privadas, logs e temporarios locais.

Nao foram alterados servidor, schema, banco, autenticacao, dados de radares ou desenho geral da interface. Nenhuma dependencia nova foi instalada. Nenhum upload de GPS/telemetria foi introduzido pelo motor; chamadas existentes de rota/busca/viewport permanecem.

## Fluxo

Geolocation/watchPosition -> quality -> state -> adaptive motion filter -> heading -> candidate corridor -> top-K costs -> hysteresis -> confidence -> blended output. RAW, ESTIMATED, MATCHED e OUTPUT ficam separados. Accuracy bruta e preservada; snap nao e apresentado como melhora fisica do GPS.

Dead reckoning exige tracking anterior, inicia depois de um segundo sem fix e termina em cinco segundos. LOST congela posicao e limpa velocidade/alertas. Recuperacao readquire confianca, inclusive quando timers do navegador nao rodaram em background. Falha no motor ou bootstrap retorna ao baseline.

## Validacao executada

| Verificacao | Resultado |
| --- | --- |
| `node --test tests/*.test.cjs` | 49/49 PASS (45 novos + 4 existentes) |
| `.venv/Scripts/python.exe -m unittest discover -p "test_*.py"` | 17/17 PASS |
| `.venv/Scripts/python.exe selftest.py` | PASS |
| JavaScript syntax checks e `git diff --check` | PASS |
| Benchmark Node em dez cenarios sinteticos | Concluido; resultados brutos preservados |
| Chrome: GPS, aquisicao, tracking, previsao, LOST, recuperacao | PASS |
| Replay repetido, seek/step e render local | Deterministico |
| Falha de runtime injetada | Baseline funcional; um diagnostico esperado |
| Modulo ausente, service worker bloqueado | Falha de carregamento observada e baseline funcional |
| Regressao mapa/navegacao baseline | Busca, rota, alertas, follow/recenter, filtros, detalhes e report sheet PASS |
| Mobile | 375x812, 390x844, 430x932 e 412px Android simulado; sem overflow |

O proxy local de teste serviu frontend e consultas publicas existentes; nao inicializou SQLite nem permitiu insercao de reportes. Os testes de falha de configuracao/autenticacao existentes geram mensagens esperadas nos logs da suite Python. O proxy pode registrar cancelamento de conexao durante recarga; isso nao e falha do motor.

## Evidencias e desempenho

- [Smoke V2 final](browser-v2-final.json): zero pageerrors; raw accuracy 8 m e altitude 700 preservadas; confianca tracking 0.902; previsao em 2,5 s; LOST em 6,5 s; recuperacao com confianca limitada a 0.6.
- [Regressao do mapa](browser-baseline-map.json) e [navegacao](browser-baseline-navigation.json): todos os oito tipos, sinais, filtros, detalhes e fluxos anteriores exercitados.
- [Performance Chrome](browser-performance.json): CPU 4x, rota de 20.000 segmentos e 600 fixes/caso. Mediana 0.30 ms sem telemetria / 0.50 ms com telemetria; p95 1.00 ms em ambos. Ultima busca examinou 263 segmentos. Preprocessamento unico da rota: 35.60 ms, sincrono.
- [Baseline](baseline.json), [V2](new-engine.json), [interpretacao comparativa](BENCHMARK.md), [parametros](PARAMETERS.md) e [limitacoes](KNOWN_LIMITATIONS.md).

Nao ha ground truth: erro fisico permanece null. A reducao de trocas nas paralelas sinteticas demonstra estabilidade nesse trace, nao identifica a via real com certeza. Distancia media da V2 em route-departure exclui unmatched; consultar match rate evita uma comparacao enganosa.

Screenshots: [debug mobile](debug-mobile.png), [replay](replay-mobile.png), [mapa mobile](legacy-mobile-390.png), [motorista](legacy-mobile-driver.png), [filtros](legacy-filters.png), [radar](legacy-detail-fixed.png), [semaforo](legacy-detail-signal.png), [lombada](legacy-detail-bump.png), [alerta](legacy-alert.png).

## Problemas encontrados e corrigidos

- Gravacao iniciada no meio da viagem ou ring truncado nao reproduzia estado anterior: checkpoint completo antes do primeiro registro retido.
- Reroute no meio da sessao: contexto de geometria versionado por fix, sem aplicar a ultima rota a toda a viagem.
- Wrappers de rota recriados consumiam o limite de contextos: identidade baseada no array canonico de coordenadas.
- Retorno do GPS apos gap sem timer LOST poderia prever cedo demais: readquisicao obrigatoria mesmo sem callback intermediario.
- Heading GPS contraditorio e velocidade impossivel: validacao/penalizacao conservadora, sem contaminar filtro com outliers.
- Teste de bootstrap podia ser mascarado por cache: contexto separado com service workers bloqueados e prova explicita da falha.
- Replay instantaneo renderizava excessivamente: processamento batch com render final, seek sem callbacks intermediarios.

## Uso e rollback

No console do app, apenas para teste controlado:

```js
relas.setLocationMode('v2');
relas.locationTelemetry.start();
// Depois do trajeto, parado:
relas.locationTelemetry.stop();
const trip = relas.locationTelemetry.exportJSON();
```

Gravacao e opt-in, em RAM, limitada a 3000 registros/uma hora/16 contextos. Exportacao e explicita; reload perde a sessao. Salve traces reais em `artifacts/location-precision-v2/private/`, ignorado pelo Git.

```powershell
node scripts/location-benchmark.cjs --session artifacts/location-precision-v2/private/trip.json
```

Para replay visual: `relas.locationReplay.load(trip).setSpeed(1).play()`; `pause()`, `step()`, `seek(index)` e velocidades .25/.5/1/2/5/10/instant disponiveis. Sair com `relas.exitLocationReplay()` retoma GPS. O replay pausa conducao/voz e nao deve ser usado dirigindo.

Debug opcional: `localStorage.setItem('relas-location-debug','1')` e proximo fix/reload. Voltar ao comportamento anterior: `relas.setLocationMode('baseline')`. Remover flag de debug desativa overlays. Falhas da V2 acionam fallback independentemente dessa escolha.

## Pendencias

Coletar sessao real consentida com parada, baixa velocidade, curva, via paralela e perda de GPS; comparar baseline/V2 offline e calibrar parametros antes de ativar por padrao. Medir em celular fisico. Confianca ainda e heuristica; matcher conhece polilinha planejada, nao toda a rede viaria. Indice grande e replay instantaneo ainda sao sincronicos. HMM/Viterbi e backend matching permanecem fora desta fase.
