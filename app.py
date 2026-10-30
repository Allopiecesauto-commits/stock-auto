import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", page_icon="🚗", layout="centered")

F_PIECES, F_MOUV = "web_pieces.csv", "web_mouvements.csv"

def charger_donnees():
    if not os.path.exists(F_PIECES):
        pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Rayon", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]).to_csv(F_PIECES, index=False)
    if not os.path.exists(F_MOUV):
        pd.DataFrame(columns=["Date", "Référence", "Désignation", "Type", "Quantité"]).to_csv(F_MOUV, index=False)
    return pd.read_csv(F_PIECES), pd.read_csv(F_MOUV)

df_p, df_m = charger_donnees()

st.title("🚗 Stock Auto Privé")

t1, t2, t3 = st.tabs(["📊 Accueil", "📦 Ajouter", "🔄 Mouvements"])

with t1:
    c1, c2 = st.columns(2)
    c1.metric("Total Références", len(df_p))
    alt = len(df_p[df_p["Quantité"] <= df_p["Alerte Min"]]) if not df_p.empty else 0
    c2.metric("Alertes rupture", alt)

    req = st.text_input("Rechercher (Réf ou Nom) :").strip().upper()
    if req and not df_p.empty:
        res = df_p[df_p["Référence"].str.contains(req, na=False) | df_p["Désignation"].str.upper().str.contains(req, na=False)]
        st.dataframe(res, use_container_width=True)
    elif not df_p.empty:
        st.dataframe(df_p, use_container_width=True)

with t2:
    st.subheader("Nouvelle pièce")
    with st.form("f_add", clear_on_submit=True):
        rf = st.text_input("Référence unique :").strip().upper()
        nm = st.text_input("Désignation / Nom :").strip()
        ct = st.text_input("Catégorie :").strip()
        ry = st.text_input("Rayon :").strip()
        col_a, col_b = st.columns(2)
        pa = col_a.number_input("Prix d'achat (€) :", min_value=0.0, step=0.5)
        qt = col_a.number_input("Stock Initial :", min_value=0, step=1)
        pv = col_b.number_input("Prix de vente (€) :", min_value=0.0, step=0.5)
        sl = col_b.number_input("Seuil alerte :", min_value=0, step=1)
        
        if st.form_submit_button("Enregistrer"):
            if not rf or not nm:
                st.error("Réf et Nom obligatoires.")
            elif not df_p.empty and rf in df_p["Référence"].values:
                st.error("Cette référence existe déjà.")
            else:
                df_p = pd.concat([df_p, pd.DataFrame([[rf, nm, ct, ry, pa, pv, qt, sl]], columns=df_p.columns)], ignore_index=True)
                df_p.to_csv(F_PIECES, index=False)
                st.success("Pièce ajoutée !")
                st.rerun()

with t3:
    st.subheader("Entrée / Sortie")
    rf_m = st.text_input("Référence de la pièce :").strip().upper()
    if rf_m:
        if not df_p.empty and rf_m in df_p["Référence"].values:
            p_inf = df_p[df_p["Référence"] == rf_m].iloc[0]
            st.info(f"Pièce : {p_inf['Désignation']} | Stock actuel : {p_inf['Quantité']}")
            typ = st.radio("Opération :", ["💸 Vente Client (Sortie)", "📦 Arrivée Fournisseur (Entrée)"])
            q_m = st.number_input("Quantité :", min_value=1, step=1)
            
            if st.button("Valider"):
                idx = df_p[df_p["Référence"] == rf_m].index
                ok = False
                if "Vente" in typ:
                    if p_inf['Quantité'] < q_m: st.error("Stock insuffisant !")
                    else:
                        df_p.at[idx, "Quantité"] -= q_m
                        ok = True
                else:
                    df_p.at[idx, "Quantité"] += q_m
                    ok = True
                if ok:
                    df_p.to_csv(F_PIECES, index=False)
                    df_m = pd.concat([df_m, pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M"), rf_m, p_inf['Désignation'], typ, q_m]], columns=df_m.columns)], ignore_index=True)
                    df_m.to_csv(F_MOUV, index=False)
                    st.success("Stock mis à jour !")
                    st.rerun()
        else: st.error("Référence inconnue.")
