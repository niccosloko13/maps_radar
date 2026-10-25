# Variaveis para Vercel e desenvolvimento

Nenhum valor secreto deve ser copiado para Git, comentarios, screenshots ou este documento. Configure os valores no painel **Settings > Environment Variables** da Vercel. Os escopos Preview e Production devem ter credenciais/chaves separadas.

| Nome | Obrigatorio? | Development local | Preview | Production | Descricao |
| --- | --- | --- | --- | --- | --- |
| `DATABASE_BACKEND` | Sim na Vercel | `sqlite` por padrao; `postgres` opcional | `postgres` | `postgres` | Vercel rejeita SQLite explicitamente. |
| `DATABASE_URL` | Para Postgres | Opcional em `.env.local` | URL pooled de branch de preview | URL pooled da branch production | Neon PostgreSQL com TLS. Nunca usar URL de production em testes de escrita. |
| `ADMIN_USERNAME` | Sim na Vercel | `admin` por padrao | Usuario escolhido | Usuario escolhido | Sem usuario padrao em modo hospedado. |
| `ADMIN_PASSWORD_HASH` | Sim na Vercel | Opcional | Hash da senha de preview | Hash da senha de production | Formato `pbkdf2_sha256$600000$SALT$DIGEST`, gerado pela ferramenta abaixo. |
| `SESSION_SECRET` | Sim na Vercel | Gerado em arquivo local quando necessario | Chave aleatoria exclusiva | Chave aleatoria exclusiva | Pelo menos 32 caracteres. Rotacionar invalida todas as sessoes assinadas. |
| `RELAS_ENV` | Opcional | `development` | `preview` fora da Vercel | `production` fora da Vercel | `VERCEL=1` sempre ativa as protecoes, independentemente desta variavel. |
| `NEON_MIGRATION_URL` | Somente para migrar | URL direta em `.env.local` | Nao necessario no runtime | Nao necessario no runtime | Conexao **sem pooler**, usada manualmente pela migracao. |
| `NEON_VALIDATION_URL` | Somente testes | URL da branch isolada | Nao necessario no runtime | Nao configurar | `tools/smoke_neon.py` usa exclusivamente esta variavel. |
| `RELAS_ADMIN_PASSWORD` | Nao; somente local | Senha opcional de desenvolvimento | Ignorada | Ignorada | Nunca serve como fallback em ambiente hospedado. |
| `RADAR_DATA_DIR` | Nao; somente local | Caminho opcional do SQLite/caches | Nao necessario | Nao necessario | Nao aponta a producao para um arquivo persistente. |
| `RADAR_PORT` | Nao; somente local | `8815` por padrao | Nao necessario | Nao necessario | ASGI na Vercel nao abre porta propria. |
| `VERCEL`, `VERCEL_ENV` | Automaticas | Nao definir para SQLite local | Injetadas pela plataforma | Injetadas pela plataforma | Deteccao do ambiente e estado do health check. |

Gere senha/hash e chave no terminal privado, com Python 3.12 e dependencias instaladas:

```powershell
python tools/admin_credentials.py
```

A ferramenta pede a senha sem eco e imprime apenas o hash e uma chave nova. Cole esses valores diretamente no gerenciador de segredos/Vercel. Nao redirecione a saida para arquivo versionado. Nao reutilize credenciais de validacao local.

O `.env.local` privado contem as URLs obtidas pela CLI autenticada. Nao contem credenciais definitivas do Admin. O modo local continua SQLite porque o backend padrao local nao muda em funcao da existencia de uma URL.

Branch de validacao criada nesta tarefa: `relas-vercel-validation`, expira em **2026-10-31 23:59:59 UTC**. Ela serve aos testes desta revisao; um Preview duradouro precisa de branch propria sem essa expiracao. A branch `production` foi migrada e nao expira por essa configuracao.

Depois de configurar as variaveis, um novo deployment precisa recebe-las. Nao basta editar variaveis de um deployment antigo. Confirme que `/api/health` retorna `ok: true`, `engine: postgres` e o ambiente esperado.
