"""Grandi Opere — SILOS: costi, gap, stato attuazione."""

import streamlit as st
import plotly.express as px
from sources import query, fmt_eur, fmt_num

st.title("🏗️ Grandi Opere (SILOS)")

# ── KPI ──────────────────────────────────────────────────────────
kpi = query("""
    SELECT COUNT(*) AS n, SUM(silos_costi_mln) AS costo,
           SUM(silos_disponibilita_mln) AS disp, SUM(silos_gap_mln) AS gap
    FROM clean_input WHERE silos_costi_mln IS NOT NULL
""").iloc[0]

if kpi["n"] == 0:
    st.warning("Nessun dato SILOS disponibile.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Opere SILOS", fmt_num(int(kpi["n"])))
k2.metric("Costo totale", fmt_eur(kpi["costo"] * 1e6))
k3.metric("Disponibilità", fmt_eur(kpi["disp"] * 1e6))
k4.metric("Gap finanziario", fmt_eur(kpi["gap"] * 1e6))

st.divider()

# ── Top opere per costo ──────────────────────────────────────────
st.subheader("Top 30 opere per costo")
top = query("""
    SELECT cup, silos_denominazione, silos_sistema, silos_stato,
           silos_costi_mln, silos_disponibilita_mln, silos_gap_mln,
           regione, anac_n_cig, pnrr_fin_pnrr
    FROM clean_input WHERE silos_costi_mln IS NOT NULL
    ORDER BY silos_costi_mln DESC LIMIT 30
""")
st.dataframe(top.rename(columns={
    "cup": "CUP", "silos_denominazione": "Denominazione", "silos_sistema": "Sistema",
    "silos_stato": "Stato", "silos_costi_mln": "Costo (mln)",
    "silos_disponibilita_mln": "Disp. (mln)", "silos_gap_mln": "Gap (mln)",
    "regione": "Regione", "anac_n_cig": "CIG", "pnrr_fin_pnrr": "PNRR",
}), width="stretch", hide_index=True)

st.divider()

# ── Gap finanziario ──────────────────────────────────────────────
st.subheader("Gap finanziario (costo - disponibilità)")
gap = query("""
    SELECT silos_denominazione AS denominazione, silos_gap_mln, cup, silos_sistema, silos_costi_mln
    FROM clean_input WHERE silos_gap_mln > 0 ORDER BY silos_gap_mln DESC LIMIT 15
""")
# Trunca nomi lunghi per leggibilità
gap["opera"] = gap["denominazione"].apply(lambda x: x[:50] + "..." if len(str(x)) > 50 else x)
fig = px.bar(gap, x="opera", y="silos_gap_mln",
             hover_data=["cup", "silos_sistema", "silos_costi_mln"],
             labels={"silos_gap_mln": "Gap (mln €)", "opera": "Opera"})
fig.update_layout(xaxis_tickangle=-45, height=500)
st.plotly_chart(fig, width="stretch")

# ── Stato attuazione ─────────────────────────────────────────────
st.subheader("Stato attuazione")
stato = query("""
    SELECT silos_macro_stato AS stato, COUNT(*) AS n
    FROM clean_input WHERE silos_costi_mln IS NOT NULL GROUP BY 1 ORDER BY 2 DESC
""")
fig = px.pie(stato, names="stato", values="n")
st.plotly_chart(fig, width="stretch")

# ── Per sistema ──────────────────────────────────────────────────
st.subheader("Costo per sistema infrastrutturale")
sistema = query("""
    SELECT silos_sistema, COUNT(*) AS n_opere, SUM(silos_costi_mln) AS costo,
           SUM(silos_gap_mln) AS gap
    FROM clean_input WHERE silos_costi_mln IS NOT NULL GROUP BY 1 ORDER BY 3 DESC
""")
fig = px.bar(sistema, x="silos_sistema", y="costo",
             hover_data=["n_opere", "gap"],
             labels={"costo": "Costo (mln €)", "silos_sistema": "Sistema"})
fig.update_layout(height=400)
st.plotly_chart(fig, width="stretch")
