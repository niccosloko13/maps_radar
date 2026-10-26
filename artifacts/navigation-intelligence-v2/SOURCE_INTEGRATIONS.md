# Fontes e fases — estado real

Esta entrega implementa a Fase A explicitamente marcada AGORA no documento de missão. B/C/D não foram silenciosamente consideradas prontas.

| Fonte/recurso | Estado |
| --- | --- |
| Registry atual e /api/map/features | Preservados; provenance sem alteração. route-alerts passa segmento e bearing. |
| Official Radar Finder | Piloto anterior preservado e isolado; contrato visual aceita verificação por data apenas quando houver vínculo aprovado. Zero importações/promovações automáticas. |
| Photon structured + full-text | ATIVO na busca. /structured para consulta enviada, /api para sugestões/fallback; ranking por número exato/cidade/proximidade. |
| ViaCEP | ATIVO somente para CEP completo enviado: confere endereço/cidade antes da geocodificação. Não fornece coordenada oficial. |
| Nominatim público | Retirado do autocomplete; demais importadores existentes fora do escopo. Não foi introduzida pesquisa incremental contra esse serviço. |
| Valhalla/OSRM | Fluxo existente preservado; metadados e instrução integral em PT-BR normalizados. Rota real de teste 54.350m trouxe SP-150/BR-050. |
| Pedágios | Pontos atuais preservados. Sem preço novo, tarifa estimada ou cadastro oficial de praça inventado. |
| Acidente/obra/comunidade | Fluxo existente; animal/interdição acrescentados como comunidade, TTL do reporte existente. Nove opções rodoviárias em ROAD_MODE e quinze em cidade. |
| PRF/PM/bases DER/concessionária/SAU/balanças | Contratos e ícones preparados; NENHUM cadastro novo importado. Fase B. |
| ARTESP CCM / DER eventos | Fontes candidatas, sem conector ao vivo implementado. Não se raspou Waze nem se assumiu licença de dados derivados. Fases B/C. |
| SP Águas / Defesa Civil | Portais oficiais localizados; SEM feed conectado ou alerta meteorológico inventado. Fase B, com interseção por corredor antes de ativar. |
| HERE Traffic | Sem chave, assinatura ou chamada paga. Avaliação de licença/custo permanece futura. |
| Presença/avatares anônimos | Não implementados: Fase D. Nenhuma transmissão de posição de usuário ou histórico público foi acrescentada. |

## Pesquisa primária

- Photon /structured, /api e campos: https://github.com/komoot/photon/blob/master/docs/api-v1.md . O servidor público recusou lang=pt com HTTP 400 e declarou default/de/en/fr; usar default mantém nomes brasileiros. Sem essa correção a antiga primeira fonte de busca falhava sistematicamente.
- ViaCEP: https://viacep.com.br/ . CEP tem oito dígitos e erro explícito; origem postal não é prova metrológica.
- Nominatim: https://operations.osmfoundation.org/policies/nominatim/ . O serviço público proíbe autocomplete e limita o total da aplicação; nenhum novo autocomplete Nominatim foi criado.
- Valhalla: https://valhalla.github.io/valhalla/api/route/api-reference/ . A classe e o ref só são usados quando realmente fornecidos; não fabricados a partir da velocidade.
- PRF: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/ ; catálogo ANTT candidato: https://dados.antt.gov.br/pt_BR/dataset/prf . Descoberta de catálogo não equivale a validação de todos os postos.
- ARTESP CCM: https://ccm.artesp.sp.gov.br/ ; catálogo: https://dadosabertos.artesp.sp.gov.br/ . Já constavam no inventário do projeto, sem feed de trânsito validado nesta fase.
- SP Águas/SIBH: https://apps.spaguas.sp.gov.br/sibh/ . Chuva Agora é apresentado pelo portal oficial, mas endpoint/licença/freshness de ingestão ainda precisam validação.
- Defesa Civil: https://admin.defesacivil.sp.gov.br/previsaodotempo/sp/alertas . Ainda sem adapter de regiões/expiração no Relas.

## Contratos preparados

Categorias estáticas e road_event estão em source-contracts.js, incluindo source/type, updated_at, source_updated_at, retrieved_at, expires_at/valid_until e geometry. Eventos vencidos são rejeitados; base estática não recebe TTL de ocorrência temporária. Comunidade não estabelece uma base oficial e não ganha OFFICIAL_VERIFIED.

Fase B deverá implementar Route Event Corridor (janela 5km atrás/até 50km à frente, lateral por tipo), fontes oficiais verificadas, interseção meteorológica, cache e dedupe multievidência. Isso NÃO está ativo agora. Não chamar “trânsito livre” ou “sem chuva” a ausência de fonte.

Busca e roteamento continuam fazendo requisições necessárias aos respectivos provedores. Telemetria é outra coisa: opcional, em RAM, sem upload; exportação explícita em JSON privado.
