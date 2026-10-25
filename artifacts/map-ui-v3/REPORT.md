# Relas Map UI V3

## Entrega

Tema claro por padrão, respeitando escolha persistida; modo escuro/automático preservado. Mapa ocupa toda tela, topo compacto, busca principal, controles SVG, ações de polegar e HUD de direção branco. Hero/slogans retirados. Painel de camadas com switches, contagem regional, mostrar todas/ocultar pontos, comunidade e chuva. Ícones próprios refeitos. Fontes, banco, autenticação, backend e módulos de Precision V2 preservados.

Checkpoint `f23e22aa8a1bbdabfc1b9146701839dd0169755f`; branch `feat/map-ui-v3`. Nenhuma migração de dados. Shell/cache v222.

## Arquivos

- `app/index.html`, `app/app.js`, `app/boot.js`, `app/sw.js`: composição, integração, source/render, versionamento e estado de erro amigável.
- `app/ui/map-ui.js`, `map-ui.css`, `weather-layer.js`: design, ícones de controles, normalização visual, filtros e contrato meteorológico.
- `app/icons/*.svg`: família de eventos, incluindo obras/acidentes/chuva/veículo parado/congestionamento.
- `tests/map-ui.test.cjs`, `scripts/map-ui-v3-smoke.js`: normalização e regressão das novas camadas.
- Scripts de browser anteriores e `selftest.py`: versão e seletores atualizados; espera por feature renderizada em vez de timer arbitrário. Runner inclui V3.
- `.gitignore`: logs/temporários de teste excluídos. Input specs e inventário TXT anterior não são parte desta mudança.

## Antes/depois

[Antes mobile](before-mobile.png): glyphs e hero/controles escuros. [Depois mobile](mobile-390.png), [urbano](urban-map.png), [desktop](desktop-v3.png), [camadas](layers-v3.png), [motorista](mobile-driver.png), [alerta](alert.png), [semáforo](detail-signal.png), [radar](detail-fixed.png), [lombada](detail-bump.png).

[Obras — fixture local](works-fixture.png) e [chuva — fixture local](rain-fixture.png) demonstram suporte; não são ocorrências reais. Nenhuma requisição de escrita desses dados foi feita.

## Diagnóstico funcional

Ver `LAYER_DIAGNOSTICS.md`: 14769 features, 6419 semáforos mapeáveis; 7 sem coordenadas. Prova dedicada: API/source/render 198/198/198. Todos oito tipos abrem detalhe correto. Fixture de colisão: 1/4 antes, 4/4 com correção. Preferências antigas mantidas, mas agora visíveis/restauráveis. Obras usam report_kind sem alterar schema.

## Testes

- `node --test tests/*.test.cjs`: 53 PASS.
- Python unittest discovery: 17 PASS; selftest PASS; `python -m py_compile server.py` PASS.
- Syntax checks e diff whitespace: PASS.
- Browser mapa: oito tipos, clique real, filtros persistidos, cluster e zero DOM markers; sem pageerrors/HTTP errors no smoke.
- Browser navegação: GPS, ausência/permissão negada, busca real, rota de 2153m/11 instruções/2 alertas, follow/recenter, 4 intensidades, excesso de velocidade, direção oposta e reporte interceptado (sem escrita).
- Precision V2: aquisição/tracking/previsão/LOST/recuperação/replay determinístico/fallback runtime/bootstrap PASS; um erro intencional esperado.
- V3: controles SVG, tema claro, obras e chuva com fixtures, invalidação de feed vencido, ocultar tudo, cluster 11.5 -> 13 e renderização PASS.
- Mobile 375x812,390x844,430x932,412x915: sem overflow, botões >=44px, HUD dentro da tela e alerta abaixo da manobra.
- Performance foreground desktop: 145 FPS, p95 frame 7.1ms. Resultado inicial anômalo de 2 FPS preservado em browser-map.json e explicitado em KNOWN_LIMITATIONS.

Evidências JSON no diretório. Nesta fase chuva é arquitetura preparada, não serviço meteorológico ativo. Ver `KNOWN_LIMITATIONS.md` e `ICON_SYSTEM.md` para contrato, limites e regras visuais.

## Publicação e rollback

Publicar somente após checks; Vercel staging de produção, health/Neon/assets/mapa e então promoção do mesmo build. O resultado da publicação será informado ao usuário. Reverter ao deployment anterior na Vercel restaura UI v221; nenhum dado precisa ser revertido. Baseline GPS permanece padrão.

Publicação concluída: runtime `e1629a8`, deployment `dpl_CRJQs2g9KH1YTQRnBPr7qcFtVkrq`, status READY, promovido para https://mapsradar-three.vercel.app/. Health confirmou PostgreSQL/196 radares/6426 objetos/19 fontes. Assets e cache v222 aprovados. Teste no domínio público: semáforos API/source/render **73/73/73** no bbox registrado em `production-verification.json`, sem overflow a 390x844. [Screenshot de produção](production-mobile.png). O commit posterior de evidências altera apenas artifacts, excluídos do bundle Vercel.
