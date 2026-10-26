# RELAS NAVIGATION INTELLIGENCE V3 — FASE B COMPLETA
## MAPA + ADMIN + TRÂNSITO + CHUVA + POSTOS + OBRAS + PEDÁGIOS + FONTES OFICIAIS

## MISSÃO

Implementar a Fase B do RELAS como uma evolução operacional completa.

REGRA PRINCIPAL:

Nenhuma integração nova termina somente no backend.

Toda nova fonte deve possuir, quando aplicável:
1. coletor/adapter;
2. normalização;
3. cache/freshness;
4. status administrativo;
5. camada/ícone no mapa;
6. card/detalhe;
7. integração com navegação;
8. regras de alerta;
9. testes;
10. telemetria/diagnóstico.

O RELAS continua RADAR-FIRST.

Radar oficial e verificado permanece acima de trânsito, clima, postos e comunidade na hierarquia do produto.

---

# 1. ARTESP CCM — OCORRÊNCIAS

Documentação oficial:
https://ccm.artesp.sp.gov.br/rodovias/api/docs/

Endpoint:
GET https://ccm.artesp.sp.gov.br/rodovias/api/ocorrencias/

Características confirmadas:
- JSON UTF-8;
- atualização em tempo real;
- autenticação por API Key;
- header Authorization: Api-Key <key>;
- rate limit padrão: 12 requests/hora;
- proteção adicional de burst por IP;
- recomendação oficial de cache e polling de aproximadamente uma chamada a cada 5 minutos;
- filtros por data, concessionária, rodovia e município;
- includes: vítimas, interdições, congestionamentos, veículos e atualizações;
- licença indicada pela própria API: CC BY-NC 4.0.

Nunca colocar API Key no frontend.

---

# 2. ARTESP CCM — INTERVENÇÕES / OBRAS

Endpoint:
GET https://ccm.artesp.sp.gov.br/rodovias/api/intervencoes/

Filtros:
- data;
- concessionária;
- rodovia;
- município IBGE;
- categoria.

Usar catálogos oficiais de concessionárias, rodovias, municípios e categorias.

Mapear para:
ROADWORK
MAINTENANCE
LANE_CLOSURE
FULL_CLOSURE
SIGNALIZATION_WORK
OTHER_INTERVENTION

---

# 3. ARTESP — DADOS ABERTOS

Usar o portal oficial para:
- Ocorrências;
- Pedágio;
- Índice de Disponibilidade de Equipamentos;
- Malha Rodoviária;
- Focos de Incêndio;
- Editais/Contratos;
- Painéis rodoviários.

A malha possui XLSX/KMZ.
O índice de equipamentos possui CSV.

Não interpretar automaticamente qualquer “equipamento” como radar.

---

# 4. PRF — UNIDADES EM SP

Fonte:
https://www.gov.br/prf/pt-br/canais-de-atendimento/unidades-prf/sao-paulo

Criar adapter para:
PRF_SUPERINTENDENCY
PRF_DELEGACY
PRF_OPERATIONAL_UNIT

No mapa, priorizar PRF_OPERATIONAL_UNIT.

Não mostrar unidade administrativa como posto operacional sem evidência.

---

# 5. PM RODOVIÁRIA SP

Criar adapter `pmrv-sp`.

Usar somente fonte oficial PMESP/CPRv e a versão mais recente encontrada.

Antes de importar:
- comparar data da fonte;
- classificar freshness;
- preservar histórico;
- não assumir atualidade de PDF antigo.

Tipos:
PMRV_COMPANY
PMRV_OPERATIONAL_BASE
PMRV_POST

---

# 6. SP ÁGUAS / SIBH — CHUVA

Fonte:
https://apps.spaguas.sp.gov.br/sibh/

Objetivo:
descobrir endpoint público legítimo utilizado pelo portal.

Procurar:
JSON
GeoJSON
REST
WFS
WMS
ArcGIS
XHR/fetch público

