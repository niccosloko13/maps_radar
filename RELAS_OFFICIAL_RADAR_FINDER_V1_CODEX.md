# RELAS OFFICIAL RADAR FINDER V1 — PILOTO PRAIA GRANDE + PSIE/INMETRO

## OBJETIVO

Construir o primeiro núcleo real do RELAS para identificar apenas equipamentos oficiais de fiscalização, associar cada equipamento municipal ao respectivo registro metrológico quando aplicável e permitir consultar sua situação em uma data histórica (ex.: data da multa).

Esta missão deve começar por PRAIA GRANDE/SP como município piloto e produzir uma arquitetura reutilizável para DER-SP, CET-SP, outros municípios e posteriormente todo o Estado de São Paulo.

O RELAS NÃO deve tratar um simples ponto no mapa como “radar verificado”.

Um radar só recebe status oficial/verificado quando existir evidência oficial suficiente.

---

# EVIDÊNCIAS CONFIRMADAS ANTES DESTA MISSÃO

## Prefeitura de Praia Grande — lista oficial atual

A página oficial municipal “Pontos de Fiscalização Eletrônica (Radares de Trânsito e Lombadas Eletrônicas)” lista atualmente 10 pontos:

### Controlador eletrônico de velocidade — Radar Fixo

1. Av. Ayrton Senna da Silva oposto 382 — Sítio do Campo
   - Sentido: PG/SV
   - Velocidade: 60 km/h

2. Av. Ayrton Senna da Silva oposto 611 — Sítio do Campo
   - Sentido: SV/PG
   - Velocidade: 60 km/h

### Redutor eletrônico de velocidade — Lombada Eletrônica

3. Av. Marechal Mallet, altura do nº 928 — Canto do Forte
   - Sentido: Fortaleza de Itaipu / Palácio das Artes
   - Velocidade: 40 km/h

4. Av. Marechal Mallet, altura do nº 1122 — Canto do Forte
   - Sentido: Fortaleza de Itaipu / Palácio das Artes
   - Velocidade: 40 km/h

5. Av. Presidente Kennedy, próximo ao nº 4520 — Aviação
   - Sentido: Aviação / Tupi
   - Velocidade: 40 km/h

6. Av. Presidente Kennedy, altura do nº 6020 — Tupi
   - Sentido: Tupi / Ocian
   - Velocidade: 40 km/h

7. Av. Presidente Kennedy, altura do nº 7954 — Ocian
   - Sentido: Ocian / Mirim
   - Velocidade: 40 km/h

8. Av. Presidente Kennedy, s/n, próximo à Prefeitura — Mirim
   - Sentido: Maracanã / Mirim
   - Velocidade: 40 km/h

9. Av. Ministro Marcos Freire, próximo ao nº 8124 — Anhanguera
   - Sentido: Anhanguera / Nova Mirim
   - Velocidade: 40 km/h

10. Av. Dr. Roberto de Almeida Vinhas, próximo ao nº 20151 — Ocian
    - Sentido: Ocian / Tupi
    - Velocidade: 40 km/h

Fonte oficial:
https://www.praiagrande.sp.gov.br/cartaservicos/Servicos/consultaCS.asp

---

# HISTÓRICO OFICIAL IMPORTANTE

A Prefeitura publicou em 02/04/2024 que novas lombadas eletrônicas seriam aferidas pelo IPEM e passariam a funcionar após o aval oficial:

- Kennedy 4520
- Kennedy 7954
- Roberto de Almeida Vinhas 20151
- Kennedy 6020
- Kennedy próximo à Prefeitura

Também anunciou posteriormente:
- Marechal Mallet 928
- Marechal Mallet próximo 1180
- Ministro Marcos Freire próximo 8134
- Ayrton Senna oposto 328
- Ayrton Senna oposto 611

Fonte:
https://www2.praiagrande.sp.gov.br/noticiaNP/id/363

Em 18/04/2024 houve aferição/ativação oficial de:
- Ministro Marcos Freire 8134
- Marechal Mallet 928
- Ayrton Senna 328
- Ayrton Senna 611

Fonte:
https://www2.praiagrande.sp.gov.br/noticia/setran-e-ipem-realizam-afericoes-de-lombadas--eletronicas-e-radares-nesta-quintafeira-18

Em 29/04/2025 a Prefeitura informou que o IPEM aferiu 8 equipamentos no município.

