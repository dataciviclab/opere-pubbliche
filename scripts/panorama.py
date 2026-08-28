#!/usr/bin/env python3
"""Panorama opere pubbliche — deliverable in data/reporting/ (md + json).

Legge gli aggregati (data/aggregati/) e serializza i numeri chiave.
Output:
  data/reporting/panorama.md
  data/reporting/panorama.json

Uso: make panorama  (o python3 scripts/panorama.py)
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parent.parent
AGG = REPO / "data" / "aggregati"
OUT = REPO / "data" / "reporting"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")

    # Sintesi nazionale
    s = con.execute(f"""
        SELECT SUM(n_cup), SUM(costo_mld_pulito), SUM(fin_pnrr)
        FROM read_parquet('{AGG / 'settore.parquet'}')
    """).fetchone()
    # Aree
    areas = con.execute(f"""
        SELECT CASE WHEN regione IN ('LOMBARDIA','PIEMONTE','VENETO','EMILIA-ROMAGNA','LIGURIA',
                                    'FRIULI-VENEZIA GIULIA','TRENTINO-ALTO ADIGE','VALLE D''AOSTA')
                          THEN 'NORD'
                    WHEN regione IN ('TOSCANA','UMBRIA','MARCHE','LAZIO') THEN 'CENTRO'
                    ELSE 'SUD+ISOLE' END area,
               SUM(n_cup), SUM(costo_mld_pulito), SUM(fin_pnrr)
        FROM read_parquet('{AGG / 'regione_settore.parquet'}')
        GROUP BY 1 ORDER BY 2 DESC
    """).fetchall()
    # Settori top
    settori = con.execute(f"""
        SELECT settore_intervento, SUM(costo_mld_pulito), SUM(fin_pnrr)
        FROM read_parquet('{AGG / 'settore.parquet'}')
        GROUP BY 1 ORDER BY 2 DESC LIMIT 6
    """).fetchall()
    # Comuni top
    comuni = con.execute(f"""
        SELECT comune, regione, SUM(costo_mld_pulito)
        FROM read_parquet('{AGG / 'comune.parquet'}')
        GROUP BY 1,2 ORDER BY 3 DESC LIMIT 5
    """).fetchall()

    data = {
        "n_cup": int(s[0]),
        "costo_mld": round(s[1] / 1e9, 1),
        "pnrr_mld": round(s[2] / 1e9, 1),
        "pnrr_pct_costo": round(s[2] / s[1] * 100, 2) if s[1] else None,
        "aree": [
            {"area": a[0], "n_cup": int(a[1]), "costo_mld": round(a[2] / 1e9, 1),
             "pnrr_mld": round(a[3] / 1e9, 1),
             "pnrr_pct": round(a[3] / a[2] * 100, 2) if a[2] else None}
            for a in areas
        ],
        "settori_top": [
            {"settore": x[0], "costo_mld": round(x[1] / 1e9, 1), "pnrr_mld": round(x[2] / 1e9, 1)}
            for x in settori
        ],
        "comuni_top": [
            {"comune": x[0], "regione": x[1], "costo_mld": round(x[2] / 1e9, 1)}
            for x in comuni
        ],
    }

    md = f"""# Panorama opere pubbliche Italia

**{data['n_cup']:,} CUP** | **€{data['costo_mld']:.1f} mld** costo | **€{data['pnrr_mld']:.1f} mld** PNRR ({data['pnrr_pct_costo']}% del costo)

## Aree
| Area | CUP | Costo (mld) | PNRR (mld) | PNRR/costo |
|---|---|---|---|---|
"""
    for a in data["aree"]:
        md += f"| {a['area']} | {a['n_cup']:,} | €{a['costo_mld']:.1f} | €{a['pnrr_mld']:.1f} | {a['pnrr_pct']:.2f}% |\n"

    md += "\n## Top settori (costo)\n| Settore | Costo (mld) | PNRR (mld) |\n|---|---|---|\n"
    for x in data["settori_top"]:
        md += f"| {x['settore']} | €{x['costo_mld']:.1f} | €{x['pnrr_mld']:.1f} |\n"

    md += "\n## Top comuni (costo)\n| Comune | Regione | Costo (mld) |\n|---|---|---|\n"
    for x in data["comuni_top"]:
        md += f"| {x['comune']} | {x['regione']} | €{x['costo_mld']:.1f} |\n"

    (OUT / "panorama.md").write_text(md)
    (OUT / "panorama.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"panorama scritto in {OUT} ({OUT / 'panorama.md'} + .json)")


if __name__ == "__main__":
    main()
