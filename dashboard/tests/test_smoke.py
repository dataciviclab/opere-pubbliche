"""Smoke test per la dashboard CUP Intelligence.

Pattern standard: py_compile su tutte le pagine.
"""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
DASHBOARD = Path(__file__).resolve().parent.parent
PAGES = DASHBOARD / "pages"


@pytest.mark.smoke
def test_all_pages_compile() -> None:
    """Tutte le pagine compilano senza errori di sintassi."""
    for f in sorted(PAGES.glob("*.py")):
        py_compile.compile(str(f), doraise=True)
