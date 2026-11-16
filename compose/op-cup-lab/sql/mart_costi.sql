-- mart_costi.sql — base d'asta, consuntivo e scostamento per regione × settore
--
-- Solo CUP con una base d'asta registrata nel quadro economico ANAC: senza
-- base lo scostamento non esiste (e non va contato come zero).
-- `anac_importo_aggiudicato` NON si usa qui: dal 2024 ANAC pubblica una copia
-- dell'importo a base in quel campo (vedi WORKFLOW.md), quindi non e' un prezzo
-- confrontabile nella serie.
SELECT
    COALESCE(regione, 'SCONOSCIUTA') AS regione,
    area,
    COALESCE(settore_intervento, 'SCONOSCIUTO') AS settore_intervento,
    COUNT(*) AS n_cup_con_base,
    ROUND(SUM(anac_importo_base) / 1e9, 3) AS importo_base_mld,
    ROUND(SUM(anac_importo_consuntivo) / 1e9, 3) AS importo_consuntivo_mld,
    ROUND((SUM(anac_importo_consuntivo) - SUM(anac_importo_base)) / 1e9, 3) AS scostamento_mld,
    ROUND(median(anac_scostamento_pct), 1) AS scostamento_pct_mediano,
    SUM(CASE WHEN anac_scostamento_pct > 10 THEN 1 ELSE 0 END) AS n_oltre_10pct,
    SUM(anac_n_varianti_qe) AS n_varianti_qe
FROM clean_input
WHERE anac_importo_base > 0
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 10
ORDER BY scostamento_mld DESC
