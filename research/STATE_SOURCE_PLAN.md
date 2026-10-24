# Radar SP · State Intelligence Plan v1.4

## Objetivo
Cobrir o Estado de São Paulo por camadas, sem misturar fiscalização oficial com descoberta comunitária.

## Espinha dorsal estadual
1. DER-SP — radares em rodovias estaduais não concedidas; inventário, operação, km, sentido e, quando disponível, coordenada oficial. A malha oficial DER permite georreferenciamento por km.
2. ANTT — radares das rodovias federais concedidas, com atualização mensal e latitude/longitude. O catálogo também publica volume de tráfego por radar.
3. ARTESP CCM — operação das rodovias estaduais concedidas: ocorrências, intervenções e tempos de percurso.

## Cobertura urbana
Conectores municipais separados, porque não existe uma API única para os 645 municípios. Prioridade:
- São Paulo capital / CET-SP
- Campinas / EMDEC
- ABC: Santo André, São Bernardo, São Caetano, Diadema, Mauá
- Baixada: Santos, Praia Grande, São Vicente, Cubatão, Guarujá
- Grandes polos: Guarulhos, Osasco, Sorocaba, São José dos Campos, Ribeirão Preto, Bauru, São José do Rio Preto, Jundiaí, Piracicaba, Limeira, Franca, Marília, Presidente Prudente.

## Tipos de fiscalização canônicos
- radar_fixo
- radar_semaforo
- lombada_eletronica
- radar_rodoviario
- restricao

## Objetos viários (não são automaticamente fiscalização)
- traffic_signal
- physical_bump
- speed_camera_osm (descoberta comunitária; precisa cruzamento oficial antes de virar fiscalização confirmada)

## Semáforos
O sistema separa localização do semáforo de sua programação.
- fixed: ciclo conhecido e documentado
- coordinated: sincronizado em rede, mas sem segundos por cruzamento
- adaptive: tempo varia de acordo com fluxo/detecção
- unknown: localização conhecida, programação ainda não conhecida

Nunca exibir contagem regressiva inventada. Em São Paulo capital, redes SCATS recalculam os tempos a cada ciclo; em Campinas há semáforos inteligentes que ajustam fase verde pela demanda; Santos opera rede sincronizada e possui pontos com detecção de demanda.

## Descoberta comunitária
OSM pode ser consultado por município no Admin para localizar semáforos e lombadas físicas. Esses dados entram com confiança menor e nunca substituem uma fonte oficial para afirmar que existe fiscalização eletrônica.

## Regra de promoção de dado
Descoberta -> candidato -> cruzamento com fonte oficial -> coordenada/velocidade/situação -> radar confirmado na base.

## Meta de cobertura
O painel acompanha separadamente:
- municípios com fiscalização oficial mapeada
- municípios com apenas inventário
- municípios com objetos viários comunitários
- municípios sem fonte cadastrada

O objetivo não é pintar 645 municípios de verde artificialmente; é aumentar cobertura mantendo rastreabilidade e confiança.

## Admin Operations v1.5 — varredura municipal persistente
O Admin permite selecionar/digitar até 5 municípios por rodada. Cada rodada:
1. cruza registros já salvos de DER-SP/ANTT por município;
2. executa conectores municipais oficiais já conhecidos;
3. consulta catálogos oficiais de dados abertos quando disponíveis;
4. opcionalmente consulta OSM apenas como descoberta de semáforos/lombadas/câmeras;
5. persiste fontes que funcionaram em `municipality_sources`;
6. persiste cada tentativa em `source_attempts`;
7. mantém municípios sem fonte oficial confirmada em `source_gaps` para investigação futura;
8. mantém histórico de rodadas em `city_scan_jobs`.

Regra rígida: falha de uma fonte nunca apaga dado bom já salvo. Uma nova sincronização atualiza/versiona; não reinicia a base.
