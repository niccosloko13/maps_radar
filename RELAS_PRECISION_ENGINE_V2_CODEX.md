# RELAS PRECISION ENGINE V2 — ESPECIFICAÇÃO DE IMPLEMENTAÇÃO

Projeto-alvo: `relas_v182`
Objetivo: transformar o sistema atual de GPS do RELAS em um motor de localização robusto, mensurável e preparado para map matching probabilístico avançado.

---

# PRINCÍPIO CENTRAL

Não otimizar para o marcador “parecer suave”.

Otimizar para:

- posição plausível;
- via correta;
- sentido correto;
- baixa latência;
- estabilidade;
- recuperação após perda de GPS;
- confiança conhecida;
- comportamento reproduzível;
- capacidade de evolução para HMM/Viterbi/Valhalla.

NUNCA declarar que a precisão física do GPS melhorou apenas porque houve filtragem ou snap.

---

# SITUAÇÃO ATUAL

Preservar como baseline o comportamento existente:

- `navigator.geolocation.watchPosition`
- `enableHighAccuracy: true`
- `maximumAge: 1000`
- `timeout: 12000`
- validação de coordenadas
- rejeição de accuracy ruim
- rejeição de timestamp antigo/futuro
- rejeição de saltos absurdos
- cálculo de velocidade
- cálculo/suavização de heading
- projeção na rota
- câmera
- alertas
- simulação
- smoke tests

Arquivos de interesse:

- `app/app.js`
- `app/navigation-core.js`
- `tests/navigation.test.cjs`
- `scripts/road-navigation-smoke.js`
- `scripts/road-browser-smoke.js`

Antes de qualquer alteração:

1. criar checkpoint/branch;
2. rodar testes atuais;
3. salvar baseline;
4. não apagar comportamento existente sem substituto testado.

---

# ARQUITETURA NOVA

Criar:

```text
app/location/
├── location-engine.js
├── fix-quality.js
├── motion-filter.js
├── heading-engine.js
├── location-state-machine.js
├── candidate-corridor.js
├── route-matcher.js
├── confidence-engine.js
├── replay-engine.js
├── metrics-engine.js
├── telemetry.js
└── location-parameters.js
```

Não criar framework novo.
Não migrar o projeto inteiro para TypeScript.
Não adicionar bundler apenas por esta implementação.

---

# API PRINCIPAL

```js
const result = RelasLocation.process(rawFix, context)
```

Resultado conceitual:

```js
{
  accepted: true,

  raw: {
    longitude,
    latitude,
    accuracy,
    altitude,
    altitudeAccuracy,
    speed,
    heading,
    timestamp
  },

  estimated: {
    longitude,
    latitude,
    speed,
    heading,
    covariance
  },

  matched: {
    longitude,
    latitude,
    along,
    segmentIndex,
    roadBearing,
    distanceToRoute,
    confidence,
    source
  },

  output: {
    longitude,
    latitude,
    speed,
    heading
  },

  quality: {
    score,
    level,
    reasons
  },

  state: "TRACKING",
  confidence: 0.93
}
```

`raw` deve permanecer RAW.

---

# 1. LOCATION STATE MACHINE

Criar:

`app/location/location-state-machine.js`

Estados:

```text
INITIALIZING
ACQUIRING
TRACKING
DEGRADED
PREDICTING
LOST
```

## INITIALIZING

Ainda sem fix utilizável.

## ACQUIRING

Recebeu fixes, mas ainda sem histórico suficiente para confiar.

Exigir sequência mínima de fixes razoáveis antes de entrar em TRACKING.

Não usar apenas “1 fix excelente = tracking”.

## TRACKING

GPS e modelo coerentes.

## DEGRADED

Ainda existe GPS, mas:

- accuracy ruim;
- jitter alto;
- heading contraditório;
- frequência irregular;
- match ruim.

## PREDICTING

Sem fix novo por curto período, mas modelo pode continuar previsão limitada.

## LOST

Sem informação confiável.

### Histerese de estado

Não oscilar:

TRACKING → DEGRADED → TRACKING

a cada fix.

Exigir evidência consecutiva para mudar estado.

Parâmetros centralizados.

---

# 2. FIX QUALITY ENGINE

Arquivo:

`fix-quality.js`

Função:

```js
evaluateFix(raw, previousRaw, previousEstimated, now)
```

Validar:

