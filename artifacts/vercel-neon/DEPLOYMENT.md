# Operacao Vercel / Neon

## Preparacao realizada

Python 3.12, `server:app` FastAPI, dependencias fixadas em `uv.lock` e `requirements.txt`, schema `001-vercel-neon`, dados migrados em production e SQLite preservado. Sem servidor HTTP manual no import e sem preload/migration por cold start. O frontend continua HTML/CSS/JS, sem build Next.js ou `npm run build`.

## Validacao conectada a Vercel (pendente de login)

A CLI 65.2.0 respondeu `Logged out` e o build respondeu `The specified token is not valid`. Nao foi aberto login automaticamente. No terminal do projeto:

```powershell
npx vercel login
npx vercel link
```

Selecione **o projeto Vercel existente conectado ao GitHub**, sem criar outro projeto. Configure as cinco variaveis obrigatorias da tabela de ambiente. Confirme Framework Preset FastAPI, Root Directory na raiz deste repositorio, Python 3.12, sem override antigo de `npm run build`, Start Command ou diretorio de saida de um framework Node.

Depois:

```powershell
npx vercel pull --yes --environment=preview
npx vercel build
```

Inspecione o output: entrypoint `server.py`, ASGI `app`, Python 3.12, assets `app/` presentes e nenhum SQLite/secret/artifact privado no bundle. A configuracao possui somente limite de 120 segundos e exclusoes do bundle; nao ha rewrites de API ou alteracao de dominios.

Somente depois do build e com **DATABASE_URL de preview isolado**, um Preview pode ser executado:

```powershell
npx vercel deploy
```

Nao usar `--prod` nesta etapa. Testar nesse URL `/`, `/admin`, assets, `/api/health`, login, `/api/admin/database-status`, mapa, bbox, cadastro controlado e reinicio/cold start. A revisao local nao substitui esse teste no runtime Linux da Vercel.

## Desenvolvimento Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe selftest.py
.\.venv\Scripts\python.exe server.py
```

`start.bat` e `start.ps1` continuam chamando Python local. Instale as dependencias no Python escolhido por esses launchers ou ative a `.venv` antes de usa-los. O modo stdlib/LAN e TLS local continuam disponiveis. Alternativa ASGI: `python -m uvicorn server:app --host 0.0.0.0 --port 8815`. Inicialize o SQLite local com `python server.py` antes do primeiro uso ASGI local; a aplicacao ASGI nao inicializa/alterara banco ao importar.

## Migracao explicita e repetivel

```powershell
python tools/migrate_sqlite_to_neon.py --sqlite "$env:LOCALAPPDATA/RadarSP/data/radar.db"
python tools/migrate_sqlite_to_neon.py --sqlite "$env:LOCALAPPDATA/RadarSP/data/radar.db" --apply
```

O primeiro comando so gera plano. O segundo cria backup consistente incluindo WAL, aplica schema e importa na mesma transacao. Usa `NEON_MIGRATION_URL` direto. Preserva IDs e compara todos os campos; conflito com destino interrompe e reverte, sem substituir dados. O destino pode conter novos registros, mas cada registro da origem precisa estar identico. Nunca use o migrador para sobrescrever mudancas posteriores feitas no Neon.

Importacoes grandes, incluindo uma nova base comunitaria inteira ou preload estadual, devem rodar como ferramenta explicita fora da Function, apontando para PostgreSQL. O comando existente `python import_community.py` utiliza `DATABASE_BACKEND=postgres` e `DATABASE_URL`; execute em modo local/development para nao depender do prazo de um request hospedado. Confira o lote e o resultado antes de publicar.

## Jobs

Admin usa POST autenticado, jobs persistidos em `runtime_jobs`, operacao dentro da requisicao e prazo cooperativo de 45 segundos. Consultas limitadas a 25 segundos, conexoes a 10 segundos; configuracao de timeout e local a transacao, compativel com o pooler Neon. O limite da Function e 120 segundos para permitir registrar falhas e finalizar a resposta. Nao existe thread hospedada apos a resposta.

Lotes de cidades e decisoes sao enviados um por vez pelo Admin. Uma importacao comunitaria que ja existe e um replay sem duplicacao. Operacoes grandes podem terminar como falha/prazo esgotado; nenhum estado `queued` implica que exista worker externo executando. `GET /api/admin/jobs` lista jobs hospedados. Operacoes longas precisam CLI ou futuro workflow/fila; nao ha Cron/Queues/Daemon provisionado.

## Rollback

No Windows, remover `RELAS_ENV` hospedado e configurar `DATABASE_BACKEND=sqlite` volta a usar o SQLite original; nao substitua esse arquivo por backups automaticamente. O migrador nunca o removeu. A URL Neon pode continuar guardada em `.env.local` sem ser utilizada em modo SQLite.

Na Vercel, SQLite **nao** e rollback aceitavel. Reverta o deployment para uma versao ASGI/PostgreSQL conhecida e preserve o Neon. Antes de reverter schema/dados, exporte o estado atual e considere o restore/branch do Neon; esta tarefa nao executa DROP, reset ou restaura dados automaticamente. Novas escritas no Neon nao aparecem retroativamente no SQLite local. Uma volta operacional definitiva exige reconciliar essas novas escritas.

## Referencias verificadas

- [Runtime Python Vercel](https://vercel.com/docs/functions/runtimes/python)
- [FastAPI na Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- [Neon: erros de conexao e parametros do pooler](https://neon.com/docs/connect/connection-errors)
- [Psycopg3: transacoes](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)
