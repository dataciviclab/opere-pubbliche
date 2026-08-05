#!/usr/bin/env python3
"""Materializza le view aggregate in parquet — approccio leggero.

NON copia il unified in un .duckdb (inutile e pesante): DuckDB legge il
parquet direttamente con predicate pushdown. Le 6 view restano in
build/views.sql (usabili con la CLI duckdb sul parquet). Qui vengono
materializzate SOLO le view aggregate (poche righe) in parquet per
consumo diretto.

Output: data/views/*.parquet (4 file piccoli)

Uso: python build/materialize_views.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
UNIFIED = REPO_ROOT / "data" / "unified_operas.parquet"
VIEWS_SQL = REPO_ROOT / "build" / "views.sql"
OUT = REPO_ROOT / "data" / "views"

# View aggregate (poche righe) da materializzare in parquet
AGG_VIEWS = (
    "v_sintesi_nazionale",
    "v_stato_avanzamento",
    "v_copertura_fonti",
    "v_analisi_gap",
)


def main() -> None:
    if not UNIFIED.exists():
        raise SystemExit(f"unified non trovato: {UNIFIED} — esegui build/build_unified.py prima")

    OUT.mkdir(parents=True, exist_ok=True)

    # Memory limit basso: le query aggregate leggono solo le colonne
    # necessarie dal parquet (DuckDB fa projection pushdown).
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")
    con.execute("SET threads=4")

    # Crea le view sul parquet (nessuna copia dati)
    sql = VIEWS_SQL.read_text().replace(
        "FROM unified_operas", f"FROM read_parquet('{UNIFIED}')"
    )
    con.execute(sql)

    for v in AGG_VIEWS:
        target = OUT / f"{v}.parquet"
        con.execute(f"COPY (SELECT * FROM {v}) TO '{target}' (FORMAT parquet)")
        print(f"  {v}.parquet ({target.stat().st_size / 1e3:.0f} KB)")

    con.close()
    print("\nfatto: 4 view aggregate materializzate in data/views/ (nessuna copia del unified)")


if __name__ == "__main__":
    main()
