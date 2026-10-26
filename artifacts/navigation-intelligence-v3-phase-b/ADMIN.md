# Fontes & Operação

Nova seção separada do painel legado. Login, cookies e autorização existentes foram reutilizados, sem alteração de autenticação.

Subseções: Visão Geral, ARTESP, SP Águas, Defesa Civil, PRF, PM Rodoviária, Pedágios (ANTT e ARTESP separados), Bases/Apoio, Eventos, Logs e Layer Diagnostics.

## Operação

Cada fonte exibe status, freshness, credencial configurada SIM/NÃO, endpoint, licença/termos, intervalo/cota, último fetch/sucesso/data da fonte, erro, contagem, versão de contrato/adapter, hash e validação do schema. Ações: sincronizar, testar conexão, habilitar/desabilitar, ver normalizados e logs. Testar/sincronizar compartilham gate e cota persistentes. Ausência de chave não simula sucesso.

ARTESP tem catálogos oficiais em cache e atualização explícita, com aviso de consumo de cota e paginação parcial. Catálogos e datasets não são buscados pelo mapa do usuário.

Inventário de infraestrutura mostra tipo, nome, rodovia/km, município, qualidade da coordenada, atualização, status e freshness. Reprocessar endereço gera proposta em tabela separada e mantém REVIEW; não publica nem substitui dado oficial. Sem endereço oficial não geocodifica apenas rodovia/km. Marcar revisão não apaga registro.

Eventos têm filtros fonte/tipo/rodovia/município/gravidade/status/data. Há mapa de diagnóstico incorporado e ação para abrir uma infraestrutura coordenada no mapa. Não há edição de alerta oficial. Logs mostram contagens criadas/atualizadas/encerradas/duplicadas e duração, sem segredo.

Layer Diagnostics cruza contagens do banco com diagnósticos explícitos de navegador. “Registrar diagnóstico do mapa” grava somente contagens agregadas, sem rota, coordenadas ou identificador de usuário. Ausência de relatório de navegador é desconhecido, nunca “rendered=active”.

## Testes

Autorização 401 sem sessão, acesso autenticado às novas APIs, desabilitação e gravação de diagnóstico foram testados no ASGI usando banco temporário. Browser testou login local isolado, abertura das subseções, AUTH_REQUIRED ARTESP, HEALTHY/FRESH SIBH/PRF, AGING ANTT, fontes não configuradas, logs, eventos e diagnóstico. Capturas nesta pasta.

## Limitações administrativas

O mapa incorporado é o mapa público real do mesmo ambiente; não é editor geográfico. Não há aprovação automática de proposta de geocoding. Conflitos multifonte são candidatos para revisão, não fusão automática. Paginação completa de catálogos ARTESP e filtros avançados/paginação de grandes tabelas ainda precisam evolução. O inventário administrativo retorna no máximo 1.500 registros por consulta.


## Encerramento

Nove fontes no painel, seis sem operação. Snapshot final: ANTT/PRF AGING; SIBH STALE, sem leituras não expiradas. Dados em source-health-final.json. Seleção de praça ANTT real no mapa do Admin aprovada (browser-admin-map.json e admin-selected-real-toll.png). Autenticação preservada. Estado geral INCOMPLETE/BLOCKED; sem push/deploy.
