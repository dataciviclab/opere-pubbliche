"""Panoramica — Visione d'insieme delle opere pubbliche italiane."""

import streamlit as st
from sources import query, fmt_eur, fmt_num

st.title("📊 Panoramica")

# ── KPI principali ────────────────────────────────────────────────
kpi = query("""
    SELECT COUNT(*) AS n_cup, SUM(costo_progetto) AS costo,
           SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) AS con_lab,
           SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS con_anac,
           SUM(CASE WHEN silos_costi_mln IS NOT NULL THEN 1 ELSE 0 END) AS con_silos
    FROM clean_input
""").iloc[0]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("CUP totali", fmt_num(int(kpi["n_cup"])))
k2.metric("Costo totale", fmt_eur(kpi["costo"]))
k3.metric("Con fonte Lab", fmt_num(int(kpi["con_lab"])))
k4.metric("ANAC (CIG)", fmt_num(int(kpi["con_anac"])))
k5.metric("SILOS", fmt_num(int(kpi["con_silos"])))

st.divider()

# ── Copertura per area ────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Copertura per area")
    area = query("""
        SELECT area, COUNT(*) AS n_cup, SUM(costo_progetto) AS costo,
               SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) AS con_fonte,
               ROUND(SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct
        FROM clean_input GROUP BY 1 ORDER BY 3 DESC
    """)
    st.dataframe(area.rename(columns={
        "area": "Area", "n_cup": "CUP", "costo": "Costo",
        "con_fonte": "Con Lab", "pct": "% Lab",
    }), width="stretch", hide_index=True)

with col2:
    st.subheader("Stato progetto")
    stato = query("""
        SELECT stato_progetto, COUNT(*) AS n FROM clean_input GROUP BY 1 ORDER BY 2 DESC
    """)
    st.dataframe(stato.rename(columns={"stato_progetto": "Stato", "n": "CUP"}),
                  width="stretch", hide_index=True)

st.divider()

# ── Top settori ───────────────────────────────────────────────────
st.subheader("Top settori per costo")
sett = query("""
    SELECT settore_intervento, COUNT(*) AS n_cup, SUM(costo_progetto) AS costo,
           SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS con_anac,
           ROUND(SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_anac
    FROM clean_input GROUP BY 1 ORDER BY 3 DESC LIMIT 10
""")
st.dataframe(sett.rename(columns={
    "settore_intervento": "Settore", "n_cup": "CUP",
    "costo": "Costo", "con_anac": "ANAC", "pct_anac": "% ANAC",
}), width="stretch", hide_index=True)

# ── Fonti di finanziamento ────────────────────────────────────────
st.subheader("Fonti di finanziamento OpenCUP")
fonti = query("""
    SELECT SUM(ha_fonte_statale) AS statale, SUM(ha_fonte_ue) AS ue,
           SUM(ha_fonte_regionale) AS regionale, SUM(ha_fonte_privata) AS privata
    FROM clean_input
""").iloc[0]
f1, f2, f3, f4 = st.columns(4)
f1.metric("Statale", fmt_num(int(fonti["statale"])))
f2.metric("UE", fmt_num(int(fonti["ue"])))
f3.metric("Regionale", fmt_num(int(fonti["regionale"])))
f4.metric("Privata", fmt_num(int(fonti["privata"])))
