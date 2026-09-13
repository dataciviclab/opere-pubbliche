"""Fetch, extract e merge dei 7 shard OpenCUP Progetti in un singolo parquet.

Output: opencup_progetti.parquet (nella directory corrente)
Toolkit legge da qui come script source.

Uso: python3 datasets/opencup-progetti/scripts/fetch_progetti.py
"""

from __future__ import annotations

import re
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
HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "it-IT,it;q=0.9",
}


def fetch_url() -> str:
    """Estrae l'URL corrente del ZIP Progetti dalla pagina Liferay."""
    from lab_connectors.http import HttpClient
    client = HttpClient(timeout=30, max_retries=2, user_agent=UA)
    page = client.get(PAGE_URL, headers=HEADERS)
    if page.response is None or page.response.status_code != 200:
        sys.exit(f"pagina non raggiungibile: HTTP {page.response.status_code if page.response else 'no response'}")
    html = page.response.content.decode("utf-8", errors="replace")
    pattern = re.compile(r'href="(/portale/documents/[^"]*?OpendataProgetti\.zip/[^"]*)"')
    match = pattern.search(html)
    if not match:
        sys.exit("URL OpendataProgetti.zip non trovato nella pagina")
    return BASE_URL + match.group(1).replace("&amp;", "&")


def download_zip(url: str, dest: Path) -> None:
    """Scarica lo ZIP se non esiste."""
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"skip (esiste): {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
        return
    from lab_connectors.http import HttpClient
    client = HttpClient(timeout=600, max_retries=2, user_agent=UA)
    print(f"download: {dest.name} ...")
    result = client.get(url, headers=HEADERS)
    if result.response is None or result.response.status_code != 200:
        sys.exit(f"download fallito: HTTP {result.response.status_code if result.response else 'no response'}")
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(result.response.content)
    tmp.rename(dest)
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

    # Skip se già esiste
    if out_path.exists() and out_path.stat().st_size > 100_000_000:
        print(f"skip (esiste): {out_path.name} ({out_path.stat().st_size / 1e9:.2f} GB)")
        return

    # Download ZIP in directory temporanea
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / ZIP_NAME

        print("1. fetch URL dalla pagina Liferay ...")
        url = fetch_url()
        print(f"   {url}\n")

        print("2. download ZIP ...")
        download_zip(url, zip_path)
        print()

        print("3. merge shard → parquet ...")
        merge_to_parquet(zip_path, out_path)

    print("\nfatto.")


if __name__ == "__main__":
    main()