Se houver endpoint:
- documentar;
- criar adapter;
- normalizar;
- cachear.

Se não houver:
- não fazer scraping agressivo;
- documentar a limitação;
- manter integração preparada.

---

# 7. DEFESA CIVIL SP

Fonte:
https://admin.defesacivil.sp.gov.br/previsaodotempo/sp/alertas

Normalizar:
tipo
mensagem
gravidade
urgência
certeza
região
valid_from
valid_until
orientação

Tipos:
HEAVY_RAIN
STORM
GALE
FLOOD_ALERT
OTHER_WEATHER_ALERT

Não mostrar todos os alertas do estado.
Cruzar com rota/região/corredor.

---

# 8. ARQUITETURA

OFFICIAL SOURCES
↓
SOURCE ADAPTERS
↓
NORMALIZER
↓
FRESHNESS / CACHE
↓
EVENT STORE
├─ ADMIN
└─ MAP
   ↓
ROUTE EVENT CORRIDOR
↓
ALERT MANAGER
↓
CARD / VOICE / UI

---

# 9. SOURCE REGISTRY

Criar `road_data_sources`.

Campos:
source_id
name
authority
category
base_url
data_format
auth_type
license
terms_version
poll_interval_seconds
rate_limit
last_attempt_at
last_success_at
last_source_timestamp
last_error
status
enabled
record_count
freshness_status
adapter_version

Status:
HEALTHY
STALE
DEGRADED
ERROR
AUTH_REQUIRED
DISABLED
NOT_CONFIGURED

---

# 10. CREDENCIAIS

Usar env/backend:
ARTESP_OCCURRENCES_API_KEY
ARTESP_INTERVENTIONS_API_KEY

Se uma chave única servir, adaptar à documentação real.

Admin mostra somente:
Credencial configurada: SIM/NÃO

Nunca exibir valor.

---

# 11. CACHE ARTESP

Nunca chamada por usuário.

Fluxo:
ARTESP → backend poll → cache/store → usuários.

Polling inicial:
300s, configurável.

Preservar último snapshot bom.

Fonte caiu:
STALE

Nunca:
ZERO EVENTS

---

# 12. ROAD EVENT MODEL

Criar `road_event`.

Campos:
event_id
source_id
external_id
event_type
subtype
severity
road
direction
municipality_ibge
municipality
km_start
km_end
lat
lon
geometry
start_at
updated_at
end_at
status
lane_impacts
total_closure
description
source_updated_at
retrieved_at
expires_at
confidence

Tipos:
ACCIDENT
ROADWORK
MAINTENANCE
CLOSURE
CONGESTION
FLOOD
LANDSLIDE
EROSION
FIRE
VEHICLE_BREAKDOWN
OBJECT_ON_ROAD
ANIMAL_ON_ROAD
WEATHER
POLICE_OPERATION
OTHER

---

# 13. DEDUPE MULTIFONTE

Preparar dedupe entre:
ARTESP
DER
Defesa Civil
SP Águas
comunidade futura

Usar:
tipo
geometria
rodovia
km
sentido
tempo

Criar `event_evidence`.

---

# 14. ROUTE EVENT CORRIDOR

CITY_MODE:
atrás 1 km
à frente 10 km

ROAD_MODE:
atrás 3 km
à frente 50 km

Ajustar por velocidade.

Evitar evento de pista paralela/sentido incompatível quando houver dados suficientes.

---

# 15. MAPA — OBRIGATÓRIO

Camadas:
road-events
road-events-clusters
roadworks
closures
floods
weather
prf-posts
pmrv-bases
toll-plazas
support-bases
rain-stations/overlay

Radar permanece acima em prioridade visual.

---

# 16. VISIBILIDADE POR ZOOM

Zoom baixo:
clusters, bloqueios grandes, clima severo, eventos críticos.

Zoom médio:
obras, acidentes, pedágios, bases policiais, chuva relevante.

