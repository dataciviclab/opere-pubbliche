-- 02_divario_aree — Nord / Centro / Sud+Isole: costo e incidenza PNRR
-- Fonte: data/aggregati/regione_settore.parquet
-- Domanda: il PNRR sta riequilibrando il divario territoriale?

SELECT
    CASE WHEN regione IN ('LOMBARDIA','PIEMONTE','VENETO','EMILIA-ROMAGNA','LIGURIA',
                          'FRIULI-VENEZIA GIULIA','TRENTINO-ALTO ADIGE','VALLE D''AOSTA')
              THEN 'NORD'
         WHEN regione IN ('TOSCANA','UMBRIA','MARCHE','LAZIO') THEN 'CENTRO'
         ELSE 'SUD+ISOLE' END AS area,
    SUM(n_cup) AS n_cup,
    ROUND(SUM(costo_mld_pulito) / 1e9, 1) AS costo_mld,
    ROUND(SUM(fin_pnrr) / 1e9, 1) AS pnrr_mld,
    ROUND(SUM(fin_pnrr) / NULLIF(SUM(costo_mld_pulito), 0) * 100, 2) AS pnrr_pct_costo
FROM read_parquet('data/aggregati/regione_settore.parquet')
GROUP BY 1
ORDER BY 3 DESC;