Fonte:
https://www2.praiagrande.sp.gov.br/noticia/ipem-realiza-afericao-de-lombadas-eletronicas-e-radares-em-pg-

IMPORTANTE:
Os endereços atuais da página municipal diferem em alguns números dos textos históricos, por exemplo:

- Ayrton Senna 328 -> página atual 382
- Mallet 1180 -> página atual 1122
- Marcos Freire 8134 -> página atual 8124

NÃO assumir que isso significa mudança física.
Pode ser:
- correção cadastral;
- atualização de numeração;
- relocação;
- erro histórico.

Criar evidência e conflito; não sobrescrever silenciosamente.

---

# PSIE / INMETRO — FONTE METROLÓGICA

O Inmetro mantém o PSIE (Portal de Serviços do Inmetro nos Estados).

Existe oficialmente um conjunto de dados abertos “Portal de Serviços do Inmetro nos Estados - PSIE”.

Esse dataset possui recursos específicos:

- Metadados - Medidores de Velocidade
- Medidores de Velocidade XML
- Medidores de Velocidade JSON

O catálogo informa:
- licença aberta CC0;
- atualização mensal;
- dados de instrumentos que sofreram verificação;
- estado pode ser selecionado/alterado.

O Plano de Dados Abertos do Inmetro também confirma que os dados do PSIE são uma base aberta, disponível em dados.gov.br, com atualização mensal.

NÃO automatizar captcha.
NÃO fazer bypass de mecanismos de proteção.

Usar prioritariamente:
1. dataset aberto oficial JSON/XML;
2. consulta pública PSIE apenas para validação manual/link quando necessário.

---

# MISSÃO 1 — DESCOBRIR O ENDPOINT OFICIAL DO PSIE OPEN DATA

Localizar, documentar e testar o recurso oficial atual:

“Medidores de Velocidade JSON”

e, se necessário:

“Medidores de Velocidade XML”

Preferir origem oficial `dados.gov.br`, Inmetro ou endpoint indicado pelos metadados oficiais.

Não depender de AmeriGEOSS como fonte primária se ele for apenas espelho/catalogador.

Criar:

`research/PSIE_OPEN_DATA.md`

Documentar:

- URL do catálogo oficial;
- URL exata do recurso JSON/XML;
- parâmetros suportados;
- forma de selecionar `UF=SP`;
- schema observado;
- frequência de atualização;
- licença;
- data da última coleta;
- exemplos reais de registros;
- limitações.

---

# MISSÃO 2 — BAIXAR MEDIDORES DE VELOCIDADE DE SP

Criar um coletor:

```text
app/data-sources/
  psie/
    psie-client.py
    psie-normalizer.py
```

ou arquitetura equivalente adequada ao projeto.

O coletor deve:

1. baixar o dataset oficial;
2. selecionar São Paulo;
3. normalizar campos;
4. preservar payload bruto;
5. nunca alterar o dado original;
6. armazenar timestamp de coleta.

Campos desejados, conforme disponíveis:

```text
instrument_type
responsible
municipality
verification_date
valid_until
result
type
brand
model
approval_ordinance
location
inmetro_number
serial_number
lane
direction
nominal_speed
certificate_number
service_type
result_type
source_url
retrieved_at
raw_payload
```

Não inventar campo ausente.

---

# MISSÃO 3 — FILTRAR PRAIA GRANDE

Filtrar todos os registros:

```text
municipality = PRAIA GRANDE
UF = SP
instrument_type = MEDIDOR DE VELOCIDADE
```

Salvar snapshot de desenvolvimento:

```text
artifacts/official-radar-finder-v1/private/psie-praia-grande.json
```

---

# MISSÃO 4 — CRIAR REGISTRO MUNICIPAL OFICIAL

Criar adapter:

```text
app/data-sources/municipal/praia-grande.*
```

Extrair a página oficial atual de fiscalização eletrônica.

Normalizar os 10 pontos.

Modelo conceitual:

```json
{
  "authority": "PRAIA_GRANDE_SETRAN",
  "municipality": "PRAIA GRANDE",
  "type": "speed_camera",
  "address_raw": "Av. Ayrton Senna da Silva oposto 382",
  "direction_raw": "PG/SV",
  "speed_limit": 60,
  "official_status": "listed",
  "source_url": "...",
  "retrieved_at": "..."
}
```

Não usar geocodificação como evidência de equipamento oficial.

Coordenada geocodificada deve ter:

```text
coordinate_source = geocoder
coordinate_confidence != official
```

---

# MISSÃO 5 — ENTITY RESOLUTION MUNICÍPIO <-> PSIE

Construir matcher que tente associar cada um dos 10 pontos oficiais ao instrumento correspondente do PSIE.

NÃO fazer apenas `address == address`.

Score deve usar:

```text
municipality
street normalization
number/proximity
equipment type
nominal speed
direction
responsible
brand/model
historical address aliases
```

Criar normalização de vias:

```text
AV.
AVENIDA
PRES.
PRESIDENTE
DR.
DOUTOR
N.
Nº
S/N
```

Normalizar acentos, caixa e pontuação.

### Endereços históricos conhecidos

Criar aliases, mas não assumir identidade automaticamente:

```text
AYRTON SENNA 328 <-> 382
MALLET 1180 <-> 1122
MARCOS FREIRE 8134 <-> 8124
```

Esses pares devem aumentar possibilidade de match apenas quando outras evidências confirmarem.

---

# MATCH CONFIDENCE

Cada associação deverá receber:

```text
EXACT
HIGH
MEDIUM
LOW
UNMATCHED
CONFLICT
```

Critérios:

## EXACT
Serial/Inmetro ID diretamente ligado à mesma localização/órgão.

## HIGH
Via + sentido + velocidade + tipo compatíveis e sem concorrente plausível.

## MEDIUM
Via/velocidade compatíveis, mas endereço ou sentido incompletos.

## LOW
Apenas similaridade textual.

## UNMATCHED
Nenhum candidato suficiente.

## CONFLICT
Duas evidências oficiais incompatíveis.

Nunca promover LOW para VERIFIED.

---

# MISSÃO 6 — HISTÓRICO METROLÓGICO

Para cada instrumento identificado, armazenar todas as verificações disponíveis.

Tabela/conceito:

```text
equipment_verifications
```

Campos:

```text
equipment_id
certificate_number
verification_date
valid_from
valid_until
result
service_type
source_url
retrieved_at
```

Nunca sobrescrever histórico anterior.

---

# MISSÃO 7 — VALIDITY AT DATE

Implementar:

```js
getEquipmentStatusAt(equipmentId, date)
```

Resposta conceitual:

```json
{
  "official_listing": true,
  "metrology_required": true,
  "metrology_record_found": true,
  "approved": true,
  "valid_at_date": true,
  "verification_date": "2025-04-28",
  "valid_until": "2026-04-27",
  "evidence": []
}
```

Se não existir evidência suficiente:

```text
UNKNOWN
```

Nunca:

```text
ILLEGAL
```

somente por ausência de dado.

---

# MISSÃO 8 — EVIDENCE MODEL

Criar entidade:

```text
equipment_evidence
```

Cada claim deve informar:

```text
equipment_id
source_authority
source_type
claim
effective_from
effective_until
retrieved_at
source_url
raw_reference
confidence
```

Tipos:

```text
OFFICIAL_LISTING
METROLOGY_VERIFICATION
ACTIVATION_NOTICE
DEACTIVATION_NOTICE
ADDRESS_UPDATE
SPEED_LIMIT
DIRECTION
SERIAL_ID
INMETRO_ID
```

---

# MISSÃO 9 — STATUS RELAS

Estados visíveis:

```text
OFFICIAL_VERIFIED
OFFICIAL_METROLOGY_PENDING
OFFICIAL_CONFLICT
HISTORICALLY_ACTIVE
DEACTIVATED
DISCOVERED_UNVERIFIED
```

## OFFICIAL_VERIFIED

Exigir:
- fonte oficial de localização/uso;
- equipamento resolvido;
- verificação metrológica válida para a data consultada quando aplicável.

## OFFICIAL_METROLOGY_PENDING

Órgão lista o equipamento, mas não foi possível localizar confirmação metrológica suficiente.

Não afirmar irregularidade.

---

# MISSÃO 10 — RELATÓRIO PILOTO PRAIA GRANDE

Criar:

`artifacts/official-radar-finder-v1/PRAIA_GRANDE_MATCH_REPORT.md`

Tabela obrigatória:

```text
municipal_location
municipal_type
speed
direction
psie_match
serial_number
inmetro_number
brand_model
last_verification
valid_until
result
match_confidence
conflicts
```

Para os 10 pontos.

No final:

```text
10 official municipal records
X EXACT
X HIGH
X MEDIUM
X LOW
X UNMATCHED
X CONFLICT
```

Esse relatório é o principal deliverable.

---

# MISSÃO 11 — TESTE DE MULTA

Criar endpoint/função de teste:

```text
findEnforcementAt({
  municipality,
  street,
  date,
  direction?,
  speed_limit?,
  serial_number?,
  inmetro_number?
})
```

Prioridade de busca:

```text
serial/inmetro id
→ official location
→ street/date
→ direction
→ speed
```

Retornar candidatos explicáveis.

Exemplo:

```json
{
  "query_date": "2026-03-01",
  "candidates": [
    {
      "equipment_id": "...",
      "match_score": 0.97,
      "official": true,
      "valid_at_date": true,
      "why": [
        "same official street",
        "same direction",
        "same speed limit",
        "metrology certificate covered query date"
      ]
    }
  ]
}
```

---

# MISSÃO 12 — NÃO ALTERAR O MAPA AINDA

Nesta missão, NÃO trocar imediatamente todos os pontos atuais.

Primeiro provar os matches.

Somente depois do relatório piloto aprovado:

- migrar Praia Grande para a nova base;
- ativar filtro “somente oficiais”;
- adicionar card de validade;
- depois expandir para outras cidades.

---

# TESTES OBRIGATÓRIOS

- parser municipal;
- PSIE parser;
- schema variation;
- street normalization;
- historical aliases;
- direction matching;
- speed matching;
- ambiguous records;
- no match;
- conflict;
- validity-at-date boundary;
- expired certificate;
- exact date on valid_until;
- multiple verification histories;
- source temporarily unavailable;
- stale cached source.

---

# CACHE E RESILIÊNCIA

Fontes públicas podem cair.

Criar cache com:

```text
last_successful_fetch
source_updated_at
retrieved_at
etag/hash se disponível
```

Nunca apagar a última base válida por falha temporária.

---

# SEGURANÇA / COMPLIANCE

- não burlar captcha;
- não simular usuário para contornar proteção;
- usar dataset aberto oficial;
- respeitar rate limits;
- cachear;
- não martelar órgãos públicos;
- preservar links das fontes.

---

# PRÓXIMA EXPANSÃO APÓS PRAIA GRANDE

Somente depois do piloto:

1. DER-SP
2. CET-SP
3. Santos
4. São Vicente
5. Guarujá
6. Cubatão
7. São Bernardo do Campo
8. Santo André
9. São Caetano
10. demais municípios SP

Criar adapters independentes por órgão.

---

# DEFINITION OF DONE

A missão termina quando:

- PSIE open data foi acessado oficialmente;
- registros SP foram importados;
- Praia Grande foi filtrada;
- 10 pontos municipais foram normalizados;
- entity resolver foi implementado;
- serial/Inmetro IDs foram capturados quando disponíveis;
- histórico foi preservado;
- validade por data funciona;
- relatório de match mostra o resultado de todos os 10;
- nenhuma irregularidade foi inferida sem evidência;
- nenhum captcha foi burlado;
- mapa atual permaneceu intacto.

---

# RELATÓRIO FINAL

Criar:

```text
artifacts/official-radar-finder-v1/REPORT.md
artifacts/official-radar-finder-v1/PRAIA_GRANDE_MATCH_REPORT.md
artifacts/official-radar-finder-v1/SOURCE_SCHEMA.md
artifacts/official-radar-finder-v1/KNOWN_LIMITATIONS.md
research/PSIE_OPEN_DATA.md
```

No REPORT, responder explicitamente:

1. O endpoint oficial PSIE open data ainda funciona?
2. Quantos medidores de velocidade existem em SP?
3. Quantos aparecem em Praia Grande?
4. Quantos dos 10 pontos municipais tiveram match?
5. Quantos tiveram serial number?
6. Quantos tiveram Inmetro number?
7. Quantos possuem verificação vigente hoje?
8. Quais conflitos de endereço foram encontrados?
9. Quais equipamentos não puderam ser resolvidos?
10. O sistema está pronto para migrar Praia Grande para “somente oficiais”?
