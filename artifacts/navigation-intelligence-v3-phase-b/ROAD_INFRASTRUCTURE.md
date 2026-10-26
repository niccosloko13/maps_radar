# Infraestrutura rodoviária

**Estado final:** ANTT validada em ambiente isolado, AGING; PRF **INCOMPLETE_COORDINATES**, AGING; PMRv, pedágios ARTESP e bases/SAU **BLOCKED_EXTERNAL_SOURCE_VALIDATION**. Nenhuma dessas classificações equivale a READY FOR PHYSICAL TEST.

## PRF SP — diretório real

Fonte: https://www.gov.br/prf/pt-br/canais-de-atendimento/unidades-prf/sao-paulo . O adapter reconhece links relativos, consulta até 30 páginas de unidades com espaçamento de 1s e janela total limitada; coleta diária, sem requisição por usuário.

Resultado real: **27 registros: 17 unidades operacionais, 9 delegacias e 1 superintendência**. Há título, endereço, rodovia/km quando fornecidos, URL individual, data da fonte e qualidade `unmapped`. Snapshot completo só publica após todas as páginas responderem e validarem.

Coordenadas comprovadas nessas páginas: **0**. Consequentemente pins PRF reais e alertas PRF reais: **0**. O Admin mostra os 27 registros e ações de revisão/reprocessamento de endereço. Geocoding gera proposta separada; não altera automaticamente o dado oficial nem publica coordenada como oficial. Unidades administrativas têm camada distinta, desativada por padrão.

Datas antigas permanecem visíveis e recebem freshness conservadora por registro. Licença geral do portal exige revisão antes de redistribuição; não presumir atualização de um endereço somente porque foi coletado hoje.

## Pedágios ANTT — cadastro geográfico real

Catálogo: https://dados.antt.gov.br/dataset/praca-de-pedagio . Adapter consulta CKAN `package_show`, seleciona recurso JSON oficial, verifica origem e licença cc-by e normaliza somente UF=SP.

Recurso observado atualizado em **28/07/2026**, catálogo em 29/07/2026. Envelope `praca-de-pedagio`. **277 praças nacionais recebidas; 73 registros SP, 73 ativos, 73 com coordenada**. Identidade determinística por concessionária/nome/rodovia/km/sentido; mesma coleta não duplica IDs.

Fonte independente `antt-tolls`; não rotular como ARTESP. Mapa `toll-plazas`, detalhe, corredor, prioridade P5, sem voz por padrão, painel Pedágios, health e logs. Freshness AGING em razão da idade da fonte. **Nenhuma tarifa foi criada: o arquivo não comprova tarifa vigente.** Teste real em Miracatu: API/source/render 1/1/1 e clique abriu detalhes.

## PM Rodoviária SP

Pesquisas oficiais localizaram material histórico (PDF PMESP de 2013 e menção no anuário DER 2023), não um cadastro atual e georreferenciado comprovado. Não foram importados como postos atuais. Fonte `pmrv-sp`: NOT_CONFIGURED; zero bases reais novas.

Contrato configurável aceita PMRV_COMPANY, PMRV_OPERATIONAL_BASE e PMRV_POST, com mapa/Admin/corredor preparados e testados TEST. Ainda falta adapter validado contra uma fonte atual concreta, comparação de versões e coordenadas. Não é integração completa.

## ARTESP pedágios e bases/SAU/DER/concessionárias

O catálogo ARTESP consultado contém volume de tráfego e acidentes em praças; esses dados não estabelecem, por si, cadastro geográfico ou tarifa. Não converter tráfego histórico em trânsito ao vivo nem equipamento genérico em radar.

Fontes `artesp-tolls` e `official-support`: NOT_CONFIGURED; zero praças ARTESP/bases/SAU novas importadas. Há contrato GeoJSON oficial, classes e camadas distintas, freshness, Admin e testes. Ainda é necessário localizar/validar uma fonte atual legítima, dados e licença. A cobertura ANTT não substitui as praças estaduais ARTESP.
