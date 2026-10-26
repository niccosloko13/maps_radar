# RELAS MAP UI V3 — LIMPEZA VISUAL, ÍCONES, CAMADAS, SEMÁFOROS, OBRAS E ALERTAS DE CHUVA

Projeto-alvo: `mapsradar-three` / `relas_v182`
Objetivo: transformar a interface do RELAS em uma experiência limpa, moderna, clara e própria, com tema branco contemporâneo, sistema de ícones consistente, correção de renderização dos semáforos/radares e novas camadas úteis como obras e alerta de chuva no estado de São Paulo.

---

# CONTEXTO

O deploy atual ainda transmite aparência de protótipo:

- o topo usa símbolos crus como `◐`, `☷`, `⌕`, `↗`, `◎`, `+`, `−`;
- a interface mistura texto, glyphs e botões sem um sistema visual único;
- o visual do mapa e dos controles ainda não tem linguagem forte própria;
- o usuário precisa perceber o RELAS como produto polido, limpo e confiável.

Também existe um problema funcional:

- semáforos e alguns radares não estão aparecendo no mapa;
- isso precisa ser diagnosticado no pipeline completo, e não tratado como simples ajuste visual.

Além disso, o usuário quer expandir a utilidade do mapa com:

- obras;
- alerta de chuva;
- interface limpa;
- ícones modernos;
- visual branco moderno;
- sistema único e fácil para o usuário.

---

# OBJETIVO DESTA MISSÃO

Entregar uma revisão forte do mapa e da interface, preservando o funcionamento do produto, mas elevando o nível visual e de usabilidade.

A missão cobre:

1. redesign visual do mapa e da UI;
2. novo sistema de ícones moderno e consistente;
3. correção de camadas que não estão aparecendo (semáforos/radares);
4. sistema de camadas melhor;
5. suporte visual para obras;
6. suporte visual para alerta de chuva em todo o estado de São Paulo;
7. refinamento mobile e desktop;
8. limpeza da interface;
9. hierarquia visual clara;
10. sem mexer em banco/auth/desenho estrutural do produto além do necessário para a experiência.

---

# O QUE FOI OBSERVADO NO DEPLOY

O site atual expõe linhas de UI ainda muito cruas, por exemplo:

- botão “Camadas” com glyphs;
- busca com caracteres crus;
- botões `◎`, `+`, `−`;
- estado “Conectando à base local…”;
- estado “Buscando sinal GPS…”.

A estrutura geral existe, mas a apresentação precisa ser redesenhada para parecer um produto maduro.

---

# PRINCÍPIOS DE DESIGN

## 1. Interface limpa e moderna

Criar um tema branco moderno, muito limpo, com sensação de produto premium/utilitário.

Direção visual:

- fundo claro predominante;
- painéis brancos;
- bordas suaves;
- sombras discretas;
- excelente legibilidade;
- mapa como protagonista;
- UI mais silenciosa e menos “barulhenta”.

## 2. Visual próprio

Não copiar Waze ou Google Maps literalmente.

Objetivo:

- parecer tão polido quanto apps grandes;
- mas com identidade própria do RELAS;
- mais elegante, mais clean, mais informativo.

## 3. Hierarquia de informação

Durante direção, o usuário precisa bater o olho e entender:

- onde está;
- o que vem à frente;
- qual tipo de risco/evento existe;
- qual alerta é importante agora.

Tudo o que não for crítico deve ficar mais discreto.

## 4. Menos ruído visual

Eliminar:

- glyphs improvisados;
- símbolos soltos;
- excesso de texto no mapa;
- controles redundantes;
- botões inconsistentes;
- rótulos poluindo a navegação.

---

# ESCOPO VISUAL

## A. SISTEMA DE ÍCONES NOVO

Criar um conjunto de ícones próprios, consistentes, modernos e legíveis.

Não usar emojis como solução final.
Não usar mistura de ícones genéricos desalinhados.
Preferir SVGs próprios e consistentes.

### Tipos de ícones obrigatórios

- radar fixo;
- radar móvel;
- radar semafórico;
- semáforo/câmera de semáforo;
- câmera;
- fiscalização/polícia;
- lombada;
- pedágio;
- acidente;
- obra;
- chuva;
- perigo/alerta geral;
- rota;
- localização atual;
- recenter;
- buscar;
- camadas;
- voz;
- simular;
- adicionar alerta;
- filtros;
- fechar;
- expandir/retrair.

### Requisitos dos ícones

- funcionar bem em 24px, 28px, 32px e 40px;
- leitura rápida em movimento;
- contraste bom sobre mapa claro e escuro;
- halo/borda quando necessário;
- estado ativo/inativo;
- estado selecionado;
- estado “à frente” com destaque;
- mesma família visual para todos.

### Linguagem visual sugerida

