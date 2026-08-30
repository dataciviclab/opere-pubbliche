-- mart_progetti: 1 riga per CUP con anagrafe tipizzata
-- (tutte le colonne sono gia' nel clean, questo mart e' un pass-through per validazione)

SELECT
    cup,
    anno_decisione,
    stato_progetto,
    costo_progetto,
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
    cup_master
FROM clean_input
