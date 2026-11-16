-- mart_costi.sql — base d'asta, consuntivo e scostamento per regione × settore
--
-- Due popolazioni diverse, dichiarate:
--   * `n_cup_con_base` / `importo_base_mld` — tutti i CUP con una base d'asta;
--   * `n_cup_con_scostamento` / consuntivo / scostamento / mediana — solo i CUP
--     che hanno **anche** il consuntivo (un terzo). Contare i CUP senza
--     consuntivo come scostamento -100% direbbe che i lavori sono costati zero.
--
-- `anac_base_sospetta` esclude i CUP con una base >= 1 mld su un singolo CIG
-- (la fonte ha importi fino a 1e73: senza guardia due CUP valgono 16 mila mld).
--
-- `anac_importo_aggiudicato` NON si usa qui: dal 2024 ANAC pubblica in
-- `importo_aggiudicazione` una copia dell'importo a base (vedi WORKFLOW.md).
SELECT
    COALESCE(regione, 'SCONOSCIUTA') AS regione,
    area,
    COALESCE(settore_intervento, 'SCONOSCIUTO') AS settore_intervento,
    COUNT(*) FILTER (WHERE anac_importo_base > 0) AS n_cup_con_base,
    ROUND(SUM(anac_importo_base) / 1e9, 3) AS importo_base_mld,
    COUNT(*) FILTER (WHERE anac_scostamento_pct IS NOT NULL) AS n_cup_con_scostamento,
    ROUND(SUM(anac_importo_consuntivo) / 1e9, 3) AS importo_consuntivo_mld,
    ROUND((SUM(anac_importo_consuntivo) FILTER (WHERE anac_scostamento_pct IS NOT NULL)
           - SUM(anac_importo_base) FILTER (WHERE anac_scostamento_pct IS NOT NULL)) / 1e9, 3)
        AS scostamento_mld,
    ROUND(median(anac_scostamento_pct), 1) AS scostamento_pct_mediano,
    COUNT(*) FILTER (WHERE anac_scostamento_pct > 10) AS n_oltre_10pct,
    SUM(anac_n_varianti_qe) AS n_varianti_qe
FROM clean_input
WHERE anac_importo_base > 0
GROUP BY 1, 2, 3
HAVING COUNT(*) FILTER (WHERE anac_importo_base > 0) >= 10
ORDER BY importo_base_mld DESC
