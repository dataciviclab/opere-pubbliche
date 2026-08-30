"""Smoke test OPI — protegge il contratto del mart e del catalogo query.

Verifica che il flusso end-to-end sia integro senza eseguire la pipeline:
- cup_fatti (mart) esiste con le colonne contrattuali e i conteggi attesi;
- le query del catalogo (queries/) eseguono sugli artefatti giusti;
- i numeri chiave del panorama sono stabili.

Marker: smoke

Uso:
  python3 -m pytest tests/ -v
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

REPO = Path(__file__).resolve().parent.parent
QUERIES = REPO / "queries"
CUP = REPO / "data" / "cup" / "cup_fatti.parquet"
AGG = REPO / "data" / "aggregati"

# Colonne contrattuali: se cambiano, aggiorna qui e in docs/data_dictionary.md.
REQUIRED_COLUMNS = {
    "cup", "regione", "comune", "soggetto_titolare", "stato_progetto",
    "costo_progetto", "pnrr_missione", "pnrr_fin_pnrr", "anac_n_cig",
    "anac_n_gare_piccole", "anac_n_collaudati", "flag_ombrello",
    "anac_n_cig_b", "anac_importo_cig_b",
}


@pytest.mark.smoke
def test_smoke() -> None:
    """smoke: golden path end-to-end del mart e del catalogo."""
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")

    # ---- 1. Mart: esiste e ha le colonne contrattuali ----
    assert CUP.exists(), (
        "cup_fatti.parquet mancante — esegui: make layers"
    )
    cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{CUP}')").fetchall()}
    missing = REQUIRED_COLUMNS - cols
    assert not missing, f"colonne contrattuali mancanti: {sorted(missing)}"
    n_cup = con.execute(f"SELECT COUNT(*) FROM read_parquet('{CUP}')").fetchone()[0]
    assert n_cup >= 11_000_000, f"n_cup >= 11M (reale: {n_cup:,})"

    # ---- 2. Catalogo query: leggono gli artefatti giusti ed eseguono ----
    for q in sorted(QUERIES.glob("*.sql")):
        sql = q.read_text()
        assert "unified_operas" not in sql, f"{q.name}: non deve usare unified_operas"
        con.execute(sql).fetchall()

    # ---- 3. Numeri chiave stabili (coerenza mart vs aggregati) ----
    totali = con.execute(f"""
        SELECT COUNT(*), SUM(CASE WHEN anac_n_cig > 0 AND NOT flag_ombrello THEN 1 ELSE 0 END)
        FROM read_parquet('{CUP}')
    """).fetchone()
    assert totali[0] == n_cup, "COUNT mart stabile"
    assert totali[1] >= 600_000, f"CUP con gara ANAC >= 600k (reale: {totali[1]:,})"
    n_comuni = con.execute(f"SELECT COUNT(*) FROM read_parquet('{AGG / 'comune.parquet'}')").fetchone()[0]
    assert n_comuni >= 8_000, f"n_comuni >= 8000 (reale: {n_comuni:,})"

    con.close()
