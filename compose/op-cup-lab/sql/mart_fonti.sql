-- mart_fonti.sql — Copertura fonti per settore × area
-- Per dashboard: analisi copertura, dove il Lab arriva, dove no

SELECT
    COALESCE(settore_intervento, 'SCONOSCIUTO') AS settore_intervento,
    area,
    COUNT(*) AS n_cup,
    ROUND(SUM(COALESCE(costo_progetto, 0)) / 1e9, 3) AS costo_mld,
    -- Copertura per fonte
    SUM(CASE WHEN ha_fonte_statale THEN 1 ELSE 0 END) AS n_fonte_statale,
    SUM(CASE WHEN ha_fonte_ue THEN 1 ELSE 0 END) AS n_fonte_ue,
    SUM(CASE WHEN ha_fonte_regionale THEN 1 ELSE 0 END) AS n_fonte_regionale,
    SUM(CASE WHEN ha_fonte_privata THEN 1 ELSE 0 END) AS n_fonte_privata,
    -- Copertura Lab
    SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS n_anac,
    SUM(CASE WHEN pnrr_fin_pnrr > 0 THEN 1 ELSE 0 END) AS n_pnrr,
    SUM(CASE WHEN coe_n_progetti > 0 THEN 1 ELSE 0 END) AS n_coesione,
    SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) AS n_con_fonte_lab,
    -- Percentuali
    ROUND(SUM(CASE WHEN ha_fonte_statale THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_statale,
    ROUND(SUM(CASE WHEN ha_fonte_ue THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_ue,
    ROUND(SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_anac,
    ROUND(SUM(CASE WHEN pnrr_fin_pnrr > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_pnrr,
    ROUND(SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_con_fonte_lab,
    -- Valori finanziari
    ROUND(SUM(pnrr_fin_pnrr) / 1e9, 3) AS pnrr_fin_mld,
    ROUND(SUM(anac_importo_aggiudicato) / 1e9, 3) AS anac_importo_mld,
    ROUND(SUM(coe_finanz_tot_pubblico) / 1e9, 3) AS coesione_fin_mld
FROM clean_input
GROUP BY 1, 2
HAVING COUNT(*) >= 10
ORDER BY costo_mld DESC
