-- 05_soggetti_titolari — chi gestisce i soldi delle opere pubbliche
-- Fonte: data/unified_operas.parquet
-- Domanda: chi sono i grandi gestori e quanto vale l'opera media per titolare?

SELECT
    soggetto_titolare,
    COUNT(*) AS n_cup,
    ROUND(SUM(costo_progetto) / 1e9, 1) AS costo_mld,
    ROUND(SUM(costo_progetto) / NULLIF(COUNT(*), 0) / 1e6, 2) AS costo_medio_mio_per_cup
FROM read_parquet('data/unified_operas.parquet')
WHERE soggetto_titolare IS NOT NULL AND soggetto_titolare <> ''
GROUP BY 1
ORDER BY 3 DESC
LIMIT 15;
