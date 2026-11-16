-- mart_costi.sql — base d'asta, consuntivo e scostamento per regione × settore
--
-- Due popolazioni dichiarate:
--   * `n_cup_con_base` / `importo_base_mld` — tutti i CUP con una base d'asta;
--   * `n_cup_con_scostamento` / `scostamento_*` — solo i CUP con almeno un CIG
--     **appaiato** (base e consuntivo sullo stesso CIG). Lo scostamento e' un
--     rapporto: sui CUP parziali (consuntivo di parte / base di tutti) sarebbe
--     strutturalmente negativo, e la mediana scenderebbe da -4,9% a -7,3%
--     pubblicando -117,7 mld dove la misura onesta e' -3,5 mld.
--   * `n_cup_parziali` conta i CUP con un consuntivo ma senza coppia completa:
--     sono esclusi dallo scostamento, non ignorati.
--
-- `anac_base_sospetta` esclude i CIG con base >= 10 mld (la fonte arriva a
-- 1e73); `anac_n_cig_base_grande` segnala quelli >= 1 mld, che sono opere vere.
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
    COUNT(*) FILTER (WHERE anac_importo_base > 0
                       AND anac_n_cig_con_consuntivo > 0
                       AND anac_scostamento_pct IS NULL) AS n_cup_parziali,
    ROUND(SUM(anac_importo_base_appaiata) / 1e9, 3) AS importo_base_appaiata_mld,
    ROUND(SUM(anac_importo_consuntivo_appaiato) / 1e9, 3) AS importo_consuntivo_appaiato_mld,
    ROUND((SUM(anac_importo_consuntivo_appaiato) - SUM(anac_importo_base_appaiata)) / 1e9, 3)
        AS scostamento_mld,
    ROUND(median(anac_scostamento_pct), 1) AS scostamento_pct_mediano,
    COUNT(*) FILTER (WHERE anac_scostamento_pct > 10) AS n_oltre_10pct,
    SUM(anac_n_varianti_qe) AS n_varianti_qe
FROM clean_input
WHERE anac_importo_base > 0
GROUP BY 1, 2, 3
HAVING COUNT(*) FILTER (WHERE anac_importo_base > 0) >= 10
ORDER BY importo_base_mld DESC