- latitude;
- longitude;
- accuracy;
- timestamp;
- idade;
- timestamp futuro;
- fix duplicado;
- fix fora de ordem;
- velocidade implícita;
- inconsistência com posição prevista;
- inconsistência com accuracy reportada.

Score sugerido de accuracy:

```text
<= 5m    1.00
<= 10m   0.95
<= 20m   0.85
<= 35m   0.70
<= 50m   0.55
<= 75m   0.35
<= 100m  0.20
> 100m   reject
```

Não usar esses números espalhados pelo código.
Colocar em `location-parameters.js`.

### Rejeição de outlier

Não rejeitar só por distância.

Considerar:

- `dt`;
- accuracy anterior;
- accuracy atual;
- velocidade estimada;
- velocidade GPS;
- aceleração implícita;
- direção.

Exemplo:

um salto de 35m pode ser normal a 100 km/h e absurdo com veículo parado.

---

# 3. MOTION FILTER — KALMAN 2D ADAPTATIVO

Arquivo:

`motion-filter.js`

Estado:

```text
x = [
  east,
  north,
  velocityEast,
  velocityNorth
]
```

Coordenadas em metros locais.

Nunca Kalman direto em latitude/longitude.

Modelo:

```text
F =
[1 0 dt 0 ]
[0 1 0  dt]
[0 0 1  0 ]
[0 0 0  1 ]
```

Medição:

```text
z = [east, north]
```

### Measurement noise

Derivar de:

```text
accuracy
```

Não usar R fixo.

### Process noise adaptativo

Perfis:

```text
STATIONARY
LOW_SPEED
URBAN
HIGH_SPEED
TURNING
GPS_DEGRADED
```

Comportamento:

- parado → reduzir drift;
- baixa velocidade → suavizar jitter;
- alta velocidade → responder mais rápido;
- curva → permitir mudança rápida;
- accuracy ruim → confiar mais no modelo;
- accuracy excelente → corrigir mais pelo GPS.

### Gap

Se `dt` muito grande:

- aumentar incerteza;
- evitar falsa confiança;
- reinicializar parcialmente se necessário.

---

# 4. HEADING ENGINE

Arquivo:

`heading-engine.js`

Fontes:

```text
1. GPS heading confiável
2. heading derivado do movimento filtrado
3. heading derivado da rota/match com peso baixo
4. heading anterior
5. null
```

Não usar heading GPS parado.

Threshold inicial configurável:

```text
speed < 1.2 m/s
```

### Smoothing circular

Usar menor delta angular.

Correto:

```text
359° -> 1° = +2°
```

Nunca:

```text
359° -> 1° = -358°
```

### Resposta adaptativa

- baixa velocidade → mais smoothing;
- alta velocidade → menos lag;
- curva detectada → resposta rápida.

---

# 5. CANDIDATE CORRIDOR

Arquivo:

`candidate-corridor.js`

Não comparar a posição com toda a rota a cada fix.

Manter corredor de segmentos plausíveis.

Base:

```text
último segmentIndex
último along
velocidade
heading
tempo desde último match
```

Janela inicial:

```text
atrás: ~150m
frente: ~1000m
```

Mas deve ser dinâmica.

Exemplo:

- parado → janela curta;
- alta velocidade → frente maior;
- GPS degradado → ampliar moderadamente;
- retorno/recalculo → permitir reset do corredor.

Se não houver candidato plausível no corredor:

1. expandir busca;
2. se continuar sem candidato, retornar unmatched;
3. não forçar snap.

---

# 6. ROUTE MATCHER V2

Arquivo:

`route-matcher.js`

Não escolher apenas o segmento geometricamente mais próximo.

Para cada candidato calcular features:

```text
lateralDistance
headingDifference
alongProgress
backwardMovement
segmentJump
previousSegmentContinuity
predictedPositionDistance
gpsAccuracy
speed
```

Score conceitual:

```text
score =
  distanceCost
+ headingCost
+ transitionCost
+ backwardCost
+ jumpCost
+ predictionCost
```

## Distance

Penalidade normalizada pela accuracy.

Exemplo conceitual:

```text
normalizedDistance = distance / max(accuracy, minimumSigma)
```

## Heading

Em movimento relevante:

- mesmo sentido → custo baixo;
- perpendicular → custo médio;
- sentido oposto → custo alto.

Não aplicar penalidade forte de heading com carro parado.

## Progress

Movimento para trás na rota deve ser possível, mas penalizado quando inconsistente com heading e histórico.

