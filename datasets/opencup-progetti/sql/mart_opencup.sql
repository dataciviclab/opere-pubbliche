-- mart_opencup: 1 riga per CUP, anagrafe + localizzazione + fonti
-- Compose di 3 tabelle OpenCUP (100% copertura incrociata).

WITH
loc AS (
    SELECT cup, regione, provincia, comune, codice_comune
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY cup ORDER BY
                CASE WHEN stato = 'ITALIA' THEN 0 ELSE 1 END,
                comune
            ) AS rn
        FROM read_parquet('{support.localizzazione.clean}')
    ) WHERE rn = 1
),

fonti AS (
    SELECT cup,
           COUNT(*) AS n_fonti,
           SUM(CASE WHEN copertura_finanziaria = 'STATALE' THEN 1 ELSE 0 END) > 0 AS ha_fonte_statale,
           SUM(CASE WHEN copertura_finanziaria = 'COMUNITARIA' THEN 1 ELSE 0 END) > 0 AS ha_fonte_ue,
           SUM(CASE WHEN copertura_finanziaria = 'REGIONALE' THEN 1 ELSE 0 END) > 0 AS ha_fonte_regionale,
           SUM(CASE WHEN copertura_finanziaria = 'PRIVATA' THEN 1 ELSE 0 END) > 0 AS ha_fonte_privata
    FROM read_parquet('{support.fonti.clean}')
    GROUP BY cup
)

SELECT
    p.cup,
    p.anno_decisione,
    p.stato_progetto,
    p.costo_progetto,
    p.costo_mld,
    p.finanziamento_progetto,
    p.soggetto_titolare,
    p.piva_soggetto_titolare,
    p.natura_intervento,
    p.tipologia_intervento,
    p.settore_intervento,
    p.categoria_intervento,
    p.codice_settore,
    p.codice_categoria,
    p.descrizione_intervento,
    p.codice_locale_progetto,
    p.data_generazione_cup,
    p.cup_master,
    p.flag_chiuso,
    p.flag_sub_progetto,
    l.regione,
    l.provincia,
    l.comune,
    l.codice_comune,
    COALESCE(f.n_fonti, 0) AS n_fonti,
    COALESCE(f.ha_fonte_statale, false) AS ha_fonte_statale,
    COALESCE(f.ha_fonte_ue, false) AS ha_fonte_ue,
    COALESCE(f.ha_fonte_regionale, false) AS ha_fonte_regionale,
    COALESCE(f.ha_fonte_privata, false) AS ha_fonte_privata
FROM mart_progetti p
LEFT JOIN loc l ON p.cup = l.cup
LEFT JOIN fonti f ON p.cup = f.cup
