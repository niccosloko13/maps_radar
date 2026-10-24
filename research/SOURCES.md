# Fontes pesquisadas — 23/10/2026

## CET São Paulo
- https://ssl.cetsp.com.br/consultas/fiscalizacao-eletronica-do-transito.aspx
- A CET declara que disponibiliza locais ativados/desativados com filtros por região e mapa georreferenciado, com informações detalhadas dinamicamente.
- A página encaminha para um painel Power BI.

## DER-SP
- https://dersp.der.sp.gov.br/
- O portal oficial contém a seção **Localização de Radares**.
- Comunicados de 2026 continuam registrando novas ativações, mostrando que a malha é dinâmica e precisa de versionamento.

## PRF
- https://www.gov.br/prf/pt-br/assuntos/fiscalizacao-de-velocidade/radares-fixos
- Página modificada em 23/09/2026.
- Disponibiliza **Mapa de Radares Fixos** e **Tabela de Radares Fixos**.
- A tabela dinâmica oficial exibe campos como identificador, concessionária, UF, município, BR, km, tipo e validade do certificado.

## INMETRO / PSIE
- https://www.gov.br/inmetro/pt-br/acesso-a-informacao/perguntas-frequentes/metrologia-legal/medidor-de-velocidade-radar/como-saber-se-determinado-radar-esta-verificado
- O INMETRO orienta consultar o PSIE para verificar um medidor de velocidade.
- https://www.gov.br/inmetro/pt-br/acesso-a-informacao/perguntas-frequentes/metrologia-legal/medidor-de-velocidade-radar/qual-e-o-prazo-para-verificacao-de-radar
- A verificação obrigatória é periódica, a cada 12 meses, conforme a orientação oficial consultada.

## Mapa / renderização
- https://maplibre.org/maplibre-gl-js/docs/
- MapLibre GL JS é open source e renderiza mapas vetoriais via WebGL.
- https://openfreemap.org/
- OpenFreeMap permite uso do serviço público sem chave e também oferece self-hosting.
- https://openfreemap.org/quick_start/
- Style usado no protótipo: `https://tiles.openfreemap.org/styles/liberty`.

## Roteamento
- https://valhalla.github.io/valhalla/
- Valhalla é open source e usa OpenStreetMap.
- https://valhalla.github.io/valhalla/api/turn-by-turn/overview/
- Suporta turn-by-turn e instruções verbais.
- https://valhalla.github.io/valhalla/api/map-matching/api-reference/
- `trace_route` e `trace_attributes` permitem map matching de GPS em vias.

## Multas / futura integração
- https://www.gov.br/conecta/catalogo/apis/wsdenatran
- WSDenatran permite acesso oficial a veículos, condutores e infrações, mas depende de autorização/contratação com SENATRAN/SERPRO; portanto não foi incorporada à V0.