Zoom alto:
detalhes, SAU, eventos menores, estações se camada ligada.

---

# 17. POSTOS PRF

Ícone próprio.

Card:
POSTO PRF
rodovia/km
município
Fonte: PRF
Atualização

Sem voz por padrão.

---

# 18. PM RODOVIÁRIA

Ícone distinto da PRF.

Card:
POLÍCIA MILITAR RODOVIÁRIA
companhia/base
rodovia/km
Fonte oficial PMESP
Atualização

---

# 19. PEDÁGIOS

Criar TOLL_PLAZA.

Mostrar:
nome
rodovia
km
concessionária
tarifa
vigência da tarifa
source_updated_at

Se valor estiver velho/desconhecido, não exibir.

---

# 20. BASES / SAU / APOIO

Categorias:
SAU
OPERATIONAL_BASE
TOW_BASE
MECHANICAL_SUPPORT
DER_BASE
CONCESSIONAIRE_BASE

Só importar de fonte oficial.

---

# 21. TRÂNSITO NO MAPA

Quando houver geometria:
usar segmento/linha, não só pin.

Mostrar:
rodovia
sentido
km início/fim
extensão
velocidade média
atraso
causa
atualização

Radar acima da linha de trânsito.

---

# 22. CHUVA NO MAPA

Modo normal:
overlay discreto + alertas relevantes à rota.

Modo debug:
estações/pluviômetros.

No Road Mode:
“Chuva forte à frente · 12 km”
quando sustentado por dado real.

---

# 23. DEFESA CIVIL NO MAPA

Representação regional adequada.

Card:
CHUVA INTENSA
Alerta grave
Vigência
Fonte: Defesa Civil SP

Não despejar texto longo na navegação.

---

# 24. ALERT MANAGER

P0 Radar iminente
P1 Bloqueio total / acidente grave / alagamento crítico
P2 Manobra iminente
P3 Obra/interdição
P4 Trânsito forte / chuva
P5 Postos/pedágios/apoio

Radar não pode ser interrompido por chuva/trânsito.

---

# 25. ADMIN — OBRIGATÓRIO

Criar/expandir:
Fontes & Operação

Subseções:
Visão Geral
ARTESP
SP Águas
Defesa Civil
PRF
PM Rodoviária
Pedágios
Bases/Apoio
Eventos
Logs
Layer Diagnostics

---

# 26. ADMIN — VISÃO GERAL

Cards:
FONTES ATIVAS
FONTES COM ERRO
FONTES DESATUALIZADAS
ÚLTIMA SINCRONIZAÇÃO
EVENTOS ATIVOS
OBRAS
INTERDIÇÕES
CONGESTIONAMENTOS
CHUVA/ALERTAS
POSTOS
PEDÁGIOS

---

# 27. ADMIN — ARTESP

Mostrar:
API configurada?
status
último fetch
último sucesso
versão dos termos
licença
rate limit
remaining
retry-after
record count
ocorrências ativas
intervenções ativas
erros

Ações:
Sincronizar agora
Testar conexão
Ver payload normalizado
Ver logs
Desabilitar fonte

Respeitar rate limit.

---

# 28. ADMIN — SP ÁGUAS

Mostrar:
adapter status
endpoint descoberto
última atualização
estações recebidas
estações com chuva
freshness
errors

Opcional:
mapa admin de cobertura.

---

# 29. ADMIN — DEFESA CIVIL

Mostrar:
alertas ativos
gravidade
regiões
vigência
última coleta

Não permitir editar alerta oficial.

---

# 30. ADMIN — PRF / PMRv

Tabela:
tipo
nome
rodovia
km/endereço
município
coordinate_quality
source
source_updated_at
status

Ações:
reprocessar geocoding
marcar revisão

---

# 31. ADMIN — PEDÁGIOS / APOIO

Tabela:
nome
tipo
rodovia
km
concessionária
status
source
freshness

