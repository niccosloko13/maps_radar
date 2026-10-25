# Limitacoes conhecidas

- Nao ha trajeto real/GNSS de rua nem ground truth nesta entrega. Os thresholds sao iniciais; baseline continua padrao de rollout. Precisao fisica do sensor nao foi melhorada nem medida.
- Matcher conhece a polilinha planejada, nao uma rede viaria completa. Via paralela ausente da rota, marginal, tunel ou multipath forte podem continuar ambiguos. Top-K/custos preparam HMM; nao executam Viterbi/Meili.
- Filtro CV em plano local com east/north independentes, ruido gaussiano aproximado e damping estacionario. Nao e uma fusao GNSS/IMU nem um modelo geodesico global/polar. accuracy reportada pode ser otimista ou pouco confiavel.
- Confianca e score heuristico, nao posterior calibrado ou raio em metros. Sem speed/heading GPS, jitter pode gerar movimento aparente; sera necessario calibrar os perfis com traces de parada e baixa velocidade reais.
- Previsao e limitada a cinco segundos, exige tracking anterior e perde confianca. Nao navega indefinidamente em tuneis. GPS em background pode ser suspenso pelo navegador/SO; a recuperacao readquire historico mesmo se timers nao dispararem.
- Indice de rota grande e construido sincronamente. Foram medidos 35,6ms para 20.000 segmentos em Chrome com CPU 4x. O hot path ficou dentro do budget; celular fisico ainda precisa medicao. Segmentos muito longos e limite do grid podem exigir buscas mais caras.
- Replay instantaneo e batch sincrono sem render por fix; uma importacao enorme pode bloquear a thread por algum tempo. Use em analise local, nao durante conducao. Replay visual encerra conducao/voz e pausa GPS; sair explicitamente com relas.exitLocationReplay().
- Telemetria em RAM: 3000 registros, uma hora, ate 16 geometrias de rota. Ha checkpoint para replay do ring e contextos de reroute, mas nada e salvo automaticamente. Reload/fechar pagina perde dados nao exportados. Campos numericos nao finitos seguem a representacao JSON (null na exportacao).
- Baseline e fallback temporarios permanecem por exigencia do rollout. Dev exibe erro local; producao guarda apenas diagnostico local limitado. A remocao exige primeiro comparar sessoes reais.
- Planejamento de rota, consultas de viewport e geocodificacao existentes continuam com seu fluxo de rede. O motor novo, replay e telemetria nao criam upload de fixes ou sessao. Nenhum backend, banco, auth ou cadastro de radar foi alterado.
