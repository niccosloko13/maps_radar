# Relas 2.1.5 ? revis?o para teste de rua

## Rodar
- Windows: `start.bat`
- App: http://127.0.0.1:8815
- Admin: http://127.0.0.1:8815/admin
- Admin: usuário `admin`; senha em `RELAS_ADMIN_PASSWORD` ou no arquivo local `%LOCALAPPDATA%\RadarSP\data\admin_password.txt` (gerado na primeira execução, nunca versionado).

## Fluxo operacional
1. **Varredura**: descobre fontes/candidatos em até 5 cidades. Não publica.
2. **Atualizar cidade**: inspeção direcionada de uma cidade (radares, semáforos/objetos ou completo). Não publica.
3. **Alimentar base**: única porta de publicação automática. Cada proposta recebe SIM/NÃO.
4. **Inventário**: mostra o que já está salvo.
5. **Logs**: acompanha todas as consultas, erros, descobertas e aplicações.

## Mapa
Camadas independentes:
- Radar — ícone de câmera
- Radar semafórico — câmera/semafórico
- Lombada eletrônica — ícone de lombada
- Radar rodoviário — câmera rodoviária
- Semáforo — ícone de sinal
- Lombada física — ícone próprio

Semáforos e lombadas comunitários só aparecem depois de uma descoberta e aprovação no Admin.

## Persistência
O banco fica em `%LOCALAPPDATA%\\RadarSP\\data` no Windows para sobreviver a upgrades de versão.

## Observação
MapLibre é cacheado localmente quando disponível. Se a biblioteca não estiver no cache na primeira execução, o loader usa fallback CDN. Tiles/rota/geocoding do protótipo ainda dependem de serviços externos.

## v1.8.2 — correções de cobertura
- Corrigido `CITY_BATCH_LOCK` ausente.
- Overpass agora usa POST + múltiplos endpoints de fallback.
- São Paulo capital: descoberta/importação de semáforos via WFS oficial GeoSampa.
- Santos: descoberta/importação de semáforos via WFS oficial SIGSantos/GeoServer.
- Varredura oficial usa WFS `resultType=hits` para mostrar contagem antes da aprovação.
- OSM permanece complementar, não substitui fonte oficial.


## v1.8.2 — lote ChatGPT/OpenAI
- Executa uma vez, em segundo plano, uma alimentação de semáforos para os 9 municípios da Baixada Santista + São Bernardo do Campo.
- Tudo inserido pelo lote recebe `ingested_by = ChatGPT/OpenAI`, `ingestion_batch` e `provenance_note`.
- Santos tenta SIGSantos/WFS oficial; São Vicente e Itanhaém recebem também cruzamentos publicados oficialmente; demais cidades usam OSM como complemento, marcado como comunitário.
- O lote usa limite administrativo OSM quando possível para evitar misturar cidades vizinhas.
- Pode ser reexecutado pelo Admin > Alimentar base.

## Mapa Relas: base comunitária de SP

O mapa usa camadas MapLibre com clustering, ícones SVG próprios, consultas por viewport, temas claro/escuro/automático e navegação com voz opcional. O banco permanece em `%LOCALAPPDATA%\RadarSP\data\radar.db` (ou `RADAR_DATA_DIR`).

Para importar o TXT detectado na raiz:

```powershell
python import_community.py
```

A importação também está no Admin > Base comunitária SP. O arquivo precisa ter o cabeçalho exato `X,Y,TYPE,SPEED,DirType,Direction`. Os polígonos e nomes dos 645 municípios do IBGE estão em `data/sp-municipalities.geojson` e `data/sp-municipality-names.json`; o importador não chama APIs por registro. Um hash identifica o lote e impede reimportação acidental.

`map_points` guarda a fonte complementar; `radars` e `road_objects` continuam sendo o inventário existente. Aprovar um ponto comunitário permite sua exibição sem transformá-lo em oficial. Ocultar é reversível. Confirmações públicas entram em `map_feedback` para revisão. Relatos recentes expiram em duas horas.

Convenção do TXT: `DirType=0` direção desconhecida/todos os sentidos, `1` sentido cadastrado e `2` dois sentidos. O azimute é interpretado como sentido de deslocamento; essa convenção precisa ser confirmada pelo fornecedor da base. A tolerância padrão é 55°, configurável na consulta de alertas da rota. O corredor da rota tem 35 m e pode ainda incluir vias muito próximas ou em níveis diferentes.

Endpoints novos:

