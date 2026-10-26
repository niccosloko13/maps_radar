# Ícones de navegação e estrada

Mantida a família Relas V3: viewBox 48, badge branco arredondado, borda cinza, traço geométrico e contraste claro/escuro. Sem emoji, clipart, brasões oficiais ou cópia de interfaces proprietárias. Normal/selecionado/iminente usam a mesma silhueta, com hierarquia, tamanho e borda do card.

| Categoria | SVG app/icons |
| --- | --- |
| Radar fixo/semafórico/avanço | fixed / signal_radar / red_light |
| Lombada eletrônica versus física | electronic-bump / bump |
| PRF_POST | prf-post |
| PM_RODOVIARIA_BASE | pm-road-base |
| POLICE_BASE | police-base |
| ROAD_INSPECTION_BASE | inspection-base |
| DER_BASE / ARTESP_BASE | der-base |
| CONCESSIONAIRE_BASE | concessionaire-base |
| TOLL_PLAZA | toll |
| WEIGH_STATION | weigh-station |
| SAU | sau |
| TOW_SERVICE / MECHANICAL_SUPPORT | guincho / mechanical-support |
| Obra/acidente | works / accident |
| Chuva/alagamento/neblina | rain / flood / fog |
| Interdição/animal/objeto/pista escorregadia | closure / animal / object / slippery |
| Fiscalização comunitária | police |
| Usuário/localização | user / user-chevron e controles SVG |

Mapeamento dos contratos em `app/navigation/source-contracts.js`. Ícone preparado NÃO significa fonte conectada nem existência oficial de base. Apenas reportes e categorias que já têm dados entram no mapa; sprites das novas ocorrências ativas são registrados no MapLibre, não DOM markers.

Controles 22px dentro de targets >=44px; pontos ~24–34px por zoom; card ~34px. HUD mais compacto, opções e gravação em bottom sheet; sem adicionar painéis permanentes ao mapa. Radar P0 e perigo P1 têm destaque acima da manobra.
