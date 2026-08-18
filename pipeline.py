#!/usr/bin/env python3
"""Pipeline unica opere-pubbliche-intelligence.

Flusso end-to-end (4 fasi, idempotenti):

  step metrics    materializza le metriche Lab per CUP in data/build/
                  (legge TUTTI i dataset Lab direttamente da GCS — bucket
                  pubblici, niente cache locale: zero stale data)
  step layers     cup_fatti (1 riga per CUP, con localizzazione e soggetto)
                  + aggregati comune/regione/settore in data/aggregati/

Gli artefatti intermedi stanno in data/build/ (separati dal codice).
Uso:

  python pipeline.py --step metrics   # quando la fonte Lab è cambiata
  python pipeline.py --step layers    # rebuild mart + aggregati (veloce)
  python pipeline.py                  # metrics + layers
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
from lab_connectors.gcs.paths import https_url

REPO = Path(__file__).resolve().parent
BUILD = REPO / "data" / "build"       # artefatti intermedi (fuori git)
OUT_CUP = REPO / "data" / "cup"
OUT_AGG = REPO / "data" / "aggregati"

# ---- Fonti locali (OpenCUP, scaricate mensilmente da opencup/scripts) ----
OC_PROGETTI = str(REPO / "opencup/data/parquet/opencup_progetti.parquet")
OC_LOCALIZZAZIONE = str(REPO / "opencup/data/parquet/opencup_localizzazione.parquet")
OC_FONTI = str(REPO / "opencup/data/parquet/opencup_fonti_copertura.parquet")

# ---- Fonti Lab su GCS (bucket pubblici, lette direttamente) ----
# Path contract canonico lab-connectors: pattern clean_parquet su bucket clean.
# URL https (letti nativamente da DuckDB, senza httpfs) per stabilità.
LAB_ANAC = https_url("clean", "clean_parquet", slug="anac_appalti_master", year=2026)
LAB_OPENCOESIONE = https_url("clean", "clean_parquet", slug="opencoesione_progetti", year=2026)
LAB_PNRR = https_url("clean", "clean_parquet", slug="pnrr_progetti", year=2026)
LAB_PNRR_GARE = https_url("clean", "clean_parquet", slug="pnrr_gare", year=2026)
LAB_PNRR_PAGAMENTI = https_url("clean", "clean_parquet", slug="pnrr_pagamenti", year=2026)

SMALL_GARE_THRESHOLD = 5_000_000


def _con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(config={"memory_limit": "3GB"})
    con.execute("SET threads=4")
    con.execute("SET temp_directory='/tmp/opencode/duckdb-spill'")
    return con


# ------------------------------------------------------------- step: metrics
def step_metrics(con: duckdb.DuckDBPyConnection) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    specs = {
        "m_pnrr": f"""
            SELECT cup, MAX(missione) AS pnrr_missione,
                   MAX(stato_avanzamento) AS pnrr_stato_avanzamento,
                   MAX(amministrazione_titolare) AS pnrr_amministrazione_titolare,
                   SUM(fin_pnrr) AS pnrr_fin_pnrr, SUM(fin_totale) AS pnrr_fin_totale
            FROM read_parquet('{LAB_PNRR}') WHERE LENGTH(cup)=15 GROUP BY cup""",
        "m_gare": f"""
            SELECT cup, COUNT(*) AS pnrr_n_gare, COUNT(cig) AS pnrr_n_gare_con_cig,
                   SUM(importo_aggiudicazione) AS pnrr_importo_aggiudicato
            FROM read_parquet('{LAB_PNRR_GARE}') GROUP BY cup""",
        "m_pagamenti": f"""
            SELECT cup, SUM(finanziamento_pnrr) AS pag_fin_pnrr,
                   SUM(pagamento_pnrr) AS pag_pagato_pnrr, SUM(pagamento_totale) AS pag_pagato_totale
            FROM read_parquet('{LAB_PNRR_PAGAMENTI}') GROUP BY cup""",
        "m_anac": f"""
            SELECT cup, COUNT(*) AS anac_n_gare, COUNT(cig) AS anac_n_cig,
                   SUM(importo_agg) AS anac_importo_aggiudicato,
                   SUM(CASE WHEN flag_pnrr THEN 1 ELSE 0 END) AS anac_n_gare_pnrr,
                   COUNT(esito_collaudo) AS anac_n_collaudati,
                   COUNT(*) FILTER (WHERE importo_complessivo_gara < {SMALL_GARE_THRESHOLD}) AS anac_n_gare_piccole,
                   SUM(importo_agg) FILTER (WHERE importo_complessivo_gara < {SMALL_GARE_THRESHOLD}) AS anac_importo_gare_piccole,
                   COUNT(*) FILTER (WHERE LEFT(cig,1) = 'B') AS anac_n_cig_b,
                   SUM(importo_agg) FILTER (WHERE LEFT(cig,1) = 'B') AS anac_importo_cig_b
            FROM read_parquet('{LAB_ANAC}')
            WHERE cup IS NOT NULL AND cup NOT IN ('ND','000000000000000','') GROUP BY cup""",
        "m_coesione": f"""
            SELECT "CUP" AS cup, COUNT(DISTINCT "COD_LOCALE_PROGETTO") AS coe_n_progetti,
                   MAX("OC_DESCR_CICLO") AS coe_ciclo, SUM("FINANZ_TOTALE_PUBBLICO") AS coe_finanz_tot_pubblico,
                   SUM("TOT_PAGAMENTI") AS coe_pagamenti
            FROM read_parquet('{LAB_OPENCOESIONE}') GROUP BY 1""",
        "m_localizzazione": f"""
            SELECT "CUP" AS cup, MAX("REGIONE") AS regione, MAX("PROVINCIA") AS provincia,
                   MAX("COMUNE") AS comune, MAX("CODICE_COMUNE") AS codice_comune
            FROM read_parquet('{OC_LOCALIZZAZIONE}') GROUP BY 1""",
        "m_fonti": f"""
            SELECT "CUP" AS cup, COUNT(*) AS n_fonti,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA"='STATALE' THEN 1 ELSE 0 END) AS ha_fonte_statale,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA"='COMUNITARIA' THEN 1 ELSE 0 END) AS ha_fonte_ue,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA"='REGIONALE' THEN 1 ELSE 0 END) AS ha_fonte_regionale,
                   SUM(CASE WHEN "COPERTURA_FINANZIARIA"='PRIVATA' THEN 1 ELSE 0 END) AS ha_fonte_privata
            FROM read_parquet('{OC_FONTI}') GROUP BY 1""",
    }
    for name, sql in specs.items():
        con.execute(f"COPY ({sql}) TO '{BUILD / (name + '.parquet')}' (FORMAT parquet)")
    print(f"metrics: {len(specs)} tabelle per CUP in {BUILD}")


# -------------------------------------------------------------- step: layers
def step_layers(con: duckdb.DuckDBPyConnection) -> None:
    OUT_CUP.mkdir(parents=True, exist_ok=True)
    OUT_AGG.mkdir(parents=True, exist_ok=True)
    def B(n: str) -> str:
        return f"read_parquet('{BUILD / n}.parquet')"

    # cup_fatti: anagrafe snella + metriche Lab + localizzazione + soggetto
    # (unico mart: tutte le domande del catalogo queries/ leggono da qui)
    con.execute(f"""
        COPY (
            SELECT b."CUP" AS cup, b."ANNO_DECISIONE" AS anno_decisione,
                   b."STATO_PROGETTO" AS stato_progetto,
                   TRY_CAST(REPLACE(b."COSTO_PROGETTO", ',', '.') AS DOUBLE) AS costo_progetto,
                   TRY_CAST(REPLACE(b."FINANZIAMENTO_PROGETTO", ',', '.') AS DOUBLE) AS finanziamento_progetto,
                   b."SOGGETTO_TITOLARE" AS soggetto_titolare,
                   b."PIVA_CODFISCALE_SOG_TITOLARE" AS piva_soggetto_titolare,
                   b."NATURA_INTERVENTO" AS natura_intervento,
                   b."TIPOLOGIA_INTERVENTO" AS tipologia_intervento,
                   b."SETTORE_INTERVENTO" AS settore_intervento,
                   b."CATEGORIA_INTERVENTO" AS categoria_intervento,
                   l.regione, l.provincia, l.comune, l.codice_comune,
                   f.n_fonti, f.ha_fonte_statale, f.ha_fonte_ue, f.ha_fonte_regionale, f.ha_fonte_privata,
                   p.pnrr_missione, p.pnrr_stato_avanzamento, p.pnrr_amministrazione_titolare,
                   p.pnrr_fin_pnrr, p.pnrr_fin_totale,
                   g.pnrr_n_gare, g.pnrr_n_gare_con_cig, g.pnrr_importo_aggiudicato,
                   pg.pag_fin_pnrr, pg.pag_pagato_pnrr, pg.pag_pagato_totale,
                   CASE WHEN pg.pag_fin_pnrr IS NOT NULL AND pg.pag_fin_pnrr > 0
                        THEN ROUND(pg.pag_pagato_pnrr / pg.pag_fin_pnrr * 100, 1) ELSE NULL END AS pag_assorbimento_pct,
                   a.anac_n_gare, a.anac_n_cig, a.anac_importo_aggiudicato,
                   a.anac_n_gare_pnrr, a.anac_n_collaudati,
                   a.anac_n_gare_piccole, a.anac_importo_gare_piccole,
                   a.anac_n_cig_b, a.anac_importo_cig_b,
                   CASE WHEN a.anac_n_cig >= 50 AND a.anac_importo_aggiudicato > TRY_CAST(REPLACE(b."COSTO_PROGETTO", ',', '.') AS DOUBLE) * 3
                        THEN true ELSE false END AS flag_ombrello,
                   c.coe_n_progetti, c.coe_finanz_tot_pubblico, c.coe_pagamenti
            FROM read_parquet('{OC_PROGETTI}') b
            LEFT JOIN {B("m_localizzazione")} l ON b."CUP" = l.cup
            LEFT JOIN {B("m_fonti")} f ON b."CUP" = f.cup
            LEFT JOIN {B("m_pnrr")} p ON b."CUP" = p.cup
            LEFT JOIN {B("m_gare")} g ON b."CUP" = g.cup
            LEFT JOIN {B("m_pagamenti")} pg ON b."CUP" = pg.cup
            LEFT JOIN {B("m_anac")} a ON b."CUP" = a.cup
            LEFT JOIN {B("m_coesione")} c ON b."CUP" = c.cup
        ) TO '{OUT_CUP / "cup_fatti.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_CUP / 'cup_fatti.parquet'}')").fetchone()[0]
    print(f"cup_fatti: {n:,} righe ({OUT_CUP / 'cup_fatti.parquet'} — {(OUT_CUP / 'cup_fatti.parquet').stat().st_size / 1e6:.0f} MB)")

    # aggregati da cup_fatti (la localizzazione è già nel mart — nessun join extra)
    base = f"""
        SELECT f.cup, f.costo_progetto, f.pnrr_fin_pnrr AS fin_pnrr, f.pnrr_fin_totale,
               f.flag_ombrello, f.anac_importo_gare_piccole, f.pag_pagato_pnrr,
               f.pnrr_missione, f.coe_n_progetti, f.settore_intervento,
               f.regione, f.provincia, f.comune, f.codice_comune
        FROM read_parquet('{OUT_CUP / 'cup_fatti.parquet'}') f
    """
    con.execute(f"""
        COPY (SELECT comune, codice_comune, regione, provincia, COUNT(*) AS n_cup,
              SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
              SUM(fin_pnrr) AS fin_pnrr, SUM(pnrr_fin_totale) AS fin_totale,
              SUM(anac_importo_gare_piccole) AS anac_importo_gare_piccole,
              SUM(pag_pagato_pnrr) AS pag_pagato_pnrr,
              COUNT(*) FILTER (WHERE pnrr_missione IS NOT NULL) AS n_cup_pnrr,
              COUNT(*) FILTER (WHERE coe_n_progetti IS NOT NULL) AS n_cup_coesione
              FROM ({base})
              WHERE comune IS NOT NULL AND comune NOT IN ('','TUTTI','TUTTI I COMUNI','AMBITO NAZIONALE')
              GROUP BY 1,2,3,4) TO '{OUT_AGG / 'comune.parquet'}' (FORMAT parquet)
    """)
    con.execute(f"""
        COPY (SELECT regione, settore_intervento, COUNT(*) AS n_cup,
              SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
              SUM(fin_pnrr) AS fin_pnrr, SUM(anac_importo_gare_piccole) AS anac_importo_gare_piccole,
              SUM(pag_pagato_pnrr) AS pag_pagato_pnrr
              FROM ({base}) WHERE regione IS NOT NULL AND regione <> '' GROUP BY 1,2)
        TO '{OUT_AGG / 'regione_settore.parquet'}' (FORMAT parquet)
    """)
    con.execute(f"""
        COPY (SELECT settore_intervento, COUNT(*) AS n_cup,
              SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
              SUM(fin_pnrr) AS fin_pnrr, SUM(pag_pagato_pnrr) AS pag_pagato_pnrr
              FROM ({base}) WHERE settore_intervento IS NOT NULL GROUP BY 1)
        TO '{OUT_AGG / 'settore.parquet'}' (FORMAT parquet)
    """)
    for agg in ("comune", "regione_settore", "settore"):
        n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_AGG / (agg + '.parquet')}')").fetchone()[0]
        print(f"aggregato {agg}: {n:,} righe")


STEPS = {"metrics": step_metrics, "layers": step_layers}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=list(STEPS) + ["all"], default="all")
    args = ap.parse_args()

    con = _con()
    steps = list(STEPS) if args.step == "all" else [args.step]
    for s in steps:
        if s in STEPS:
            print(f"\n== step {s} ==")
            STEPS[s](con)
    con.close()


if __name__ == "__main__":
    main()
