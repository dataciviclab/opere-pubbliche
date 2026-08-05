-- 07_esecuzione_anac — quante opere arrivano davvero all'esecuzione
-- Fonte: data/unified_operas.parquet
-- Domanda: quante opere hanno una gara ANAC tracciata e quante arrivano a collaudo?
-- (esclude i CUP ombrello per non inquinare i conteggi)

SELECT
    COUNT(*) AS n_cup_totali,
    COUNT(*) FILTER (WHERE anac_n_cig > 0 AND NOT flag_ombrello) AS n_con_gara,
    COUNT(*) FILTER (WHERE anac_n_gare_piccole > 0 AND NOT flag_ombrello) AS n_con_gara_piccola,
    COUNT(*) FILTER (WHERE anac_n_collaudati > 0 AND NOT flag_ombrello) AS n_collaudati,
    ROUND(COUNT(*) FILTER (WHERE anac_n_cig > 0 AND NOT flag_ombrello) * 100.0 / COUNT(*), 2) AS pct_con_gara,
    ROUND(COUNT(*) FILTER (WHERE anac_n_collaudati > 0 AND NOT flag_ombrello) * 100.0 / COUNT(*), 2) AS pct_collaudati
FROM read_parquet('data/unified_operas.parquet');
