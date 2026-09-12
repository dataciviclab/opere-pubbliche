"""Smoke test OPI — protegge il contratto del compose op-cup-lab.

Verifica che il clean del compose esista con le colonne contrattuali
e i conteggi attesi.

Marker: smoke
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

REPO = Path(__file__).resolve().parent.parent
CLEAN = REPO / "out" / "data" / "clean" / "op_cup_lab" / "2026" / "op_cup_lab_2026_clean.parquet"

# Colonne contrattuali minime del clean compose
REQUIRED_COLUMNS = {
    "cup", "regione", "comune", "soggetto_titolare", "stato_progetto",
    "costo_progetto", "settore_intervento", "area",
    "anac_n_cig", "anac_n_gare", "anac_importo_aggiudicato",
    "pnrr_fin_pnrr", "pnrr_missione",
    "coe_n_progetti", "flag_ombrello",
    "con_almeno_una_fonte_lab", "n_fonti_lab",
    "silos_costi_mln", "silos_macro_stato",
}


@pytest.mark.smoke
def test_smoke() -> None:
    """smoke: clean compose esiste e ha le colonne contrattuali."""
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")

    assert CLEAN.exists(), (
        "op_cup_lab clean mancante — esegui: TOOLKIT_ALLOW_SCRIPT_SOURCE=1 toolkit run --config compose/op-cup-lab/dataset.yml"
    )

    cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{CLEAN}')").fetchall()}
    missing = REQUIRED_COLUMNS - cols
    assert not missing, f"colonne contrattuali mancanti: {sorted(missing)}"

    n_cup = con.execute(f"SELECT COUNT(*) FROM read_parquet('{CLEAN}')").fetchone()[0]
    assert n_cup >= 11_000_000, f"n_cup >= 11M (reale: {n_cup:,})"

    # Copertura Lab minima
    r = con.execute(f"""
        SELECT SUM(con_almeno_una_fonte_lab), SUM(CASE WHEN silos_costi_mln IS NOT NULL THEN 1 ELSE 0 END)
        FROM read_parquet('{CLEAN}')
    """).fetchone()
    assert r[0] >= 2_500_000, f"copertura Lab >= 2.5M (reale: {r[0]:,})"
    assert r[1] >= 1_000, f"SILOS >= 1k CUP (reale: {r[1]:,})"

    con.close()