## Continuidade

Trocar de segmento exige evidência.

---

# 7. HYSTERESIS DO MAP MATCHING

ESSENCIAL.

Se o sistema está no segmento A:

não trocar para B apenas porque em um único fix B ficou 2m mais próximo.

Manter:

```js
currentCandidate
challengerCandidate
challengerWins
```

Só trocar quando:

- candidato novo vence por margem mínima;
- por N fixes consecutivos;
- OU evidência muito forte;
- OU segmento atual ficou impossível.

Parâmetros configuráveis:

```text
MATCH_SWITCH_MARGIN
MATCH_SWITCH_CONFIRMATIONS
MATCH_HARD_RESET_DISTANCE
```

Objetivo:

reduzir troca entre:

- vias paralelas;
- marginais;
- alças;
- pistas locais/expressas;
- cruzamentos.

---

# 8. MULTI-CANDIDATE MATCHING PREPARADO PARA HMM

Mesmo antes do HMM completo, `route-matcher` deve retornar top-K candidatos.

Exemplo:

```js
{
  candidates: [
    { segmentIndex: 120, score: 0.16 },
    { segmentIndex: 123, score: 0.31 },
    { segmentIndex: 118, score: 0.72 }
  ],
  chosen: ...
}
```

Não desenhar arquitetura que só permite um candidato.

Isso prepara diretamente para Viterbi depois.

---

# 9. POSITION BLENDING

Não usar snap duro em confidence intermediária.

### Sem match

```text
output = estimated
```

### Match excelente

```text
output = matched
```

### Match médio

Blend gradual:

```text
output = estimated * (1 - w)
       + matched   * w
```

`w` baseado em match confidence.

Evitar:

```text
GPS -> rua -> GPS -> rua
```

---

# 10. DEAD RECKONING CURTO

Apenas para interrupções curtas.

Sugestão inicial:

```text
0–2s  prediction forte
2–5s  prediction degradada
>5s   parar de afirmar posição precisa
```

Confidence cai continuamente.

Não deixar posição “andar sozinha” indefinidamente.

---

# 11. CONFIDENCE ENGINE

Arquivo:

`confidence-engine.js`

Combinar:

- raw accuracy;
- idade;
- fix quality;
- covariance;
- estabilidade;
- heading;
- match distance;
- match continuity;
- quantidade de bons fixes;
- estado;
- tempo desde último fix.

Saída:

```text
0.90–1.00 excellent
0.75–0.89 good
0.55–0.74 fair
0.35–0.54 weak
<0.35 poor
```

IMPORTANTE:

`confidence != GPS accuracy`

Nunca mostrar confidence como “±metros”.

---

# 12. REPLAY ENGINE — OBRIGATÓRIO

Arquivo:

`replay-engine.js`

Esse módulo é essencial para calibrar o motor sem dirigir novamente.

Aceitar sessão JSON exportada pela telemetria.

API:

```js
RelasLocationReplay.load(session)
RelasLocationReplay.play()
RelasLocationReplay.pause()
RelasLocationReplay.seek(index)
RelasLocationReplay.setSpeed(1)
RelasLocationReplay.step()
RelasLocationReplay.reset()
```

### Determinismo

O mesmo trace + mesmos parâmetros deve gerar a mesma saída.

Não depender de:

```text
Date.now()
Math.random()
timers imprevisíveis
```

durante replay.

Usar timestamp do trace.

### Velocidades

Permitir:

```text
0.25x
0.5x
1x
2x
5x
10x
instant
```

### Modo instant

Processar toda sessão sem renderizar mapa a cada fix.

Usado para benchmark.

---

# 13. TELEMETRIA

Arquivo:

`telemetry.js`

Registrar por fix:

```js
{
  timestamp,

  raw,

  quality,

  state,

  estimated,

  candidates,

  matched,

  output,

  confidence,

  metrics: {
    processingMs
  }
}
```

API:

```js
relas.locationTelemetry.start()
relas.locationTelemetry.stop()
relas.locationTelemetry.clear()
relas.locationTelemetry.exportJSON()
```

Local apenas.

Sem upload automático.

---

# 14. METRICS ENGINE

Arquivo:

`metrics-engine.js`

Ao processar sessão/replay gerar:

