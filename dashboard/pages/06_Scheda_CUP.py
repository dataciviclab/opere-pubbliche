"""Scheda CUP — Lookup singolo CUP con tutti gli attributi."""

import streamlit as st
from sources import query, fmt_eur, fmt_num

st.title("🔍 Scheda CUP")

# ── Ricerca ──────────────────────────────────────────────────────
cup_input = st.text_input("Inserisci CUP", placeholder="es. F81H92000000008")
search = st.button("Cerca")

if search and cup_input:
    row = query(f"SELECT * FROM clean_input WHERE cup = '{cup_input.strip()}' LIMIT 1")
    if row.empty:
        st.warning(f"Nessun CUP trovato: {cup_input}")
    else:
        r = row.iloc[0]

        st.subheader(f"`{r['cup']}`")
        st.caption(str(r.get("descrizione_intervento", r.get("silos_denominazione", "N/A"))))

        # ── Anagrafe ─────────────────────────────────────────────
        st.markdown("**Anagrafe**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stato", r.get("stato_progetto", "N/A"))
        c2.metric("Anno decisione", r.get("anno_decisione", "N/A"))
        c3.metric("Costo", fmt_eur(r.get("costo_progetto", 0)))
        c4.metric("Finanziamento", fmt_eur(r.get("finanziamento_progetto", 0)))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Soggetto", str(r.get("soggetto_titolare", "N/A"))[:40])
        c2.metric("Settore", str(r.get("settore_intervento", "N/A"))[:30])
        c3.metric("Regione", r.get("regione", "N/A"))
        c4.metric("Comune", r.get("comune", "N/A"))

        st.divider()

        # ── Fonti ────────────────────────────────────────────────
        st.markdown("**Fonti**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("N. fonti OpenCUP", int(r.get("n_fonti", 0)))
        c2.metric("Statale", "✅" if r.get("ha_fonte_statale") else "❌")
        c3.metric("UE", "✅" if r.get("ha_fonte_ue") else "❌")
        c4.metric("Regionale", "✅" if r.get("ha_fonte_regionale") else "❌")

        st.divider()

        # ── ANAC ─────────────────────────────────────────────────
        st.markdown("**ANAC**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CIG", fmt_num(int(r.get("anac_n_cig", 0))))
        c2.metric("Gare", fmt_num(int(r.get("anac_n_gare", 0))))
        c3.metric("Importo agg.", fmt_eur(r.get("anac_importo_aggiudicato", 0)))
        c4.metric("SAL", fmt_num(int(r.get("anac_n_sal", 0))))

        c1, c2 = st.columns(2)
        c1.metric("Importo SAL", fmt_eur(r.get("anac_importo_sal", 0)))

        st.divider()

        # ── PNRR ─────────────────────────────────────────────────
        if r.get("pnrr_fin_pnrr", 0) > 0:
            st.markdown("**PNRR**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Missione", str(r.get("pnrr_missione", "N/A"))[:30])
            c2.metric("Fin. PNRR", fmt_eur(r.get("pnrr_fin_pnrr", 0)))
            c3.metric("Gare PNRR", fmt_num(int(r.get("pnrr_n_gare", 0))))
            st.divider()

        # ── SILOS ────────────────────────────────────────────────
        if r.get("silos_costi_mln") is not None:
            st.markdown("**SILOS**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Sistema", str(r.get("silos_sistema", "N/A"))[:25])
            c2.metric("Costo SILOS", fmt_eur(r.get("silos_costi_mln", 0) * 1e6))
            c3.metric("Disponibilità", fmt_eur(r.get("silos_disponibilita_mln", 0) * 1e6))
            c4.metric("Gap", fmt_eur(r.get("silos_gap_mln", 0) * 1e6))
            st.caption(f"Stato SILOS: {r.get('silos_stato', 'N/A')}")
            st.divider()

        # ── OpenCoesione ─────────────────────────────────────────
        if r.get("coe_n_progetti", 0) > 0:
            st.markdown("**OpenCoesione**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Progetti", fmt_num(int(r.get("coe_n_progetti", 0))))
            c2.metric("Finanz. pubblico", fmt_eur(r.get("coe_finanz_tot_pubblico", 0)))
            c3.metric("Pagamenti", fmt_eur(r.get("coe_pagamenti", 0)))

        # ── Flag ─────────────────────────────────────────────────
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Ombrello", "⚠️ SÌ" if r.get("flag_ombrello") else "NO")
        c2.metric("Sub-progetto", "SÌ" if r.get("flag_sub_progetto") else "NO")
