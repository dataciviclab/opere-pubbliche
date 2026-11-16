"""Lo ZIP OpenCUP deve essere verificato prima del merge.

Un download interrotto a 2 GB su 3 produce un file che *sembra* completo: senza
controllo, l'estrazione fallisce a metà o — peggio — produce un parquet monco.
La cache persistente (`~/.cache/dataciviclab/opencup/`) rende utile il
`curl -C -` tra run diversi, ma solo se il file parziale non viene scambiato
per buono.
"""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "datasets" / "opencup-progetti" / "scripts" / "fetch_progetti.py"


def _modulo():
    spec = importlib.util.spec_from_file_location("fetch_progetti", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.mark.regression
def test_zip_valido_accetta_uno_zip_integro(tmp_path: Path) -> None:
    path = tmp_path / "ok.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("a.csv", "x;y\n1;2\n")
    assert _modulo().zip_valido(path) is True


@pytest.mark.regression
def test_zip_valido_rifiuta_un_parziale(tmp_path: Path) -> None:
    path = tmp_path / "ok.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("a.csv", "x;y\n" + "1;2\n" * 500)
    troncato = tmp_path / "troncato.zip"
    troncato.write_bytes(path.read_bytes()[: path.stat().st_size // 2])

    modulo = _modulo()
    assert modulo.zip_valido(troncato) is False, "un download interrotto non e' uno ZIP valido"
    assert modulo.zip_valido(tmp_path / "assente.zip") is False


@pytest.mark.regression
def test_marker_non_salva_uno_zip_troncato(tmp_path: Path) -> None:
    """Il marker `.ok` evita di ri-testare 3 GB, ma non deve fidarsi di un file
    cambiato dopo la verifica: la firma (dimensione+mtime) non torna e si
    riverifica."""
    path = tmp_path / "ok.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("a.csv", "x;y\n" + "1;2\n" * 500)
    modulo = _modulo()
    assert modulo.zip_valido(path) is True
    assert (tmp_path / "ok.zip.ok").exists(), "la verifica scrive il marker"

    path.write_bytes(path.read_bytes()[: path.stat().st_size // 2])
    assert modulo.zip_valido(path) is False
