#!/usr/bin/env python3
"""Build unified — profilo per CUP (1 riga per CUP), 2 step con materializzazione.

Unisce OpenCup (anagrafe universale) con i dataset del Lab:
  OpenCup progetti + localizzazione + fonti copertura
  + Lab: pnrr_progetti, pnrr_gare, pnrr_pagamenti, anac (appalti), opencoesione

Grano: 1 riga per CUP. Le metriche dei sottoinsiemi Lab sono aggregate
(n_*, tot_*). Output: data/unified_operas.parquet (fuori git).

Perché 2 step: il join diretto OpenCup (11,86M) × anac (6M) esaurisce la RAM
di macchine piccole. Step 1 materializza le metriche Lab aggregate per CUP
(tabelle piccole), step 2 le join con l'anagrafe. Memory limit basso.

Uso: python build/build_unified.py [--out data/unified_operas.parquet]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD = REPO_ROOT / "build" / "_intermediate"
UNIFIED = REPO_ROOT / "data" / "unified_operas.parquet"

# Path fonti (allineati a build/join_map.yaml)
OC_PROGETTI = str(REPO_ROOT / "opencup/data/parquet/opencup_progetti.parquet")
OC_LOCALIZZAZIONE = str(REPO_ROOT / "opencup/data/parquet/opencup_localizzazione.parquet")
OC_FONTI = str(REPO_ROOT / "opencup/data/parquet/opencup_fonti_copertura.parquet")

LAB_PNRR = "gs://dataciviclab-clean/pnrr_progetti/2026/pnrr_progetti_2026_clean.parquet"
LAB_PNRR_GARE = "gs://dataciviclab-clean/pnrr_gare/2026/pnrr_gare_2026_clean.parquet"
LAB_PNRR_PAGAMENTI = "gs://dataciviclab-clean/pnrr_pagamenti/2026/pnrr_pagamenti_2026_clean.parquet"
LAB_ANAC = "gs://dataciviclab-clean/anac_appalti_master/2026/anac_appalti_master_2026_clean.parquet"
LAB_OPENCOESIONE = "gs://dataciviclab-clean/opencoesione_progetti/2026/opencoesione_progetti_2026_clean.parquet"


def _resolve(path_key: str) -> str:
    """Cache-first: usa data/cache/ se il file esiste, altrimenti GCS.

    Il layer clean del Lab su GCS è grande (anac_appalti_master 674MB):
    leggerlo a ogni build costa egress GCS e tempo. Scaricato una volta in
    data/cache/ (vedi build/cache_lab.py), il build usa il locale.
    """
    cache = {
        "anac": "data/cache/anac_appalti_master_2026_clean.parquet",
        "opencoesione": "data/cache/opencoesione_progetti_2026_clean.parquet",
    }
    p = Path(cache.get(path_key, ""))
    if p.exists():
        return str(p)
    return {"anac": LAB_ANAC, "opencoesione": LAB_OPENCOESIONE}[path_key]

# Soglia per "gare piccole" (CIG sotto soglia = metriche affidabili, non ombrello)
SMALL_GARE_THRESHOLD = 5_000_000


def _step_lab_metrics(con: duckdb.DuckDBPyConnection) -> None:
    """Step 1: materializza le metriche Lab aggregate per CUP (tabelle piccole)."""
    BUILD.mkdir(parents=True, exist_ok=True)

    con.execute(f"""
        COPY (
            SELECT "CUP" AS cup, MAX("REGIONE") AS regione, MAX("PROVINCIA") AS provincia,
                   MAX("COMUNE") AS comune, MAX("CODICE_COMUNE") AS codice_comune
            FROM read_parquet('{OC_LOCALIZZAZIONE}') GROUP BY 1
        ) TO '{BUILD / "m_localizzazione.parquet"}' (FORMAT parquet)
    """)

    con.execute(f"""
        COPY (
            SELECT "CUP" AS cup, COUNT(*) AS n_fonti,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'STATALE' THEN 1 ELSE 0 END) AS ha_fonte_statale,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'COMUNITARIA' THEN 1 ELSE 0 END) AS ha_fonte_ue,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'REGIONALE' THEN 1 ELSE 0 END) AS ha_fonte_regionale,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA" = 'PRIVATA' THEN 1 ELSE 0 END) AS ha_fonte_privata
            FROM read_parquet('{OC_FONTI}') GROUP BY 1
        ) TO '{BUILD / "m_fonti.parquet"}' (FORMAT parquet)
    """)

    con.execute(f"""
        COPY (
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
        ) TO '{BUILD / "m_pnrr.parquet"}' (FORMAT parquet)
    """)

    con.execute(f"""
        COPY (
            SELECT cup,
                   COUNT(*) AS pnrr_n_gare,
                   COUNT(cig) AS pnrr_n_gare_con_cig,
                   SUM(importo_aggiudicazione) AS pnrr_importo_aggiudicato
            FROM read_parquet('{LAB_PNRR_GARE}')
            GROUP BY cup
        ) TO '{BUILD / "m_gare.parquet"}' (FORMAT parquet)
    """)

    con.execute(f"""
        COPY (
            SELECT cup,
                   SUM(finanziamento_pnrr) AS pag_fin_pnrr,
                   SUM(pagamento_pnrr) AS pag_pagato_pnrr,
                   SUM(pagamento_totale) AS pag_pagato_totale
            FROM read_parquet('{LAB_PNRR_PAGAMENTI}')
            GROUP BY cup
        ) TO '{BUILD / "m_pagamenti.parquet"}' (FORMAT parquet)
    """)

    con.execute(f"""
        COPY (
            SELECT cup,
                   COUNT(*) AS anac_n_gare,
                   COUNT(cig) AS anac_n_cig,
                   SUM(importo_agg) AS anac_importo_aggiudicato,
                   SUM(CASE WHEN flag_pnrr THEN 1 ELSE 0 END) AS anac_n_gare_pnrr,
                   COUNT(esito_collaudo) AS anac_n_collaudati,
                   COUNT(*) FILTER (WHERE importo_complessivo_gara < {SMALL_GARE_THRESHOLD}) AS anac_n_gare_piccole,
                   SUM(importo_agg) FILTER (WHERE importo_complessivo_gara < {SMALL_GARE_THRESHOLD}) AS anac_importo_gare_piccole
            FROM read_parquet('{_resolve("anac")}')
            WHERE cup IS NOT NULL
              AND cup NOT IN ('ND', '000000000000000', '')
            GROUP BY cup
        ) TO '{BUILD / "m_anac.parquet"}' (FORMAT parquet)
    """)

    con.execute(f"""
        COPY (
            SELECT "CUP" AS cup,
                   COUNT(DISTINCT "COD_LOCALE_PROGETTO") AS coe_n_progetti,
                   MAX("OC_DESCR_CICLO") AS coe_ciclo,
                   SUM("FINANZ_TOTALE_PUBBLICO") AS coe_finanz_tot_pubblico,
                   SUM("TOT_PAGAMENTI") AS coe_pagamenti
            FROM read_parquet('{_resolve("opencoesione")}')
            GROUP BY 1
        ) TO '{BUILD / "m_coesione.parquet"}' (FORMAT parquet)
    """)
    print("step 1: metriche materializzate (7 tabelle per CUP: loc, fonti, pnrr, gare, pag, anac, coesione)")


def _step_join(con: duckdb.DuckDBPyConnection, out: Path) -> None:
    """Step 2: join anagrafe OpenCup con le metriche Lab (per CUP)."""
    b = BUILD

    con.execute(f"""
        COPY (
            SELECT b.cup,
                   b.descrizione, b.anno_decisione, b.stato_progetto,
                   b.costo_progetto, b.finanziamento_progetto,
                   b.soggetto_titolare, b.piva_soggetto_titolare,
                   b.natura_intervento, b.tipologia_intervento,
                   b.settore_intervento, b.categoria_intervento,
                   l.regione, l.provincia, l.comune, l.codice_comune,
                   f.n_fonti, f.ha_fonte_statale, f.ha_fonte_ue,
                   f.ha_fonte_regionale, f.ha_fonte_privata,
                   p.pnrr_missione, p.pnrr_stato_avanzamento, p.pnrr_amministrazione_titolare,
                   p.pnrr_fin_pnrr, p.pnrr_fin_totale,
                   g.pnrr_n_gare, g.pnrr_n_gare_con_cig, g.pnrr_importo_aggiudicato,
                   pg.pag_fin_pnrr, pg.pag_pagato_pnrr, pg.pag_pagato_totale,
                   CASE WHEN pg.pag_fin_pnrr IS NOT NULL AND pg.pag_fin_pnrr > 0
                        THEN ROUND(pg.pag_pagato_pnrr / pg.pag_fin_pnrr * 100, 1)
                        ELSE NULL END AS pag_assorbimento_pct,
                   a.anac_n_gare, a.anac_n_cig, a.anac_importo_aggiudicato,
                   a.anac_n_gare_pnrr, a.anac_n_collaudati,
                   a.anac_n_gare_piccole, a.anac_importo_gare_piccole,
                   CASE WHEN a.anac_n_cig >= 50
                             AND a.anac_importo_aggiudicato > b.costo_progetto * 3
                        THEN true ELSE false END AS flag_ombrello,
                   c.coe_n_progetti, c.coe_ciclo,
                   c.coe_finanz_tot_pubblico, c.coe_pagamenti
            FROM (
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
                       "CATEGORIA_INTERVENTO" AS categoria_intervento
                FROM read_parquet('{OC_PROGETTI}')
            ) b
            LEFT JOIN read_parquet('{b / "m_localizzazione.parquet"}') l ON b.cup = l.cup
            LEFT JOIN read_parquet('{b / "m_fonti.parquet"}') f ON b.cup = f.cup
            LEFT JOIN read_parquet('{b / "m_pnrr.parquet"}') p ON b.cup = p.cup
            LEFT JOIN read_parquet('{b / "m_gare.parquet"}') g ON b.cup = g.cup
            LEFT JOIN read_parquet('{b / "m_pagamenti.parquet"}') pg ON b.cup = pg.cup
            LEFT JOIN read_parquet('{b / "m_anac.parquet"}') a ON b.cup = a.cup
            LEFT JOIN read_parquet('{b / "m_coesione.parquet"}') c ON b.cup = c.cup
        ) TO '{out}' (FORMAT parquet, COMPRESSION zstd)
    """)
    print(f"step 2: unified scritto -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/unified_operas.parquet")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    # Memory limit basso + spill: funziona anche su macchine piccole (5,8GB)
    con.execute("SET memory_limit='1GB'")
    con.execute("SET threads=4")
    con.execute("SET temp_directory='/tmp/opencode/duckdb-spill'")

    _step_lab_metrics(con)
    _step_join(con, out)

    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    n_anagrafe = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OC_PROGETTI}')").fetchone()[0]
    print(f"unified: {n:,} CUP su {n_anagrafe:,} anagrafe ({100 * n / n_anagrafe:.1f}%) "
          f"-> {out} ({out.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
