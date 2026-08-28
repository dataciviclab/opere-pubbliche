#!/usr/bin/env python3
"""Genera cup_fatti: 1 riga per CUP con anagrafe + metriche Lab.

Legge:
- OpenCUP progetti (da out/data/mart/ — prodotto da toolkit run)
- Localizzazione + fonti (da out/data/clean/ — prodotto da toolkit run)
- Metriche ANAC/PNRR/coesione (da data/build/ — prodotto da metriche_anac.py)

Produce:
- data/cup/cup_fatti.parquet (mart unico)
- data/aggregati/comune.parquet, regione_settore.parquet, settore.parquet

Uso: python scripts/cup_fatti.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "out" / "data"
BUILD = REPO / "data" / "build"
OUT_CUP = REPO / "data" / "cup"
OUT_AGG = REPO / "data" / "aggregati"


def _con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(config={"memory_limit": "8GB"})
    con.execute("SET threads=2")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET temp_directory='/tmp/opencode/duckdb-spill'")
    return con


def _mart_path(slug: str) -> str:
    """Trova il parquet mart di un dataset."""
    mart_dir = OUT / "mart" / slug
    if not mart_dir.exists():
        return ""
    years = sorted(mart_dir.iterdir(), reverse=True)
    for y in years:
        files = list(y.glob("*.parquet"))
        if files:
            return str(files[0])
    return ""


def _clean_path(slug: str) -> str:
    """Trova il parquet clean di un dataset."""
    clean_dir = OUT / "clean" / slug
    if not clean_dir.exists():
        return ""
    years = sorted(clean_dir.iterdir(), reverse=True)
    for y in years:
        files = list(y.glob("*.parquet"))
        if files:
            return str(files[0])
    return ""


def build_cup_fatti(con: duckdb.DuckDBPyConnection) -> None:
    OUT_CUP.mkdir(parents=True, exist_ok=True)

    progetti = _mart_path("opencup_progetti")
    localizzazione = _clean_path("opencup_localizzazione")
    fonti = _clean_path("opencup_fonti")

    if not progetti:
        print("ERROR: opencup_progetti mart non trovato. Esegui prima: make run-all")
        sys.exit(1)

    def B(name: str) -> str:
        return f"read_parquet('{BUILD / name}.parquet')"

    def T(path: str) -> str:
        return f"read_parquet('{path}')"

    # Localizzazione: prendi la prima riga per CUP (priorita' Italia)
    loc_sql = f"""
        SELECT cup, regione, provincia, comune, codice_comune
        FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY cup ORDER BY
                CASE WHEN stato = 'ITALIA' THEN 0 ELSE 1 END,
                comune
            ) AS rn
            FROM {T(localizzazione)}
        ) WHERE rn = 1
    """ if localizzazione else "SELECT cup, NULL AS regione, NULL AS provincia, NULL AS comune, NULL AS codice_comune FROM (SELECT DISTINCT cup FROM read_parquet('" + progetti + "'))"

    # Fonti: aggrega per CUP
    fonti_sql = f"""
        SELECT cup,
               COUNT(*) AS n_fonti,
               SUM(CASE WHEN copertura_finanziaria = 'STATALE' THEN 1 ELSE 0 END) AS ha_fonte_statale,
               SUM(CASE WHEN copertura_finanziaria = 'COMUNITARIA' THEN 1 ELSE 0 END) AS ha_fonte_ue,
               SUM(CASE WHEN copertura_finanziaria = 'REGIONALE' THEN 1 ELSE 0 END) AS ha_fonte_regionale,
               SUM(CASE WHEN copertura_finanziaria = 'PRIVATA' THEN 1 ELSE 0 END) AS ha_fonte_privata
        FROM {T(fonti)} GROUP BY 1
    """ if fonti else "SELECT cup, 0 AS n_fonti, FALSE AS ha_fonte_statale, FALSE AS ha_fonte_ue, FALSE AS ha_fonte_regionale, FALSE AS ha_fonte_privata FROM (SELECT DISTINCT cup FROM read_parquet('" + progetti + "'))"

    con.execute(f"""
        COPY (
            SELECT p.cup, p.anno_decisione, p.stato_progetto,
                   p.costo_progetto, p.finanziamento_progetto,
                   p.soggetto_titolare, p.piva_soggetto_titolare,
                   p.natura_intervento, p.tipologia_intervento,
                   p.settore_intervento, p.categoria_intervento,
                   p.codice_settore, p.codice_categoria,
                   p.descrizione_intervento, p.codice_locale_progetto,
                   l.regione, l.provincia, l.comune, l.codice_comune,
                   f.n_fonti, f.ha_fonte_statale, f.ha_fonte_ue,
                   f.ha_fonte_regionale, f.ha_fonte_privata,
                   pnrr.pnrr_missione, pnrr.pnrr_stato_avanzamento,
                   pnrr.pnrr_amministrazione_titolare,
                   pnrr.pnrr_fin_pnrr, pnrr.pnrr_fin_totale,
                   g.pnrr_n_gare, g.pnrr_n_gare_con_cig, g.pnrr_importo_aggiudicato,
                   pg.pag_fin_pnrr, pg.pag_pagato_pnrr, pg.pag_pagato_totale,
                   CASE WHEN pg.pag_fin_pnrr IS NOT NULL AND pg.pag_fin_pnrr > 0
                        THEN ROUND(pg.pag_pagato_pnrr / pg.pag_fin_pnrr * 100, 1)
                        ELSE NULL END AS pag_assorbimento_pct,
                   a.anac_n_gare, a.anac_n_cig, a.anac_importo_aggiudicato,
                   a.anac_n_gare_pnrr, a.anac_n_collaudati,
                   a.anac_n_gare_piccole, a.anac_importo_gare_piccole,
                   a.anac_n_cig_b, a.anac_importo_cig_b,
                   CASE WHEN a.anac_n_cig >= 50
                             AND a.anac_importo_aggiudicato > p.costo_progetto * 3
                        THEN true ELSE false END AS flag_ombrello,
                   c.coe_n_progetti, c.coe_finanz_tot_pubblico, c.coe_pagamenti
            FROM {T(progetti)} p
            LEFT JOIN ({loc_sql}) l ON p.cup = l.cup
            LEFT JOIN ({fonti_sql}) f ON p.cup = f.cup
            LEFT JOIN {B("m_pnrr")} pnrr ON p.cup = pnrr.cup
            LEFT JOIN {B("m_gare")} g ON p.cup = g.cup
            LEFT JOIN {B("m_pagamenti")} pg ON p.cup = pg.cup
            LEFT JOIN {B("m_anac")} a ON p.cup = a.cup
            LEFT JOIN {B("m_coesione")} c ON p.cup = c.cup
        ) TO '{OUT_CUP / "cup_fatti.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_CUP / 'cup_fatti.parquet'}')").fetchone()[0]
    print(f"cup_fatti: {n:,} righe ({OUT_CUP / 'cup_fatti.parquet'})")


def build_aggregati(con: duckdb.DuckDBPyConnection) -> None:
    OUT_AGG.mkdir(parents=True, exist_ok=True)

    base = f"""
        SELECT cup, costo_progetto, pnrr_fin_pnrr AS fin_pnrr, pnrr_fin_totale,
               flag_ombrello, anac_importo_gare_piccole, pag_pagato_pnrr,
               pnrr_missione, coe_n_progetti, settore_intervento,
               regione, provincia, comune, codice_comune
        FROM read_parquet('{OUT_CUP / 'cup_fatti.parquet'}')
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
        print(f"  aggregato {agg}: {n:,} righe")


def main() -> None:
    print("== step layers ==")
    con = _con()
    build_cup_fatti(con)
    build_aggregati(con)
    con.close()
    print("\nlayers completati.")


if __name__ == "__main__":
    main()
