-- 04_missioni_pnrr — dove va il PNRR per missione e quanto pesa sul costo
-- Fonte: data/cup/cup_fatti.parquet
-- Domanda: quale missione è più PNRR-dipendente?

SELECT
    pnrr_missione,
    COUNT(*) AS n_cup,
    ROUND(SUM(pnrr_fin_pnrr) / 1e9, 1) AS pnrr_mld,
    ROUND(SUM(pnrr_fin_totale) / 1e9, 1) AS tot_mld,
    ROUND(SUM(pnrr_fin_pnrr) / NULLIF(SUM(pnrr_fin_totale), 0) * 100, 1) AS pnrr_pct_totale
FROM read_parquet('data/cup/cup_fatti.parquet')
WHERE pnrr_missione IS NOT NULL
GROUP BY 1
ORDER BY 3 DESC;
