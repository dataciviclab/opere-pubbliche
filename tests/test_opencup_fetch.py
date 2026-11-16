"""Lo ZIP OpenCUP deve essere verificato prima del merge.

Un download interrotto a 2 GB su 3 produce un file che *sembra* completo: senza
controllo, l'estrazione fallisce a metà o — peggio — produce un parquet monco.
La cache persistente (`~/.cache/dataciviclab/opencup/`) rende utile il
`curl -C -` tra run diversi, ma solo se il file parziale non viene scambiato
per buono.
"""

from __future__ import annotations

import importlib.util
import subprocess
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


@pytest.mark.regression
def test_download_diretto_prima_del_proxy(tmp_path: Path, monkeypatch) -> None:
    """Il proxy e' un ripiego, non il percorso di default.

    Il 2026-11-16 la pipeline e' morta con `curl: (28)` perche' il proxy non
    raggiungeva opencup.gov.it, mentre la connessione diretta funzionava: la
    richiesta andava *sempre* con `-x`.
    """
    monkeypatch.setenv("BLOCKED_SOURCE_PROXY", "http://proxy.example:3128")
    modulo = _modulo()

    chiamate: list[list[str]] = []

    def _fake_run(cmd, **kwargs):
        chiamate.append(list(cmd))
        # il primo tentativo (diretto) fallisce, il secondo (proxy) produce lo ZIP
        if len(chiamate) == 1:
            return subprocess.CompletedProcess(cmd, 28, "", "Failed to connect")
        out = cmd[cmd.index("-o") + 1]
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("a.csv", "x;y\n1;2\n")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(modulo.subprocess, "run", _fake_run)

    dest = tmp_path / "cache" / "OpendataProgetti.zip"
    modulo.download_zip("https://www.opencup.gov.it/x.zip", dest)

    assert len(chiamate) == 2, f"attesi due tentativi, trovati {len(chiamate)}"
    assert "-x" not in chiamate[0], "il primo tentativo deve essere diretto"
    assert "-x" in chiamate[1], "il ripiego passa dal proxy"
    assert chiamate[1][chiamate[1].index("-x") + 1] == "http://proxy.example:3128"
    assert dest.exists() and dest.stat().st_size > 0


@pytest.mark.regression
def test_senza_proxy_un_solo_tentativo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("BLOCKED_SOURCE_PROXY", raising=False)
    modulo = _modulo()
    chiamate: list[list[str]] = []

    def _fake_run(cmd, **kwargs):
        chiamate.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 28, "", "Failed to connect")

    monkeypatch.setattr(modulo.subprocess, "run", _fake_run)
    with pytest.raises(SystemExit):
        modulo.download_zip("https://www.opencup.gov.it/x.zip", tmp_path / "x.zip")
    assert len(chiamate) == 1