- traços simples;
- formas geométricas claras;
- preenchimento suave;
- sem excesso de detalhe;
- aparência moderna de app de mobilidade.

---

## B. CORES E TEMA

Tema principal:

- branco moderno;
- cinzas claros sofisticados;
- texto escuro legível;
- uma cor principal do RELAS;
- uma cor de destaque para alertas.

Exemplo conceitual de função das cores:

- neutro/base: branco + cinza muito claro;
- primária: azul/verde/teal sofisticado;
- alerta moderado: âmbar/laranja;
- alerta forte: vermelho;
- informação auxiliar: cinza azulado.

Não precisa seguir exatamente essas cores; o importante é coerência e limpeza.

### Regras

- não usar cores gritantes demais em todos os pontos;
- reservar cores fortes para alertas críticos;
- distinguir claramente tipos de evento;
- não transformar o mapa em carnaval visual.

---

## C. CONTROLES DO MAPA

Redesenhar os controles laterais/superiores.

### Substituir completamente os glyphs crus

Remover da interface final:

- `◐`
- `☷`
- `⌕`
- `↗`
- `◎`
- `+`
- `−`

Esses comportamentos permanecem, mas com ícones reais e botões modernos.

### Controles principais desejados

- botão de camadas;
- busca;
- recentralizar;
- zoom;
- localização/follow;
- voz;
- simulação;
- reportar/alertar.

### Regras visuais

- botões de mesmo tamanho e raio;
- agrupamento lógico;
- espaçamento consistente;
- sombras discretas;
- resposta tátil clara;
- foco keyboard e acessibilidade.

---

## D. BUSCA / HERO / CABEÇALHO

O topo atual precisa ser simplificado.

Objetivo:

- menos “hero de landing page”;
- mais “produto utilitário vivo”.

### Melhorias

- reduzir ruído textual;
- tornar a busca o principal elemento superior;
- usar placeholder claro;
- botão de ação mais limpo;
- melhorar chip de localização (“São Paulo • Público e sem fins comerciais” etc.);
- deixar o estado do sistema mais elegante.

### O que evitar

- frases grandes demais disputando com o mapa;
- excesso de slogans no contexto de navegação;
- elementos que empurrem o mapa para baixo no mobile.

---

## E. PAINEL DE ALERTA / CARD DO MOTORISTA

O card inferior de navegação precisa ficar muito mais forte.

### Deve mostrar com clareza

- tipo de alerta à frente;
- distância;
- velocidade atual;
- instrução principal;
- voz ligada/desligada;
- simulação;
- estado do sinal;
- estado do modo de navegação.

### Direção visual

- card limpo;
- destaque só no que importa agora;
- tipografia forte;
- menos linhas supérfluas;
- bom uso de espaço em telas pequenas.

---

## F. CAMADAS E FILTROS

Criar um sistema de camadas claro e agradável.

### O painel de camadas deve permitir

- ligar/desligar categorias;
- entender visualmente cada categoria;
- ver contagem quando útil;
- filtrar rápido.

### Camadas principais

- radares fixos;
- radares móveis;
- radares semafóricos;
- semáforos/câmeras de semáforo;
- polícia/fiscalização;
- lombadas;
- pedágios;
- acidentes;
- obras;
- chuva;
- comunidade/alertas enviados.

### Regras

- painel simples e limpo;
- switches ou chips;
- não parecer debug panel;
- manter consistência visual com o restante da UI.

---

# PARTE FUNCIONAL CRÍTICA — SEMÁFOROS E RADARES NÃO APARECENDO

## MISSÃO OBRIGATÓRIA DE DIAGNÓSTICO

Não chutar CSS.
Não assumir que é apenas ícone faltando.

O Codex deve inspecionar o pipeline completo de semáforos e radares:

```text
fonte/bruto
→ normalização de tipo
→ armazenamento em memória
→ geração de GeoJSON/source
→ filtro da layer
→ minzoom/maxzoom
→ registro do ícone
→ renderização final
```

### Produzir diagnóstico objetivo por tipo

Exemplo esperado:

```text
SEMAFOROS
- recebidos da fonte: X
- após normalização: X
- elegíveis para source: X
- presentes no GeoJSON: X
- elegíveis na layer: X
- efetivamente renderizados: X
- causa se zero: [motivo]
```

Fazer o mesmo para:

- radar fixo;
- radar semafórico;
- câmera;
- outros tipos relevantes.

### Verificações obrigatórias

- nomes dos tipos (`signal`, `traffic_signal`, `camera_signal`, etc.);
- filtros da layer;
- propriedade usada para icon-image;
- minzoom exagerado;
- clustering engolindo itens;
- source não atualizado;
- categorias desativadas por padrão;
- bug de normalização;
- bug de deduplicação;
- bug de estilo/ícone inexistente;
- bug de cache/service worker;
- bug no deploy.

