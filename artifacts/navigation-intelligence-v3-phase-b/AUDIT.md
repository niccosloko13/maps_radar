# Auditoria antes da implementação

Checkpoint: branch `feat/navigation-v3-phase-b`, arquivo privado `private/checkpoint.zip`. O trabalho anterior não foi commitado nem sobrescrito. Baseline: 75 testes JS, 47 Python e selftest aprovados; saídas nos arquivos baseline-*.

## Arquitetura encontrada

- `server.H`: rotas compartilhadas pelo HTTP local e adaptador FastAPI em web_app.py. Autenticação Admin existente por cookie/Authorization, preservada.
- `db`: conexão central SQLite/Postgres com placeholders auditados. Schema Postgres explícito, nenhum DDL ao importar Function. Novas tabelas têm migração separada explícita.
- MapLibre: sources e layers de radares, semáforos, clusters e alertas da rota; nenhuma source de ocorrências oficiais ou de bases policiais na Fase A.
- `/api/map/features` e `/api/map/route-alerts`: inventário legado/comunitário, preservados. Novos dados auxiliares não alteram radar registry.
- `source-contracts.js`: contratos e ícones apenas; não havia coleta/cache/freshness para ARTESP/SIBH/Defesa Civil/PRF/PMRv.
- `road-runtime.js` e `intelligence.js`: progresso, câmera e radar P0. Integração auxiliar usa mesmo AlertManager; não altera processamento GPS.
- Admin: painel de fontes antigo deve continuar funcionando; novo painel separado `Fontes & Operação` para fontes rodoviárias.
- Service worker exclui APIs/Admin e usa assets versionados. Nova release local v225.
- Jobs em produção precisam terminar dentro da requisição; nenhuma thread permanente será criada. Coleta manual Admin/CLI, leitura de cache pelo usuário.

## Evidências externas iniciais

- ARTESP docs 1.0: autenticação Api-Key, 12 req/h por credencial, paginação 100 itens no máximo, inclui status ativa/finalizada e licença CC BY-NC 4.0. Duas chaves ausentes, confirmado pelo usuário.
- SIBH: HTML oficial aponta `https://cth.daee.sp.gov.br/sibh/api/v2/measurements/now?station_type_id=2&show_all=false&serializer=complete&public=true&hours=1`. Endpoint público respondeu 200; `measurements` e `references`, valor acumulado e max_date por estação. Filtrar municípios SP; não inventar cobertura regional a partir de ponto.
- PRF: index oficial contém links relativos; unidades individuais têm título, endereço, rodovia/km e data. Não presume coordenada nem unidade operacional a partir de delegacia.
- Defesa Civil: timeout de rede em duas tentativas, sem endpoint machine-readable validado.
- PMRv: pesquisas localizaram PDF de 2013 e referência a anuário DER 2023; nenhum cadastro atual comprovado. Não importar como atual.
- ARTESP dados abertos: volume de tráfego em praça não é cadastro geográfico nem tarifa vigente. Índice de equipamentos não é cadastro de radares.

Sem alteração de banco pessoal/Neon, auth, Official Radar Finder ou filtro/matcher do Precision Engine.