```text
fixCount
acceptedFixes
rejectedFixes
outlierCount
averageAccuracy
medianAccuracy
p95Accuracy
averageProcessingMs
p95ProcessingMs
stateTransitions
timeTracking
timeDegraded
timePredicting
timeLost
matchSuccessRate
matchSwitchCount
lowConfidenceCount
maxPredictionGap
```

Quando rota conhecida:

```text
averageDistanceToRoute
medianDistanceToRoute
p95DistanceToRoute
backwardJumpCount
segmentSwitchCount
implausibleSegmentSwitchCount
```

Se houver ground truth no futuro, preparar:

```text
positionErrorMean
positionErrorMedian
positionErrorP95
headingError
```

Não inventar ground truth.

---

# 15. PARAMETER REGISTRY

Arquivo:

`location-parameters.js`

TODOS os magic numbers devem morar aqui.

Categorias:

```text
QUALITY
FILTER
HEADING
STATE_MACHINE
MATCHER
HYSTERESIS
PREDICTION
CONFIDENCE
PERFORMANCE
```

Exportar snapshot dos parâmetros junto da telemetria.

Assim cada replay sabe exatamente com quais parâmetros foi gerado.

---

# 16. PERFORMANCE BUDGET

O motor roda em celular.

Não aceitar algoritmo que trave UI.

Metas iniciais:

```text
process(fix) median < 5 ms
process(fix) p95 < 15 ms
```

Se browser/device não atingir, documentar.

Regras:

- evitar alocação gigante por fix;
- não percorrer milhares de segmentos se corredor existe;
- evitar JSON stringify dentro do hot path;
- debug pesado apenas quando habilitado;
- limitar ring buffer.

Se necessário:

usar Web Worker futuramente, mas NÃO introduzir antes de medir.

---

# 17. DEBUG VISUAL

Modo:

```js
localStorage.setItem("relas-location-debug", "1")
```

Layers:

```text
RAW
ESTIMATED
MATCHED
OUTPUT
ACCURACY CIRCLE
CANDIDATES
CURRENT CORRIDOR
```

Mostrar opcionalmente:

```text
state
confidence
accuracy
speed
heading
segment index
match distance
processing ms
```

Não mostrar isso na UI normal.

---

# 18. INTEGRAÇÃO COM app.js

`receivePosition()` deve virar consumidor do motor.

Não continuar contendo toda a inteligência.

Fluxo desejado:

```js
function receivePosition(fix) {
  if (S.simulation) return;

  const result = RelasLocation.process(fix, {
    route: S.route,
    segments: S.segments,
    previousPosition: S.position,
    driving: S.driving
  });

  if (!result.accepted) {
    handleRejectedLocation(result);
    return;
  }

  S.position = [
    result.output.longitude,
    result.output.latitude
  ];

  S.speed = result.output.speed;
  S.heading = result.output.heading;
  S.accuracy = result.raw.accuracy;
  S.locationConfidence = result.confidence;
  S.locationState = result.state;
  S.routeMatch = result.matched;
  S.gpsAt = result.raw.timestamp;

  markPosition(S.position, S.heading, S.speed);

  if (S.driving) {
    updateDrive(S.position, S.speed, S.heading);
  }
}
```

API pode variar.
Separação arquitetural não.

---

# 19. REMOVER DUPLICIDADE DE PROJEÇÃO

Se existe `project(p)` dentro de `app.js`:

extrair para módulo compartilhável.

Não deixar:

```text
map matcher A
+
project() B
```

com regras divergentes.

`updateDrive()` e localização devem consumir o mesmo núcleo geométrico.

---

# 20. ALERTAS PREPARADOS PARA ROAD-AWARE

Não alterar comportamento atual de alertas nesta etapa se houver risco de regressão.

Mas preparar:

```js
S.routeMatch = {
  along,
  segmentIndex,
  roadBearing,
  confidence
}
```

Fase seguinte:

```text
alerta pertence ao mesmo corredor?
segmento atual/futuro?
mesmo sentido?
distância ao longo da via?
```

Isso será superior a raio geográfico puro.

---

# 21. TESTES UNITÁRIOS

Criar:

```text
tests/location-quality.test.cjs
tests/location-filter.test.cjs
tests/location-heading.test.cjs
tests/location-state.test.cjs
tests/location-matcher.test.cjs
tests/location-replay.test.cjs
tests/location-metrics.test.cjs
```

## Casos obrigatórios

### Quality