- `GET /api/map/features?bbox=west,south,east,north&types=fixed,bump&zoom=14`
- `POST /api/map/route-alerts` com `coordinates` e `tolerance`
- `POST /api/map/report` com `kind`, `longitude`, `latitude`
- `POST /api/map/feedback` com `id`, `action`
- `GET /api/admin/community` e `/api/admin/community/export` (autenticados)
- `POST /api/admin/community/import` e `/api/admin/community/bulk` (autenticados)

Validação: `python selftest.py`, `python -m unittest test_community -v` e o relatório em `artifacts/road-test-review/REPORT.md`. Tiles, geocoding e cálculo de rota continuam dependendo de serviços externos; GPS móvel requer contexto seguro HTTPS. O relatório distingue testes de navegador e testes físicos pendentes.

## Teste de rua — 2.1.5

Python 3.10+ e acesso à internet para mapa-base, busca e cálculo de rota. Backend e importador usam a biblioteca padrão; não é necessário instalar dependências Python.

```powershell
python selftest.py
python server.py
```

Abra o endereço com versão informado no terminal, por exemplo `http://127.0.0.1:8815/?v=215`. Ele evita reutilizar o HTML que uma versão antiga deixou no cache HTTP. O shell atual registra service worker, atualiza HTML/bootstrap pela rede e usa assets com versão; APIs e autenticação não entram no cache.

Na primeira inicialização de um banco limpo, são carregados o snapshot público de cruzamentos do GeoSampa e o TXT comunitário de SP. As coordenadas públicas do snapshot estão em `data/geosampa_signals_snapshot.json`, com fonte e data; não há banco pessoal no repositório. Repetir a inicialização não multiplica os pontos nem substitui registros oficiais existentes. O snapshot possui 6.419 observações, que correspondem a 6.367 coordenadas únicas na precisão usada pela carga inicial. Bancos anteriores conservam seus registros.

### Acesso pelo celular e GPS

No telefone, use **HTTPS com certificado confiável para o endereço acessado** e permita localização precisa. O HTTP pelo IP da rede local permite explorar o mapa, mas o navegador bloqueia o GPS; o app informa esse motivo. O HTTPS pode ser servido por um proxy ou pelo próprio backend:

```powershell
$env:RELAS_TLS_CERT = 'C:\certificados\relas.crt'
$env:RELAS_TLS_KEY = 'C:\certificados\relas.key'
python server.py
```

O certificado precisa corresponder ao host/IP e ser confiável no telefone. Chaves e certificados privados não devem entrar no Git. `RADAR_PORT` altera a porta; `RADAR_DATA_DIR` permite usar um banco isolado. O teste TLS automatizado desta revisão validou cadeia e hostname com uma CA de teste, sem desativar verificação de certificado. Ele não instala confiança no seu celular.

O mapa pede localização ao abrir e acompanha também caminhadas fora de rota. Arrastar suspende o acompanhamento; **Recentralizar** o retoma. A seta representa movimento com heading conhecido e o ponto representa parada/heading desconhecido. GPS impreciso, negado, antigo ou indisponível ganha indicação explícita. A prévia de rota pausa o watch real para não disputar a câmera.

### Administração

Usuário `admin`. Defina `RELAS_ADMIN_PASSWORD` antes de iniciar ou use a senha aleatória gerada no arquivo privado `%LOCALAPPDATA%\RadarSP\data\admin_password.txt`. Com `RADAR_DATA_DIR`, o arquivo fica nesse diretório. A senha demonstrativa anterior foi removida do código e do formulário. As bases e operações administrativas foram preservadas.

### Repetir a validação

```powershell
python scripts/road_audit.py
node --test tests/navigation.test.cjs
```

Para os smokes de navegador, com o servidor iniciado:

```powershell
npm install --no-save --package-lock=false playwright
npx playwright install chromium
node scripts/run-road-browser.cjs
```

Essas dependências são opcionais para testes; `node_modules` não é versionado. Os smokes usam coordenadas GPS simuladas e interceptam o envio de incidente para não gerar relatos falsos no banco real. A gravação do backend é verificada em bancos temporários.

Relatório inicial: [INITIAL_AUDIT.md](artifacts/road-test-review/INITIAL_AUDIT.md). Relatório final, screenshots e medições: [REPORT.md](artifacts/road-test-review/REPORT.md).

Limites do teste: houve validação Chromium com os viewports solicitados e GPS simulado; sensores físicos, Safari/iOS, suspensão em segundo plano e conectividade de rua devem ser observados no primeiro teste controlado. O corredor é geométrico (35 m), sem correspondência topológica garantida em viadutos ou vias paralelas muito próximas. A convenção `DirType` adotada é 0 desconhecido/todos, 1 sentido cadastrado, 2 dois sentidos; os campos originais ficam preservados. A velocidade do radar não é tratada como prova do limite atual da via.
