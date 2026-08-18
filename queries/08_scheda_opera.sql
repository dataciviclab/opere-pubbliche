-- 08_scheda_opera — cosa sappiamo di un'opera (1 CUP = 1 scheda)
-- Fonte: data/cup/cup_fatti.parquet + SILOS (GCS Lab, denominazione/stato/costo)
-- Domanda: qual è la scheda completa di un'opera, dai dati anagrafe ai collaudi?
--
-- Uso: sostituire {cup} con il CUP da analizzare (es. F81H92000000008 = Terzo Valico)
--   duckdb -c "$(sed 's/{cup}/F81H92000000008/' queries/08_scheda_opera.sql)"
--   oppure via reports/scheda_opera.py (genera data/reporting/schede/)

SELECT
    f.cup,
    s.denominazione AS opera,
    f.soggetto_titolare,
    s.soggetto_competente,
    s.sistema_infrastrutturale AS sistema,
    f.anno_decisione,
    f.stato_progetto,
    s.stato_attuazione AS stato_silos,
    -- Costi: anagrafe OpenCUP vs stima SILOS (entrambi ufficiali, prospettive diverse)
    ROUND(f.costo_progetto / 1e9, 2) AS costo_anagrafe_mld,
    ROUND(f.finanziamento_progetto / 1e9, 2) AS finanziamento_mld,
    ROUND(s.costi_mln_euro / 1000, 1) AS costo_silos_mld,
    ROUND(s.disponibilita_mln_euro / 1000, 1) AS disponibilita_silos_mld,
    ROUND(s.fabbisogno_mln_euro / 1000, 1) AS fabbisogno_silos_mld,
    -- Fonti di copertura
    f.n_fonti, f.ha_fonte_statale, f.ha_fonte_ue, f.ha_fonte_regionale, f.ha_fonte_privata,
    -- Esecuzione (ANAC)
    f.anac_n_cig AS n_gare_anac,
    f.anac_n_gare_pnrr AS n_gare_pnrr,
    f.anac_n_collaudati,
    f.anac_n_gare_piccole AS n_gare_piccole,
    -- Affidamenti diretti (CIG prefisso B — smartCIG + affidamenti estesi)
    f.anac_n_cig_b AS n_gare_affidamento_diretto,
    f.anac_importo_cig_b AS importo_affidamento_diretto,
    f.flag_ombrello,
    -- Programmi
    f.pnrr_missione,
    f.pnrr_stato_avanzamento,
    f.pnrr_amministrazione_titolare,
    f.coe_n_progetti AS n_progetti_coesione,
    -- Localizzazione
    f.regione, f.provincia, f.comune,
    f.codice_comune
FROM read_parquet('data/cup/cup_fatti.parquet') f
LEFT JOIN (
    -- SILOS: CUP multi-valore normalizzati (split su ' - '), 1 riga per CUP
    SELECT
        UNNEST(STRING_SPLIT(cup, ' - ')) AS cup_singolo,
        MAX(denominazione) AS denominazione,
        MAX(soggetto_competente) AS soggetto_competente,
        MAX(sistema_infrastrutturale) AS sistema_infrastrutturale,
        MAX(stato_attuazione) AS stato_attuazione,
        MAX(costi_mln_euro) AS costi_mln_euro,
        MAX(disponibilita_mln_euro) AS disponibilita_mln_euro,
        MAX(fabbisogno_mln_euro) AS fabbisogno_mln_euro
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/silos_infrastrutture/2024/silos_infrastrutture_2024_clean.parquet')
    WHERE cup IS NOT NULL AND cup <> ''
    GROUP BY cup
) s ON f.cup = s.cup_singolo
WHERE f.cup = '{cup}';
