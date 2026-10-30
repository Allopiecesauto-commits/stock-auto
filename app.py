import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Gestion Stock Auto", page_icon="🚗", layout="centered")

FILE_PIECES = "web_pieces.csv"
FILE_MOUVEMENTS = "web_mouvements.csv"

def charger_donnees():
    if not os.path.exists(FILE_PIECES):
        df = pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Rayon", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"])
        df.to_csv(FILE_PIECES, index=False)
    if not os.path.exists(FILE_MOUVEMENTS):
        df = pd.DataFrame(columns=["Date", "Référence", "Désignation", "Type", "Quantité"])
        df.to_csv(FILE_MOUVEMENTS, index=False)
    return pd.read_csv(FILE_PIECES), pd.read_csv(FILE_MOUVEMENTS)

df_pieces, df_mouv = charger_donnees()

st.title("🚗 Gestion de Stock Auto Privé")
st.write("Connecté en temps réel pour toute l'équipe")

tab1, tab2, tab3 = st.tabs(["📊 Accueil & Recherche", "📦 Ajouter une pièce", "🔄 Entrées / Sorties"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Références", len(df_pieces))
    with col2:
        if not df_pieces.empty:
            alertes = df_pieces[df_pieces["Quantité"] <= df_pieces["Alerte Min"]]
            st.metric("Pièces en alerte rupture", len(alertes))
        else:
            st.metric("Pièces en alerte rupture", 0)

    st.subheader("🔍 Rechercher un article")
    recherche = st.text_input("Tapez une référence ou un nom :").strip().upper()
    
    if recherche and not df_pieces.empty:
        resultat = df_pieces[df_pieces["Référence"].str.contains(recherche, na=False) | df_pieces["Désignation"].str.upper().str.contains(recherche, na=False)]
        if not resultat.empty:
            st.dataframe(resultat, use_container_width=True)
        else:
            st.warning("Aucun article ne correspond à votre recherche.")
    elif not df_pieces.empty:
        st.write("### Liste globale du stock")
        st.dataframe(df_pieces, use_container_width=True)

with tab2:
    st.subheader("📝 Enregistrer une nouvelle pièce")
    with st.form("form_ajout", clear_on_submit=True):
        ref = st.text_input("Référence unique :").strip().upper()
        nom = st.text_input("Désignation / Nom de la pièce :").strip()
        cat = st.text_input("Catégorie (ex: Freinage) :").strip()
        rayon = st.text_input("Rayon / Emplacement :").strip()
        
        c1, c2 = st.columns(2)
        with c1:
            pa = st.number_input("Prix d'achat (€) :", min_value=0.0, step=0.5)
            qte = st.number_input("Stock Initial :", min_value=0, step=1)
        with c2:
            pv = st.number_input("Prix de vente (€) :", min_value=0.0, step=0.5)
            seuil = st.number_input("Seuil d'alerte minimum :", min_value=0, step=1)
            
        submit = st.form_submit_button("💾 Enregistrer dans le stock")
        
        if submit:
            if not ref or not nom:
                st.error("La référence et le nom sont obligatoires.")
            elif not df_pieces.empty and ref in df_pieces["Référence"].values:
                st.error("Cette référence existe déjà dans le système.")
            else:
                nouvelle_ligne = pd.DataFrame([[ref, nom, cat, rayon, pa, pv, qte, seuil]], columns=df_pieces.columns)
                df_pieces = pd.concat([df_pieces, nouvelle_ligne], ignore_index=False)
                df_pieces.to_csv(FILE_PIECES, index=False)
                st.success(f"La pièce '{nom}' a bien été ajoutée au site !")
                st.rerun()

with tab3:
    st.subheader("⚡ Mouvement de stock")
    ref_mouv = st.text_input("Référence de la pièce concernée :", key="ref_mouv").strip().upper()
    
    if ref_mouv:
        if not df_pieces.empty and ref_mouv in df_pieces["Référence"].values:
            piece_info = df_pieces[df_pieces["Référence"] == ref_mouv].iloc[0]
            st.info(f"Pièce sélectionnée : **{piece_info['Désignation']}** | Stock actuel : **{piece_info['Quantité']}**")
            
            type_m = st.radio("Nature de l'opération :", ["💸 Vente Client (Sortie)", "📦 Réception Fournisseur (Entrée)"])
            qte_m = st.number_input("Quantité concernée :", min_value=1, step=1)
            
            if st.button("Valider l'opération"):
                idx = df_pieces[df_pieces["Référence"] == ref_mouv].index
                action_ok = False
                
                if "Vente" in type_m:
                    if piece_info['Quantité'] < qte_m:
                        st.error("Action impossible : le stock disponible est insuffisant.")
                    else:
                        df_pieces.at[idx[0], "Quantité"] -= qte_m
                        action_ok = True
                else:
                    df_pieces.at[idx[0], "Quantité"] += qte_m
                    action_ok = True
                    
                if action_ok:
                    df_pieces.to_csv(FILE_PIECES, index=False)
                    n_mouv = pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M"), ref_mouv, piece_info['Désignation'], type_m, qte_m]], columns=df_mouv.columns)
                    df_mouv = pd.concat([df_mouv, n_mouv], ignore_index=False)
                    df_mouv.to_csv(FILE_MOUVEMENTS, index=False)
                    st.success("Le stock a été mis à jour instantanément !")
                    st.rerun()
        else:
            st.error("Cette référence
