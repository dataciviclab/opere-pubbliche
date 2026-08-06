#!/usr/bin/env python3
"""Smoke test OPI — protegge il contratto del mart e del catalogo query.

Verifica che il flusso end-to-end sia integro senza eseguire la pipeline:
- cup_fatti (mart) esiste con le colonne contrattuali e i conteggi attesi;
- le 7 query del catalogo (queries/) eseguono sugli artefatti giusti;
- i numeri chiave del panorama sono stabili.

Marker: smoke

Uso: python3 test_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parent
QUERIES = REPO / "queries"
CUP = REPO / "data" / "cup" / "cup_fatti.parquet"
AGG = REPO / "data" / "aggregati"


def check(cond: bool, msg: str) -> None:
    status = "ok" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        sys.exit(1)


def main() -> None:
    print("OPI smoke test")
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")

    # ---- 1. Mart: esiste e ha le colonne contrattuali ----
    print("\n1. mart data/cup/cup_fatti.parquet")
    if not CUP.exists():
        check(False, "cup_fatti.parquet mancante — esegui: python pipeline.py --step layers")
    cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{CUP}')").fetchall()}
    required = {"cup", "regione", "comune", "soggetto_titolare", "stato_progetto",
                "costo_progetto", "pnrr_missione", "pnrr_fin_pnrr", "anac_n_cig",
                "anac_n_gare_piccole", "anac_n_collaudati", "flag_ombrello"}
    missing = required - cols
    check(not missing, f"colonne contrattuali presenti (mancano: {sorted(missing) or 'nessuna'})")
    n_cup = con.execute(f"SELECT COUNT(*) FROM read_parquet('{CUP}')").fetchone()[0]
    check(n_cup >= 11_000_000, f"n_cup >= 11M (reale: {n_cup:,})")

    # ---- 2. Catalog query eseguono sugli artefatti giusti ----
    print("\n2. queries/ catalogo (7 domande)")
    # Le query non devono più puntare al monolite eliminato
    for q in sorted(QUERIES.glob("*.sql")):
        sql = q.read_text()
        check("unified_operas" not in sql, f"{q.name}: non usa unified_operas")
    for q in sorted(QUERIES.glob("*.sql")):
        try:
            con.execute(q.read_text()).fetchall()
            print(f"  [ok] {q.name} esegue")
        except Exception as e:  # noqa: BLE001
            check(False, f"{q.name} fallisce: {e}")

    # ---- 3. Numeri chiave stabili (coerenza mart vs aggregati) ----
    print("\n3. coerenza numeri chiave")
    totali = con.execute(f"""
        SELECT COUNT(*), SUM(CASE WHEN anac_n_cig > 0 AND NOT flag_ombrello THEN 1 ELSE 0 END)
        FROM read_parquet('{CUP}')
    """).fetchone()
    check(totali[0] == n_cup, "COUNT mart stabile")
    check(totali[1] >= 600_000, f"CUP con gara ANAC >= 600k (reale: {totali[1]:,})")
    n_comuni = con.execute(f"SELECT COUNT(*) FROM read_parquet('{AGG / 'comune.parquet'}')").fetchone()[0]
    check(n_comuni >= 8_000, f"n_comuni >= 8000 (reale: {n_comuni:,})")

    # ---- 4. Scheda opera (query 08) — il contratto del forum ----
    print("\n4. scheda opera (queries/08_scheda_opera.sql)")
    q08 = (REPO / "queries" / "08_scheda_opera.sql")
    check(q08.exists(), "08_scheda_opera.sql presente nel catalogo")
    if q08.exists():
        sql = q08.read_text().replace("{cup}", "F81H92000000008")
        row = con.execute(sql).fetchone()
        check(row is not None, "scheda Terzo Valico risolve (F81H92000000008)")
        if row is not None:
            cols = [c[0] for c in con.description]
            d = dict(zip(cols, row))
            check(d.get("pnrr_missione") is not None, "scheda contiene missione PNRR (M3)")
            check((d.get("n_gare_anac") or 0) > 50, f"scheda contiene gare ANAC (reale: {d.get('n_gare_anac')})")
    con.close()
    print("\nOK — smoke test superato")


if __name__ == "__main__":
    main()
