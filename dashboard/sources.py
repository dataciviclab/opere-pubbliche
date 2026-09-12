"""Fonti dati per la dashboard CUP Intelligence.

Pattern standard: lab_connectors.duckdb.queries + lab_connectors.formatters.
"""

from __future__ import annotations

import streamlit as st

from lab_connectors.duckdb.queries import load_mart_table, query_clean
from lab_connectors.formatters import fmt_eur, fmt_num, fmt_pct

PREFIX = "opere_pubbliche_intelligence/"
SLUG = "op_cup_lab"
YEARS = [2026]


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart(table: str, year: int = 2026):
    """Carica un singolo mart table (cached 1h)."""
    return load_mart_table(SLUG, table, year, prefix=PREFIX)


@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str, years: tuple[int, ...] = tuple(YEARS)):
    """Esegue SQL sul clean layer (cached 1h)."""
    return query_clean(SLUG, sql, list(years), prefix=PREFIX)
