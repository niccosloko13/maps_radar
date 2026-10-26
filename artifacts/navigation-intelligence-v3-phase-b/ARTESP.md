# ARTESP CCM — implementação e impedimento real

**BLOCKED_EXTERNAL_API_KEY.** Nenhuma tentativa de forçar autenticação foi feita no encerramento.

Documentação consultada: https://ccm.artesp.sp.gov.br/rodovias/api/docs/ (contrato 1.0.0). Fontes separadas `artesp-occurrences` e `artesp-interventions`.

## Credenciais

`ARTESP_OCCURRENCES_API_KEY` e `ARTESP_INTERVENTIONS_API_KEY` estão ausentes no ambiente de validação. O usuário confirmou que ainda não possui as chaves. `ARTESP_API_KEY` é fallback opcional de backend, somente se a mesma credencial for autorizada para ambos os produtos. Nenhum valor de credencial foi registrado, enviado ao frontend ou adicionado ao Git.

**Conexão autenticada real: NÃO COMPROVADA. Ocorrências/intervenções reais ingeridas: 0/0. Não chamar isso de feed operacional concluído.**

## Fluxo implementado

- GET com Authorization Api-Key somente no backend.
- `filtro_finalizada=1` significa ativa conforme documentação; inclui vítimas, interdições, congestionamentos e atualizações nos nomes aceitos pelo contrato.
- 100 registros por página. Uma chamada por execução; cursor e páginas normalizadas ficam no banco. Somente a última página publica o snapshot. Erro em qualquer página não encerra os eventos do snapshot anterior.
- Contador persistente por hash da credencial e janela de uma hora; gates atômicos SQL, sem lock global de processo no Postgres. Intervalo mínimo 300s, 12 chamadas/hora; a mesma chave compartilha cota entre produtos.
- Chamada manual de teste também consome a cota e não publica dados. HTTP 429 bloqueia novas tentativas; remaining=0 aguarda a janela seguinte.
- Não há polling por usuário. Mapa lê exclusivamente o event store. Sync é uma operação Admin explícita ou CLI.
- Parser diferencia ocorrências, manutenção, obras/sinalização e congestionamentos filhos. Bloqueio total e vítimas graves/fatais sustentam prioridade crítica.
- Geometria fornecida é preservada. Rodovia/km sem coordenada permanecem no inventário; não desenhar linha nem pin presumido.
- Catálogos oficiais de concessionárias, rodovias, municípios e categorias/subclasses têm cache e ação Admin explícita, compartilhando a cota. A primeira página guarda metadados e é identificada como parcial; paginação completa de catálogos permanece uma limitação.
- Headers seguros de quota, Retry-After, licença e termos ficam no Admin. O corpo de erro e o header Authorization nunca são armazenados nos logs.

## Licença

Registrar CC BY-NC 4.0, atribuição ARTESP e versão de termos recebida por header. Acesso depende do aceite da versão de termos e eventualmente allowlist; 403 não deve ser contornado.

## Testes

200, 401, 403, 429, timeout, envelope alterado, versão incompatível, vazio válido, snapshot stale, quota compartilhada, limite horário, paginação, probe e cache de catálogo testados com payloads TEST em SQLite temporário. Fluxo banco/API/mapa/corredor/AlertManager foi testado em servidor TEST isolado; isso não comprova autenticação nem dados reais ARTESP.

## Para ativar

Obter as chaves em Minha Conta no portal oficial, aceitar os termos, configurar exclusivamente no backend, aplicar a migração em ambiente isolado, usar Testar conexão e aguardar a cota antes de Sincronizar. Comparar log/contagem/snapshot e renderização real antes de declarar integração completa. Não há deploy automático nesta entrega.
