-- clean.sql — Compose op-cup-lab: 1 riga per CUP con tutti gli attributi
-- Dataset del repo: {support.name.clean} / {support.name.mart} (path locali)
-- Dataset esterni: {support.name.path} (risolto da support type: external)

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
),

pnrr AS (
    SELECT cup, missione AS pnrr_missione, stato_avanzamento AS pnrr_stato_avanzamento,
           fin_pnrr AS pnrr_fin_pnrr, fin_totale AS pnrr_fin_totale
    FROM read_parquet('{support.pnrr_progetti.path}')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
    QUALIFY ROW_NUMBER() OVER (PARTITION BY cup ORDER BY fin_pnrr DESC) = 1
),

pnrr_gare AS (
    SELECT cup, COUNT(*) AS pnrr_n_gare,
           SUM(COALESCE(importo_aggiudicazione, 0)) AS pnrr_importo_aggiudicato
    FROM read_parquet('{support.pnrr_gare.path}')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
    GROUP BY cup
),

pnrr_pagamenti AS (
    SELECT cup, SUM(COALESCE(pagamento_pnrr, 0)) AS pag_pagato_pnrr,
           SUM(COALESCE(pagamento_totale, 0)) AS pag_pagato_totale
    FROM read_parquet('{support.pnrr_pagamenti.path}')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
    GROUP BY cup
),

anac_cig AS (
    -- Mapping CIG -> CUP. Il vecchio compose `anac_cross` teneva un solo CUP per
    -- CIG (MIN) perche' i consumer CUP-level joinano su una stringa singola:
    -- stessa scelta qui, altrimenti un CIG con due CUP verrebbe contato due volte
    -- e `flag_ombrello` (>= 50 CIG) cambierebbe significato.
    SELECT cig, MIN(cup) AS cup
    FROM read_parquet('{support.anac_cup.path}')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
      AND cup NOT IN ('ND', '000000000000000')
      AND cig IS NOT NULL AND TRIM(cig) != ''
    GROUP BY cig
),

anac_agg AS (
    -- Stessi filtri del clean CIG-level che stavamo leggendo: le aggiudicazioni
    -- a importo nullo o fuori scala non contano.
    SELECT cig,
           COUNT(DISTINCT id_aggiudicazione) AS n_aggiudicazioni,
           SUM(importo_aggiudicazione) AS importo_totale_agg,
           MAX(data_aggiudicazione_definitiva) AS data_ultima_agg
    FROM read_parquet('{support.anac_aggiudicazioni.path}')
    WHERE importo_aggiudicazione > 0
      AND importo_aggiudicazione < 100000000000
    GROUP BY cig
),

anac_sal AS (
    SELECT cig,
           COUNT(*) AS n_sal,
           SUM(importo_quota) AS importo_totale_sal
    FROM read_parquet('{support.anac_stati_avanzamento.path}')
    WHERE data_emissione_sal IS NOT NULL
    GROUP BY cig
),

anac AS (
    -- Base: tutti i CIG con un CUP reale (il vecchio compose partiva da
    -- "tutti i CIG noti a una qualunque fonte ANAC", non solo da quelli
    -- aggiudicati): un CIG senza aggiudicazione conta in `anac_n_cig` e vale 0
    -- nelle metriche, esattamente come prima.
    SELECT m.cup,
           COUNT(DISTINCT m.cig) AS anac_n_cig,
           SUM(COALESCE(g.n_aggiudicazioni, 0)) AS anac_n_gare,
           SUM(COALESCE(g.importo_totale_agg, 0)) AS anac_importo_aggiudicato,
           SUM(COALESCE(sl.n_sal, 0)) AS anac_n_sal,
           SUM(COALESCE(sl.importo_totale_sal, 0)) AS anac_importo_sal,
           MAX(g.data_ultima_agg) AS anac_data_ultima_agg
    FROM anac_cig m
    LEFT JOIN anac_agg g ON m.cig = g.cig
    LEFT JOIN anac_sal sl ON m.cig = sl.cig
    GROUP BY m.cup
),

sal_ritardo AS (
    SELECT m.cup, COUNT(*) AS n_ritardo
    FROM read_parquet('{support.anac_stati_avanzamento.path}') s
    JOIN anac_cig m ON s.cig = m.cig
    WHERE s.flag_ritardo = 'IN RITARDO'
    GROUP BY m.cup
),

opencoesione AS (
    SELECT CUP AS cup, COUNT(*) AS coe_n_progetti,
           SUM(COALESCE(FINANZ_TOTALE_PUBBLICO, 0)) AS coe_finanz_tot_pubblico
    FROM read_parquet('{support.opencoesione_progetti.path}')
    WHERE CUP IS NOT NULL AND TRIM(CUP) != ''
    GROUP BY CUP
),