Se semáforos estiverem faltando por problema de naming ou filter mismatch, corrigir na raiz.

---

# OBRAS

Adicionar sistema para obras / interdições / manutenção viária.

## Escopo desta fase

Se já existir fonte viável no projeto, integrar.
Se não existir fonte pronta, ao menos preparar arquitetura visual e camada.

### UX

- camada “Obras”;
- ícone exclusivo moderno;
- cor e sinalização próprias;
- card resumido ao tocar;
- impacto visual moderado, sem poluir o mapa.

### Informações possíveis

- tipo de obra;
- faixa/interdição;
- data/horário;
- observação;
- fonte, se houver.

### Comportamento

- só mostrar se dados existirem;
- não inventar obras;
- interface preparada para crescimento.

---

# ALERTA DE CHUVA — ESTADO DE SÃO PAULO INTEIRO

O usuário quer alerta de chuva para o estado inteiro de SP.

## Objetivo desta fase

Preparar e/ou implementar um sistema de alerta de chuva de forma limpa.

### O que deve existir

- camada de chuva;
- item no painel de camadas;
- status visual simples e útil;
- modo de exibir alerta relevante para o usuário;
- sem poluição do mapa.

### Abordagem de UX sugerida

Separar dois níveis:

#### 1. Mapa / Camada
- exibir chuva/alerta climático em camada discreta;
- preferir áreas/regiões/overlay, não mil pins inúteis.

#### 2. Alerta contextual
- “Chuva forte na região”
- “Alerta de chuva no trajeto”
- “Estado de SP com alerta em X regiões”

### Importante

- esta fase pode preparar a UI/arquitetura mesmo que a integração de dados ainda dependa de fonte oficial;
- não usar dados falsos;
- se não houver feed confiável pronto, deixar o sistema preparado e documentado;
- se houver fonte disponível no projeto, integrar com elegância.

---

# HIERARQUIA POR ZOOM

Isso é obrigatório para limpar o mapa.

## Zoom baixo
Mostrar apenas:
- clusters;
- eventos mais relevantes;
- categorias macro.

## Zoom médio
Mostrar:
- radares principais;
- pedágios;
- fiscalização;
- obras relevantes.

## Zoom alto / próximo
Mostrar:
- semáforos;
- lombadas;
- detalhes;
- itens mais densos;
- labels auxiliares quando fizer sentido.

Não despejar tudo no mapa ao mesmo tempo.

---

# CLUSTERING

Implementar ou melhorar clustering onde fizer sentido.

### Regras

- cluster limpo e moderno;
- contagem legível;
- aparência compatível com o tema branco;
- expandir de forma intuitiva;
- não clusterizar indevidamente alertas que precisem ficar individuais no modo de navegação próxima.

---

# MOBILE FIRST

O RELAS precisa parecer muito bom no celular.

## Melhorias obrigatórias

- mapa aproveitando a tela;
- barra de busca compacta;
- botões acessíveis ao toque;
- painel de camadas funcional em telas pequenas;
- card do motorista sem overflow;
- tipografia legível;
- bottom sheet elegante;
- sem blocos gigantes ocupando o viewport.

---

# LIMPEZA GERAL DA INTERFACE

Remover tudo que pareça rascunho ou debug.

### Revisar e limpar

- cabeçalho;
- subtítulos longos;
- microcopy repetitivo;
- chips redundantes;
- painéis muito pesados;
- textos auxiliares excessivos;
- botões duplicados;
- símbolos improvisados.

A regra é:

se não ajuda o usuário de forma clara, reduzir, simplificar ou remover.

---

# SISTEMA DE ESTADOS

Redesenhar visualmente os estados do app:

- carregando;
- buscando GPS;
- sem sinal;
- sinal fraco;
- navegando;
- simulando;
- sem dados;
- replay;
- erro leve;
- fallback.

Esses estados devem parecer estados de produto, não mensagens técnicas jogadas na tela.

---

# ACESSIBILIDADE

Obrigatório:

- contraste adequado;
- foco visível;
- aria-labels em botões;
- tooltips ou labels quando necessário;
- tamanhos de toque corretos;
- navegação por teclado razoável;
- sem depender só de cor para distinguir estados.

---

# SEM MEXER

Não alterar nesta missão, a menos que seja estritamente necessário:

- banco;
- autenticação;
- arquitetura do servidor;
- esquema de dados de usuários;
- Precision Engine V2, exceto integração visual pontual;
- lógica crítica de navegação, exceto onde necessário para exibir dados.

---

# ARTEFATOS ESTRUTURAIS DE IMPLEMENTAÇÃO

O Codex pode criar/ajustar, se fizer sentido:

