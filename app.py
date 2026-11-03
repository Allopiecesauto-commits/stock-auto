from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Stock Auto", layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzH7w2yTxxslMP0lAD45LslEJTZkcbSbXVyoPONJEeO8kWiS1rhZWSS6ORVzBAEM33BJQ/exec"


def load_data():
    try:
        res_p = requests.get(f"{WEB_APP_URL}?sheet=Pieces", timeout=10)
        data_p = res_p.json()
        df_p = pd.DataFrame(data_p) if data_p else pd.DataFrame()
    except Exception:
        df_p = pd.DataFrame()

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

    try:
        res_v = requests.get(f"{WEB_APP_URL}?sheet=Ventes", timeout=10)
        data_v = res_v.json()
        df_v = pd.DataFrame(data_v) if data_v else pd.DataFrame()
    except Exception:
        df_v = pd.DataFrame()

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

    return df_p, df_v


def save_pieces(df_p):
    try:
        requests.post(
            WEB_APP_URL,
            json={"sheet": "Pieces", "rows": df_p.to_dict(orient="records")},
            timeout=10,
        )
    except Exception:
        pass


def save_ventes(df_v):
    try:
        requests.post(
            WEB_APP_URL,
            json={"sheet": "Ventes", "rows": df_v.to_dict(orient="records")},
            timeout=10,
        )
    except Exception:
        pass


df_p, df_v = load_data()

st.title("🚗 Gestion de Stock Auto")

t1, t2 = st.tabs(["📦 Stock & Ventes", "➕ Ajouter une pièce"])

with t1:
    st.subheader("Inventaire actuel")
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True)
    else:
        st.info("Aucun article dans la base pour le moment.")

with t2:
    st.subheader("Ajouter une référence")
    r = st.text_input("Référence").strip().upper()
    n = st.text_input("Désignation").strip()
    c = st.text_input("Catégorie").strip()
    pa = st.number_input("Prix d'achat", min_value=0.0, step=0.5)
    pv = st.number_input("Prix de vente", min_value=0.0, step=0.5)
    q = st.number_input("Quantité en stock", min_value=0, step=1)
    s = st.number_input("Seuil d'alerte", min_value=0, step=1)

    if st.button("Enregistrer", type="primary"):
        if r and n:
            new_row = pd.DataFrame(
                [[r, n, c, pa, pv, q, s]], columns=df_p.columns
            )
            df_p = pd.concat([df_p, new_row], ignore_index=True)
            save_pieces(df_p)
            st.success("Pièce ajoutée avec succès !")
            st.rerun()
        else:
            st.error("La référence et le nom sont obligatoires.")
