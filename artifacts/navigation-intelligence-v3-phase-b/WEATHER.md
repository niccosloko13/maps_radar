# Chuva e Defesa Civil — estado real

**INCOMPLETE.** SIBH possui coleta real e camada de estações, mas não integração meteorológica regional completa; está STALE no snapshot de encerramento, com último snapshot preservado. Defesa Civil: **BLOCKED_EXTERNAL_ENDPOINT / AVAILABILITY / LICENSE_VALIDATION**. Nenhuma nova tentativa externa foi feita para encerrar.

## SP Águas / SIBH

O HTML público de https://apps.spaguas.sp.gov.br/sibh/ utiliza o endpoint:

`https://cth.daee.sp.gov.br/sibh/api/v2/measurements/now?station_type_id=2&show_all=false&serializer=complete&public=true&hours=1`

Foi encontrado por inspeção do HTML do portal, sem contornar autenticação. GET real retornou 200. Envelope: `measurements` e `references`; a medição contém estação, coordenadas, município/IBGE, `value`, `min_date` e `max_date`.

O adapter filtra municípios com IBGE iniciado por 35, valida números/coordenadas e preserva data de leitura. Cache de coleta de 600s, expiração por leitura após 2h. Sem leitura válida não há observação publicável. Schema inesperado/falha de rede preserva snapshot anterior.

Primeira coleta: 962 recebidas, 958 normalizadas SP. Atualização posterior: 958 recebidas, 954 normalizadas SP; três novas e sete ausentes no snapshot novo foram registradas, sem apagar histórico. Contagens finais detalhadas em DATA_COUNTS.json; inventário histórico e snapshot ativo são medidas diferentes.

Mapa: camada opt-in `rain-stations`, zoom 14+, clusters no afastamento quando habilitada. Detalhe mostra acumulado em 1h, data da leitura, origem e freshness. Teste real dedicado: API/source/render 1/1/1 em São Bernardo do Campo.

Navegação: estações são intersectadas com o corredor e aparecem no resumo de contexto, mas **não geram voz nem são convertidas em “chuva forte na pista”**. Uma estação não comprova cobertura regional. Rota real Praia Grande–São Bernardo teve uma estação relevante ao corredor.

**Não estão implementados um radar meteorológico/overlay regional validado, classificação oficial de chuva forte na pista ou orientação meteorológica equivalente à Defesa Civil. Licença de redistribuição do SIBH ainda precisa confirmação; não publicar como integração completa.**

## Defesa Civil

Portal indicado: https://admin.defesacivil.sp.gov.br/previsaodotempo/sp/alertas . Duas tentativas de acesso expiraram, inclusive pelo browser HTTP. Nenhum endpoint automatizável desse portal foi validado nesta execução.

Status: NOT_CONFIGURED / BROKEN; zero alertas reais ingeridos. Adapter de GeoJSON oficial revisado permite HEAVY_RAIN, STORM, GALE, FLOOD_ALERT e OTHER_WEATHER_ALERT, exige validade e geometria, preserva campos originais e suporta regiões/expiração/corredor. Isso é um contrato preparado, **não uma integração real concluída**. `RELAS_DEFESA_CIVIL_SP_URL` só deve ser preenchida após validar o endpoint, schema e licença.

Testes cobrem validade obrigatória, expiração, fora da rota e renderização regional com fixtures isoladas TEST. Sem dados não se informa “sem chuva” nem “sem alertas”.

## Snapshot de encerramento

Às 04:03:24 UTC de 26/10/2026, SIBH estava STALE: **0 leituras elegíveis**, **954 observações na última coleta**, **961 IDs históricos preservados**. Não houve nova chamada externa para obter READY. O teste real 1/1/1 ocorreu antes da expiração. Isso não informa ausência de chuva.