silos AS (
    SELECT cup, denominazione AS silos_denominazione,
           sistema_infrastrutturale AS silos_sistema,
           stato_attuazione AS silos_stato, macro_stato AS silos_macro_stato,
           costi_mln_euro AS silos_costi_mln,
           disponibilita_mln_euro AS silos_disponibilita_mln,
           gap_finanziario_mln_euro AS silos_gap_mln
    FROM read_parquet('{support.silos.mart}')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
    QUALIFY ROW_NUMBER() OVER (PARTITION BY cup ORDER BY costi_mln_euro DESC NULLS LAST) = 1
)

SELECT
    p.cup, p.anno_decisione, p.stato_progetto, p.costo_progetto, p.costo_mld,
    p.finanziamento_progetto, p.soggetto_titolare, p.settore_intervento,
    p.descrizione_intervento, p.flag_chiuso, p.flag_sub_progetto,
    l.regione, l.provincia, l.comune,
    COALESCE(f.n_fonti, 0) AS n_fonti,
    COALESCE(f.ha_fonte_statale, false) AS ha_fonte_statale,
    COALESCE(f.ha_fonte_ue, false) AS ha_fonte_ue,
    COALESCE(f.ha_fonte_regionale, false) AS ha_fonte_regionale,
    COALESCE(f.ha_fonte_privata, false) AS ha_fonte_privata,
    pnrr.pnrr_missione, pnrr.pnrr_stato_avanzamento,
    COALESCE(pnrr.pnrr_fin_pnrr, 0) AS pnrr_fin_pnrr,
    COALESCE(pnrr.pnrr_fin_totale, 0) AS pnrr_fin_totale,
    COALESCE(pnrr_gare.pnrr_n_gare, 0) AS pnrr_n_gare,
    COALESCE(pnrr_gare.pnrr_importo_aggiudicato, 0) AS pnrr_importo_aggiudicato,
    COALESCE(pnrr_pagamenti.pag_pagato_pnrr, 0) AS pag_pagato_pnrr,
    COALESCE(pnrr_pagamenti.pag_pagato_totale, 0) AS pag_pagato_totale,
    COALESCE(a.anac_n_cig, 0) AS anac_n_cig,
    COALESCE(a.anac_n_gare, 0) AS anac_n_gare,
    COALESCE(a.anac_importo_aggiudicato, 0) AS anac_importo_aggiudicato,
    COALESCE(a.anac_n_sal, 0) AS anac_n_sal,
    COALESCE(a.anac_importo_sal, 0) AS anac_importo_sal,
    COALESCE(sr.n_ritardo, 0) AS anac_sal_in_ritardo,
    CASE WHEN COALESCE(a.anac_n_cig, 0) >= 50 THEN true ELSE false END AS flag_ombrello,
    COALESCE(oc.coe_n_progetti, 0) AS coe_n_progetti,
    COALESCE(oc.coe_finanz_tot_pubblico, 0) AS coe_finanz_tot_pubblico,
    s.silos_denominazione, s.silos_sistema, s.silos_stato, s.silos_macro_stato,
    s.silos_costi_mln, s.silos_disponibilita_mln, s.silos_gap_mln,
    CASE
        WHEN l.regione IN ('LOMBARDIA','PIEMONTE','VENETO','EMILIA-ROMAGNA','TOSCANA','LIGURIA',
                           'FRIULI VENEZIA GIULIA','TRENTINO-ALTO ADIGE','VALLE D''AOSTA') THEN 'NORD'
        WHEN l.regione IN ('LAZIO','MARCHE','UMBRIA','ABRUZZO','MOLISE') THEN 'CENTRO'
        ELSE 'SUD+ISOLE'
    END AS area,
    CASE WHEN COALESCE(a.anac_n_cig, 0) > 0 OR pnrr.pnrr_fin_pnrr > 0 OR oc.coe_n_progetti > 0
         THEN true ELSE false END AS con_almeno_una_fonte_lab,
    (CASE WHEN COALESCE(a.anac_n_cig, 0) > 0 THEN 1 ELSE 0 END +
     CASE WHEN pnrr.pnrr_fin_pnrr > 0 THEN 1 ELSE 0 END +
     CASE WHEN oc.coe_n_progetti > 0 THEN 1 ELSE 0 END) AS n_fonti_lab
FROM raw_input p
LEFT JOIN loc l ON p.cup = l.cup
LEFT JOIN fonti f ON p.cup = f.cup
LEFT JOIN pnrr ON p.cup = pnrr.cup
LEFT JOIN pnrr_gare ON p.cup = pnrr_gare.cup
LEFT JOIN pnrr_pagamenti ON p.cup = pnrr_pagamenti.cup
LEFT JOIN anac a ON p.cup = a.cup
LEFT JOIN sal_ritardo sr ON p.cup = sr.cup
LEFT JOIN opencoesione oc ON p.cup = oc.cup
LEFT JOIN silos s ON p.cup = s.cup
