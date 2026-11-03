from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Stock Auto", layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzH7w2yTxxslMP0lAD45LslEJTZkcbSbXVyoPONJEeO8kWiS1rhZWSS6ORVzBAEM33BJQ/exec"


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE AVEC CACHE OPTIMISÉ ---
@st.cache_data(ttl=60)
def load_data():
    try:
        res_p = requests.get(f"{WEB_APP_URL}?sheet=Pieces", timeout=10)
        data_p = res_p.json()
        df_p = pd.DataFrame(data_p) if data_p else pd.DataFrame()
    except Exception:
        df_p = pd.DataFrame()

    if df_p.empty or not all(
        col in df_p.columns
        for col in [
            "Référence",
            "Désignation",
            "Catégorie",
            "Prix Achat",
            "Prix Vente",
            "Quantité",
            "Alerte Min",
        ]
    ):
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
    except Exception:
        df_v = pd.DataFrame()

    if df_v.empty or not all(
        col in df_v.columns
        for col in [
            "Date",
            "Référence",
            "Désignation",
            "Quantité",
            "Total Vente",
            "Tiers",
            "Paiement",
        ]
    ):
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
    try:
        requests.post(
            WEB_APP_URL,
            json={"sheet": "Pieces", "rows": df_p.to_dict(orient="records")},
            timeout=10,
        )
        st.cache_data.clear()
    except Exception:
        pass


def save_ventes(df_v):
    try:
        requests.post(
            WEB_APP_URL,
            json={"sheet": "Ventes", "rows": df_v.to_dict(orient="records")},
            timeout=10,
        )
        st.cache_data.clear()
    except Exception:
        pass


df_p, df_v = load_data()

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3 = st.tabs(
    [
        "📦 Stock & Ventes",
        "➕ Ajouter une pièce",
        "📈 Historique & Bilan Mensuel",
    ]
)

# ---------------------------------------------------------------------
# ONGLET 1 : STOCK & ACTIONS EN DIRECT & MODIFICATION COMPLÈTE
# ---------------------------------------------------------------------
with t1:
    st.subheader("📋 Liste du stock et Actions en direct")

    if not df_p.empty:
        # --- GESTION DES ALERTES DE STOCK ---
        df_p_alert = df_p.copy()
        df_p_alert["Qte_Num"] = (
            pd.to_numeric(df_p_alert["Quantité"], errors="coerce").fillna(0)
        )
        df_p_alert["Seuil_Num"] = (
            pd.to_numeric(df_p_alert["Alerte Min"], errors="coerce").fillna(0)
        )
        alertes = df_p_alert[df_p_alert["Qte_Num"] <= df_p_alert["Seuil_Num"]]

        if not alertes.empty:
            st.warning(
                f"⚠️ **Attention : {len(alertes)} pièce(s) ont atteint ou sont"
                " sous leur seuil d'alerte minimal !**"
