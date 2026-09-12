"""Territorio — Analisi geografica delle opere pubbliche."""

import streamlit as st
import plotly.express as px
from sources import query, load_mart, fmt_eur, fmt_num

st.title("🌍 Territorio")

# ── Bar chart regioni ────────────────────────────────────────────
st.subheader("Costo per regione")
reg = query("""
    SELECT regione, COUNT(*) AS n_cup, SUM(costo_progetto) AS costo,
           SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) AS con_lab
    FROM clean_input GROUP BY 1 ORDER BY 3 DESC
""")
fig = px.bar(reg.head(15), x="regione", y="costo",
             labels={"costo": "Costo (€)", "regione": "Regione"})
st.plotly_chart(fig, width="stretch")

# ── Dettaglio regione ────────────────────────────────────────────
st.subheader("Dettaglio regione")
regione = st.selectbox("Seleziona regione", sorted(reg["regione"].unique()))

reg_df = query(f"""
    SELECT COUNT(*) AS n_cup, SUM(costo_progetto) AS costo,
           SUM(CASE WHEN con_almeno_una_fonte_lab THEN 1 ELSE 0 END) AS con_lab,
           SUM(CASE WHEN anac_n_cig > 0 THEN 1 ELSE 0 END) AS con_anac
    FROM clean_input WHERE regione = '{regione}'
""").iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("CUP", fmt_num(int(reg_df["n_cup"])))
k2.metric("Costo", fmt_eur(reg_df["costo"]))
k3.metric("Con Lab", fmt_num(int(reg_df["con_lab"])))
k4.metric("ANAC", fmt_num(int(reg_df["con_anac"])))

sett_reg = query(f"""
    SELECT settore_intervento, COUNT(*) AS n_cup, SUM(costo_progetto) AS costo
    FROM clean_input WHERE regione = '{regione}' GROUP BY 1 ORDER BY 3 DESC LIMIT 8
""")
st.dataframe(sett_reg.rename(columns={
    "settore_intervento": "Settore", "n_cup": "CUP", "costo": "Costo",
}), width="stretch", hide_index=True)
