# Relas — fontes de semáforos e objetos viários

Prioridade de consulta:

1. Fonte oficial municipal geoespacial (WFS/GeoJSON/GeoServer)
2. Fonte oficial municipal textual/catálogo
3. Fonte estadual/rodoviária
4. OpenStreetMap/Overpass apenas como descoberta complementar

## São Paulo capital
- GeoSampa — camada oficial **Cruzamentos Semaforizados**.
- WFS público: https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs
- A v1.8.1 descobre automaticamente a FeatureType de semáforos e consulta `resultType=hits` antes de pedir aprovação.

## Santos
- SIGSantos/Santos Mapeada — mapa oficial de Semáforos.
- GeoServer municipal público com WFS: https://egov.santos.sp.gov.br/geoserver/ows
- A v1.8.1 descobre automaticamente a camada de semáforos e consulta a contagem antes da aprovação.

## Praia Grande
- Portal municipal de Dados Abertos/GeoNetwork é mantido como fonte candidata oficial.
- Enquanto um serviço vetorial oficial específico não estiver confirmado, OSM/Overpass entra apenas como descoberta complementar.

## OpenStreetMap
- `highway=traffic_signals`: semáforos
- `traffic_calming=*`: lombadas/traffic calming
- `highway=speed_camera` e `enforcement=maxspeed`: candidatos de fiscalização
- v1.8.1 usa POST e múltiplos servidores Overpass para evitar dependência de um único endpoint.

## Google
O fato de o Google Maps desenhar semáforos não significa que exista uma API pública de exportação dessa base no Brasil. Não usar scraping/base proprietária do Google como fonte do Relas.
