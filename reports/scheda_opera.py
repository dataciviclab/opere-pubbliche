#!/usr/bin/env python3
"""Genera la scheda markdown di un'opera dal catalogo queries/08_scheda_opera.sql.

Uso:
    python3 reports/scheda_opera.py F81H92000000008          # 1 opera → data/reporting/schede/
    python3 reports/scheda_opera.py --all                    # tutte le schede in config SEED

Le schede sono pensate per il forum (1 discussione = 1 opera): numeri dal mart,
formato compatto, niente fronzoli. Output: data/reporting/schede/{cup}.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
QUERY = REPO / "queries" / "08_scheda_opera.sql"
OUT = REPO / "data" / "reporting" / "schede"

# Opere-icona del seed forum (CUP, nome leggibile)
SEED = [
    ("F81H92000000008", "Terzo Valico dei Giovi"),
    ("D51B02000050001", "Sistema MO.S.E. (Venezia)"),
    ("F11B06000270007", "Pedemontana Lombarda"),
    ("J11H03000180001", "Palermo-Catania — nuova linea"),
    ("C11J05000030001", "Torino-Lione (TELT)"),
]


def fmt_mld(v) -> str:
    return f"{v:.1f}" if v is not None else "n.d."


def fmt_int(v) -> str:
    """Intero senza decimali (es. gare, collaudi), robusto a float/None."""
    if v is None:
        return "0"
    return f"{int(v):,}".replace(",", ".")


def fmt_loc(comune: str | None, provincia: str | None, regione: str | None) -> str:
    """Localizzazione leggibile: i placeholder 'TUTTI'/'TUTTE'/'AMBITO NAZIONALE' indicano
    opere multi-localizzazione (es. Terzo Valico, Ponte) — non un comune singolo."""
    if not comune or comune in ("TUTTI", "TUTTI I COMUNI", "AMBITO NAZIONALE", ""):
        return f"{regione or '—'} (opera multi-localizzazione)"
    return f"{comune} ({provincia or '—'}, {regione or '—'})"


def scheda(con: duckdb.DuckDBPyConnection, cup: str, nome: str | None = None) -> str:
    sql = QUERY.read_text().replace("{cup}", cup)
    row = con.execute(sql).fetchone()
    if row is None:
        raise SystemExit(f"CUP {cup}: nessuna riga nel mart — verifica il codice")
    cols = [c[0] for c in con.description]

    r = dict(zip(cols, row))
    opera = nome or (r["opera"] or r["cup"])

    md = [f"# {opera}", ""]
    md += [f"**CUP**: `{r['cup']}` | **Soggetto titolare**: {r['soggetto_titolare'] or 'n.d.'}", ""]
    md += ["| Dato | Valore |", "|---|---|"]
    md += [f"| Stato | {r['stato_progetto'] or 'n.d.'} |"]
    md += [f"| Anno decisione | {r['anno_decisione'] or 'n.d.'} |"]
    md += [f"| Sistema | {r['sistema'] or 'n.d.'} |"]
    md += [f"| Soggetto competente (SILOS) | {r['soggetto_competente'] or 'n.d.'} |"]
    md += ["", "## Costi", "", "| Prospettiva | Valore |", "|---|---|"]
    md += [f"| Costo anagrafe OpenCUP | €{fmt_mld(r['costo_anagrafe_mld'])} mld |"]
    md += [f"| Finanziamento dichiarato | €{fmt_mld(r['finanziamento_mld'])} mld |"]
    md += [f"| Costo stimato SILOS | €{fmt_mld(r['costo_silos_mld'])} mld |"]
    md += [f"| Disponibilità SILOS | €{fmt_mld(r['disponibilita_silos_mld'])} mld |"]
    md += [f"| Fabbisogno residuo SILOS | €{fmt_mld(r['fabbisogno_silos_mld'])} mld |"]

    md += ["", "## Esecuzione (ANAC)", "", "| Dato | Valore |", "|---|---|"]
    md += [f"| Gare tracciate | {fmt_int(r['n_gare_anac'])} |"]
    md += [f"| Gare PNRR | {fmt_int(r['n_gare_pnrr'])} |"]
    md += [f"| Collaudi | {fmt_int(r['anac_n_collaudati'])} |"]
    md += [f"| Gare sotto soglia €5M | {fmt_int(r['n_gare_piccole'])} |"]
    md += [f"| Affidamenti diretti (CIG-B) | {fmt_int(r['n_gare_affidamento_diretto'])} |"]
    if r.get('importo_affidamento_diretto'):
        imp_b = r['importo_affidamento_diretto']
        if imp_b >= 1e9:
            md += [f"| Importo affidamenti diretti | €{fmt_mld(imp_b / 1e9)} mld |"]
        else:
            md += [f"| Importo affidamenti diretti | €{fmt_mld(imp_b / 1e6)} mio |"]
    md += [f"| CUP-programma (ombrello) | {'sì' if r['flag_ombrello'] else 'no'} |"]

    md += ["", "## Programmi", "", "| Dato | Valore |", "|---|---|"]
    md += [f"| Missione PNRR | {r['pnrr_missione'] or '—'} |"]
    md += [f"| Stato avanzamento PNRR | {r['pnrr_stato_avanzamento'] or '—'} |"]
    md += [f"| Amm. titolare PNRR | {r['pnrr_amministrazione_titolare'] or '—'} |"]
    md += [f"| Progetti coesione | {fmt_int(r['n_progetti_coesione'])} |"]

    md += ["", "## Localizzazione", ""]
    md += [f"- {fmt_loc(r['comune'], r['provincia'], r['regione'])}"]
    md += ["", "_Fonte: OpenCUP + Lab (ANAC/PNRR/coesione) + SILOS. Generata da `reports/scheda_opera.py`._"]
    return "\n".join(md)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cups", nargs="*", help="CUP da schedulare")
    ap.add_argument("--nome", help="nome leggibile dell'opera (per schede fuori seed)")
    ap.add_argument("--all", action="store_true", help="genera tutte le schede del seed")
    args = ap.parse_args()

    cups = args.cups
    if args.all:
        cups = [c for c, _ in SEED]

    if not cups:
        ap.error("serve almeno un CUP o --all")

    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")

    for cup in cups:
        nome = None
        if args.all:
            nome = dict(SEED)[cup]
        elif args.nome and len(cups) == 1:
            nome = args.nome
        md = scheda(con, cup, nome)
        target = OUT / f"{cup}.md"
        target.write_text(md)
        print(f"  scheda scritta: {target}")
    con.close()


if __name__ == "__main__":
    main()