Mostrar duplicatas/conflitos.

---

# 32. ADMIN — EVENTOS

Filtros:
ativo/finalizado
tipo
fonte
rodovia
município
gravidade
data

Tabela:
evento
fonte
local
status
início
última atualização
expiração
evidências

Mapa admin selecionável.

---

# 33. ADMIN — LOGS

Campos:
source
started_at
finished_at
status
http_status
records_received
records_normalized
records_created
records_updated
records_expired
duplicates
errors
duration_ms

Nunca registrar segredo.

---

# 34. ADMIN — FRESHNESS

Status:
FRESH
AGING
STALE
BROKEN

Thresholds por fonte.

---

# 35. SOURCE CONTRACTS

Mostrar:
source contract version
adapter version
schema hash
last schema validation

Se schema mudar:
PARSER_DEGRADED

Preservar dados anteriores.

---

# 36. MAPA E ADMIN DEVEM BATER

Diagnóstico por camada:

received
normalized
active
eligible_map
eligible_route
rendered
alerted

Exemplo:
ARTESP_OCCURRENCES
received 120
normalized 120
active 23
map eligible 23
viewport 5
rendered 5
route corridor 2
alert eligible 1

---

# 37. CONFIGURAÇÃO DE CAMADAS DO USUÁRIO

Camadas:
Radares
Semáforos fiscalizadores
Lombadas eletrônicas
Trânsito
Obras
Interdições
Chuva
Defesa Civil
PRF
PM Rodoviária
Pedágios
Bases de apoio

Presets:
Essencial
Estrada
Completo
Personalizado

Road Mode pode sugerir “Estrada”, sem sobrescrever escolha explícita.

---

# 38. ÍCONES

Criar família SVG única para:
PRF
PMRv
pedágio
SAU
base
obra
bloqueio
acidente
alagamento
deslizamento
erosão
incêndio
chuva
vendaval
trânsito

Estados:
normal
selected
critical
stale

---

# 39. APIs INTERNAS

Exemplos:
GET /api/road-events
GET /api/road-events/route
GET /api/road-infrastructure
GET /api/weather
GET /api/source-health

Admin protegido:
GET /api/admin/sources
POST /api/admin/sources/{id}/sync
GET /api/admin/sources/{id}/logs
GET /api/admin/layer-diagnostics

Adaptar ao padrão real do projeto.

---

# 40. PERFORMANCE

Não enviar todos os eventos do estado ao frontend.

Backend filtra por:
viewport
rota
corredor
zoom

Usar clustering.

---

# 41. PRIVACIDADE

Não salvar histórico de localização por causa desta fase.

Preferir:
viewport
current route corridor

Sem comunidade/presença agora.

---

# 42. LICENÇAS

Registrar:
license
terms_url
terms_version
attribution
commercial_restrictions

ARTESP: tratar CC BY-NC 4.0 conforme documentação.

---

# 43. TESTES DE FONTE

ARTESP:
200
401
403
429
timeout
schema change
empty valid response
stale fallback

SP Águas:
normal
sem leitura
dado velho
schema diferente
indisponível

Defesa Civil:
ativo
expirado
grave
fora da rota

PRF/PMRv:
endereço
km
coordenada oficial/geocodificada
duplicata

---

# 44. TESTES DE MAPA

event appears
filtered by zoom
outside viewport absent
outside corridor not alerted
direction mismatch not alerted
radar above traffic
cluster works
icons load
click detail works

---

# 45. TESTES DO ADMIN

source health
manual sync respeita rate limit
erro visível
stale visível
counts corretos
layer diagnostics corretos
API key nunca exposta
logs
filtros

---

# 46. TEST DRIVE

Cenário:
Praia Grande → São Bernardo

Testar:
SP-055
SP-160
Anchieta/Imigrantes

Validar:
ROAD_MODE
PRF/PMRv
pedágio
ARTESP event
obra
trânsito
chuva
Defesa Civil
radar
prioridade de voz

