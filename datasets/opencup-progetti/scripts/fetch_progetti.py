"""Fetch, extract e merge dei 7 shard OpenCUP Progetti in un singolo parquet.

Output: opencup_progetti.parquet (nella directory corrente)
Toolkit legge da qui come script source.

Supporta:
- **Cache persistente** dello ZIP in `~/.cache/dataciviclab/opencup/` (override con
  `OPENCUP_CACHE_DIR`): il `curl -C -` riprende davvero tra un run e l'altro.
  Prima lo ZIP stava in una `TemporaryDirectory`, cancellata all'uscita: un
  download interrotto a 2 GB su 3 ripartiva sempre da zero.
- Retry su qualunque errore (`--retry-all-errors`), non solo HTTP.
- **Verifica d'integrita'** dello ZIP prima del merge: un parziale che sembra
  completo produrrebbe un parquet monco in silenzio. Un marker `.ok` (firma
  dimensione+mtime) evita di ri-testare 3 GB a ogni run dalla cache.
- Proxy `BLOCKED_SOURCE_PROXY` come **ripiego** (prima il tentativo diretto)
- Timeout configurabile (default 3600s)

Uso: python3 scripts/fetch_progetti.py
"""

from __future__ import annotations

import os
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


def zip_valido(path: Path) -> bool:
    """True se lo ZIP si apre e tutti i membri hanno il CRC corretto.

    `testzip()` su 3 GB e' una decompressione completa: un marker `.ok` con
    firma (dimensione + mtime) evita di ripeterla a ogni run quando il file
    viene dalla cache. Se il file cambia, la firma non torna e si riverifica.
    """
    if not path.exists():
        return False
    marker = path.with_name(path.name + ".ok")
    firma = f"{path.stat().st_size}:{int(path.stat().st_mtime)}"
    try:
        if marker.exists() and marker.read_text(encoding="utf-8").strip() == firma:
            return True
    except OSError:
        pass
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                return False
    except (zipfile.BadZipFile, OSError):
        return False
    try:
        marker.write_text(firma, encoding="utf-8")
    except OSError:
        pass
    return True


def _curl(dest: Path, url: str, proxy: str = "") -> subprocess.CompletedProcess:
    """Un tentativo di download con curl (resume dal parziale in cache)."""
    cmd = [
        "curl", "-sSL", "--fail",
        "--retry", "3", "--retry-delay", "5",
        "--retry-all-errors",  # anche errori di rete, non solo HTTP
        "-C", "-",  # resume dalla cache
        "-H", f"User-Agent: {UA}",
        "-o", str(dest),
    ]
    if proxy:
        cmd.extend(["-x", proxy])
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def download_zip(url: str, dest: Path) -> None:
    """Scarica lo ZIP in cache persistente: **diretto prima, proxy come ripiego**.

    Il proxy (`BLOCKED_SOURCE_PROXY`) e' un ripiego per le fonti che bloccano
    l'IP del runner, non il percorso di default: forzarlo su tutte le richieste
    significa che se il proxy non raggiunge la fonte il download fallisce anche
    quando la connessione diretta funzionerebbe. E' quello che e' successo il
    2026-11-16 (`curl: (28)` via proxy su opencup.gov.it, irraggiungibile dal
    proxy, mentre il sito rispondeva).
    """
    proxy = os.environ.get("BLOCKED_SOURCE_PROXY", "")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if zip_valido(dest):
        print(f"cache: {dest} ({dest.stat().st_size / 1e6:.0f} MB) integro, skip download")
        return
    if dest.exists():
        print(f"cache parziale/invalida: riparto da {dest.stat().st_size / 1e6:.0f} MB")

    print(f"download diretto: {dest.name} ...")
    result = _curl(dest, url)
    if result.returncode != 0 and proxy:
        print(f"diretto fallito (exit {result.returncode}), riprovo via proxy ...")
        result = _curl(dest, url, proxy)
    if result.returncode != 0:
        if dest.exists():
            print(f"parziale in cache: {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)"
                  " — il prossimo run riprende da qui")
        sys.exit(f"download fallito (exit {result.returncode}): {result.stderr[:200]}")

    if not zip_valido(dest):
        dest.unlink(missing_ok=True)
        sys.exit(f"ZIP corrotto dopo il download ({dest}) — rimosso, riprova")
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

    import os
    cache_dir = Path(
        os.environ.get("OPENCUP_CACHE_DIR", Path.home() / ".cache" / "dataciviclab" / "opencup")
    )
    zip_path = cache_dir / ZIP_NAME

    print("1. fetch URL dalla pagina Liferay ...")
    url = fetch_url()
    print(f"   {url}\n")

    print("2. download ZIP in cache persistente ...")
    download_zip(url, zip_path)
    print()

    print("3. merge shard → parquet ...")
    merge_to_parquet(zip_path, out_path)

    print("\nfatto.")


if __name__ == "__main__":
    main()
