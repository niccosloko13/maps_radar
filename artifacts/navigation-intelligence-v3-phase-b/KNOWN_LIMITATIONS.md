# Limitações e critérios ainda não satisfeitos

**INCOMPLETE / BLOCKED — NOT READY FOR PHYSICAL TEST.** Encerramento no estado atual, sem novas tentativas de obter fontes externas ou transformar o status em READY nesta sessão.

1. ARTESP exige duas chaves que o usuário ainda não possui. Autenticação real, cobertura total paginada, ocorrências/intervenções atuais e quotas reais não foram comprovadas.
2. Defesa Civil expirou nas tentativas de acesso. Não há adapter validado contra um endpoint real dessa fonte. GeoJSON configurável/testado não equivale à integração real.
3. SIBH fornece observações pontuais; não há overlay meteorológico regional validado nem sustentação de “chuva forte na pista”. Licença de redistribuição precisa confirmação.
4. PRF: 27 endereços reais, mas zero coordenadas comprovadas e nenhum pin real. Geocoding só cria propostas em revisão; precisa validação cartográfica antes de publicar.
5. Não foi encontrado cadastro atual validado PMRv. PDFs antigos não foram tratados como atuais. Nenhuma base PMRv importada.
6. Praças ANTT: 73 SP reais, recurso de julho/2026, AGING; sem tarifa. Cobertura federal não substitui pedágios ARTESP estaduais. Bases/SAU/apoio seguem sem feed atual validado.
7. Adapter GeoJSON configurável é uma extensão preparada para fontes oficiais revisadas; não deve ser considerado adapter de um portal ainda não validado. URLs precisam origem, licença e schema comprovados antes da configuração.
8. Catálogos ARTESP atualmente armazenam uma página e metadados de paginação, sem varredura completa automática. Snapshots de eventos só publicam após última página; datasets muito grandes podem exigir várias janelas de cota.
9. Dedupe multifonte gera candidatos conservadores para revisão; não há reconciliação automática aprovada. Histórico/snapshots é preservado e ainda precisa política operacional de retenção para longo prazo.
10. Corredor é geométrico, sem garantia absoluta de faixa/carreata em vias paralelas próximas. Direções cardinais são conservadoras em curvas. Geometrias suportadas: Point, LineString e Polygon; não MultiPolygon/MultiLineString. Limite de rota 5.000 pontos e consulta até 3.000 registros; retorno do mapa limitado a 1.500 por classe/viewport.
11. Sem scheduler de produção instalado. Coleta é Admin/CLI explícita e request-bound. Não existe thread eterna nem coleta disparada por usuário do mapa.
12. Há estados SVG normal/selected/critical/stale e seleção de registro no mapa do Admin já implementados e testados. Ainda faltam mapa administrativo de cobertura dedicado, revisão completa por lote e paginação de tabelas grandes; não tratar essas ações avançadas como concluídas.
13. Não houve teste físico, áudio real via Bluetooth/sistema operacional ou validação em aparelho físico. Viewports são emulação Chromium. Providers públicos de mapa/rota seguem sujeitos a disponibilidade.
14. Migração aplicada só em SQLite isolado e branch Neon temporária; banco pessoal e produção preservados. Nenhuma ativação em produção, push ou deploy foi executado.

Não remover esses impedimentos do relatório por haver código, fixture ou screenshot. Finalizar a missão integral requer resolver os pontos acima, repetir fluxo real por fonte e obter evidência de mapa/Admin/rota com essas fontes.

## Congelamento final

Não há tentativa de transformar o status em READY nesta sessão. Seis fontes seguem BLOCKED por chave/feed/endpoint/licença/disponibilidade. SIBH e PRF permanecem INCOMPLETE em relação à missão integral. O snapshot de encerramento tem zero observações SIBH não expiradas, sem apagar o histórico ou inferir ausência de chuva.