Se não houver evento real:
usar fixture explicitamente TEST.

Nunca inserir fixture na base real.

---

# 47. ARTEFATOS

Criar:
artifacts/navigation-intelligence-v3-phase-b/REPORT.md
artifacts/navigation-intelligence-v3-phase-b/SOURCE_MATRIX.md
artifacts/navigation-intelligence-v3-phase-b/ADMIN.md
artifacts/navigation-intelligence-v3-phase-b/MAP_LAYERS.md
artifacts/navigation-intelligence-v3-phase-b/ARTESP.md
artifacts/navigation-intelligence-v3-phase-b/WEATHER.md
artifacts/navigation-intelligence-v3-phase-b/ROAD_INFRASTRUCTURE.md
artifacts/navigation-intelligence-v3-phase-b/LAYER_DIAGNOSTICS.md
artifacts/navigation-intelligence-v3-phase-b/KNOWN_LIMITATIONS.md

---

# 48. SOURCE_MATRIX

Colunas:
Source
Authority
Data
Format
Auth
Rate limit
Freshness
License
Backend adapter
Map layer
Admin panel
Status

---

# 49. RELATÓRIO FINAL — RESPONDER

1. ARTESP API Key foi configurada?
2. Conexão real funcionou?
3. Quantas ocorrências ativas?
4. Quantas intervenções ativas?
5. Quantas entraram no mapa?
6. Quantas foram relevantes à rota?
7. SP Águas tem endpoint público automatizável?
8. Quantos pluviômetros/leituras ingeridos?
9. Defesa Civil integrada?
10. Quantos alertas ativos?
11. Quantas unidades PRF importadas?
12. Quantas bases PMRv?
13. Quantos pedágios?
14. Quantas bases/SAU?
15. Road Mode mostra corretamente?
16. Radar continua P0?
17. Admin mostra health/freshness/logs?
18. Alguma chave apareceu no frontend?
19. Alguma fonte está stale?
20. Está pronto para teste físico?

---

# 50. ORDEM DE EXECUÇÃO

1. checkpoint
2. auditar source-contracts existentes
3. Source Registry
4. Admin Source Health
5. ARTESP adapter
6. cache/rate limit
7. ocorrências
8. intervenções
9. road_event
10. mapa ARTESP
11. admin ARTESP
12. descobrir SP Águas
13. integrar chuva
14. Defesa Civil
15. mapa clima
16. admin clima
17. PRF
18. PMRv
19. pedágios
20. bases/SAU
21. map layers
22. admin infrastructure
23. Route Event Corridor
24. AlertManager
25. diagnostics
26. backend tests
27. frontend tests
28. admin tests
29. mobile
30. rota real
31. relatório

---

# 51. NÃO FAZER

- Não usar chave ARTESP no frontend.
- Não exceder rate limit.
- Não fazer polling por usuário.
- Não inventar dado SP Águas.
- Não usar Waze como fonte de radar.
- Não marcar posto genérico como oficial.
- Não esconder freshness.
- Não zerar dataset se fonte falhar.
- Não mexer no Official Radar Finder.
- Não deployar automaticamente.
- Não implementar comunidade nesta fase.
- Não permitir que trânsito/clima tire prioridade do radar.

---

# DEFINIÇÃO DE PRONTO

Uma integração só conta como pronta quando possuir:

BACKEND
+
CACHE
+
NORMALIZAÇÃO
+
MAPA
+
NAVEGAÇÃO
+
ADMIN
+
DIAGNÓSTICO
+
TESTES

O operador deve abrir o ADMIN e saber:
- quais fontes estão funcionando;
- quando atualizaram;
- quantos registros entregaram;
- o que foi ao mapa;
- por que algo não apareceu;
- quando uma fonte quebrou.

O usuário deve abrir o MAPA e receber somente informações úteis à sua rota, sempre com RADAR como prioridade máxima.
