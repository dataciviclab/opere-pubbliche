-- 06_stato_gestione — segnali di gestione per regione ("chiuso d'ufficio")
-- Fonte: data/cup/cup_fatti.parquet
-- Domanda: dove le opere vengono chiuse d'ufficio (mancata realizzazione)?

SELECT
    regione,
    COUNT(*) FILTER (WHERE stato_progetto = 'CHIUSO D''UFFICIO') AS n_chiuso_ufficio,
    ROUND(SUM(costo_progetto) FILTER (WHERE stato_progetto = 'CHIUSO D''UFFICIO') / 1e9, 1) AS mld_chiuso_ufficio,
    ROUND(SUM(costo_progetto) FILTER (WHERE stato_progetto = 'CHIUSO D''UFFICIO')
          / NULLIF(SUM(costo_progetto), 0) * 100, 2) AS pct_chiuso_ufficio
FROM read_parquet('data/cup/cup_fatti.parquet')
WHERE regione IS NOT NULL AND regione <> '' AND regione <> 'TUTTI'
GROUP BY 1
HAVING SUM(costo_progetto) FILTER (WHERE stato_progetto = 'CHIUSO D''UFFICIO') > 0
ORDER BY 3 DESC;
