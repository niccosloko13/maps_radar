# RELAS NAVIGATION INTELLIGENCE V2
## Radar-first + Modo Estrada + Trânsito + Chuva + Polícia Rodoviária + Comunidade

### OBJETIVO

Evoluir a navegação do RELAS sem perder o foco principal do produto:

> RADARES OFICIAIS, CORRETOS, NA VIA CERTA, NO SENTIDO CERTO E COM VALIDADE/IDENTIDADE VERIFICÁVEL.

Trânsito, chuva, obras, postos rodoviários, pedágios, polícia, comunidade e pontos de apoio entram como camadas auxiliares.

---

# 1. PRINCÍPIO RADAR-FIRST

Prioridade global:

```text
P0  Radar iminente / alerta crítico de velocidade
P1  Acidente / bloqueio / alagamento grave
P2  Manobra iminente
P3  Posto rodoviário / pedágio / fiscalização oficial fixa
P4  Chuva / trânsito / obra
P5  Comunidade / apoio / informação secundária
```

Nada pode ocultar ou competir visualmente com radar iminente.

---

# 2. MODO ESTRADA — NOVO

Criar modo automático:

```text
CITY_MODE
ROAD_MODE
```

O modo pode ser detectado por:

- classificação da via;
- código de rodovia (`SP-160`, `SP-150`, `BR-116`, etc.);
- velocidade;
- contexto da rota;
- dados do grafo/roteamento.

Permitir override manual:

```text
Auto
Cidade
Estrada
```

---

# 3. COMPORTAMENTO DO MODO ESTRADA

Ao entrar em rodovia:

### Aumentar prioridade de:
- radares;
- pedágios;
- postos PRF;
- bases PM Rodoviária;
- bases DER/ARTESP/concessionárias;
- obras;
- bloqueios;
- acidentes;
- chuva forte;
- neblina;
- alagamento;
- pista escorregadia;
- objetos/animais na pista;
- socorro mecânico;
- SAU;
- balanças/pesagem;
- interdições.

### Reduzir prioridade de:
- detalhes urbanos irrelevantes;
- semáforos comuns;
- pequenos POIs;
- informações que não ajudam na condução.

### UI:
- mais mapa à frente;
- zoom adaptado à velocidade;
- cards mais compactos;
- alertas antecipados;
- menos botões permanentes.

---

# 4. BUSCA DE ENDEREÇO COMPLETO

Corrigir busca:

```text
Rua
Rua + número
Rua + número + cidade
CEP
Bairro + cidade
```

Pipeline:

```text
raw query
→ normalização
→ structured geocoding
→ fallback full-text
→ ranking por proximidade/cidade
→ endereço completo
```

Testar exemplos reais.

---

# 5. PROGRESSO DA ROTA

Usar `routeMatch.along`.

Dividir:

```text
TRAVELED
REMAINING
```

O trecho percorrido:
- desaparece; OU
- fica muito discreto.

A rota futura permanece destacada.

Recalculo deve recompor corretamente a linha.

---

# 6. GPS / ATRASO VISUAL

Não resolver atraso apenas com animação.

Medir:

```text
gpsFixAgeMs
locationEngineMs
routeMatchMs
markerRenderLagMs
cameraLagMs
```

Objetivo:
reduzir atraso perceptível sem inventar posição.

A câmera pode deslocar o foco à frente conforme heading/velocidade.

---

# 7. RADAR VOICE ENGINE

Separar:

```text
Navigation Voice
Radar Voice
Critical Alerts
```

Permitir:

```text
Navigation Voice = OFF
Radar Voice = ON
```

Mensagens:

```text
Radar à frente. Limite 60.
Radar a 500 metros. Limite 60.
Radar a 200 metros.
```

Antecipação por velocidade.

Nunca alertar radar de:
- pista oposta;
- alça errada;
- rua paralela;
- segmento fora da rota.

Usar:
- routeMatch;
- segmentIndex;
- direction;
- road bearing;
- confidence.

### Limitação web/PWA

Não prometer ignorar:
- volume zero do aparelho;
- Bluetooth;
- políticas do iOS/Android;
- bloqueios de autoplay.

O RELAS deve apenas manter o Radar Voice independente do mute interno da navegação.

---

# 8. CARD DE RADAR

Estados:

```text
UPCOMING
NEAR
IMMINENT
PASSED
```

Exemplo:

```text
RADAR FIXO
60 km/h
380 m
✓ Oficial
```

Quando Official Finder confirmar:

```text
✓ Verificado
```

Evitar “Confirmado” genérico.

---

# 9. POSTOS RODOVIÁRIOS / POLÍCIA

Adicionar categorias oficiais separadas:

```text
PRF_POST
PM_RODOVIARIA_BASE
POLICE_BASE
ROAD_INSPECTION_BASE
```

Cada tipo deve ter ícone próprio.

Detalhe:

```text
POSTO PRF
BR-116 · km 271
Fonte: PRF
Atualizado: ...
```

ou:

```text
BASE PM RODOVIÁRIA
SP-160 · km ...
Fonte: Polícia Militar Rodoviária / órgão oficial
```

