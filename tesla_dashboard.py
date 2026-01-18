import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Tesla på FINN", layout="wide")
st.title("🚗 Tesla på FINN – Analyse & prisforslag (PRO)")

CSV_FILE = "tesla_finn.csv"

# -----------------------------
# Helpers
# -----------------------------
def safe_int(x):
    try:
        if pd.isna(x):
            return None
        return int(float(x))
    except:
        return None


def last_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)

    # sikre numeriske felt
    for col in ["Årsmodell", "Km", "Pris"]:
        if col in df.columns:
            df[col] = df[col].apply(safe_int)

    return df


def fmt_kr(x):
    if x is None or pd.isna(x):
        return ""
    return f"{int(x):,} kr".replace(",", " ")


# -----------------------------
# Load data
# -----------------------------
df = last_data()

st.sidebar.header("Data")
st.sidebar.caption("✅ Data oppdateres automatisk via GitHub Actions.")

if df.empty:
    st.error("CSV er tom eller manglar. Vent litt og prøv igjen.")
    st.stop()

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Alle Tesla", "📈 Marknad", "💰 Prisforslag"])

# =============================
# TAB 1: LISTE
# =============================
with tab1:
    st.sidebar.header("Filter")

    # søk
    søk = st.sidebar.text_input("Søk (tekst/URL)", value="")

    modell = st.sidebar.multiselect(
        "Modell",
        sorted(df["Modell"].dropna().unique()),
        default=sorted(df["Modell"].dropna().unique())
    )

    driv = st.sidebar.multiselect(
        "Drivlinje",
        sorted(df["Drivlinje"].dropna().unique()),
        default=sorted(df["Drivlinje"].dropna().unique())
    )

    farge = st.sidebar.multiselect(
        "Farge",
        sorted(df["Farge"].dropna().unique())
    )

    interiør = st.sidebar.multiselect(
        "Interiør",
        sorted(df["Interiør"].dropna().unique())
    )

    df2 = df.copy()

    # filtrer
    df2 = df2[df2["Modell"].isin(modell)]
    df2 = df2[df2["Drivlinje"].isin(driv)]

    if farge:
        df2 = df2[df2["Farge"].isin(farge)]
    if interiør:
        df2 = df2[df2["Interiør"].isin(interiør)]

    if søk.strip():
        s = søk.lower().strip()
        df2 = df2[
            df2.astype(str).apply(lambda row: row.str.lower().str.contains(s, na=False)).any(axis=1)
        ]

    # sliders berre om data finnes
    if df2["Årsmodell"].notna().any():
        år_min, år_max = int(df2["Årsmodell"].min()), int(df2["Årsmodell"].max())
        år = st.sidebar.slider("Årsmodell", år_min, år_max, (år_min, år_max))
        df2 = df2[df2["Årsmodell"].between(*år)]

    if df2["Km"].notna().any():
        km_min, km_max = int(df2["Km"].min()), int(df2["Km"].max())
        km = st.sidebar.slider("Kilometer", km_min, km_max, (km_min, km_max))
        df2 = df2[df2["Km"].between(*km)]

    # sortering
    sortering = st.selectbox("Sorter etter", ["Pris (lav→høg)", "Pris (høg→lav)", "Km (lav→høg)", "Årsmodell (ny→gammal)"])

    if sortering == "Pris (lav→høg)":
        df2 = df2.sort_values("Pris", ascending=True)
    elif sortering == "Pris (høg→lav)":
        df2 = df2.sort_values("Pris", ascending=False)
    elif sortering == "Km (lav→høg)":
        df2 = df2.sort_values("Km", ascending=True)
    elif sortering == "Årsmodell (ny→gammal)":
        df2 = df2.sort_values("Årsmodell", ascending=False)

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Treff", len(df2))
    if df2["Pris"].notna().any():
        c2.metric("Medianpris", fmt_kr(df2["Pris"].median()))
        c3.metric("Billigast", fmt_kr(df2["Pris"].min()))
        c4.metric("Dyrast", fmt_kr(df2["Pris"].max()))
    else:
        c2.metric("Medianpris", "-")
        c3.metric("Billigast", "-")
        c4.metric("Dyrast", "-")

    st.divider()

    # gjør link klikkbar
    df_show = df2.copy()
    if "FINN-link" in df_show.columns:
        df_show["FINN-link"] = df_show["FINN-link"].apply(lambda x: f"[Lenke]({x})" if isinstance(x, str) and x.startswith("http") else "")

    st.dataframe(
        df_show,
        use_container_width=True,
        column_config={
            "FINN-link": st.column_config.LinkColumn("FINN-link")
        }
    )

