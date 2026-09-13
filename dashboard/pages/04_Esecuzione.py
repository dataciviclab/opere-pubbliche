"""Esecuzione — Funnel ANAC: gare, aggiudicazioni, SAL, collaudo."""

import streamlit as st
from sources import query, fmt_eur, fmt_num

st.title("⏱️ Esecuzione")

# ── Funnel ANAC ──────────────────────────────────────────────────
st.subheader("Funnel esecuzione (CUP con ANAC)")
anac = query("""
    SELECT COUNT(*) AS n_cup, SUM(anac_n_gare) AS n_gare,
           SUM(anac_importo_aggiudicato) AS importo,
           SUM(anac_n_sal) AS sal, SUM(anac_importo_sal) AS importo_sal,
           SUM(anac_sal_in_ritardo) AS sal_ritardo
    FROM clean_input WHERE anac_n_cig > 0
""").iloc[0]

k1, k2, k3 = st.columns(3)
k1.metric("CUP con gare", fmt_num(int(anac["n_cup"])))
k2.metric("Totale gare", fmt_num(int(anac["n_gare"])))
k3.metric("Importo agg.", fmt_eur(anac["importo"]))

st.divider()

st.subheader("Stati di avanzamento (SAL)")
k1, k2, k3 = st.columns(3)
k1.metric("Totale SAL", fmt_num(int(anac["sal"])))
k2.metric("Importo SAL", fmt_eur(anac["importo_sal"]))
k3.metric("SAL in ritardo", fmt_num(int(anac["sal_ritardo"])))

st.divider()

# ── Ombrello ─────────────────────────────────────────────────────
st.subheader("CUP ombrello")
n_ombrello = query("SELECT COUNT(*) AS n FROM clean_input WHERE flag_ombrello").iloc[0]["n"]
st.metric("CUP ombrello", fmt_num(int(n_ombrello)))

if n_ombrello > 0:
    omb = query("""
        SELECT cup, soggetto_titolare, regione, anac_n_cig, costo_progetto
        FROM clean_input WHERE flag_ombrello ORDER BY anac_n_cig DESC LIMIT 20
    """)
    st.dataframe(omb.rename(columns={
        "cup": "CUP", "soggetto_titolare": "Soggetto",
        "regione": "Regione", "anac_n_cig": "CIG", "costo_progetto": "Costo",
    }), width="stretch", hide_index=True)