Não usar report comunitário para afirmar existência de base oficial.

---

# 10. BASES DE APOIO / CONCESSIONÁRIA

Adicionar:

```text
DER_BASE
ARTESP_BASE
CONCESSIONAIRE_BASE
SAU
TOW_SERVICE
MECHANICAL_SUPPORT
```

Mostrar apenas quando:
- na rota;
- relevante;
- usuário tocar;
- Modo Estrada ativo.

---

# 11. PEDÁGIOS

Categoria:

```text
TOLL_PLAZA
```

Exibir:
- nome;
- rodovia/km;
- concessionária;
- forma de cobrança, se disponível;
- valor, se houver fonte oficial e atual.

Não usar valor antigo sem data.

---

# 12. BALANÇA / PESAGEM

Categoria:

```text
WEIGH_STATION
```

Prioridade baixa para carro comum.
Maior relevância para perfil de veículo pesado no futuro.

---

# 13. TRÂNSITO EM TEMPO REAL

## ARTESP CCM
Prioridade para rodovias estaduais/concedidas.

Importar quando publicamente disponível:

```text
road
direction
start_km
end_km
severity
speed
delay_minutes
cause
updated_at
source
```

A ARTESP pode publicar dados derivados de Waze em painel oficial.

Não extrair banco proprietário do Waze.

## DER-SP
Usar:
- câmeras;
- condições;
- ocorrências disponíveis.

## HERE Traffic
Avaliar para:
- flow;
- incidents;
- jam factor;
- expected speed;
- closures.

Somente se licença/custo forem adequados.

---

# 14. CHUVA / CLIMA — ESTADO DE SP

## SP Águas / SIBH
Integrar:
- Chuva Agora;
- pluviômetros;
- intensidade;
- nível/vazão quando relevante.

## Defesa Civil SP
Integrar:
- chuva intensa;
- tempestade;
- vendaval;
- alagamento;
- outros alertas oficiais.

### Filtro por rota

Nunca inundar o mapa com alertas estaduais.

Cruzar com CORREDOR DA ROTA.

Exemplo:

```text
Chuva forte à frente
trecho em ~8 km
```

---

# 15. EVENTOS DE RODOVIA

Modelo:

```text
road_event
```

Tipos:

```text
ACCIDENT
ROADWORK
CLOSURE
FLOOD
OBJECT_ON_ROAD
ANIMAL_ON_ROAD
HAZARD
POLICE_OPERATION
WEATHER
FOG
SLIPPERY_ROAD
LANDSLIDE
```

Cada evento tem:

```text
source
source_type
severity
confidence
valid_from
valid_until
updated_at
geometry
direction
road
km
```

---

# 16. COMUNIDADE RELAS

Sistema leve.

Usuário pode:

- escolher avatar pré-definido;
- opt-in para aparecer;
- reportar ocorrência;
- confirmar ocorrência.

Nunca mostrar:
- nome;
- telefone;
- e-mail;
- rota completa;
- histórico público.

### Posição
- aproximada;
- atualização limitada;
- TTL curto;
- apenas enquanto opt-in.

### Radar comunitário
Sempre:

```text
COMMUNITY_DISCOVERY
```

Nunca:
```text
OFFICIAL_VERIFIED
```

sem passar pelo Official Enforcement Finder.

---

# 17. + ALERTAR

Bottom sheet:

```text
Radar
Acidente
Obra
Alagamento
Objeto na via
Animal na pista
Fiscalização
Interdição
Outro perigo
```

Em Modo Estrada, ordenar por relevância rodoviária.

---

# 18. SISTEMA DE ÍCONES — REFAZER

Família SVG própria RELAS:

```text
radar fixo
radar semafórico
lombada eletrônica
semáforo fiscalizador
PRF
PM Rodoviária
posto policial
base DER
base concessionária
pedágio
balança
SAU
guincho
obra
acidente
alagamento
chuva
neblina
interdição
animal na pista
objeto na pista
fiscalização
usuário
localização
```

Regras:
- mesma linguagem;
- sem emojis;
- sem clipart;
- legível em movimento;
- contraste dark/light;
- estados normal/selected/imminent;
- tamanhos consistentes.

---

# 19. UI — LIMPAR MAIS

Pelas capturas atuais:

- card de manobra muito alto;
- card inferior grande;
- botão info genérico;
- +Alertar grande;
- mapa pesado;
- radar card ainda precisa refino.

Direção:

```text
mapa = protagonista
radar = prioridade
manobra = compacta
velocidade = clara
ações = discretas
```

Modo Estrada:
- ainda menos UI;
- mais área útil do mapa.

---

# 20. PT-BR

Corrigir instruções híbridas como:

```text
Turn à direita toward...
```

Tudo deve ser:
- exibido em PT-BR;
- falado em PT-BR.

Não concatenar tradução parcial.

---

# 21. CÂMERA DE NAVEGAÇÃO

Adaptativa:

### Cidade
- zoom mais próximo;
- mais contexto lateral.

### Estrada
- zoom um pouco mais aberto;
- usuário mais abaixo na tela;
- muito mais mapa à frente;
- adaptação por velocidade;
- adaptação por próxima manobra.

