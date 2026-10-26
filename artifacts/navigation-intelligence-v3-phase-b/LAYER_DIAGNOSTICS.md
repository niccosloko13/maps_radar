# Diagnóstico de camada

Não inferir renderização pela existência de uma linha no banco.

- `received`: registros da resposta upstream, nos logs por coleta. No cliente significa features devolvidas ao viewport; são medidas explicitamente distintas.
- `normalized`: registros normalizados no lote; no diagnóstico agrupado do banco, inventário armazenado por fonte/tipo.
- `active`: status ativo e não expirado no momento da consulta.
- `eligible_map`: ativo com geometria, antes dos filtros/preset/zoom do usuário.
- `eligible_route`: interseção geométrica e direção compatível no corredor da requisição; depois filtros do usuário/freshness podem reduzir.
- `rendered`: queryRenderedFeatures do navegador, deduplicado por event_id. Clusters não são arbitrariamente contados como todos os símbolos individuais.
- `alerted`: card auxiliar selecionado naquele diagnóstico; não é histórico de todos os avisos emitidos.

GET `/api/admin/layer-diagnostics`: saúde, contagens agrupadas, logs recentes, candidatos multifonte e relatórios de clientes. Registro de cliente é opcional e Admin protegido: POST `/api/road-events/diagnostics`. Aceita apenas contagens limitadas, gerais/por fonte conhecida. Não aceita rota/localização como dado persistente. TTL dos diagnósticos de cliente: 24h.

Client runtime: `relas.phaseB.diagnostics()`. Admin possui captura explícita do mapa incorporado. Sem cliente reportado, rendered/alerted permanecem desconhecidos.

## Evidência

`browser-live-map.json`: ANTT 1/1/1, estação SIBH 1/1/1. `browser-phase-b.json`: cada um dos onze tipos TEST renderizado/clicado, cluster 11 e quatro viewports. `browser-e2e-TEST.json`: banco/API/mapa/corredor/AlertManager com fixtures claramente isoladas. `DATA_COUNTS.json`: contagens reais do banco isolado, sem fixtures. `postgres-tests.json`: nenhuma alteração de contagem em tabela legada da branch Neon.

Erros encontrados e corrigidos: links PRF relativos; script embutido contaminando nome PRF; handler novo sobrescrito pelo bind assíncrono do Admin; fonte de cluster inexistente no provedor; corrida entre rota e instalação assíncrona das sources do mapa; precisão float4 inadequada para epoch no Postgres. O teste de service worker inicialmente falhou porque o contexto o bloqueava; repetido com worker habilitado e passou. Uma verificação repetida de contagens Neon incluiu tabelas novas de histórico do próprio teste; foi corrigida para comparar explicitamente somente tabelas legadas, mantendo os resultados do CRUD separado.


## Fechamento e falhas anteriores

A repetição de browser interrompida não foi usada como nova evidência. Falhas iniciais do chevron foram registradas; instalação das camadas auxiliares passou a aguardar o core e os testes posteriores aprovaram o chevron. Isso não substitui medição em aparelho físico. Tematização preserva as cores das novas sources; validade é normalizada em UTC. Falhas mantêm snapshot e freshness STALE. Fontes desabilitadas permanecem no inventário, mas saem da elegibilidade de mapa/rota; testes finais aprovados.

A única rodada Python de fechamento aprovou 71 testes. Não houve novas tentativas externas. PRIVACY_CHECK.json registra zero correspondências de segredos reais em 199 arquivos publicáveis, zero fixtures no banco de coletas reais e onze em banco TEST separado. Servidores locais encerrados e credencial temporária removida, preservando código e dados válidos.
