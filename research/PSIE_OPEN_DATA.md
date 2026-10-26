# PSIE — recurso oficial de medidores de velocidade

Consulta realizada em 25/10/2026. A descoberta foi confirmada no catálogo oficial, não no espelho AmeriGEOSS.

- Catálogo: https://dados.gov.br/dados/conjuntos-dados/portal-de-servicos-do-inmetro-nos-estados-psie
- API usada pela página pública: https://dados.gov.br/api/publico/conjuntos-dados/portal-de-servicos-do-inmetro-nos-estados-psie
- Metadados oficiais: https://servicos.rbmlq.gov.br/dados-abertos/metadados_medidores_velocidade.pdf
- JSON SP: https://servicos.rbmlq.gov.br/dados-abertos/SP/medidores.json
- XML SP: https://servicos.rbmlq.gov.br/dados-abertos/SP/medidores.xml
- Template documentado: `/dados-abertos/{UF}/medidores.json` ou `.xml`. A seleção de UF é no caminho, substituindo `AC` por `SP`; não foi identificado filtro municipal remoto ou paginação. Município é filtrado localmente, sem uma chamada por registro.
- Recurso JSON: `6b7a9e15-940d-44c6-be60-03978faccf0b`; XML: `e140adf5-30c5-40fd-9229-be32ec94d017`.

O catálogo público exige JavaScript; uma chamada direta sem contexto retornou 401. A navegação pública normal retornou os metadados com HTTP 200. Não foram obtidos tokens, resolvidos captchas ou contornadas proteções. O JSON de dados é diretamente acessível via Python com HTTP 200, sem autenticação. Recursos relevantes do catálogo estão em `psie-catalog-resources.json`.

## Coleta comprovada

JSON com 18.142.779 bytes, SHA-256 `ac5cbc140a5c16738f01e0f18da5ef484709a1683bee503d4841f90d52b93e90`. `Last-Modified: Thu, 01 Oct 2026 00:59:26 GMT`; ETag preservada no manifesto. Timestamps exatos da coleta em `artifacts/official-radar-finder-v1/summary.json`. A data do download não é a data da última verificação nem transforma o arquivo mensal em consulta ao vivo.

9444 registros SP; 9435 chaves normalizadas de identidade, incluindo uma sem serial/Inmetro; nove chaves aparecem em mais de um registro, preservados como versões. Não interpretar essa deduplicação técnica como censo exato de equipamentos físicos. Praia Grande: 15 registros, 15 grupos identificados, dez com histórico aprovado cobrindo 25/10/2026 no snapshot disponível e cinco mais antigos sem cobertura vigente.

## Schema observado

Raiz JSON: array. Campos observados: `SiglaUf`, `Estado`, `Municipio`, `LocalVerificacao`, `DataUltimaVerificacao`, `DataValidade`, `UltimoResultado`, `TipoMedidor`; arrays `Faixas` e `Historico`; objeto `Proprietario`. Descrição completa em `artifacts/official-radar-finder-v1/SOURCE_SCHEMA.md`.

Exemplo real, com vínculo municipal ainda pendente: local PSIE Ayrton Senna oposto 328, Inmetro `15801145`, série `1396`, verificação `25/02/2026`, validade `24/02/2027`, resultado `Aprovado`. A lista municipal usa 382. Não se equiparam automaticamente esses números.

Todos os registros de Praia Grande apresentam `VelocidadeNominal="0"`; o normalizador preserva o bruto e retorna velocidade nominal desconhecida. Marca/modelo/portaria de aprovação não constam nesses registros. Histórico inclui reprovações, reparos e certificados vazios; nada disso é descartado.

## Frequência e licença

O PDF oficial informa atualização mensal. O Plano de Dados Abertos do Inmetro 2024–2026 também indica periodicidade mensal: https://www.gov.br/inmetro/pt-br/acesso-a-informacao/dados-abertos/plano-de-dados-abertos-2024-2026.pdf/@@download/file . O catálogo apresenta `license_id=cc-zero` / Creative Commons CCZero; o PDF usa a descrição genérica Creative Commons. A interface do catálogo mostra “Atualização não verificável”; não se assumiu garantia de atualização diária.

O portal público de validação manual é https://psie.inmetro.gov.br/Instrumento . O aviso de mudança do portal de consultas não invalida o endpoint legado de dados abertos, que respondeu 200 neste teste. Não foi automatizada a consulta protegida.

## Limitações

O JSON foi efetivamente baixado/importado. O XML é alternativa indicada pelos metadados; seu parser foi testado com fixture, não foi necessário baixar todo o XML SP. O dataset não fornece prova municipal de ativação para cada serial, geometrias oficiais ou todas as informações desejadas. Ausência de registro, lacuna temporal ou certificado vencido no snapshot não demonstra irregularidade de uma multa.
