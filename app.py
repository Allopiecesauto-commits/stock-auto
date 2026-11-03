from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Stock Auto", layout="wide")

# URL de votre passerelle Google Apps Script intégrée
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzH7w2yTxxslMP0lAD45LslEJTZkcbSbXVyoPONJEeO8kWiS1rhZWSS6ORVzBAEM33BJQ/exec"


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE VIA API ---
def load_data():
    try:
        res_p = requests.get(f"{WEB_APP_URL}?sheet=Pieces", timeout=10)
        data_p = res_p.json()
        df_p = pd.DataFrame(data_p) if data_p else pd.DataFrame()
        if df_p.empty:
            df_p = pd.DataFrame(
                columns=[
                    "Référence",
                    "Désignation",
                    "Catégorie",
                    "Prix Achat",
                    "Prix Vente",
                    "Quantité",
                    "Alerte Min",
                ]
            )
    except Exception:
        df_p = pd.DataFrame(
            columns=[
                "Référence",
                "Désignation",
                "Catégorie",
                "Prix Achat",
                "Prix Vente",
                "Quantité",
                "Alerte Min",
            ]
        )

    try:
        res_v = requests.get(f"{WEB_APP_URL}?sheet=Ventes", timeout=10)
        data_v = res_v.json()
        df_v = pd.DataFrame(data_v) if data_v else pd.DataFrame()
        if df_v.empty:
            df_v = pd.DataFrame(
                columns=[
                    "Date",
                    "Référence",
                    "Désignation",
                    "Quantité",
                    "Total Vente",
                    "Tiers",
                    "Paiement",
                ]
            )
    except Exception:
        df_v = pd.DataFrame(
            columns=[
                "Date",
                "Référence",
                "Désignation",
                "Quantité",
                "Total Vente",
                "Tiers",
                "Paiement",
            ]
        )

    return df_p, df_v


def save_pieces(df_p):
    payload = {"sheet": "Pieces", "rows": df_p.to_dict(orient="records")}
    try:
        requests.post(WEB_APP_URL, json=payload, timeout=10)
    except Exception:
        pass


def save_ventes(df_v):
    payload = {"sheet": "Ventes", "rows": df_v.to_dict(orient="records")}
    try:
        requests.post(WEB_APP_URL, json=payload, timeout=10)
    except Exception:
        pass


# Chargement initial
df_p, df_v = load_data()

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3 = st.tabs(
    [
        "📊 Accueil & Actions rapides",
        "📦 Créer Nouvelle Fiche",
        "📈 Historique & Bilan Mensuel",
    ]
)

if "filtre_alerte" not in st.session_state:
    st.session_state.filtre_alerte = False

if not df_p.empty:
    for idx, row in df_p.iterrows():
        r_id = str(row["Référence"])
        if f"pop_act_{r_id}" not in st.session_state:
            st.session_state[f"pop_act_{r_id}"] = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL & GESTION DU STOCK DIRECT
# ---------------------------------------------------------------------
with t1:
    st.subheader("📋 Liste du stock et Actions en direct")

    alt_df = (
        df_p[
            pd.to_numeric(df_p["Quantité"], errors="coerce").fillna(0)
            <= pd.to_numeric(df_p["Alerte Min"], errors="coerce").fillna(0)
        ]
        if not df_p.empty
        else pd.DataFrame()
    )
    nb_alt = len(alt_df)

    c1, c2 = st.columns(2)
    if c1.button(
        f"📋 Total Références : {len(df_p)}",
        use_container_width=True,
        key="btn_tot_ref",
    ):
        st.session_state.filtre_alerte = False
        st.
