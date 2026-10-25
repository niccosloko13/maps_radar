# Parametros do Precision Engine V2

Fonte executavel: `app/location/location-parameters.js`. Snapshot: [parameters.json](parameters.json). Todos os valores abaixo sao iniciais; nao foram calibrados com GNSS real. Constantes matematicas (0/1, graus/radianos, fatores da matriz de Kalman, percentis) nao sao thresholds. Conversao geometrica e compartilhada em navigation-core.js; metros locais nao equivalem a geodesia centimetrica.

## BASELINE

Compatibilidade temporaria com o checkpoint; nao usar para calibrar V2.

| Parametro | Valor |
| --- | --- |
| `BASELINE.maxJumpSpeed` | `70` |
| `BASELINE.maxJumpGap` | `15` |
| `BASELINE.derivedMinDt` | `0.5` |
| `BASELINE.derivedMaxDt` | `10` |
| `BASELINE.derivedMinTravel` | `5` |
| `BASELINE.accuracyFactor` | `0.3` |
| `BASELINE.headingTravel` | `8` |
| `BASELINE.headingWeight` | `0.4` |

## QUALITY

Barreiras conservadoras para entrada GPS; accuracy e raio reportado, scores nao sao probabilidades calibradas.

| Parametro | Valor |
| --- | --- |
| `QUALITY.accuracyScores` | `[[5,1],[10,0.95],[20,0.85],[35,0.7],[50,0.55],[75,0.35],[100,0.2]]` |
| `QUALITY.maxAccuracy` | `100` |
| `QUALITY.maxAgeMs` | `15000` |
| `QUALITY.futureMs` | `5000` |
| `QUALITY.maxSpeed` | `70` |
| `QUALITY.maxAcceleration` | `12` |
| `QUALITY.innovationSigma` | `4` |
| `QUALITY.uncertaintyFactor` | `2` |
| `QUALITY.minDt` | `0.2` |
| `QUALITY.gapResetSeconds` | `15` |
| `QUALITY.outlierFloor` | `18` |
| `QUALITY.innovationPenalty` | `0.5` |
| `QUALITY.frequencyPenalty` | `0.8` |
| `QUALITY.headingPenalty` | `0.8` |

## FILTER

Modelo de velocidade constante em metros locais; ruido por perfil e R derivado de accuracy. Valores iniciais exigem traces reais.

| Parametro | Valor |
| --- | --- |
| `FILTER.metresLatitude` | `110540` |
| `FILTER.metresLongitude` | `111320` |
| `FILTER.minimumSigma` | `3` |
| `FILTER.accuracyToSigma` | `0.5` |
| `FILTER.initialVelocityVariance` | `100` |
| `FILTER.reinitializeGap` | `12` |
| `FILTER.stationarySpeed` | `0.8` |
| `FILTER.lowSpeed` | `3` |
| `FILTER.highSpeed` | `22` |
| `FILTER.turnDegrees` | `25` |
| `FILTER.stationaryDamping` | `0.25` |
| `FILTER.profiles.STATIONARY` | `0.2` |
| `FILTER.profiles.LOW_SPEED` | `1` |
| `FILTER.profiles.URBAN` | `3` |
| `FILTER.profiles.HIGH_SPEED` | `5` |
| `FILTER.profiles.TURNING` | `10` |
| `FILTER.profiles.GPS_DEGRADED` | `4` |

## HEADING

Ignora heading parado, usa menor delta e reduz prioridade de GPS contraditorio com movimento filtrado coerente.

| Parametro | Valor |
| --- | --- |
| `HEADING.movingSpeed` | `1.2` |
| `HEADING.minDisplacement` | `4` |
| `HEADING.gpsGoodAccuracy` | `35` |
| `HEADING.lowWeight` | `0.2` |
| `HEADING.highWeight` | `0.65` |
| `HEADING.turnWeight` | `0.85` |
| `HEADING.turnDegrees` | `30` |
| `HEADING.routeWeight` | `0.12` |
| `HEADING.velocityMin` | `1.2` |
| `HEADING.maxVelocityVariance` | `100` |
| `HEADING.contradictionDegrees` | `100` |

## STATE_MACHINE

Evidencia consecutiva evita oscilacao; adquirir/recuperar exige tres bons fixes.

| Parametro | Valor |
| --- | --- |
| `STATE_MACHINE.acquireFixes` | `3` |
| `STATE_MACHINE.badFixes` | `2` |
| `STATE_MACHINE.recoverFixes` | `3` |
| `STATE_MACHINE.goodScore` | `0.65` |
| `STATE_MACHINE.regularGapSeconds` | `3` |
| `STATE_MACHINE.predictAfterMs` | `1000` |

## MATCHER

Janela e indice espacial evitam varredura integral; custos usam distancia, heading, progresso, continuidade e previsao.

