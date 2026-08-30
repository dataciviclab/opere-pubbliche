-- clean.sql: OpenCUP Progetti
-- raw_input: parquet con 62 colonne (tutte VARCHAR), 11.86M righe
-- Seleziona e tipizza le colonne utili per cup_fatti.

SELECT
    CUP AS cup,
    ANNO_DECISIONE AS anno_decisione,
    STATO_PROGETTO AS stato_progetto,
    TRY_CAST(REPLACE(COSTO_PROGETTO, ',', '.') AS DOUBLE) AS costo_progetto,
    TRY_CAST(REPLACE(FINANZIAMENTO_PROGETTO, ',', '.') AS DOUBLE) AS finanziamento_progetto,
    SOGGETTO_TITOLARE AS soggetto_titolare,
    PIVA_CODFISCALE_SOG_TITOLARE AS piva_soggetto_titolare,
    NATURA_INTERVENTO AS natura_intervento,
    TIPOLOGIA_INTERVENTO AS tipologia_intervento,
    SETTORE_INTERVENTO AS settore_intervento,
    CATEGORIA_INTERVENTO AS categoria_intervento,
    CODICE_SETTORE_INTERVENTO AS codice_settore,
    CODICE_CATEGORIA_INTERVENTO AS codice_categoria,
    DESCRIZIONE_INTERVENTO AS descrizione_intervento,
    CODICE_LOCALE_PROGETTO AS codice_locale_progetto,
    DATA_GENERAZIONE_CUP AS data_generazione_cup,
    CUP_MASTER AS cup_master
FROM raw_input