- 5m;
- 20m;
- 80m;
- >100m;
- stale;
- future timestamp;
- duplicated;
- out of order;
- NaN;
- impossible jump.

### Filter

- reto com ruído;
- curva;
- parada;
- aceleração;
- deceleração;
- accuracy degradando;
- outlier;
- gap.

### Heading

- 359→1;
- 1→359;
- parado;
- baixa velocidade;
- curva;
- GPS heading null.

### State machine

- INITIALIZING→ACQUIRING;
- ACQUIRING→TRACKING;
- TRACKING→DEGRADED;
- DEGRADED→TRACKING;
- TRACKING→PREDICTING;
- PREDICTING→LOST;
- LOST→ACQUIRING.

Confirmar hysteresis.

### Matcher

- rota reta;
- GPS lateral;
- duas vias paralelas;
- sentido oposto;
- interseção;
- alça;
- retorno;
- saída real da rota;
- GPS ruim;
- challenger vencendo só 1 fix;
- challenger vencendo N fixes.

### Replay

Mesmo JSON + parâmetros iguais:

saída byte-equivalent ou numericamente equivalente dentro de tolerância definida.

---

# 22. TRACES SINTÉTICOS

Criar:

```text
tests/fixtures/location/
```

Arquivos:

```text
straight-clean.json
straight-noisy.json
parallel-road.json
intersection.json
turn.json
gps-dropout.json
outlier.json
accuracy-degradation.json
heading-wrap.json
route-departure.json
```

Esses traces devem ser permanentes.

---

# 23. BROWSER SMOKE

Atualizar scripts existentes.

Validar:

- navegador abre;
- permissão GPS tratada;
- simulation preservada;
- debug off por padrão;
- debug on funciona;
- replay funciona;
- nenhum erro console;
- navigation continua funcionando;
- alertas continuam funcionando;
- mapa não congela.

---

# 24. BASELINE VS V2

Criar benchmark comparativo.

Salvar:

```text
artifacts/location-precision-v2/baseline.json
artifacts/location-precision-v2/new-engine.json
```

Comparar:

```text
rejected fixes
match switches
distance to route
heading stability
processing latency
state stability
prediction gaps
```

Não escrever “melhorou X%” sem métrica que sustente.

---

# 25. FASE HMM / VITERBI — PREPARAR, NÃO EXECUTAR AGORA

A arquitetura deve permitir depois:

```text
fixes
 ↓
candidate generation
 ↓
emission probability
 ↓
transition probability
 ↓
Viterbi
 ↓
most likely road sequence
```

Os candidatos retornados hoje devem ser compatíveis com essa evolução conceitual.

No futuro:

```text
Local Matcher
  ↓
Sliding Window Trace
  ↓
Backend Valhalla/Meili
  ↓
Matched Edge Sequence
  ↓
Frontend Hysteresis/Interpolation
```

Não chamar backend a cada animation frame.

---

# 26. VALHALLA — FASE FUTURA

Quando chegar a hora:

- rodar Valhalla fora do frontend;
- avaliar hospedagem adequada;
- usar trace/map matching em janelas;
- enviar accuracy quando disponível;
- usar OpenStreetMap;
- retornar edge/segment e matched point;
- cachear quando possível.

Não tentar colocar Valhalla dentro de bundle web/Vercel Function sem análise de infraestrutura.

---

# 27. SENSOR FUSION — FASE FUTURA

Somente depois do motor base validado.

Possíveis sinais:

- DeviceMotion;
- DeviceOrientation;
- acelerômetro;
- giroscópio;
- magnetômetro;
- native sensors.

Progressive enhancement.

Sensor ausente:

RELAS continua funcionando.

Magnetômetro inconsistente:

ignorar/reduzir peso.

---

# 28. ANDROID NATIVE — FASE FUTURA

Arquitetura futura:

```text
Android Fused Location Provider
+
Raw GNSS
+
IMU
+
map matching
```

Depois:

- multi-constellation;
- raw measurements;
- carrier phase;
- RTK/NTRIP;
- GNSS/INS;
- factor graph.

Não bloquear web por isso.

---

# 29. SAFETY / PRIVACY / DATA

Localização é dado sensível.

Nesta fase:

- telemetria local;
- exportação manual;
- sem envio automático;
- sem persistência permanente por padrão;
- sem localização em logs de produção;
- sem console log contínuo em production.

Adicionar limite de sessão.

---

# 30. FAIL-SAFE

Se o motor novo falhar em runtime:

