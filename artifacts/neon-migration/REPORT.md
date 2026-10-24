# Relas — Neon PostgreSQL: estado da preparação

## Situação atual

**Aguardando autenticação Neon. PostgreSQL ainda não está pronto nem foi ativado.**

A auditoria prévia foi concluída em [AUDIT.md](AUDIT.md), com [schema SQLite](schema-sqlite.sql) e [inspeção de tabelas/índices/chamadas SQL](sqlite-inspection.json). O SQLite foi inspecionado em modo somente leitura. Nenhum runtime, tabela ou registro foi alterado nesta etapa.

## Arquitetura e dados auditados

Python síncrono, servidor HTTP com threads, SQLite/WAL, frontend estático MapLibre e Admin. Sem Next.js e sem build npm de frontend. São 24 tabelas e 8 índices explícitos; a base inclui 196 radares, 6.426 objetos viários, 8.259 pontos comunitários e 224 registros no histórico de radares. Demais contagens, constraints, imports, endpoints e locks estão no AUDIT.

Recomendação técnica inicial: psycopg3 síncrono numa camada central `db.py`, sem ORM pesado. SQLite deve continuar como backend padrão e ser selecionado explicitamente; a existência de DATABASE_URL não deve disparar troca ou migração. Ainda não foi instalado driver Python.

## Comandos e problemas encontrados

1. `npm i -g neon@latest`: sucesso; CLI instalada globalmente.
2. `neon init -y --org-id org-weathered-leaf-68637248 --project-id shy-art-03849128 --branch production --services postgres`: interrompido no setup opcional de agentes. O computador tem Node 22.14.0 e a instalação de skills exige 22.20.0+.
3. Runtime temporário por `npx --yes --package=node@22.20.0 --package=neon@latest -c "node --version"`: confirmou 22.20.0, sem substituir o Node global.
4. Repetição do init nesse runtime: etapa opcional de plugins retornou `plugins CLI failed` antes do vínculo de projeto.
5. `neon init --help`: confirmou `--no-agent-setup` para dispensar instalação de agentes e configurar somente os serviços solicitados.
6. `neon profile list -o json`: perfil DEFAULT sem conta/autenticação e armazenamento ausente. Não há DATABASE_URL, DATABASE_URL_UNPOOLED ou NEON_API_KEY no ambiente, nem `.env`, `.env.local`, `.neon` ou `neon.ts` no projeto no momento da verificação. Nenhum valor de credencial foi registrado.

A primeira tentativa disponibilizou o plugin Neon em escopo de usuário. As skills `neon` e `neon-postgres` foram consultadas. Sua recomendação para migrações é conexão direta e teste isolado antes de aplicar alterações em production. O usuário já escolheu organização, projeto e branch; não se deve criar outro projeto/claimable como atalho para falta de login.

O próximo init usará os mesmos IDs e serviços, com `--no-agent-setup`, para evitar repetir o setup opcional que falhou. Se faltar autenticação, a execução deverá parar e solicitar `neon login`, conforme pedido do usuário.

## Não executado ainda

- Vínculo concluído com a branch production e `neon deploy`.
- Conexão ao Postgres ou inspeção do destino.
- Criação de schema PostgreSQL, `db.py` e `.env.example`.
- Instalação do psycopg3 e script de migração.
- Backup anterior à cópia, migração de registros e comparação SQLite x PostgreSQL.
- Testes CRUD/rollback/upsert, importadores, Admin e HTTP em Postgres.
- Reinicialização com prova de persistência no Neon.

Nenhum desses itens é declarado concluído apenas pela instalação da CLI. O relatório será atualizado após autenticar e executar as etapas restantes.

## Preservação e retorno ao SQLite

O projeto continua usando exatamente o SQLite anterior, no diretório persistente configurado. Não há mudança de backend para desfazer, nenhum banco removido e nenhum preload apagado. A futura implementação manterá `DATABASE_BACKEND=sqlite` como retorno explícito. Não será usada troca silenciosa de backend em caso de falha do Postgres.

## Próxima ação do usuário

Executar `neon login` no PowerShell e concluir a autenticação no navegador, se a CLI informar falta de sessão. Não enviar senha, token ou connection string pelo chat. Depois disso será possível continuar o init/deploy, camada compatível, migração com backup e validação completa.
