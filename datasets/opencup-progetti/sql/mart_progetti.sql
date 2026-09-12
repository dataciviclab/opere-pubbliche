-- mart_progetti: 1 riga per CUP con anagrafe tipizzata + colonne utili
-- Output del toolkit: out/data/mart/opencup_progetti/{year}/mart_progetti.parquet

SELECT
    cup,
    anno_decisione,
    stato_progetto,
    costo_progetto,
    ROUND(costo_progetto / 1e9, 3) AS costo_mld,
    finanziamento_progetto,
    soggetto_titolare,
    piva_soggetto_titolare,
    natura_intervento,
    tipologia_intervento,
    settore_intervento,
    categoria_intervento,
    codice_settore,
    codice_categoria,
    descrizione_intervento,
    codice_locale_progetto,
    data_generazione_cup,
    cup_master,
    -- Flag utili
    CASE WHEN stato_progetto IN ('CHIUSO', 'ANNULLATO', 'REVOCATO')
         THEN true ELSE false END AS flag_chiuso,
    CASE WHEN cup_master IS NOT NULL AND TRIM(cup_master) != ''
         THEN true ELSE false END AS flag_sub_progetto
FROM clean_input
