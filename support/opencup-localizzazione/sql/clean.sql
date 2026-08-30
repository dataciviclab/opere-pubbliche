-- clean.sql: OpenCUP Localizzazione
-- raw_input: 13.5M righe, 12 colonne (tutte VARCHAR)
-- Una riga per CUP × localizzazione (un CUP puo' avere piu' localizzazioni)

SELECT
    CUP AS cup,
    CODICE_STATO AS codice_stato,
    STATO AS stato,
    CODICE_REGIONE AS codice_regione,
    REGIONE AS regione,
    CODICE_PROVINCIA AS codice_provincia,
    SIGLA_PROVINCIA AS sigla_provincia,
    PROVINCIA AS provincia,
    CODICE_COMUNE AS codice_comune,
    COMUNE AS comune
FROM raw_input
