# Sistema de ícones Relas V3

Família própria de pictogramas geométricos: traço 2.4 no viewBox 48, badge branco com borda cinza e raio 12. Sem emojis, marcas policiais oficiais ou cópia de produtos. Câmera fixa, tripé móvel, câmera com semáforo, semáforo com câmera lateral e semáforo comum são distintos. Corpo do semáforo é escuro, com vermelho/âmbar/verde.

| Tipo | SVG em app/icons |
| --- | --- |
| fixed / câmera | fixed.svg |
| signal_radar | signal_radar.svg |
| red_light | red_light.svg |
| mobile | mobile.svg |
| police | police.svg |
| bump | bump.svg |
| toll | toll.svg |
| signal | signal.svg |
| report_kind=works | works.svg |
| report_kind=accident | accident.svg |
| chuva / alagamento | rain.svg |
| veículo parado | stopped.svg |
| congestionamento | congestion.svg |
| outros perigos | other.svg |

Controles inline em `app/ui/map-ui.js`: busca, camadas, localização, recenter, zoom, voz/mudo, simulação, reportar, rota, filtro, fechar, expandir/retrair, manobra esquerda/direita/reto e tema. SVG decorativo aria-hidden; botão fornece label/aria-label. Os sinais de mais/menos são caminhos SVG, não caracteres crus.

Tamanhos: controles 22px, targets 44–54px; mapa aproximadamente 22–34px conforme zoom; painel 36px; alertas 40px. Badge mantém contraste no mapa claro/escuro. Switch distingue por posição e cor; voz usa aria-pressed; foco explícito; toque ativo reduz escala. Alerta à frente usa borda/label/distância, âmbar e vermelho por intensidade. Ícone do usuário/Precision V2 preservado.
