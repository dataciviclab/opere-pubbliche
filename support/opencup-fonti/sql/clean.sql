-- clean.sql: OpenCUP Fonti di Copertura
-- raw_input: 22.7M righe, 3 colonne (tutte VARCHAR)
-- Un CUP puo' avere piu' fonti (statale, regionale, UE, privata)

SELECT
    CUP AS cup,
    CODICE_COPERTURA_FINANZIARIA AS codice_copertura,
    COPERTURA_FINANZIARIA AS copertura_finanziaria
FROM raw_input
