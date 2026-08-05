#!/usr/bin/env python3
"""Cache locale del layer clean Lab grande (anac, opencoesione).

Il layer clean del Lab su GCS è grande (anac_appalti_master 674MB): leggerlo
a ogni build costa egress GCS e tempo. Questo script lo scarica UNA volta in
data/cache/ — il build legge da lì (cache-first, vedi build_unified._resolve).

Uso: python build/cache_lab.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "data" / "cache"

SOURCES = {
    "anac_appalti_master": "gs://dataciviclab-clean/anac_appalti_master/2026/anac_appalti_master_2026_clean.parquet",
    "opencoesione_progetti": "gs://dataciviclab-clean/opencoesione_progetti/2026/opencoesione_progetti_2026_clean.parquet",
}


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET memory_limit='2GB'")
    for name, gs in SOURCES.items():
        dst = CACHE / f"{name}_2026_clean.parquet"
        if dst.exists():
            print(f"{name}: già in cache ({dst.stat().st_size / 1e6:.0f} MB)")
            continue
        con.execute(f"COPY (SELECT * FROM read_parquet('{gs}')) TO '{dst}' (FORMAT parquet, COMPRESSION zstd)")
        print(f"{name}: cache ok ({dst.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
