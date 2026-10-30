import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", layout="wide")

F_PIECES, F_MOUV = "web_pieces.csv", "web_mouvements.csv"

# Initialisation des fichiers
if not os.path.exists(F_PIECES):
    pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]).to_csv(F_PIECES, index=False)
if not os.path.exists(F_MOUV):
    pd.DataFrame(columns=["Date", "Référence", "Type", "Quantité", "Total Achat", "Total Vente", "Tiers", "Paiement"]).to_csv(F_MOUV, index=False)

df_p = pd.read_csv(F_PIECES)
df_m = pd.read_csv(F_MOUV)

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3, t4, t5 = st.tabs(["📊 Accueil & Stock", "📦 Ajouter / Modifier", "📥 Commande Fournisseur", "📤 Retour Fournisseur", "📈 Bilans & Caisse"])

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL & RECHERCHE
# ---------------------------------------------------------------------
with t1:
    st.subheader("Liste du stock en magasin")
    recherche = st.text_input("Saisir un nom ou une référence pour chercher :").strip().upper()
    
    if not df_p.empty:
        if recherche:
            df_filtre = df_p[df_p["Référence"].astype(str).str.contains(recherche, na=False) | df_p["Désignation"].astype(str).str.upper().str.contains(recherche, na=False)]
            st.dataframe(df_filtre, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_p, use_container_width=True, hide_index=True)
    else:
        st.info("Le catalogue est vide pour le moment.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER OU MODIFIER UNE FICHE
# ---------------------------------------------------------------------
with t2:
    st.subheader("📦 Créer ou Modifier une pièce")
    ref_add = st.text_input("Référence unique (Ex: 70AH) :", key="r_add").strip().upper()
    nom_add = st.text_input("Nom / Désignation de la pièce :", key="n_add").strip()
    cat_add = st.text_input("Catégorie (Ex: Batterie) :", key="c_add").strip()
    pa_add = st.number_input("Prix d'achat unitaire (€) :", min_value=0.0, step=0.5, key="pa_add")
    pv_add = st.number_input("Prix de vente unitaire (€) :", min_value=0.0, step=0.5, key="pv_add")
    stock_add = st.number_input("Stock de départ (Uniquement pour une création) :", min_value=0, step=1, key="s_add")
    seuil_add = st.number_input("Seuil d'alerte minimum :", min_value=0, step=1, key="seuil_add")
    
    if st.button("💾 Enregistrer la pièce dans le catalogue", type="primary", use_container_width=True):
        if not ref_add or not nom_add:
            st.error("La Référence et le Nom sont obligatoires.")
        else:
            if ref_add in df_p["Référence"].astype(str).values:
                df_p.loc[df_p["Référence"] == ref_add, ["Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Alerte Min"]] = [nom_add, cat_add, pa_add, pv_add, seuil_add]
                st.success("Modifications enregistrées !")
            else:
                nouvelle_ligne = pd.DataFrame([[ref_add, nom_add, cat_add, pa_add, pv_add, stock_add, seuil_add]], columns=df_p.columns)
                df_p = pd.concat([df_p, nouvelle_ligne], ignore_index=True)
                st.success("Nouvelle pièce ajoutée au catalogue !")
            df_p.to_csv(F_PIECES, index=False)
            st.rerun()

# ---------------------------------------------------------------------
# ONGLET 3 : COMMANDE FOURNISSEUR & VENTES
# ---------------------------------------------------------------------
with t3:
    st.subheader("📥 Enregistrer une Vente ou une Entrée Fournisseur")
    ref_mouv = st.text_input("Référence de la pièce concernée :", key="r_mouv").strip().upper()
    nom_tiers = st.text_input("Nom du Client ou du Fournisseur :", key="t_mouv").strip()
    qte_mouv = st.number_input("Quantité de pièces :", min_value=1, step=1, value=1, key="q_mouv")
    mode_reglement = st.radio("Mode de règlement (Pour les ventes uniquement) :", ["💵 Espèces", "💳 Carte Bancaire"], horizontal=True)
    
    col_v, col_a = st.columns(2)
    
    if col_v.button("💸 Valider la Vente (Sortie de stock)", use_container_width=True):
        if not ref_mouv or not nom_tiers:
            st.error("Veuillez remplir la référence et le nom du client.")
        elif ref_mouv not in df_p["Référence"].astype(str).values:
            st.error("Cette référence n'existe pas.")
        else:
            idx = df_p[df_p["Référence"] == ref_mouv].index[0]
            stock_actuel = int(df_p.at[idx, "Quantité"])
            if stock_actuel < qte_mouv:
                st.error(f"Stock insuffisant ! Il ne reste que {stock_actuel} pièces.")
            else:
                df_p.at[idx, "Quantité"] -= qte_mouv
                df_p.to_csv(F_PIECES, index=False)
                
                pa_t = float(df_p.at[idx, "Prix Achat"] * qte_mouv)
                pv_t = float(df_p.at[idx, "Prix Vente"] * qte_mouv)
                
                nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_mouv, "Vente", int(qte_mouv), pa_t, pv_t, nom_tiers, mode_reglement]], columns=df_m.columns)
                df_m = pd.concat([df_m, nouvel_hist], ignore_index=True)
                df_m.to_csv(F_MOUV, index=False)
                st.success("Vente enregistrée avec succès !")
                st.rerun()

    if col_a.button("📦 Valider la Livraison (Entrée de stock)", use_container_width=True):
        if not ref_mouv or not nom_tiers:
            st.error("Veuillez remplir la référence et le nom du fournisseur.")
        elif ref_mouv not in df_p["Référence"].astype(str).values:
            st.error("Cette référence n'existe pas.")
        else:
            idx = df_p[df_p["Référence"] == ref_mouv].index[0]
            df_p.at[idx, "Quantité"] += qte_mouv
            df_p.to_csv(F_PIECES, index=False)
            
            pa_t = float(df_p.at[idx, "Prix Achat"] * qte_mouv)
            
            nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_mouv, "Livraison", int(qte_mouv), pa_t, 0.0, nom_tiers, "Fournisseur"]], columns=df_m.columns)
            df_m = pd.concat([df_m, nouvel_hist], ignore_index=True)
            df_m.to_csv(F_MOUV, index=False)
            st.success("Livraison fournisseur enregistrée !")
            st.rerun()

