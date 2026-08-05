#!/usr/bin/env python3
"""Estrae gli zip OpenCUP e converte i CSV in parquet.

- Progetti: 7 shard CSV (~15 GB) → parquet unico (tipizzato, ~2,7 GB)
- Localizzazione / Soggetti / FontiCopertura: zip singoli → parquet

I parquet sono salvati in opencup/data/parquet/ (fuori git).

Uso: python convert_to_parquet.py [--raw DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import duckdb


def _extract_zip(zip_path: Path, dest: Path) -> list[Path]:
    """Estrae lo zip in dest, ritorna i file estratti."""
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)
    return sorted(dest.glob("*.csv"))


def convert_progetti(raw: Path, out: Path) -> None:
    """7 shard CSV → parquet unico (schema tipizzato)."""
    csv_files = sorted(raw.glob("OpenCup_Progetti*.csv"))
    if not csv_files:
        print("WARNING: nessuno shard OpenCup_Progetti*.csv trovato")
        return
    csv_paths = [str(f) for f in csv_files]
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    con.execute("SET threads=8")
    target = out / "opencup_progetti.parquet"
    # all_varchar per sniffare lo schema prima di tipizzare; qui import diretto
    # con inferenza DuckDB (all_varchar=true se si vuole schema controllato).
    con.execute(
        f"""
        COPY (
            SELECT * FROM read_csv(
                {csv_paths!r},
                delim=';', header=true, encoding='utf-8',
                all_varchar=true
            )
        ) TO '{target}' (FORMAT parquet, COMPRESSION zstd)
        """
    )
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{target}')").fetchone()[0]
    print(f"progetti: {n:,} righe → {target} ({target.stat().st_size / 1e9:.2f} GB)")


def convert_simple(zip_path: Path, out: Path, name: str) -> None:
    """Zip singolo (Localizzazione/Soggetti/Fonti) → parquet."""
    tmp = zip_path.parent / f"_extract_{zip_path.stem}"
    files = _extract_zip(zip_path, tmp)
    if not files:
        print(f"WARNING: {zip_path.name} non contiene CSV")
        return
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{name}.parquet"
    con = duckdb.connect()
    con.execute(
        f"""
        COPY (
            SELECT * FROM read_csv({[str(f) for f in files]!r},
                delim=';', header=true, encoding='utf-8', all_varchar=true)
        ) TO '{target}' (FORMAT parquet, COMPRESSION zstd)
        """
    )
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{target}')").fetchone()[0]
    print(f"{name}: {n:,} righe → {target} ({target.stat().st_size / 1e6:.0f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="opencup/data/raw", help="cartella zip")
    ap.add_argument("--out", default="opencup/data/parquet", help="cartella parquet output")
    args = ap.parse_args()
    raw = Path(args.raw)
    out = Path(args.out)

    convert_progetti(raw, out)
    for name in ("opencup_localizzazione", "opencup_soggetti", "opencup_fonti_copertura"):
        zip_map = {
            "opencup_localizzazione": "OpendataLocalizzazione.zip",
            "opencup_soggetti": "OpendataSoggetti.zip",
            "opencup_fonti_copertura": "OpendataFontiCopertura.zip",
        }
        zp = raw / zip_map[name]
        if zp.exists():
            convert_simple(zp, out, name)
        else:
            print(f"WARNING: {zp.name} assente — skip")


if __name__ == "__main__":
    main()
