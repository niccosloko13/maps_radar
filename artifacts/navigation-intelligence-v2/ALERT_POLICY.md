# Política de alerta e voz

Foco P0 radar iminente; P1 interdição/acidente/alagamento crítico; P2 próxima manobra; P3 radar ainda distante/pedágio/fiscalização; P4 demais eventos; P5 apoio/comunidade secundária, quando houver fonte. A manobra continua no HUD compacto; o card P0/P1 passa acima dela. Voz e dedupe são centralizados em AlertManager/VoiceQueue.

- Radar iminente para prioridade: distância <=max(500m, velocidade*20s). Acima disso fica secundário à manobra iminente e evento crítico.
- Estados: UPCOMING, NEAR <=max(500m, velocidade*12s), IMMINENT <=max(200m, velocidade*5s), PASSED após passar. Card some para pontos atrás. Intensidade/contraste também consideram distância e excesso do limite cadastrado no equipamento.
- Lombada eletrônica é radar quando a fonte explicitamente informa radar_type=lombada_eletronica. Lombada física comunitária TYPE 8 não vira medidor de velocidade.
- Projeção do equipamento recebe segment_index, along_m, road_bearing e distância lateral. Radar tem corredor lateral de 15m; demais alertas 35m. Veículo deve estar <=25m da rota. Sentido oposto, bearing incompatível (>70°), branch ambíguo e segmento paralelo fora do corredor são suprimidos. Os mesmos critérios filtram o destaque de ícones na rota, além do card.
- Sentido unidirecional conhecido com heading do veículo ausente não gera radar de navegação. Direção desconhecida é conservadora. Voz exige heading conhecido, confiança >=.65 e accuracy <=35m. GPS LOST, extrapolação e replay não emitem voz/alerta novo. Simulação não fala por padrão.
- Sem grafo de faixas/IDs de via, não se garante separar ruas paralelas a menos de 15m ou coordenadas incorretas. A prova automatizada cobre pista contrária, paralela a 25m e branch ambíguo; não transforma proximidade em identidade oficial.

## Voz independente

Três opções persistidas: Navigation Voice OFF, Radar Voice ON, Critical Alerts ON por padrão. O botão mute do HUD controla APENAS navegação. Opções mostram os três canais, sem volume próprio ou promessa de ignorar volume zero/Bluetooth/autoplay do iOS/Android.

Radar: aviso inicial até max(700m, velocidade*35s), limitado a 1800m; depois estágios 500m e 200m. Dedupe por equipamento/estágio; cooldown global 2.5s e por radar 8s. Estágio 200m pode superar o intervalo por estágio, mantendo o limite global. Nada usa setInterval para repetir a mesma fala.

Fila serializada; prioridade maior interrompe a inferior. Só onstart confirma emissão na telemetria. Erro do sintetizador é registrado localmente e a UI informa áudio indisponível até nova ação na opção de voz. Cancelar mute de navegação não cancela radar. Reprodução física em celular ainda precisa teste real.

## Oficial versus verificado

“Oficial” descreve proveniência. “Fontes compatíveis” substitui o genérico “Confirmado”. “Comunidade” continua descoberta comunitária. “Verificado” exige um resultado explícito do Official Finder, EXACT/HIGH, valid_at_date=true e query_date igual à data consultada. O piloto anterior não aprovou vínculo dos dez pontos; esta missão não os promoveu nem alterou o registry.
