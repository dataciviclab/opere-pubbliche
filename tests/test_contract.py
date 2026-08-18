"""Contract test per Opere Pubbliche Intelligence.

Verifica la forma del repo, non i dati:
- presenza dei componenti richiesti (README, licenza, docs, workflow, tooling);
- convenzione verticale consumer: catalogo query, mart unico, registri in build/;
- non si committano output di run (data/, _local/, parquet/csv/zip).

Non richiede i layer dati: è il gate rapido della CI.

Marker: contract
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "Makefile",
    "pyproject.toml",
    "conftest.py",
    "pipeline.py",
    "test_smoke.py",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/test.yml",
    "docs/README.md",
    "docs/overview.md",
    "docs/sources.md",
    "docs/data_dictionary.md",
    "docs/decisions.md",
    "docs/contributing.md",
    "docs/lab_links.md",
    "docs/join-cup-anac-rules.md",
    "reports/panorama.py",
]

IGNORE_ENTRIES = {"data/", "_local/", "*.parquet", "*.csv", "*.zip", "__pycache__/", "opencup/data/raw/", "opencup/data/parquet/", ".venv/", ".env"}
BLOCKED_SUFFIXES = {".parquet", ".csv", ".zip", ".pyc"}


@pytest.mark.contract
def test_required_files_exist() -> None:
    missing = [p for p in REQUIRED_FILES if not (REPO_ROOT / p).exists()]
    assert not missing, f"file richiesti mancanti: {missing}"


@pytest.mark.contract
def test_required_dir_layout() -> None:
    assert (REPO_ROOT / "queries").is_dir(), "queries/ obbligatoria (catalogo domande)"
    assert (REPO_ROOT / "reports").is_dir(), "reports/ obbligatoria (deliverable)"
    query_sqls = list((REPO_ROOT / "queries").glob("*.sql"))
    assert query_sqls, "queries/ deve contenere almeno un file .sql"


@pytest.mark.contract
def test_gitignore_blocks_outputs() -> None:
    gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    missing = [entry for entry in IGNORE_ENTRIES if entry not in gi]
    assert not missing, f".gitignore deve contenere: {missing}"


@pytest.mark.contract
def test_no_run_outputs_tracked() -> None:
    """Nessun artefatto dati tracked: usa git ls-files per escludere anche i symlink."""
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True, text=True, check=True,
    )
    offenders = [
        line for line in out.stdout.splitlines()
        if line and Path(line).suffix.lower() in BLOCKED_SUFFIXES
    ]
    assert not offenders, f"artefatti dati non vanno committati: {offenders}"


@pytest.mark.contract
def test_queries_read_only_artifacts() -> None:
    """Le query del catalogo leggono solo dal mart o dagli aggregati (niente unified)."""
    allowed = {"data/cup/cup_fatti.parquet", "data/aggregati/"}
    for q in sorted((REPO_ROOT / "queries").glob("*.sql")):
        text = q.read_text(encoding="utf-8")
        assert "unified_operas" not in text, f"{q.name}: non deve usare unified_operas"
        # ogni read_parquet deve puntare agli artefatti consentiti
        for line in text.splitlines():
            if "read_parquet('data/" in line:
                assert any(a in line for a in allowed), f"{q.name}: path non consentito: {line.strip()}"


@pytest.mark.contract
def test_join_rules_have_no_local_references() -> None:
    """docs/join-cup-anac-rules.md non deve contenere path locali assoluti o riferimenti interni."""
    text = (REPO_ROOT / "docs" / "join-cup-anac-rules.md").read_text(encoding="utf-8")
    assert "/home/" not in text, "regole join non devono contenere path home assoluti"
    drive = re.compile(r"(^|[\s\W])[A-Za-z]:[\\/]", re.MULTILINE)
    assert not drive.search(text), "regole join non devono contenere path Windows (es. C:\\...)"