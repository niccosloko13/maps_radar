# Limitações conhecidas

- Obras: fonte disponível é a contribuição pública existente, temporária. Não há conector de obras oficiais ativo. Nenhum evento foi inventado; zero obras/acidentes ativos na auditoria. As fixtures das screenshots são explicitamente locais e não foram gravadas.
- Chuva: sem feed confiável integrado. UI, source/layers poligonais, toggle e adaptador estão preparados, mas não há cobertura meteorológica real de SP. “Fonte ainda não conectada” é estado indisponível, não ausência de chuva.
- Integração futura: `relas.weather.setData(FeatureCollection, {source,updatedAt,expiresAt})`. Rejeita datas inválidas/vencidas, mais de 500 regiões e polígonos abertos/fora do bbox SP. O fornecedor deve recortar aos limites reais de SP (bbox não é máscara estadual). Depois ligar a camada. Alerta contextual desta fase informa regiões fornecidas; não calcula interseção meteorológica com rota. Expiração limpa geometria em até um minuto.
- Clusters não são inventário estadual: representam pontos retornados para o viewport. Contagem do painel usa o catálogo do bbox, inclusive categorias desligadas. O teto atual do endpoint é 25 mil; auditoria estadual retornou 14769.
- Ícones de segurança próximos deixam de desaparecer por colisão, mas podem sobrepor em cruzamentos muito densos. Semáforos no zoom 13 ainda usam seleção por colisão; 14+ permite todos.
- Provedor externo do mapa falhou uma vez no teste do fallback; o teste isolado usa um estilo mínimo para não confundir falha do provedor com falha do motor. A aplicação mantém mensagem de erro/retry.
- Um primeiro benchmark visual produziu 2 FPS não reproduzíveis; repetição com página em foreground resultou em 145 FPS/p95 7.1ms. Hardware desktop, não celular real. Não é garantia de FPS em aparelhos móveis.
- Precision V2 continua opt-in; não foi modificado. Esta entrega não substitui calibração real nem teste de rua.
