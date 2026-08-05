#!/usr/bin/env python3
"""Build unified — profilo per CUP (1 riga per CUP).

Unisce OpenCup (anagrafe universale) con i dataset del Lab:
  OpenCup progetti + localizzazione + fonti copertura
  + Lab: pnrr_progetti, pnrr_gare, anac (appalti), opencoesione

Grano: 1 riga per CUP. Le metriche dei sottoinsiemi Lab sono aggregate
(n_*, tot_*). Output: data/unified_operas.parquet (fuori git).

Uso: python build/build_unified.py [--out data/unified_operas.parquet]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]

# Path fonti (allineati a build/join_map.yaml)
OC_PROGETTI = str(REPO_ROOT / "opencup/data/parquet/opencup_progetti.parquet")
OC_LOCALIZZAZIONE = str(REPO_ROOT / "opencup/data/parquet/opencup_localizzazione.parquet")
OC_FONTI = str(REPO_ROOT / "opencup/data/parquet/opencup_fonti_copertura.parquet")

LAB_PNRR = "gs://dataciviclab-clean/pnrr_progetti/2026/pnrr_progetti_2026_clean.parquet"
LAB_PNRR_GARE = str(REPO_ROOT.parent / "dataset-incubator/out/data/clean/pnrr_gare/2026/pnrr_gare_2026_clean.parquet")
LAB_ANAC = "gs://dataciviclab-clean/anac_appalti_master/2026/anac_appalti_master_2026_clean.parquet"
LAB_OPENCOESIONE = "gs://dataciviclab-clean/opencoesione_progetti/2026/opencoesione_progetti_2026_clean.parquet"


SQL = f"""
WITH base AS (
    SELECT "CUP" AS cup,
           "DESCRIZIONE_SINTETICA_CUP" AS descrizione,
           "ANNO_DECISIONE" AS anno_decisione,
           "STATO_PROGETTO" AS stato_progetto,
           TRY_CAST(REPLACE("COSTO_PROGETTO", ',', '.') AS DOUBLE) AS costo_progetto,
           TRY_CAST(REPLACE("FINANZIAMENTO_PROGETTO", ',', '.') AS DOUBLE) AS finanziamento_progetto,
           "SOGGETTO_TITOLARE" AS soggetto_titolare,
           "PIVA_CODFISCALE_SOG_TITOLARE" AS piva_soggetto_titolare,
           "NATURA_INTERVENTO" AS natura_intervento,
           "TIPOLOGIA_INTERVENTO" AS tipologia_intervento,
           "SETTORE_INTERVENTO" AS settore_intervento,
           "CATEGORIA_INTERVENTO" AS categoria_intervento,
           "CODICE_LOCALE_PROGETTO" AS codice_locale_progetto,
           "DATA_GENERAZIONE_CUP" AS data_generazione_cup
    FROM read_parquet('{OC_PROGETTI}')
),
localizzazione AS (
    SELECT "CUP" AS cup,
           MAX("REGIONE") AS regione,
           MAX("PROVINCIA") AS provincia,
           MAX("COMUNE") AS comune,
           MAX("CODICE_COMUNE") AS codice_comune
    FROM read_parquet('{OC_LOCALIZZAZIONE}')
    GROUP BY 1
),
fonti AS (
    SELECT "CUP" AS cup,
           COUNT(*) AS n_fonti,
           SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'STATALE' THEN 1 ELSE 0 END) AS ha_fonte_statale,
           SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'COMUNITARIA' THEN 1 ELSE 0 END) AS ha_fonte_ue,
           SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'REGIONALE' THEN 1 ELSE 0 END) AS ha_fonte_regionale,
           SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'PRIVATA' THEN 1 ELSE 0 END) AS ha_fonte_privata
    FROM read_parquet('{OC_FONTI}')
    GROUP BY 1
),
pnrr AS (
    SELECT cup,
           MAX(missione) AS pnrr_missione,
           MAX(descrizione_missione) AS pnrr_descrizione_missione,
           MAX(stato_avanzamento) AS pnrr_stato_avanzamento,
           MAX(amministrazione_titolare) AS pnrr_amministrazione_titolare,
           SUM(fin_pnrr) AS pnrr_fin_pnrr,
           SUM(fin_totale) AS pnrr_fin_totale
    FROM read_parquet('{LAB_PNRR}')
    WHERE LENGTH(cup) = 15
    GROUP BY cup
),
gare AS (
    SELECT cup,
           COUNT(*) AS pnrr_n_gare,
           COUNT(cig) AS pnrr_n_gare_con_cig,
           SUM(importo_aggiudicazione) AS pnrr_importo_aggiudicato
    FROM read_parquet('{LAB_PNRR_GARE}')
    GROUP BY cup
),
anac AS (
    SELECT cup,
           COUNT(*) AS anac_n_gare,
           COUNT(cig) AS anac_n_cig,
           SUM(importo_agg) AS anac_importo_aggiudicato,
           SUM(CASE WHEN flag_pnrr THEN 1 ELSE 0 END) AS anac_n_gare_pnrr,
           COUNT(esito_collaudo) AS anac_n_collaudati,
           -- Colonne "piccole" (CIG sotto soglia): la somma totale è distorta
           -- dai CUP-programma/ombrello (vedi build/join-cup-anac-rules.md).
           COUNT(*) FILTER (WHERE importo_complessivo_gara < 5000000) AS anac_n_gare_piccole,
           SUM(importo_agg) FILTER (WHERE importo_complessivo_gara < 5000000) AS anac_importo_gare_piccole
    FROM read_parquet('{LAB_ANAC}')
    WHERE cup IS NOT NULL
      AND cup NOT IN ('ND', '000000000000000', '')
    GROUP BY cup
),
coesione AS (
    SELECT "CUP" AS cup,
           COUNT(DISTINCT "COD_LOCALE_PROGETTO") AS coe_n_progetti,
           MAX("OC_DESCR_CICLO") AS coe_ciclo,
           SUM("FINANZ_TOTALE_PUBBLICO") AS coe_finanz_tot_pubblico,
           SUM("TOT_PAGAMENTI") AS coe_pagamenti
    FROM read_parquet('{LAB_OPENCOESIONE}')
    GROUP BY 1
)
SELECT
    b.cup,
    b.descrizione, b.anno_decisione, b.stato_progetto,
    b.costo_progetto, b.finanziamento_progetto,
    b.soggetto_titolare, b.piva_soggetto_titolare,
    b.natura_intervento, b.tipologia_intervento,
    b.settore_intervento, b.categoria_intervento,
    l.regione, l.provincia, l.comune, l.codice_comune,
    f.n_fonti, f.ha_fonte_statale, f.ha_fonte_ue, f.ha_fonte_regionale, f.ha_fonte_privata,
    p.pnrr_missione, p.pnrr_stato_avanzamento, p.pnrr_amministrazione_titolare,
    p.pnrr_fin_pnrr, p.pnrr_fin_totale,
    g.pnrr_n_gare, g.pnrr_n_gare_con_cig, g.pnrr_importo_aggiudicato,
    a.anac_n_gare, a.anac_n_cig, a.anac_importo_aggiudicato, a.anac_n_gare_pnrr, a.anac_n_collaudati,
    a.anac_n_gare_piccole, a.anac_importo_gare_piccole,
    -- CUP ombrello: molti CIG (>=50) E importo gare >> costo anagrafe.
    -- Il solo n_cig alto non basta: il Terzo Valico (97 CIG, costo 4,7 mld)
    -- è un'opera vera, non un contenitore. La distorsione nasce quando le
    -- gare collegate superano di molto il costo dell'anagrafe.
    CASE WHEN a.anac_n_cig >= 50
              AND a.anac_importo_aggiudicato > b.costo_progetto * 3
         THEN true ELSE false END AS flag_ombrello,
    c.coe_n_progetti, c.coe_ciclo, c.coe_finanz_tot_pubblico, c.coe_pagamenti
FROM base b
LEFT JOIN localizzazione l ON b.cup = l.cup
LEFT JOIN fonti f ON b.cup = f.cup
LEFT JOIN pnrr p ON b.cup = p.cup
LEFT JOIN gare g ON b.cup = g.cup
LEFT JOIN anac a ON b.cup = a.cup
LEFT JOIN coesione c ON b.cup = c.cup
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/unified_operas.parquet")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET memory_limit='8GB'")
    con.execute("SET threads=8")

    con.execute(f"COPY ({SQL}) TO '{out}' (FORMAT parquet, COMPRESSION zstd)")
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    n_anagrafe = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{OC_PROGETTI}')"
    ).fetchone()[0]
    print(f"unified: {n:,} CUP su {n_anagrafe:,} anagrafe "
          f"({100 * n / n_anagrafe:.1f}%) -> {out} ({out.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
