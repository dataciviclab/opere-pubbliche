-- 03_settori_pnrr — dove il PNRR pesa di più sul costo delle opere
-- Fonte: data/aggregati/settore.parquet
-- Domanda: quali settori dipendono di più dal PNRR?

SELECT
    settore_intervento,
    n_cup,
    ROUND(costo_mld_pulito / 1e9, 1) AS costo_mld,
    ROUND(fin_pnrr / 1e9, 1) AS pnrr_mld,
    ROUND(fin_pnrr / NULLIF(costo_mld_pulito, 0) * 100, 2) AS pnrr_pct_costo
FROM read_parquet('data/aggregati/settore.parquet')
WHERE costo_mld_pulito > 0
ORDER BY pnrr_pct_costo DESC;
