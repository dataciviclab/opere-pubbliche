"""Fonti — Copertura finanziaria e fonti Lab."""

import streamlit as st
import plotly.express as px
from sources import query, load_mart, fmt_num

st.title("💰 Fonti")

# ── Copertura cumulativa ─────────────────────────────────────────
kpi = query("""
    SELECT SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS anac,
           SUM(CASE WHEN pnrr_fin_pnrr > 0 THEN 1 ELSE 0 END) AS pnrr,
           SUM(CASE WHEN coe_n_progetti > 0 THEN 1 ELSE 0 END) AS coesione,
           SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) AS totale
    FROM clean_input
""").iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("ANAC", fmt_num(int(kpi["anac"])))
k2.metric("PNRR", fmt_num(int(kpi["pnrr"])))
k3.metric("Coesione", fmt_num(int(kpi["coesione"])))
k4.metric("Almeno 1 fonte", fmt_num(int(kpi["totale"])))

st.divider()

# ── Copertura per settore ────────────────────────────────────────
st.subheader("Copertura ANAC per settore")
sett = query("""
    SELECT settore_intervento, COUNT(*) AS n_cup,
           SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS con_anac,
           ROUND(SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct
    FROM clean_input GROUP BY 1
    HAVING SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) > 0
    ORDER BY 4 DESC LIMIT 10
""")
fig = px.bar(sett, x="settore_intervento", y="pct",
             labels={"pct": "% con ANAC", "settore_intervento": "Settore"})
fig.update_layout(height=400, xaxis_tickangle=-45)
st.plotly_chart(fig, width="stretch")

# ── Dettaglio fonti per settore × area ───────────────────────────
st.subheader("Dettaglio fonti per settore × area")
fonti = load_mart("mart_fonti")
st.dataframe(fonti.rename(columns={
    "settore_intervento": "Settore", "area": "Area", "n_cup": "CUP",
    "pct_anac": "% ANAC", "pct_pnrr": "% PNRR", "pct_con_fonte_lab": "% Lab",
}), width="stretch", hide_index=True)
