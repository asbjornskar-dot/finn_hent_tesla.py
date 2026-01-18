import streamlit as st
import pandas as pd
import os
from datetime import datetime

import finn_hent_tesla

st.set_page_config(page_title="Tesla på FINN", layout="wide")
st.title("🚗 Tesla på FINN – Analyse & prisforslag")

CSV_FILE = "tesla_finn.csv"

# --------------------------
# LAST DATA (fra csv)
# --------------------------
def last_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame()

# --------------------------
# SIDEBAR: Oppdater-knapp
# --------------------------
st.sidebar.header("Data")

if st.sidebar.button("🔄 Oppdater Tesla-data frå FINN"):
    with st.spinner("Hentar nye Tesla-annonsar frå FINN..."):
        df_ny = finn_hent_tesla.lagre_csv(CSV_FILE, max_pages=10)
        st.session_state["df"] = df_ny
    st.sidebar.success(f"Oppdatert! {len(df_ny)} annonser.")
    st.sidebar.caption(f"Sist oppdatert: {datetime.now().strftime('%H:%M:%S')}")

# Bruk session-state om den finst
if "df" in st.session_state:
    df = st.session_state["df"]
else:
    df = last_data()

# Hvis tom (første gong)
if df.empty:
    st.warning("Ingen data endå. Trykk 'Oppdater Tesla-data frå FINN' i menyen til venstre.")
    st.stop()

tab1, tab2 = st.tabs(["📊 Alle Tesla", "💰 Prisforslag"])

# --------------------------
# FANE 1
# --------------------------
with tab1:
    st.sidebar.header("Filtrer")

    modell = st.sidebar.multiselect(
        "Modell",
        sorted(df["Modell"].unique()),
        default=sorted(df["Modell"].unique())
    )

    driv = st.sidebar.multiselect(
        "Drivlinje",
        sorted(df["Drivlinje"].unique()),
        default=sorted(df["Drivlinje"].unique())
    )

    år_min, år_max = int(df["Årsmodell"].min()), int(df["Årsmodell"].max())
    år = st.sidebar.slider("Årsmodell", år_min, år_max, (år_min, år_max))

    km_min, km_max = int(df["Km"].min()), int(df["Km"].max())
    km = st.sidebar.slider("Kilometer", km_min, km_max, (km_min, km_max))

    filtrert = df[
        (df["Modell"].isin(modell)) &
        (df["Drivlinje"].isin(driv)) &
        (df["Årsmodell"].between(*år)) &
        (df["Km"].between(*km))
    ].sort_values("Pris")

    st.markdown(f"### Treffer: **{len(filtrert)}**")
    st.dataframe(filtrert, use_container_width=True)

# --------------------------
# FANE 2 – Prisforslag (STRAM)
# --------------------------
with tab2:
    st.subheader("💰 Foreslå annonsepris (STRAM samanlikning)")

    m = st.selectbox("Modell", sorted(df["Modell"].unique()))
    d = st.selectbox("Drivlinje", ["AWD", "RWD"])
    år_inn = st.number_input("Årsmodell", 2013, 2025, 2021)
    km_inn = st.number_input("Kilometerstand", 0, 500000, 60000)

    if st.button("Beregn pris"):
        s = df[
            (df["Modell"] == m) &
            (df["Drivlinje"] == d) &
            (df["Årsmodell"].between(år_inn - 1, år_inn + 1)) &
            (df["Km"].between(km_inn - 15000, km_inn + 15000))
        ]

        if len(s) < 3:
            st.warning("For få samanliknbare bilar. Prøv å justere km/år.")
        else:
            st.success(f"🎯 Anbefalt pris: **{int(s['Pris'].median()):,} kr**")
            st.caption(f"Basert på {len(s)} bilar")
            st.dataframe(s.sort_values("Pris"), use_container_width=True)
