-- 01_panorama — il quadro macro delle opere pubbliche italiane
-- Fonte: data/aggregati/settore.parquet + data/aggregati/regione_settore.parquet
-- Domanda: quanti CUP, quanto costo, quanto PNRR, dove?

-- 1.1 Sintesi nazionale (da settore.parquet)
SELECT
    COUNT(*) AS n_settori,
    SUM(n_cup) AS n_cup,
    ROUND(SUM(costo_mld_pulito) / 1e9, 1) AS costo_mld,
    ROUND(SUM(fin_pnrr) / 1e9, 1) AS pnrr_mld,
    ROUND(SUM(fin_pnrr) / NULLIF(SUM(costo_mld_pulito), 0) * 100, 2) AS pnrr_pct_costo
FROM read_parquet('data/aggregati/settore.parquet');

-- 1.2 Top 10 comuni per costo pulito
SELECT comune, regione, n_cup,
       ROUND(costo_mld_pulito / 1e9, 1) AS costo_mld,
       n_cup_pnrr
FROM read_parquet('data/aggregati/comune.parquet')
ORDER BY costo_mld_pulito DESC
LIMIT 10;
