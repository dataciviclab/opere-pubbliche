-- mart_territorio.sql — Aggregati per regione × settore × anno
-- Per dashboard: heatmap, trend territorio, confronto aree

SELECT
    COALESCE(regione, 'SCONOSCIUTA') AS regione,
    area,
    COALESCE(settore_intervento, 'SCONOSCIUTO') AS settore_intervento,
    anno_decisione,
    COUNT(*) AS n_cup,
    ROUND(SUM(COALESCE(costo_progetto, 0)) / 1e9, 3) AS costo_mld,
    ROUND(SUM(COALESCE(finanziamento_progetto, 0)) / 1e9, 3) AS finanziamento_mld,
    SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) AS n_con_fonte_lab,
    ROUND(SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_con_fonte_lab,
    SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS n_con_anac,
    SUM(CASE WHEN pnrr_fin_pnrr > 0 THEN 1 ELSE 0 END) AS n_con_pnrr,
    SUM(CASE WHEN coe_n_progetti > 0 THEN 1 ELSE 0 END) AS n_con_coesione,
    ROUND(SUM(pnrr_fin_pnrr) / 1e9, 3) AS pnrr_fin_mld,
    ROUND(SUM(anac_importo_aggiudicato) / 1e9, 3) AS anac_importo_mld,
    SUM(CASE WHEN flag_ombrello THEN 1 ELSE 0 END) AS n_ombrello
FROM clean_input
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) >= 10
ORDER BY costo_mld DESC
