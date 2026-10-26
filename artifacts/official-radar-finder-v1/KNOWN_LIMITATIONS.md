# Limitações do piloto

- Ainda NÃO aprovado para migrar o mapa de Praia Grande para somente oficiais/verificados. Dez candidatos não equivalem a dez identidades resolvidas.
- Cinco MEDIUM e cinco CONFLICT; zero EXACT/HIGH. Velocidade nominal é zero nos 15 registros PSIE de PG, portanto desconhecida. Marca/modelo/portaria ausentes.
- Duas gerações de instrumentos aparecem para alguns endereços; datas/IDs antigos são mantidos. Certificado vencido não prova desativação nem operação irregular. Falta evidência de ativação/desativação individual por serial.
- Divergências 328/382, 1180/1122 e 8134/8124 não provam mudança física. Sentidos municipais e PSIE às vezes usam referências geográficas diferentes; equivalência depende de revisão oficial/manual.
- A notícia 01/04/2024 anuncia aferições em 02/04; a de 17/04 anuncia 18/04. São anúncios condicionados ao aval, não certificados de cada serial. A notícia de 29/04/2025 informa oito aferições em 28–29/04, sem enumerar séries; não foi vinculada automaticamente aos dez pontos.
- Dados mensais, `Last-Modified` 01/10/2026; conclusão vale para a evidência disponível, não é monitoramento ao vivo em 25/10.
- Uma das chaves SP não tem serial/Inmetro; nove chaves têm mais de um registro. Contagem de registros/chaves não é censo físico exato.
- XML testado com fixtures, não com arquivo SP inteiro. Variação futura não reconhecida falha de forma explícita, mantendo cache válido.
- Protótipo é biblioteca/CLI local e arquivo de evidências isolado. Não há endpoint público, UI de consulta, migração de schema Neon ou integração do mapa nesta fase. Autenticação e banco atual não foram alterados.
- Cache tem TTL 24h, ETag, hash e fallback stale explícito; não há worker/polling. `--refresh` faz uma coleta condicional por fonte. Se falhar sem cache, o comando falha; não inventa snapshot vazio.
- Histórico pode conter informação administrativa imprecisa. Datas são dias, não horários; reprovação/aprovação conflitantes no mesmo dia não são arbitrariamente ordenadas.
