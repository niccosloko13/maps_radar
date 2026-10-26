# Schema e proveniência

Implementação Python independente em `official_radar/`, compatível com a arquitetura atual. Nenhum código novo foi importado por `server.py` ou pelo mapa.

| Campo normalizado | Origem PSIE JSON | Tratamento |
| --- | --- | --- |
| uf / municipality | SiglaUf / Municipio | Somente SP; município com caixa/acentos normalizados |
| instrument_type | Escopo oficial do recurso medidores | Derivado explicitamente, com instrument_type_basis |
| type | TipoMedidor | Fixo/Estático/Portátil, sem converter lombada eletrônica em lombada física |
| location | LocalVerificacao | Texto original preservado |
| responsible | Proprietario.Nome | Proprietário não é automaticamente o órgão autuador |
| verification_date | DataUltimaVerificacao | dd/mm/aaaa -> ISO, inválida -> null |
| valid_until / result | DataValidade / UltimoResultado | Sem inferir validade de outra observação |
| lanes[].lane | Faixas[].NumeroFaixa | Texto |
| lanes[].inmetro_number | Faixas[].NumeroInmetro | Texto, zeros iniciais preservados |
| lanes[].serial_number | Faixas[].NumeroSerie | Texto |
| lanes[].direction | Faixas[].Sentido | Bruto e forma normalizada separados |
| lanes[].nominal_speed | Faixas[].VelocidadeNominal | Zero/ausente -> desconhecida; bruto preservado |
| verifications[].certificate_number | Historico[].NumeroCertificado | Vazio -> null; evento mantido |
| verification_date / valid_from | Historico[].DataLaudo | Data da verificação usada como início operacional da consulta, sem granularidade horária |
| valid_until | Historico[].DataValidade | Limite inclusivo por dia |
| result / service_type | Historico[].Resultado / TipoServico | Inclui Reprovado e Após Reparo |
| brand / model / approval_ordinance | Marca / Modelo / PortariaAprovacao se presentes | null quando ausentes; não enriquecidos por suposição |
| source_url / retrieved_at / raw_payload | Coleta | URL oficial e timestamp; payload bruto mantido |

Variações de caixa, underscores, envelopes JSON e XML simples são aceitas. Schema desconhecido, entidades XML e objetos aninhados inválidos são rejeitados antes de substituir o cache válido. O corpo bruto é preservado em blobs por SHA-256. Os fixtures XML são sintéticos; JSON real de SP foi processado integralmente.

## Município

Parser extrai o serviço oficial 249 do JSON embutido na página HTML, decodificando UTF-8 ou CP1252. Exige dez pontos distintos com endereço, sentido, tipo e velocidade; alteração na quantidade/schema exige revisão, não descarte silencioso. Não geocodifica. `coordinate_source`, coordenadas e confiança ficam null.

## Arquivo isolado de desenvolvimento

`private/official-radar-pilot.sqlite` é um arquivo NOVO do piloto, não o SQLite existente do Relas nem o Neon. Conceitos/tabelas: `source_snapshots`, `equipment`, `equipment_versions`, `equipment_verifications`, `equipment_evidence`, `municipal_versions`. IDs de instrumentos usam conjuntos de serial/Inmetro por faixa; sem identificador, a chave de conteúdo não representa identidade física comprovada.

Importações são transacionais, somente INSERT/ON CONFLICT DO NOTHING; nenhum DELETE/REPLACE/UPDATE de histórico. Versões divergentes e eventos com mesmo certificado mas resultado diferente são preservados. Índices por município/UF, instrumento/data e instrumento/claim. Arquivo é privado/ignorado pelo Git; não há estado novo no filesystem de Functions da Vercel. Integração ao Neon é uma fase futura, depois da revisão do piloto.

Evidências carregam equipment_id, source_authority/type, claim, effective_from/until, retrieved_at, source_url, raw_reference e confidence. Listing municipal tem início conhecido apenas na data de coleta; não é retroativamente aplicado em 2024. Notícias permanecem referências municipais sem serial resolvido. Aliases são hipóteses LOW, não alterações físicas confirmadas.

## Matching e consulta temporal

Score explicável: município .10, via .30, número/marco .20, alias .10, proximidade numérica .04 (não metros), sentido .15, velocidade .10, tipo .07; proprietário .04, marca/modelo .02 cada apenas se ambos informados. Identificador direto pode elevar para EXACT somente com local compatível e sem conflito. Ausência não ganha pontos. Penalidade de número distante -.15; concorrente dentro de .08 derruba HIGH/EXACT para MEDIUM. Score mínimo .25; abaixo disso UNMATCHED. Scores são heurísticos, não probabilidades calibradas.

HIGH exige via/endereço/sentido/velocidade/tipo compatíveis e candidato único. LOW nunca vira VERIFIED. Números históricos não são substituídos. Sentidos textuais divergentes geram revisão, sem alegar que fisicamente são opostos.

Para validade, usa-se a última data de verificação até a data consultada, com datas-limite inclusivas. Reprovação posterior prevalece sobre aprovação anterior; resultados incompatíveis no mesmo dia geram conflito. Gaps anteriores ao primeiro registro permanecem UNKNOWN. A validade do instrumento (`instrument_valid_at_date`) é separada da validade do ponto municipal (`valid_at_date`), que também exige vínculo EXACT/HIGH e evidência temporal municipal. Consulta não decide validade jurídica de multa.

Uma observação da lista municipal não prova que ela continuou vigente depois da coleta: sem intervalo oficial explícito, a consulta também não projeta o listing para datas posteriores à observação. Notícias de equipamento diferente não se aplicam ao instrumento consultado.
