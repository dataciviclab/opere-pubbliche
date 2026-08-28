"""Materializza le metriche Lab per CUP in data/build/.

Legge i clean parquet da GCS (bucket pubblici, zero stale data) e produce
tabelle aggregate per CUP in data/build/. Da eseguire quando la fonte Lab
cambia (refresh mensile) o per rebuild deliberato.

Uso: python scripts/metriche_anac.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / "data" / "build"

# ---- Fonti Lab su GCS (bucket pubblici, letti direttamente) ----
try:
    from lab_connectors.gcs.paths import https_url
except ImportError:
    print("lab-connectors non installato. Esegui: pip install -e '.[pipeline]'")
    sys.exit(1)

LAB_ANAC = https_url("clean", "clean_parquet", slug="anac_appalti_master", year=2026)
LAB_PNRR = https_url("clean", "clean_parquet", slug="pnrr_progetti", year=2026)
LAB_PNRR_GARE = https_url("clean", "clean_parquet", slug="pnrr_gare", year=2026)
LAB_PNRR_PAGAMENTI = https_url("clean", "clean_parquet", slug="pnrr_pagamenti", year=2026)
LAB_OPENCOESIONE = https_url("clean", "clean_parquet", slug="opencoesione_progetti", year=2026)

SMALL_GARE_THRESHOLD = 5_000_000


def _con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(config={"memory_limit": "3GB"})
    con.execute("SET threads=2")
    con.execute("SET temp_directory='/tmp/opencode/duckdb-spill'")
    return con


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
    }

    for name, sql in specs.items():
        out = BUILD / f"{name}.parquet"
        con.execute(f"COPY ({sql}) TO '{out}' (FORMAT parquet)")
        n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
        print(f"  {name}: {n:,} righe → {out.name}")


def main() -> None:
    print("== step metrics ==")
    con = _con()
    step_metrics(con)
    con.close()
    print(f"\nmetrics: {len(list(BUILD.glob('*.parquet')))} tabelle in {BUILD}")


if __name__ == "__main__":
    main()