# =============================
# TAB 2: MARKNAD (grafer)
# =============================
with tab2:
    st.subheader("📈 Marknad")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### Prisfordeling")
        dfp = df[df["Pris"].notna()].copy()
        if len(dfp) > 3:
            st.bar_chart(dfp["Pris"], height=260)
        else:
            st.info("For få datapunkt med pris.")

    with colB:
        st.markdown("### Medianpris per modell")
        dfm = df[df["Pris"].notna()].groupby("Modell")["Pris"].median().sort_values()
        if len(dfm) > 0:
            st.bar_chart(dfm, height=260)
        else:
            st.info("Ingen prisdata tilgjengeleg.")

    st.divider()

    st.markdown("### Enkle marknadstal")
    c1, c2, c3 = st.columns(3)
    c1.metric("Totalt annonser", len(df))
    if df["Pris"].notna().any():
        c2.metric("Medianpris (alle)", fmt_kr(df["Pris"].median()))
    else:
        c2.metric("Medianpris (alle)", "-")
    if df["Km"].notna().any():
        c3.metric("Median km", f"{int(df['Km'].median()):,} km".replace(",", " "))
    else:
        c3.metric("Median km", "-")

# =============================
# TAB 3: PRISFORSLAG
# =============================
with tab3:
    st.subheader("💰 Prisforslag (STRAM + smart intervall)")

    m = st.selectbox("Modell", sorted(df["Modell"].dropna().unique()))
    d = st.selectbox("Drivlinje", sorted(df["Drivlinje"].dropna().unique()))
    år_inn = st.number_input("Årsmodell", 2010, 2026, 2021)
    km_inn = st.number_input("Kilometerstand", 0, 600000, 60000)

    km_spenn = st.slider("Km-spenn (±)", 5000, 50000, 15000, step=5000)
    år_spenn = st.slider("År-spenn (±)", 0, 3, 1)

    if st.button("Beregn pris"):
        s = df.copy()

        # filter
        s = s[(s["Modell"] == m) & (s["Drivlinje"] == d)]
        s = s[s["Årsmodell"].between(år_inn - år_spenn, år_inn + år_spenn)]
        s = s[s["Km"].between(km_inn - km_spenn, km_inn + km_spenn)]
        s = s[s["Pris"].notna()]

        if len(s) < 3:
            st.warning(f"For få samanliknbare bilar ({len(s)}). Prøv større spenn.")
        else:
            median = float(s["Pris"].median())
            q25 = float(s["Pris"].quantile(0.25))
            q75 = float(s["Pris"].quantile(0.75))

            st.success(f"🎯 Anbefalt pris: **{fmt_kr(median)}**")
            st.caption(f"Intervall (Q1–Q3): {fmt_kr(q25)} – {fmt_kr(q75)}  |  Basert på {len(s)} annonser")

            # show
            s_show = s.sort_values("Pris").copy()
            if "FINN-link" in s_show.columns:
                s_show["FINN-link"] = s_show["FINN-link"].apply(lambda x: f"[Lenke]({x})" if isinstance(x, str) and x.startswith("http") else "")

            st.dataframe(
                s_show,
                use_container_width=True,
                column_config={"FINN-link": st.column_config.LinkColumn("FINN-link")}
            )
