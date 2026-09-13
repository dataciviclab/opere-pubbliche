"""Fetch, extract e merge dei 7 shard OpenCUP Progetti in un singolo parquet.

Output: opencup_progetti.parquet (nella directory corrente)
Toolkit legge da qui come script source.

Supporta:
- Resume del download con curl -C - (riprende da dove era)
- Proxy via BLOCKED_SOURCE_PROXY (se configurato)
- Timeout configurabile (default 3600s)

Uso: python3 scripts/fetch_progetti.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

import duckdb

PAGE_URL = "https://www.opencup.gov.it/portale/web/opencup/accesso-agli-open-data"
BASE_URL = "https://www.opencup.gov.it"
ZIP_NAME = "OpendataProgetti.zip"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


def fetch_url() -> str:
    """Estrae l'URL corrente del ZIP Progetti dalla pagina Liferay."""
    from lab_connectors.http import download
    html = download(PAGE_URL, timeout=30, user_agent=UA).decode("utf-8", errors="replace")
    pattern = re.compile(r'href="(/portale/documents/[^"]*?OpendataProgetti\.zip/[^"]*)"')
    match = pattern.search(html)
    if not match:
        sys.exit("URL OpendataProgetti.zip non trovato nella pagina")
    return BASE_URL + match.group(1).replace("&amp;", "&")


def download_zip(url: str, dest: Path) -> None:
    """Scarica lo ZIP con resume (curl -C -)."""
    import os
    proxy = os.environ.get("BLOCKED_SOURCE_PROXY", "")

    cmd = [
        "curl", "-sSL", "--fail",
        "--retry", "3", "--retry-delay", "5",
        "-C", "-",  # resume
        "-H", f"User-Agent: {UA}",
        "-o", str(dest),
    ]
    if proxy:
        cmd.extend(["-x", proxy])

    cmd.append(url)

    # Se il file esiste già e sembra completo, skip
    if dest.exists() and dest.stat().st_size > 100_000_000:
        print(f"skip (esiste): {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
        return

    print(f"download: {dest.name} ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Se il file parziale esiste, fallo vedere
        if dest.exists():
            print(f"parziale: {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
        sys.exit(f"download fallito (exit {result.returncode}): {result.stderr[:200]}")

    print(f"ok: {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")


def merge_to_parquet(zip_path: Path, out_path: Path) -> None:
    """Estrae i 7 CSV dal ZIP e li merge in un singolo parquet."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as z:
            csv_names = sorted(f for f in z.namelist() if f.endswith(".csv"))
            if not csv_names:
                sys.exit("nessun CSV nello ZIP")
            print(f"estrazione {len(csv_names)} shard ...")
            z.extractall(tmp_path)
        csv_paths = sorted(str(p) for p in tmp_path.glob("*.csv"))
        print(f"merge {len(csv_paths)} CSV → parquet ...")
        con = duckdb.connect()
        con.execute("SET memory_limit='6GB'")
        con.execute("SET threads=4")
        con.execute(f"""
            COPY (
                SELECT * FROM read_csv(
                    {csv_paths!r},
                    delim=';', header=true, encoding='utf-8',
                    all_varchar=true
                )
            ) TO '{out_path}' (FORMAT parquet, COMPRESSION zstd)
        """)
        n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out_path}')").fetchone()[0]
        con.close()
        print(f"ok: {n:,} righe → {out_path} ({out_path.stat().st_size / 1e9:.2f} GB)")


def main() -> None:
    out_path = Path("opencup_progetti.parquet")

    if out_path.exists() and out_path.stat().st_size > 100_000_000:
        print(f"skip (esiste): {out_path.name} ({out_path.stat().st_size / 1e9:.2f} GB)")
        return

    import os
    proxy = os.environ.get("BLOCKED_SOURCE_PROXY", "")
    if proxy:
        print(f"proxy: {proxy[:50]}...")

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / ZIP_NAME

        print("1. fetch URL dalla pagina Liferay ...")
        url = fetch_url()
        print(f"   {url}\n")

        print("2. download ZIP (resume-friendly) ...")
        download_zip(url, zip_path)
        print()

        print("3. merge shard → parquet ...")
        merge_to_parquet(zip_path, out_path)

    print("\nfatto.")


if __name__ == "__main__":
    main()
