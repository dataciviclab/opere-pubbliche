#!/usr/bin/env python3
"""Build a 3 strati — separa il monolite unified in layer per grano.

Motivazione (vedi build/join-cup-anac-rules.md e sessione 2026-08-05):
il unified monolitico (11,86M righe, colonna descrizione ~1,6GB) rende ogni
aggregazione pesante e il CUP-ombrello distorce i totali. Si separa in:

  data/cup/cup_fatti.parquet        grano CUP, snello (senza descrizioni pesanti)
  data/aggregati/comune.parquet     per comune (8k righe)
  data/aggregati/regione_settore.parquet  per regione x settore (231 righe)
  data/aggregati/settore.parquet    per settore (11 righe)
  data/unified_operas.parquet       derivato: join dei layer (su richiesta)

Le metriche ANAC usano le colonne "piccole" (sotto soglia) e flag_ombrello
per non inquinare gli aggregati con i CUP-programma.

Uso: python build/build_layers.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
UNIFIED = REPO_ROOT / "data" / "unified_operas.parquet"
OUT_CUP = REPO_ROOT / "data" / "cup"
OUT_AGG = REPO_ROOT / "data" / "aggregati"

# Soglia importo per "gare piccole" (allineata a build_unified.py)
SMALL_GARE_THRESHOLD = 5_000_000


def main() -> None:
    if not UNIFIED.exists():
        raise SystemExit(f"unified non trovato: {UNIFIED}")

    OUT_CUP.mkdir(parents=True, exist_ok=True)
    OUT_AGG.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    u = f"read_parquet('{UNIFIED}')"

    # ---- Strato 1: cup_fatti (grano CUP, snello) ----
    con.execute(f"""
        COPY (
            SELECT cup, anno_decisione, stato_progetto,
                   costo_progetto, finanziamento_progetto,
                   piva_soggetto_titolare,
                   natura_intervento, tipologia_intervento,
                   settore_intervento, categoria_intervento,
                   n_fonti, ha_fonte_statale, ha_fonte_ue,
                   ha_fonte_regionale, ha_fonte_privata,
                   pnrr_missione, pnrr_stato_avanzamento,
                   pnrr_fin_pnrr, pnrr_fin_totale,
                   pnrr_n_gare, pnrr_importo_aggiudicato,
                   anac_n_cig, anac_importo_gare_piccole,
                   anac_n_gare_piccole, anac_n_collaudati,
                   flag_ombrello,
                   coe_n_progetti, coe_finanz_tot_pubblico, coe_pagamenti
            FROM {u}
        ) TO '{OUT_CUP / "cup_fatti.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_CUP / 'cup_fatti.parquet'}')").fetchone()[0]
    print(f"cup_fatti: {n:,} righe ({ (OUT_CUP/'cup_fatti.parquet').stat().st_size/1e6:.0f} MB)")

    # ---- Strato 2: aggregati ----
    # comune: metriche pulite (solo CUP non-ombrello per gli importi ANAC)
    con.execute(f"""
        COPY (
            SELECT comune, codice_comune, regione, provincia,
                   COUNT(*) AS n_cup,
                   SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
                   SUM(pnrr_fin_pnrr) AS fin_pnrr,
                   SUM(pnrr_fin_totale) AS fin_totale,
                   SUM(CASE WHEN NOT flag_ombrello THEN pnrr_fin_pnrr ELSE 0 END) AS fin_pnrr_pulito,
                   SUM(anac_importo_gare_piccole) AS anac_importo_gare_piccole,
                   COUNT(*) FILTER (WHERE pnrr_missione IS NOT NULL) AS n_cup_pnrr,
                   COUNT(*) FILTER (WHERE coe_n_progetti IS NOT NULL) AS n_cup_coesione
            FROM {u}
            WHERE comune IS NOT NULL AND comune <> '' AND comune <> 'TUTTI'
              AND comune <> 'TUTTI I COMUNI' AND comune <> 'AMBITO NAZIONALE'
            GROUP BY 1,2,3,4
        ) TO '{OUT_AGG / "comune.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_AGG / 'comune.parquet'}')").fetchone()[0]
    print(f"comune: {n:,} righe")

    # regione x settore
    con.execute(f"""
        COPY (
            SELECT regione, settore_intervento,
                   COUNT(*) AS n_cup,
                   SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
                   SUM(pnrr_fin_pnrr) AS fin_pnrr,
                   SUM(anac_importo_gare_piccole) AS anac_importo_gare_piccole
            FROM {u}
            WHERE regione IS NOT NULL AND regione <> ''
            GROUP BY 1,2
        ) TO '{OUT_AGG / "regione_settore.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_AGG / 'regione_settore.parquet'}')").fetchone()[0]
    print(f"regione_settore: {n:,} righe")

    # settore
    con.execute(f"""
        COPY (
            SELECT settore_intervento,
                   COUNT(*) AS n_cup,
                   SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
                   SUM(pnrr_fin_pnrr) AS fin_pnrr
            FROM {u}
            WHERE settore_intervento IS NOT NULL
            GROUP BY 1
        ) TO '{OUT_AGG / "settore.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_AGG / 'settore.parquet'}')").fetchone()[0]
    print(f"settore: {n:,} righe")

    # ---- Strato 3: unified resta come derivato (già esistente) ----
    con.close()
    print("\nstrati generati. unified_operas.parquet resta come derivato su richiesta.")


if __name__ == "__main__":
    main()