| Parametro | Valor |
| --- | --- |
| `MATCHER.cellMetres` | `150` |
| `MATCHER.maxGridCells` | `50000` |
| `MATCHER.maxSegmentCells` | `400` |
| `MATCHER.searchCells` | `2` |
| `MATCHER.behind` | `150` |
| `MATCHER.ahead` | `1000` |
| `MATCHER.stationaryAhead` | `180` |
| `MATCHER.lookaheadSeconds` | `20` |
| `MATCHER.degradedExpansion` | `1.5` |
| `MATCHER.expandedFactor` | `3` |
| `MATCHER.maxDistance` | `110` |
| `MATCHER.minimumSigma` | `8` |
| `MATCHER.topK` | `5` |
| `MATCHER.headingWeight` | `3` |
| `MATCHER.progressWeight` | `0.4` |
| `MATCHER.backwardWeight` | `2` |
| `MATCHER.jumpWeight` | `0.7` |
| `MATCHER.predictionWeight` | `0.25` |
| `MATCHER.continuityWeight` | `0.15` |
| `MATCHER.plausibleProgressFloor` | `30` |
| `MATCHER.headingMovingSpeed` | `1.2` |
| `MATCHER.outputReuseMetres` | `3` |
| `MATCHER.maxOppositeDegrees` | `125` |
| `MATCHER.maxScore` | `15` |
| `MATCHER.scoreDecay` | `4` |
| `MATCHER.separationFloor` | `0.5` |
| `MATCHER.separationWeight` | `0.5` |

## HYSTERESIS

Challenger precisa margem e confirmacoes; avance adjacente coerente e segmento inviavel permitem troca imediata.

| Parametro | Valor |
| --- | --- |
| `HYSTERESIS.MATCH_SWITCH_MARGIN` | `0.6` |
| `HYSTERESIS.MATCH_SWITCH_CONFIRMATIONS` | `3` |
| `HYSTERESIS.MATCH_HARD_RESET_DISTANCE` | `120` |
| `HYSTERESIS.strongMargin` | `4` |
| `HYSTERESIS.adjacentAlong` | `40` |

## PREDICTION

Previsao local curta, somente apos TRACKING; decai confianca e para apos cinco segundos.

| Parametro | Valor |
| --- | --- |
| `PREDICTION.strongMs` | `2000` |
| `PREDICTION.maxMs` | `5000` |
| `PREDICTION.confidenceDecayMs` | `3000` |
| `PREDICTION.minimumConfidence` | `0.35` |

## CONFIDENCE

Combinacao heuristica, distinta de accuracy; limites por estado e blend gradual.

| Parametro | Valor |
| --- | --- |
| `CONFIDENCE.excellent` | `0.9` |
| `CONFIDENCE.good` | `0.75` |
| `CONFIDENCE.fair` | `0.55` |
| `CONFIDENCE.weak` | `0.35` |
| `CONFIDENCE.covarianceScale` | `60` |
| `CONFIDENCE.acquiringCap` | `0.6` |
| `CONFIDENCE.degradedCap` | `0.54` |
| `CONFIDENCE.ageDecayMs` | `15000` |
| `CONFIDENCE.blendStart` | `0.55` |
| `CONFIDENCE.blendEnd` | `0.9` |
| `CONFIDENCE.blendWeightStep` | `0.2` |
| `CONFIDENCE.unknownHeadingWeight` | `0.5` |
| `CONFIDENCE.noMatchWeight` | `0.5` |
| `CONFIDENCE.weights.quality` | `0.4` |
| `CONFIDENCE.weights.covariance` | `0.2` |
| `CONFIDENCE.weights.history` | `0.2` |
| `CONFIDENCE.weights.heading` | `0.1` |
| `CONFIDENCE.weights.match` | `0.1` |

## PERFORMANCE

Limites de CPU, memoria, tempo de sessao e diagnostico; telemetria somente opt-in.

| Parametro | Valor |
| --- | --- |
| `PERFORMANCE.medianBudgetMs` | `5` |
| `PERFORMANCE.p95BudgetMs` | `15` |
| `PERFORMANCE.telemetryCapacity` | `3000` |
| `PERFORMANCE.maxRouteContexts` | `16` |
| `PERFORMANCE.sessionLimitMs` | `3600000` |
| `PERFORMANCE.debugCirclePoints` | `32` |
| `PERFORMANCE.heartbeatMs` | `500` |
| `PERFORMANCE.diagnosticCapacity` | `20` |

## Unidades e contratos

- Distancias/accuracy/corredores: metros; velocidades: m/s; aceleracao: m/s²; headings: graus; timestamps e limites Ms: milissegundos; gaps Seconds: segundos. Covariancia: m² nas posicoes e (m/s)² nas velocidades. Custos e confianca: adimensionais.
- Perfis FILTER.profiles sao desvios de aceleracao usados no ruido de processo. accuracyToSigma=0.5 e uma aproximacao inicial, nao converte garantidamente um raio GPS numa distribuicao gaussiana real.
- MATCH_SWITCH_MARGIN se aplica ao custo menor-melhor. Forte evidencia ou candidato atual invalido podem trocar sem N confirmacoes. O gate lateral de 110m pode invalidar o candidato antes do hard-reset de 120m.
- PREDICTION requer historico TRACKING e confianca minima. GPS parado pode ser previsto sem deslocamento. Nenhuma previsao continua apos maxMs.
- CONFIDENCE nao deve ser mostrado como ±metros. A UI normal continua exibindo somente accuracy original do dispositivo.
- Ring de telemetria guarda ate 3000 registros e estados anteriores; export inclui checkpoint do primeiro registro retido. Expira em uma hora ou ao atingir limite de contextos de rota.
- Thresholds BASELINE sao apenas a referencia legada; nao foram modificados para fazer o V2 parecer melhor.
