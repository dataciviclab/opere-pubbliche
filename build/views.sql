-- View analitiche su data/unified_operas.parquet
-- Uso: duckdb -c "CREATE VIEW ... AS ..." oppure importa in un DB DuckDB.
-- Convenzione: prefissi colonne per fonte (anagrafe_, pnrr_, anac_, coe_, fonti_).

-- 1. Sintesi nazionale — il quadro macro (1 riga)
CREATE OR REPLACE VIEW v_sintesi_nazionale AS
SELECT
    COUNT(*) AS n_cup,
    ROUND(SUM(costo_progetto) / 1e9, 1) AS costo_mld,
    ROUND(SUM(finanziamento_progetto) / 1e9, 1) AS finanziamento_mld,
    ROUND(SUM(costo_progetto) / NULLIF(SUM(finanziamento_progetto), 0) * 100, 1) AS copertura_pct,
    SUM(ha_fonte_statale) AS n_cup_fonte_statale,
    SUM(ha_fonte_ue) AS n_cup_fonte_ue,
    SUM(ha_fonte_regionale) AS n_cup_fonte_regionale,
    SUM(ha_fonte_privata) AS n_cup_fonte_privata,
    SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS n_cup_con_gara,
    SUM(CASE WHEN pnrr_missione IS NOT NULL THEN 1 ELSE 0 END) AS n_cup_pnrr,
    SUM(CASE WHEN coe_n_progetti IS NOT NULL THEN 1 ELSE 0 END) AS n_cup_coesione
FROM unified_operas;

-- 2. CUP rilevanti — la shortlist per l'intelligence:
--    progetti con gara ANAC e/o PNRR e/o coesione (tracciabili end-to-end)
CREATE OR REPLACE VIEW v_cup_rilevanti AS
SELECT *
FROM unified_operas
WHERE anac_n_cig > 0 OR pnrr_missione IS NOT NULL OR coe_n_progetti IS NOT NULL;

-- 3. Territorio × settore — dove cadono i soldi
CREATE OR REPLACE VIEW v_territorio_settore AS
SELECT
    regione, settore_intervento,
    COUNT(*) AS n_cup,
    ROUND(SUM(costo_progetto) / 1e9, 1) AS costo_mld,
    ROUND(SUM(finanziamento_progetto) / 1e9, 1) AS finanziamento_mld
FROM unified_operas
WHERE regione IS NOT NULL
GROUP BY 1, 2
HAVING SUM(costo_progetto) > 0
ORDER BY 4 DESC;

-- 4. Stato avanzamento — costo per stato
CREATE OR REPLACE VIEW v_stato_avanzamento AS
SELECT
    stato_progetto,
    COUNT(*) AS n_cup,
    ROUND(SUM(costo_progetto) / 1e9, 1) AS costo_mld,
    ROUND(SUM(costo_progetto) / SUM(SUM(costo_progetto)) OVER () * 100, 1) AS pct_costo
FROM unified_operas
GROUP BY 1
ORDER BY 3 DESC;

-- 5. Copertura fonti per settore — quanta mix di fonti per CUP
CREATE OR REPLACE VIEW v_copertura_fonti AS
SELECT
    settore_intervento,
    COUNT(*) AS n_cup,
    ROUND(AVG(n_fonti), 1) AS fonti_medie_per_cup,
    ROUND(SUM(ha_fonte_statale) * 100.0 / COUNT(*), 1) AS pct_fonte_statale,
    ROUND(SUM(ha_fonte_ue) * 100.0 / COUNT(*), 1) AS pct_fonte_ue,
    ROUND(SUM(ha_fonte_regionale) * 100.0 / COUNT(*), 1) AS pct_fonte_regionale,
    ROUND(SUM(ha_fonte_privata) * 100.0 / COUNT(*), 1) AS pct_fonte_privata
FROM unified_operas
WHERE settore_intervento IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC;

-- 6. Analisi gap — CUP senza gara tracciata (il "sommerso")
CREATE OR REPLACE VIEW v_analisi_gap AS
SELECT
    regione, settore_intervento, stato_progetto,
    COUNT(*) AS n_cup_senza_gara,
    ROUND(SUM(costo_progetto) / 1e9, 1) AS costo_mld
FROM unified_operas
WHERE (anac_n_cig IS NULL OR anac_n_cig = 0)
GROUP BY 1, 2, 3
ORDER BY 4 DESC;
