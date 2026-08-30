SELECT
    SOGGETTO_TITOLARE AS soggetto_titolare,
    PIVA_CODFISCALE_SOG_TITOLARE AS piva_codfiscale_sog_titolare,
    INDIRIZZO_SOG_TITOLARE AS indirizzo_sog_titolare,
    COMUNE_SOGGETTO_TITOLARE AS comune_soggetto_titolare,
    CODICE_COMUNE_SOGG_TITOLARE AS codice_comune_sogg_titolare,
    CODICE_CATEGORIA_SOGGETTO AS codice_categoria_soggetto,
    CATEGORIA_SOGGETTO AS categoria_soggetto,
    CODICE_AREA_SOGGETTO AS codice_area_soggetto,
    AREA_SOGGETTO AS area_soggetto,
    SOGGETTO_RICHIEDENTE AS soggetto_richiedente
FROM raw_input
