#!/usr/bin/env python3
"""Scarica gli Open Data OpenCUP (Progetti, Localizzazione, Soggetti, Fonti).

Gli URL ufficiali vengono letti dalla pagina "Accesso agli Open Data" del portale
Liferay OpenCUP. Il server risponde HTTP 200 a GET con header browser; gli URL
contengono un timestamp (?t=...) che cambia a ogni pubblicazione: lo script
estrae gli URL correnti dalla pagina invece di hardcodarli.

Uso: python download_opencup.py [--out DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lab_connectors.http import HttpClient

PAGE_URL = "https://www.opencup.gov.it/portale/web/opencup/accesso-agli-open-data"
BASE_URL = "https://www.opencup.gov.it"

# Nomi dei file target (subset della pagina — si possono estendere)
TARGETS = ("OpendataProgetti.zip", "OpendataLocalizzazione.zip",
           "OpendataSoggetti.zip", "OpendataFontiCopertura.zip")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}


def extract_zip_urls(html: str) -> dict[str, str]:
    """Estrae {filename: full_url} per gli zip target dalla pagina."""
    found: dict[str, str] = {}
    # href="/portale/documents/21195/299152/OpendataProgetti.zip/7384382b-...?t=..."
    pattern = re.compile(r'href="(/portale/documents/[^"]*?([^/]+\.zip)/[^"]*)"')
    for full, name in pattern.findall(html):
        if name in TARGETS:
            found[name] = BASE_URL + full.replace("&amp;", "&")
    return found


def download(url: str, dest: Path, client: HttpClient) -> bool:
    """Scarica url su dest (skip se esiste già). Ritorna True se scaricato."""
    if dest.exists() and dest.stat().st_size > 0:
        print(f"skip (esiste): {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
        return False
    print(f"download: {url}")
    result = client.get(url, headers=HEADERS)
    if result.response is None or result.response.status_code != 200:
        status = (result.response.status_code if result.response is not None
                  else f"no response (is_ok={result.is_ok})")
        raise RuntimeError(f"Download fallito {url}: HTTP {status}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(result.response.content)
    tmp.rename(dest)
    print(f"  ok: {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="opencup/data/raw", help="cartella output zip")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    client = HttpClient(timeout=600, max_retries=2, user_agent=UA)
    print(f"pagina: {PAGE_URL}")
    page = client.get(PAGE_URL, headers=HEADERS)
    if page.response is None or page.response.status_code != 200:
        sys.exit(f"pagina OpenCUP non raggiungibile: HTTP "
                 f"{page.response.status_code if page.response else 'no response'}")
    urls = extract_zip_urls(page.response.content.decode("utf-8", errors="replace"))
    if not urls:
        sys.exit("nessun URL zip trovato nella pagina (pattern cambiato?)")

    for name in TARGETS:
        if name not in urls:
            print(f"WARNING: {name} non trovato nella pagina — skip")
            continue
        download(urls[name], out / name, client)

    print("\nfatto.")


if __name__ == "__main__":
    main()