Sem movimentos bruscos.

---

# 22. ROAD MODE DETECTION

Criar detector com score.

Sinais:

```text
road class
road ref = SP/BR
speed
route segment type
access properties
lane count when available
distance between intersections
```

Exemplo:

```text
roadModeScore > threshold
→ ROAD_MODE
```

Usar histerese para não alternar cidade/estrada a cada segundo.

---

# 23. ROAD MODE UI POLICY

Quando `ROAD_MODE`:

Mostrar/priorizar:
- radar;
- velocidade;
- próxima manobra;
- trânsito;
- chuva;
- pedágio;
- posto rodoviário;
- obra/interdição.

Ocultar/reduzir:
- detalhes urbanos;
- semáforos comuns;
- POIs menores;
- botões pouco usados.

---

# 24. CORREDOR INTELIGENTE

Não carregar tudo ao redor.

Criar:

```text
Route Event Corridor
```

Exemplo:

```text
5 km atrás
50 km à frente
buffer lateral configurável
```

Adaptar pela velocidade.

Radar pode usar janela menor e mais precisa.
Clima/trânsito pode usar janela maior.

---

# 25. ALERT MANAGER

Criar um orquestrador central:

```text
AlertManager
```

Entrada:
- radar;
- traffic;
- weather;
- road_event;
- maneuver;
- community.

Saída:
- prioridade;
- card;
- voz;
- duração;
- cooldown;
- dedupe.

Evitar:
- 3 vozes ao mesmo tempo;
- alertas repetidos;
- card piscando.

---

# 26. DEDUPE

Se ARTESP, DER e comunidade reportarem a mesma obra:

não mostrar 3 ocorrências.

Criar dedupe por:
- localização;
- tempo;
- tipo;
- sentido;
- fonte.

Manter várias evidências por trás de um único evento.

---

# 27. FRESHNESS

Cada dado deve ter:

```text
updated_at
source_updated_at
retrieved_at
expires_at
```

Eventos temporários expiram.

Postos/bases não.

---

# 28. TEST DRIVE / TELEMETRIA

Registrar:

```text
roadModeTransitions
routeProgress
gpsFixAge
renderLag
cameraLag
radarAlertDistance
radarVoiceTimestamp
trafficEventShown
weatherEventShown
roadEventShown
```

Replay obrigatório.

---

# 29. FASES DE IMPLEMENTAÇÃO

## FASE A — AGORA
- busca rua+número;
- progresso da rota;
- radar voice independente;
- PT-BR;
- UI/ícones;
- medir GPS lag;
- Modo Estrada;
- câmera adaptativa;
- AlertManager base.

## FASE B
- postos PRF / PM Rodoviária;
- pedágios;
- bases de apoio;
- ARTESP traffic;
- SP Águas;
- Defesa Civil;
- Route Event Corridor.

## FASE C
- obras/interdições estruturadas;
- DER events;
- HERE traffic, se aprovado;
- rerouting por tráfego.

## FASE D
- comunidade;
- avatares;
- usuários anônimos;
- reportes;
- confirmações.

---

# 30. NÃO DESVIAR DO OFFICIAL RADAR FINDER

Esta missão deve conviver com:

```text
RELAS OFFICIAL ENFORCEMENT FINDER SP
```

Arquitetura:

```text
OFFICIAL RADAR REGISTRY
        |
        v
NAVIGATION CORE
  + ROAD MODE
  + TRAFFIC
  + WEATHER
  + ROAD EVENTS
  + COMMUNITY
```

O radar registry continua sendo o coração.

---

# 31. DEFINITION OF DONE

O usuário deve conseguir:

- buscar rua+número;
- iniciar rota;
- entrar automaticamente em Modo Estrada;
- ver só a rota restante;
- ter câmera olhando à frente;
- ouvir radar com voz de navegação desligada;
- receber só radar da própria via/sentido;
- ver posto rodoviário/pedágio/obra relevantes;
- ver trânsito à frente;
- saber se há chuva relevante na rota;
- reportar ocorrência em poucos toques;
- continuar entendendo claramente o que é OFICIAL e o que é COMUNITÁRIO;
- usar o mapa sem poluição visual.

---

# 32. DELIVERABLES

Criar:

```text
artifacts/navigation-intelligence-v2/REPORT.md
artifacts/navigation-intelligence-v2/ROAD_MODE.md
artifacts/navigation-intelligence-v2/ICON_SYSTEM.md
artifacts/navigation-intelligence-v2/ALERT_POLICY.md
artifacts/navigation-intelligence-v2/SOURCE_INTEGRATIONS.md
artifacts/navigation-intelligence-v2/KNOWN_LIMITATIONS.md
```

---

# 33. REGRA FINAL

O RELAS deve parecer um navegador moderno, mas não um clone.

O diferencial é:

> RADAR OFICIAL + VIA CERTA + SENTIDO CERTO + VALIDADE + CONTEXTO DE NAVEGAÇÃO.

Modo Estrada existe para deixar isso ainda mais forte quando o usuário sai do ambiente urbano.