não pode derrubar navegação inteira.

Implementar fallback controlado:

```text
new engine error
 ↓
log diagnóstico local
 ↓
fallback para comportamento baseline
```

Somente quando seguro.

Não esconder bugs silenciosamente durante desenvolvimento.

Em development:
falha deve aparecer claramente.

---

# 31. FEATURE FLAG

Adicionar:

```text
relas-location-engine-v2
```

ou configuração equivalente.

Permitir comparar:

```text
BASELINE
V2
```

Sem manter duas arquiteturas permanentemente.

Flag existe para rollout/teste.

---

# 32. CRITÉRIOS DE SUCESSO DESTA MISSÃO

- [ ] baseline salvo;
- [ ] testes antigos continuam passando;
- [ ] location engine separado;
- [ ] state machine;
- [ ] fix quality;
- [ ] adaptive Kalman;
- [ ] heading engine;
- [ ] candidate corridor;
- [ ] multi-candidate route matcher;
- [ ] hysteresis;
- [ ] confidence;
- [ ] short dead reckoning;
- [ ] telemetry;
- [ ] deterministic replay;
- [ ] metrics;
- [ ] centralized parameters;
- [ ] debug layers;
- [ ] feature flag;
- [ ] fallback;
- [ ] unit tests;
- [ ] synthetic traces;
- [ ] browser smoke;
- [ ] performance measurement;
- [ ] relatório final.

---

# 33. ORDEM DE EXECUÇÃO OBRIGATÓRIA

1. checkpoint;
2. baseline tests;
3. baseline metrics;
4. parameters registry;
5. raw model;
6. fix quality;
7. state machine;
8. adaptive filter;
9. heading engine;
10. corridor;
11. multi-candidate matcher;
12. hysteresis;
13. confidence;
14. dead reckoning;
15. telemetry;
16. replay;
17. metrics;
18. integrate app.js;
19. debug visualization;
20. feature flag/fallback;
21. unit tests;
22. synthetic traces;
23. browser smoke;
24. performance benchmark;
25. regression fixes;
26. final report.

Não pular diretamente para Valhalla.

---

# 34. RELATÓRIO FINAL

Criar:

```text
artifacts/location-precision-v2/REPORT.md
artifacts/location-precision-v2/PARAMETERS.md
artifacts/location-precision-v2/BENCHMARK.md
artifacts/location-precision-v2/KNOWN_LIMITATIONS.md
```

REPORT deve listar:

- arquivos criados;
- arquivos modificados;
- arquitetura;
- testes;
- resultados;
- regressões encontradas;
- regressões corrigidas;
- performance;
- comportamento baseline vs V2;
- limitações;
- próximo passo.

PARAMETERS:

todos os thresholds e justificativas.

BENCHMARK:

dados objetivos.

KNOWN_LIMITATIONS:

problemas não resolvidos.

---

# 35. NÃO FAZER

Não:

- alterar banco;
- alterar auth;
- alterar dados de radar;
- redesenhar UI;
- adicionar Valhalla agora;
- adicionar RTKLIB agora;
- adicionar WebXR;
- adicionar SLAM;
- adicionar dependências gigantes;
- enviar localização a terceiros;
- esconder regressões;
- declarar precisão centimétrica;
- chamar snap de precisão física;
- usar apenas distância geométrica para escolher via;
- espalhar magic numbers;
- remover baseline antes da comparação.

---

# 36. DEFINIÇÃO FINAL DE “PRONTO”

Esta missão só termina quando:

```text
INPUT REAL
   ↓
QUALITY
   ↓
STATE MACHINE
   ↓
ADAPTIVE MOTION FILTER
   ↓
HEADING
   ↓
CANDIDATE CORRIDOR
   ↓
MULTI-CANDIDATE MATCHER
   ↓
HYSTERESIS
   ↓
CONFIDENCE
   ↓
OUTPUT
```

estiver funcionando e testado.

E quando pudermos pegar uma sessão real:

```text
trip.json
```

executar:

```text
BASELINE
vs
V2
```

e comparar objetivamente sem sair de carro novamente.

---

# 37. PRÓXIMA MISSÃO APÓS V2

Somente depois de uma sessão real:

```text
HMM/Viterbi Map Matching
+
Valhalla/Meili backend
+
road-direction-aware radar matching
```

A escolha dos parâmetros dessa fase deve ser baseada nos traces reais do RELAS.