- `app/styles/tokens.css`
- `app/styles/map-ui.css`
- `app/styles/icons.css`
- `app/ui/icons/`
- `app/ui/layers-panel.*`
- `app/ui/map-controls.*`
- `app/ui/search-bar.*`
- `app/ui/driver-card.*`
- `app/ui/weather-layer.*`
- `app/ui/works-layer.*`

O importante é organizar bem o código e não espalhar bagunça.

---

# FEATURE FLAGS SUGERIDAS

Se necessário, usar flags para rollout controlado:

- `relas-ui-v3`
- `relas-works-layer`
- `relas-rain-layer`

Mas a correção de semáforos/radares não deve depender de flag se for bug real.

---

# TESTES OBRIGATÓRIOS

## Funcionais

- semáforos aparecem;
- radares aparecem;
- obras aparecem quando houver dados;
- chuva aparece quando houver dados;
- filtros ligam/desligam corretamente;
- busca continua funcionando;
- rota continua funcionando;
- follow/recenter continua funcionando;
- driver card continua funcionando;
- mobile sem overflow.

## Visuais

- ícones corretos por tipo;
- ícones carregam sem falha;
- estados ativo/inativo;
- contraste adequado;
- zoom não polui o mapa;
- cluster comporta-se bem.

## Regressão

- não quebrar navegação;
- não quebrar Precision V2;
- não quebrar replay;
- não quebrar alertas existentes;
- não quebrar camadas antigas.

---

# PERFORMANCE

A limpeza visual não pode piorar muito o desempenho.

### Regras

- SVGs otimizados;
- evitar renderização desnecessária;
- camadas bem organizadas;
- filtros eficientes;
- não criar centenas de componentes pesados sem necessidade;
- cluster e visibilidade por zoom para reduzir poluição e custo.

---

# DELIVERABLES

Criar:

```text
artifacts/map-ui-v3/REPORT.md
artifacts/map-ui-v3/ICON_SYSTEM.md
artifacts/map-ui-v3/LAYER_DIAGNOSTICS.md
artifacts/map-ui-v3/KNOWN_LIMITATIONS.md
```

## REPORT.md
Deve conter:
- o que mudou;
- arquivos criados/alterados;
- antes/depois;
- impacto visual;
- impacto funcional;
- testes executados.

## ICON_SYSTEM.md
Deve conter:
- famílias de ícones;
- regras de uso;
- tamanhos;
- estados;
- mapeamento de tipo -> ícone.

## LAYER_DIAGNOSTICS.md
Obrigatório.
Deve conter:
- diagnóstico completo de semáforos;
- diagnóstico de radares;
- contagem por categoria;
- causa raiz dos itens que não apareciam;
- correção aplicada.

## KNOWN_LIMITATIONS.md
Deve registrar:
- fonte de obras disponível ou não;
- fonte de chuva disponível ou não;
- o que ficou preparado;
- pendências.

---

# ORDEM DE EXECUÇÃO

1. criar checkpoint;
2. auditar UI atual;
3. auditar pipeline de layers (semáforos/radares);
4. corrigir causa raiz de semáforos/radares;
5. desenhar sistema de ícones;
6. aplicar novo tema branco moderno;
7. redesenhar controles;
8. redesenhar busca/topo;
9. redesenhar card inferior;
10. reorganizar painel de camadas/filtros;
11. adicionar/estruturar obras;
12. adicionar/estruturar chuva SP;
13. revisar clustering/hierarquia por zoom;
14. validar mobile;
15. rodar testes funcionais;
16. gerar screenshots;
17. gerar relatórios.

---

# DEFINIÇÃO DE PRONTO

A missão só termina quando:

- a interface parecer um produto moderno e limpo;
- os símbolos improvisados antigos tiverem sumido;
- os ícones estiverem consistentes e modernos;
- o mapa estiver visualmente mais claro;
- semáforos e radares ausentes tiverem diagnóstico e correção real;
- obras estiverem suportadas;
- chuva em SP estiver suportada/preparada;
- o sistema de camadas estiver bom para o usuário;
- o mobile estiver polido;
- o relatório estiver documentado.

---

# INSTRUÇÃO FINAL AO CODEX

Implemente uma revisão profunda da UI do mapa do RELAS para deixá-lo limpo, moderno, claro e único para o usuário. Crie um sistema visual próprio com tema branco moderno, conjunto de ícones consistente e interface simplificada. Elimine símbolos improvisados e elementos visuais que transmitam aparência de protótipo. Corrija a renderização dos semáforos e dos radares ausentes auditando todo o pipeline de dados e layers até encontrar a causa raiz. Adicione suporte visual para obras e para alerta de chuva no estado de São Paulo de forma elegante e não poluente. Preserve o funcionamento existente, não mexa em banco ou autenticação e entregue relatórios completos com diagnóstico de layers e sistema de ícones.
