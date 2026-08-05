#!/usr/bin/env python3
"""Refresh leggero dei layer: aggiunge i pagamenti a cup_fatti + rigenera aggregati.

NON tocca il unified_operas (derivato pesante, richiede RAM che questa macchina
non ha). Usa gli intermedi già materializzati (build/_intermediate/m_*.parquet)
con join piccoli per-CUP.

  data/cup/cup_fatti.parquet        <- + pag_fin_pnrr, pag_pagato_pnrr, pag_assorbimento_pct
  data/aggregati/comune.parquet     <- rigenerato (con pagamenti)
  data/aggregati/regione_settore.parquet  <- idem
  data/aggregati/settore.parquet    <- idem

Uso: python build/refresh_layers.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
INTER = REPO / "build" / "_intermediate"
OUT_CUP = REPO / "data" / "cup"
OUT_AGG = REPO / "data" / "aggregati"


def main() -> None:
    if not (INTER / "m_pagamenti.parquet").exists():
        raise SystemExit("intermedi mancanti: esegui build_unified.py step 1 prima")

    OUT_CUP.mkdir(parents=True, exist_ok=True)
    OUT_AGG.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("SET memory_limit='1.5GB'")
    con.execute("SET threads=4")

    # Idempotenza: rimuove eventuali colonne pag_* residue dal cup_fatti
    # (il join le ri-aggiunge senza duplicati a ogni run).
    fatti_path = OUT_CUP / "cup_fatti.parquet"
    fatti_cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{fatti_path}')").fetchall()]
    pag_dups = [c for c in fatti_cols if c.startswith('pag_')]
    if pag_dups:
        clean = [c for c in fatti_cols if not c.startswith('pag_')]
        sel = ", ".join(clean)
        con.execute(f"COPY (SELECT {sel} FROM read_parquet('{fatti_path}')) TO '{fatti_path}' (FORMAT parquet, COMPRESSION zstd)")
        print(f"rimossi {len(pag_dups)} colonne pag_* residue (idempotenza)")

    fatti = f"read_parquet('{fatti_path}')"
    pag = f"read_parquet('{INTER / 'm_pagamenti.parquet'}')"
    loc = f"read_parquet('{INTER / 'm_localizzazione.parquet'}')"

    # ---- 1. cup_fatti + pagamenti (join piccolo su cup) ----
    con.execute(f"""
        COPY (
            SELECT f.*,
                   p.pag_fin_pnrr, p.pag_pagato_pnrr, p.pag_pagato_totale,
                   CASE WHEN p.pag_fin_pnrr IS NOT NULL AND p.pag_fin_pnrr > 0
                        THEN ROUND(p.pag_pagato_pnrr / p.pag_fin_pnrr * 100, 1)
                        ELSE NULL END AS pag_assorbimento_pct
            FROM {fatti} f
            LEFT JOIN {pag} p ON f.cup = p.cup
        ) TO '{OUT_CUP / "cup_fatti.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    print(f"cup_fatti aggiornato ({OUT_CUP / 'cup_fatti.parquet'})")

    # ---- 2. aggregati da cup_fatti + localizzazione (join piccolo) ----
    base = f"""
        SELECT f.cup, f.costo_progetto, f.pnrr_fin_pnrr AS fin_pnrr, f.pnrr_fin_totale,
               f.flag_ombrello, f.anac_importo_gare_piccole,
               f.pag_pagato_pnrr, f.pag_assorbimento_pct,
               f.pnrr_missione, f.coe_n_progetti,
               l.regione, l.provincia, l.comune, l.codice_comune,
               f.settore_intervento
        FROM {fatti} f
        LEFT JOIN {loc} l ON f.cup = l.cup
    """

    con.execute(f"""
        COPY (
            SELECT comune, codice_comune, regione, provincia,
                   COUNT(*) AS n_cup,
                   SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
                   SUM(fin_pnrr) AS fin_pnrr,
                   SUM(pnrr_fin_totale) AS fin_totale,
                   SUM(CASE WHEN NOT flag_ombrello THEN fin_pnrr ELSE 0 END) AS fin_pnrr_pulito,
                   SUM(anac_importo_gare_piccole) AS anac_importo_gare_piccole,
                   SUM(pag_pagato_pnrr) AS pag_pagato_pnrr,
                   COUNT(*) FILTER (WHERE pnrr_missione IS NOT NULL) AS n_cup_pnrr,
                   COUNT(*) FILTER (WHERE coe_n_progetti IS NOT NULL) AS n_cup_coesione
            FROM ({base})
            WHERE comune IS NOT NULL AND comune <> '' AND comune <> 'TUTTI'
              AND comune <> 'TUTTI I COMUNI' AND comune <> 'AMBITO NAZIONALE'
            GROUP BY 1,2,3,4
        ) TO '{OUT_AGG / "comune.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_AGG / 'comune.parquet'}')").fetchone()[0]
    print(f"comune.parquet: {n:,} righe (con pagamenti)")

    con.execute(f"""
        COPY (
            SELECT regione, settore_intervento,
                   COUNT(*) AS n_cup,
                   SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
                   SUM(fin_pnrr) AS fin_pnrr,
                   SUM(anac_importo_gare_piccole) AS anac_importo_gare_piccole,
                   SUM(pag_pagato_pnrr) AS pag_pagato_pnrr
            FROM ({base})
            WHERE regione IS NOT NULL AND regione <> ''
            GROUP BY 1,2
        ) TO '{OUT_AGG / "regione_settore.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_AGG / 'regione_settore.parquet'}')").fetchone()[0]
    print(f"regione_settore.parquet: {n:,} righe")

    con.execute(f"""
        COPY (
            SELECT settore_intervento,
                   COUNT(*) AS n_cup,
                   SUM(CASE WHEN NOT flag_ombrello THEN costo_progetto ELSE 0 END) AS costo_mld_pulito,
                   SUM(fin_pnrr) AS fin_pnrr,
                   SUM(pag_pagato_pnrr) AS pag_pagato_pnrr
            FROM ({base})
            WHERE settore_intervento IS NOT NULL
            GROUP BY 1
        ) TO '{OUT_AGG / "settore.parquet"}' (FORMAT parquet, COMPRESSION zstd)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUT_AGG / 'settore.parquet'}')").fetchone()[0]
    print(f"settore.parquet: {n:,} righe")

    con.close()
    print("\nfatto: cup_fatti con pagamenti + 3 aggregati rigenerati (unified NON toccato)")


if __name__ == "__main__":
    main()
