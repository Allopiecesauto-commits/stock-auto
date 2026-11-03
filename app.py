from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Stock Auto", layout="wide")

# Lien de votre Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1H4GYOMMqA6lGpbXhbQ-HrzFJAeoBjj7TdFcq_62nirg/edit?usp=sharing"

# Connexion aux Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE ---
def load_data():
    try:
        df_p = conn.read(spreadsheet=SHEET_URL, worksheet="Pieces", ttl=0)
        df_p = df_p.dropna(how="all")
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
        df_v = conn.read(spreadsheet=SHEET_URL, worksheet="Ventes", ttl=0)
        df_v = df_v.dropna(how="all")
    except Exception:
