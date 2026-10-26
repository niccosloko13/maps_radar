# Relas Official Radar Finder V1 — piloto Praia Grande

## Resultado

Coletor oficial, normalização, arquivo de evidências append-only, candidatos explicáveis e consulta temporal implementados e executados. **O piloto não está aprovado para migrar o mapa para “somente oficiais/verificados”.** O mapa atual permaneceu intacto.

Checkpoint `4943cd4`; branch `feat/official-radar-finder-v1`. Nenhuma alteração em app/, server.py, autenticação, schema ou dados do banco atual. Não houve deploy nem alteração no Neon nesta missão.

Principal entrega: [tabela dos dez pontos e candidatos](PRAIA_GRANDE_MATCH_REPORT.md).

## Respostas às dez perguntas

| Pergunta | Resultado observado |
| --- | --- |
| 1. Endpoint PSIE funciona? | Sim: JSON oficial SP HTTP 200, 18.142.779 bytes; SHA-256 e cabeçalhos registrados em summary.json. |
| 2. Quantos medidores em SP? | 9444 registros do recurso; 9435 chaves agrupadas por identificadores, das quais uma sem ID físico. Nove chaves possuem mais de um registro. Não é censo físico deduplicado certificado. |
| 3. Quantos em Praia Grande? | 15 registros / 15 grupos identificados no PSIE; dez pontos na lista municipal atual. |
| 4. Quantos dos dez tiveram match? | Dez possuem candidatos; 0 EXACT, 0 HIGH, 5 MEDIUM, 0 LOW, 0 UNMATCHED, 5 CONFLICT. Zero identidades aprovadas. |
| 5. Quantos tiveram serial? | Dez candidatos principais possuem série; os 15 registros PG têm identificadores por faixa. Isso não confirma o vínculo municipal. |
| 6. Quantos tiveram Inmetro? | Dez candidatos principais possuem número Inmetro, sujeito à mesma ressalva de vínculo. |
| 7. Quantos têm verificação vigente hoje? | Dez instrumentos PSIE de PG têm histórico aprovado cobrindo 25/10/2026 no snapshot mensal. Zero pontos municipais podem receber OFFICIAL_VERIFIED com as associações atuais. |
| 8. Quais conflitos de endereço? | 328/382 (Ayrton Senna), aliases históricos 1180/1122 (Mallet), 8134/8124 (Marcos Freire); além de quatro divergências de descrição de sentido. Não se afirma relocação. |
| 9. Quais não foram resolvidos? | Todos os dez vínculos permanecem sem EXACT/HIGH. Os cinco MEDIUM são Ayrton 611, Kennedy 4520/6020/7954 e Roberto Vinhas 20151; os demais cinco estão em CONFLICT. |
| 10. Pronto para somente oficiais? | Não. É necessária revisão dos vínculos, sentidos, números históricos e velocidade nominal ausente; não trocar a base do mapa. |

Data da coleta/consulta: 25/10/2026. Arquivo PSIE `Last-Modified` 01/10/2026: evidência mensal, não consulta em tempo real ao instrumento.

## Implementação

- `official_radar/client.py`: fontes oficiais HTTPS, limite 64MiB, timeout, cache 24h, ETag/304, SHA-256, última coleta boa e fallback stale; sem polling ou captcha.
- `official_radar/normalize.py`: JSON/XML, aliases de campos, datas, faixas/histórico/proprietário, zero como velocidade desconhecida, payload bruto preservado.
- `official_radar/municipal.py`: extrai serviço municipal 249 ao vivo, exige dez pontos completos, sem geocodificação; separa lista atual e referências históricas.
- `official_radar/resolver.py`: município/via/número/marco/tipo/velocidade/sentido, IDs, proprietário/marca/modelo quando disponíveis, aliases e concorrentes; score com razões e conflitos.
- `official_radar/repository.py`: arquivo SQLite NOVO e privado do piloto, sem conectar ao SQLite atual ou ao Neon. Histórico/eventos e versões somente adicionados. Estrutura transferível à camada de banco existente após aprovação.
- `official_radar/service.py`: `OfficialRadarFinder.getEquipmentStatusAt(equipmentId,date)` e `findEnforcementAt(query)`; separa validade metrológica do instrumento de identidade/uso municipal e cobertura temporal. Consulta é função local, sem endpoint público nesta fase.
- `tools/official_radar_pilot.py`: coleta/importa SP, filtra PG localmente, gera snapshot privado, relatório de dez pontos, exemplo histórico e resumo público.
- `test_official_radar.py`, fixture municipal em `tests/fixtures/official-radar/`, `.gitignore`, `research/PSIE_OPEN_DATA.md` e relatórios.

## Preservação e contagens

Arquivo privado: `artifacts/official-radar-finder-v1/private/official-radar-pilot.sqlite`. Importação realizada: 9435 chaves de equipamento, 9444 versões de registro, **37367 eventos históricos únicos**, dez versões municipais e cinco snapshots de fontes. Contagens completas de evidências e antes/depois em `summary.json`.

Importar o mesmo snapshot duas vezes manteve as contagens. Nova versão divergente não substitui a antiga. Snapshot PG normalizado em `private/psie-praia-grande.json`; bruto integral SP, bruto municipal, três notícias e manifestos de cache preservados. Arquivo privado/SQLite não entram no Git ou no deploy.

## Execução e uso

```powershell
.venv\Scripts\python.exe tools/official_radar_pilot.py --date 2026-10-25
# --refresh: uma requisição condicional por fonte, sem tentativas em loop.
```

```python
import json
from pathlib import Path
from official_radar import OfficialRadarFinder

private = Path('artifacts/official-radar-finder-v1/private')
municipal = json.loads((private/'municipal-praia-grande.json').read_text(encoding='utf-8'))
instruments = json.loads((private/'psie-praia-grande.json').read_text(encoding='utf-8'))
finder = OfficialRadarFinder(municipal, instruments)
status = finder.getEquipmentStatusAt(municipal[0]['equipment_id'], '2026-03-01')
candidates = finder.findEnforcementAt({
    'municipality': 'Praia Grande', 'street': 'Av. Presidente Kennedy, 4520',
    'date': '2025-04-29', 'serial_number': '1389'
})
```

A consulta anterior à coleta da lista municipal não presume que o equipamento estava listado/ativo naquela data. O snapshot contém uma reprovação do candidato série 1389 em 29/04/2025 e posterior reparo; o histórico é mantido, sem emitir conclusão sobre multa ou vínculo incerto. Notícias anunciando aferição não foram convertidas em certificado ou ativação individual comprovada.

## Testes e problemas corrigidos

- 21 testes novos: parser municipal real, JSON/XML, variação de schema, bruto/zero, vias, aliases, sentido, velocidade, concorrência de candidatos, ausência, conflito, início/fim inclusivos, expiração, múltiplos históricos/reparo, conflito no mesmo dia, escopo de notícia, busca por ID, idempotência, fonte indisponível e payload inválido com cache anterior preservado.
- Suite Python completa: 38 testes; suite JavaScript existente: 53; selftest existente e compileall. Nenhum teste exige chamada a produção ou portal protegido.
- Piloto real executado, reexecutado com cache e checagem de contagens idempotentes.
- Falhas de pesquisa tratadas: API do catálogo sem contexto retornou 401; página pública normal forneceu metadados. Um comando py_compile com wildcard literal no Windows falhou; verificação correta com compileall passou. Não houve bypass.
- Corrigidos durante testes: possível uso de aviso de outro equipamento, validade após desativação e promoção indevida de candidato concorrente. Rejeição posterior supera aprovação antiga; dados incompatíveis não são ordenados arbitrariamente.

## Fontes e pendências

[Pesquisa do endpoint oficial](../../research/PSIE_OPEN_DATA.md), [schema/proveniência](SOURCE_SCHEMA.md), [limitações](KNOWN_LIMITATIONS.md). Fontes primárias: [catálogo federal](https://dados.gov.br/dados/conjuntos-dados/portal-de-servicos-do-inmetro-nos-estados-psie), [JSON SP](https://servicos.rbmlq.gov.br/dados-abertos/SP/medidores.json), [lista municipal](https://www.praiagrande.sp.gov.br/cartaservicos/Servicos/consultaCS.asp).

Próximo passo: revisão humana/oficial dos candidatos e obtenção de evidência individual de local/sentido/velocidade/ativação, antes de qualquer importação no Neon ou filtro “somente oficiais”. DER/CET e outras cidades permanecem fora deste piloto.
