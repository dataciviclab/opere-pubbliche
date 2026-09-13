-- clean.sql — Compose op-cup-lab: 1 riga per CUP con tutti gli attributi
-- Ottimizzato: niente JOIN esterni, tutto da parquet locali

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
        FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/opere-pubbliche/out/data/clean/opencup_localizzazione/2026/opencup_localizzazione_2026_clean.parquet')
    ) WHERE rn = 1
),

fonti AS (
    SELECT cup,
           COUNT(*) AS n_fonti,
           SUM(CASE WHEN copertura_finanziaria = 'STATALE' THEN 1 ELSE 0 END) > 0 AS ha_fonte_statale,
           SUM(CASE WHEN copertura_finanziaria = 'COMUNITARIA' THEN 1 ELSE 0 END) > 0 AS ha_fonte_ue,
           SUM(CASE WHEN copertura_finanziaria = 'REGIONALE' THEN 1 ELSE 0 END) > 0 AS ha_fonte_regionale,
           SUM(CASE WHEN copertura_finanziaria = 'PRIVATA' THEN 1 ELSE 0 END) > 0 AS ha_fonte_privata
    FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/opere-pubbliche/out/data/clean/opencup_fonti/2026/opencup_fonti_2026_clean.parquet')
    GROUP BY cup
),

pnrr AS (
    SELECT cup, missione AS pnrr_missione, stato_avanzamento AS pnrr_stato_avanzamento,
           fin_pnrr AS pnrr_fin_pnrr, fin_totale AS pnrr_fin_totale
    FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/incubation/dataset-incubator/out/data/clean/pnrr_progetti/2026/pnrr_progetti_2026_clean.parquet')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
    QUALIFY ROW_NUMBER() OVER (PARTITION BY cup ORDER BY fin_pnrr DESC) = 1
),

pnrr_gare AS (
    SELECT cup, COUNT(*) AS pnrr_n_gare,
           SUM(COALESCE(importo_aggiudicazione, 0)) AS pnrr_importo_aggiudicato
    FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/incubation/dataset-incubator/out/data/clean/pnrr_gare/2026/pnrr_gare_2026_clean.parquet')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
    GROUP BY cup
),

pnrr_pagamenti AS (
    SELECT cup, SUM(COALESCE(pagamento_pnrr, 0)) AS pag_pagato_pnrr,
           SUM(COALESCE(pagamento_totale, 0)) AS pag_pagato_totale
    FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/incubation/dataset-incubator/out/data/clean/pnrr_pagamenti/2026/pnrr_pagamenti_2026_clean.parquet')
    WHERE cup IS NOT NULL AND TRIM(cup) != ''
    GROUP BY cup
),

anac AS (
    SELECT cup, COUNT(DISTINCT cig) AS anac_n_cig,
           SUM(n_aggiudicazioni) AS anac_n_gare,
           SUM(importo_totale_agg) AS anac_importo_aggiudicato,
           SUM(n_sal) AS anac_n_sal,
           SUM(importo_totale_sal) AS anac_importo_sal,
           MAX(data_ultima_agg) AS anac_data_ultima_agg
    FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/appalti-pubblici/out/data/clean/anac_cross/2026/anac_cross_2026_clean.parquet')
    WHERE cup IS NOT NULL AND cup NOT IN ('ND', '000000000000000', '') AND TRIM(cup) != ''
    GROUP BY cup
),

opencoesione AS (
    SELECT CUP AS cup, COUNT(*) AS coe_n_progetti,
           SUM(COALESCE(FINANZ_TOTALE_PUBBLICO, 0)) AS coe_finanz_tot_pubblico
    FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/incubation/dataset-incubator/out/data/clean/opencoesione_progetti/2026/opencoesione_progetti_2026_clean.parquet')
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
    FROM read_parquet('/home/gabry/dev/dataciviclab-workspace/opere-pubbliche/out/data/mart/silos_infrastrutture/2024/mart_silos.parquet')
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
LEFT JOIN opencoesione oc ON p.cup = oc.cup
LEFT JOIN silos s ON p.cup = s.cup