# ---------------------------------------------------------------------
# ONGLET 4 : RETOUR FOURNISSEUR
# ---------------------------------------------------------------------
with t4:
    st.subheader("📤 Formulaire de Retour Marchandise")
    ref_ret = st.text_input("Référence de la pièce à renvoyer :", key="r_ret").strip().upper()
    fourn_ret = st.text_input("Nom du Fournisseur :", key="f_ret").strip()
    qte_ret = st.number_input("Quantité à retourner :", min_value=1, step=1, value=1, key="q_ret")
    prix_ret = st.number_input("Prix d'achat unitaire remboursé par le fournisseur (€) :", min_value=0.0, step=0.5, key="p_ret")
    
    if st.button("📤 Valider le Retour au fournisseur", type="primary", use_container_width=True):
        if not ref_ret or not fourn_ret:
            st.error("Veuillez remplir la référence et le nom du fournisseur.")
        elif ref_ret not in df_p["Référence"].astype(str).values:
            st.error("Cette référence n'existe pas dans le système.")
        else:
            idx = df_p[df_p["Référence"] == ref_ret].index[0]
            stock_actuel = int(df_p.at[idx, "Quantité"])
            if stock_actuel < qte_ret:
                st.error(f"Stock insuffisant en magasin ! Vous n'avez que {stock_actuel} pièces.")
            else:
                df_p.at[idx, "Quantité"] -= qte_ret
                df_p.to_csv(F_PIECES, index=False)
                
                total_rembourse = float(prix_ret * qte_ret)
                nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_ret, "Retour", int(qte_ret), total_rembourse, 0.0, fourn_ret, "Remboursement"]], columns=df_m.columns)
                df_m = pd.concat([df_m, nouvel_hist], ignore_index=True)
                df_m.to_csv(F_MOUV, index=False)
                st.success("Retour marchandise validé et enregistré !")
                st.rerun()

# ---------------------------------------------------------------------
# ONGLET 5 : COMPTABILITÉ & CAISSE (JOUR PAR JOUR SIMPLIFIÉ)
# ---------------------------------------------------------------------
with t5:
    st.subheader("📈 Synthèse de la caisse et des bénéfices")
    
    if not df_m.empty:
        df_m["Quantité"] = pd.to_numeric(df_m["Quantité"], errors='coerce').fillna(0).astype(int)
        df_m["Total Achat"] = pd.to_numeric(df_m["Total Achat"], errors='coerce').fillna(0.0).astype(float)
        df_m["Total Vente"] = pd.to_numeric(df_m["Total Vente"], errors='coerce').fillna(0.0).astype(float)
        
        # Séparation propre
        v_esp = df_m[(df_m["Type"] == "Vente") & (df_m["Paiement"] == "💵 Espèces")]
        v_cb = df_m[(df_m["Type"] == "Vente") & (df_m["Paiement"] == "💳 Carte Bancaire")]
        ret_fourn = df_m[df_m["Type"] == "Retour"]
        t_ventes = df_m[df_m["Type"] == "Vente"]
        
        # Groupements simples
        ca_esp = v_esp.groupby("Date")["Total Vente"].sum()
        ca_cb = v_cb.groupby("Date")["Total Vente"].sum()
        ret_val = ret_fourn.groupby("Date")["Total Achat"].sum()
        
        v_qte = t_ventes.groupby("Date")["Quantité"].sum()
        v_ca = t_ventes.groupby("Date")["Total Vente"].sum()
        v_pa = t_ventes.groupby("Date")["Total Achat"].sum()
        
        # Tableau final fusionné
        dates_uniques = df_m["Date"].unique()
        lignes_bilan = []
        
        for d in dates_uniques:
            q_v = int(v_qte.get(d, 0))
            e_v = float(ca_esp.get(d, 0.0))
            c_v = float(ca_cb.get(d, 0.0))
