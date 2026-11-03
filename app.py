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

    if df
