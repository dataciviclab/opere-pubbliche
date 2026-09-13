#!/usr/bin/env python3
"""CUP Intelligence · Dashboard Streamlit"""

import streamlit as st
from lab_connectors.branding import apply_branding

st.set_page_config(
    page_title="CUP Intelligence · Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_branding(
    repo_name="opere-pubbliche",
    repo_url="https://github.com/dataciviclab/opere-pubbliche",
)

pages = {
    "Panoramica": [
        st.Page("pages/01_Panoramica.py", title="Panoramica", icon="📊", default=True),
        st.Page("pages/02_Territorio.py", title="Territorio", icon="🌍"),
    ],
    "Intelligence": [
        st.Page("pages/03_Fonti.py", title="Fonti", icon="💰"),
        st.Page("pages/04_Esecuzione.py", title="Esecuzione", icon="⏱️"),
        st.Page("pages/05_Grandi_Opere.py", title="Grandi Opere", icon="🏗️"),
    ],
    "Esplorazione": [
        st.Page("pages/06_Scheda_CUP.py", title="Scheda CUP", icon="🔍"),
        st.Page("pages/07_SQL.py", title="Query SQL", icon="🧪"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
