-- SILOS — Infrastrutture strategiche e prioritarie
-- Report Camera dei Deputati 2024
-- Numeri in formato italiano: uso macro toolkit

SELECT
    {year}::INTEGER AS anno,
    normalize_string("Link alla scheda") AS link_scheda,
    cast_int("Progressivo") AS progressivo,
    cast_int("Livello") AS livello,
    normalize_string("Commissariate o PNRR-PNC") AS flag_commissariato_pnrr,
    normalize_string("Sistema infrastrutturale") AS sistema_infrastrutturale,
    normalize_string("Cup") AS cup,
    normalize_string("Denominazione") AS denominazione,
    normalize_string("Soggetto competente") AS soggetto_competente,
    normalize_string("Luogo lavori") AS luogo_lavori,
    normalize_string("Stato di attuazione") AS stato_attuazione,
    cast_int("Ultimazione lavori al 31/08/2024") AS anno_ultimazione_previsto,
    normalize_italian_number("Costi al 31/08/2024") AS costi_mln_euro,
    normalize_italian_number("Disponibilità al 31/08/2024") AS disponibilita_mln_euro,
    normalize_italian_number("Fabbisogno al 31/08/2024") AS fabbisogno_mln_euro
FROM raw_input
