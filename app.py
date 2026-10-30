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

# Nettoyage forcé de sécurité pour l'historique
if not df_m.empty and len(df_m.columns) != 8:
    df_m = pd.DataFrame(columns=["Date", "Référence", "Type", "Quantité", "Total Achat", "Total Vente", "Tiers", "Paiement"])
    df_m.to_csv(F_MOUV, index=False)

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3, t4, t5 = st.tabs(["📊 Accueil & Stock", "📦 Ajouter / Modifier", "📥 Commande Fournisseur", "📤 Retour Fournisseur", "📈 Bilans & Caisse"])

# Initialisation des états d'affichage
for idx, row in df_p.iterrows():
    if f"pop_v_{row['Référence']}" not in st.session_state:
        st.session_state[f"pop_v_{row['Référence']}"] = False
    if f"pop_a_{row['Référence']}" not in st.session_state:
        st.session_state[f"pop_a_{row['Référence']}"] = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL & RECHERCHE (VENTE COMPTOIR DIRECTE)
# ---------------------------------------------------------------------
with t1:
    st.subheader("Liste du stock en magasin")
    recherche = st.text_input("Saisir un nom ou une référence pour chercher :", key="main_search").strip().upper()
    
    df_affichage = df_p
    if recherche and not df_p.empty:
        df_affichage = df_p[df_p["Référence"].astype(str).str.contains(recherche, na=False) | df_p["Désignation"].astype(str).str.upper().str.contains(recherche, na=False)]
        
    if not df_affichage.empty:
        st.write("---")
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([2, 2.5, 2, 1.2, 1.2, 1, 1, 2.5])
        col_h1.markdown("**Référence**")
        col_h2.markdown("**Désignation**")
        col_h3.markdown("**Catégorie**")
        col_h4.markdown("**P. Achat**")
        col_h5.markdown("**P. Vente**")
        col_h6.markdown("**Stock**")
        col_h7.markdown("**Seuil**")
        col_h8.markdown("**Actions**")
        st.write("---")

        for idx, row in df_affichage.iterrows():
            ref_id = row['Référence']
            prefix = "⚠️ " if row['Quantité'] <= row['Alerte Min'] else ""
            
            col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7, col_r8 = st.columns([2, 2.5, 2, 1.2, 1.2, 1, 1, 2.5])
            col_r1.write(f"{prefix}{ref_id}")
            col_r2.write(row['Désignation'])
            col_r3.write(row['Catégorie'])
            col_r4.write(f"{row['Prix Achat']} €")
            col_r5.write(f"{row['Prix Vente']} €")
            col_r6.write(f"**{row['Quantité']}**")
            col_r7.write(str(row['Alerte Min']))
            
            c_btn1, c_btn2 = col_r8.columns(2)
            if c_btn1.button("💸", key=f"btn_t_v_{ref_id}"):
                st.session_state[f"pop_v_{ref_id}"] = not st.session_state[f"pop_v_{ref_id}"]
            if c_btn2.button("❌", key=f"btn_t_a_{ref_id}"):
                st.session_state[f"pop_a_{ref_id}"] = not st.session_state[f"pop_a_{ref_id}"]
                
            if st.session_state[f"pop_v_{ref_id}"]:
                st.info(f"💸 Vente rapide pour : {ref_id}")
                q_client = st.text_input("Nom du Client :", value="Client comptoir", key=f"qc_{ref_id}").strip()
                q_vendu = st.number_input("Quantité à vendre :", min_value=1, max_value=int(row['Quantité']) if int(row['Quantité']) > 0 else 1, step=1, key=f"qv_{ref_id}")
                q_paye = st.radio("Mode de règlement :", ["💵 Espèces", "💳 Carte Bancaire"], horizontal=True, key=f"qp_{ref_id}")
                
                if st.button("Confirmer la vente", key=f"conf_v_action_{ref_id}", type="primary"):
                    if row['Quantité'] < q_vendu:
                        st.error("Stock insuffisant !")
                    elif not q_client:
                        st.error("Le nom du client est obligatoire.")
                    else:
                        df_p.at[idx, "Quantité"] -= q_vendu
                        df_p.to_csv(F_PIECES, index=False)
                        pa_t = float(row["Prix Achat"] * q_vendu)
                        pv_t = float(row["Prix Vente"] * q_vendu)
                        nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, "Vente", int(q_vendu), float(pa_t), float(pv_t), str(q_client), str(q_paye)]], columns=df_m.columns)
                        pd.concat([df_m, nouvel_hist], ignore_index=True).to_csv(F_MOUV, index=False)
                        st.session_state[f"pop_v_{ref_id}"] = False
                        st.rerun()
                        
            if st.session_state[f"pop_a_{ref_id}"]:
                st.warning(f"Supprimer définitivement la fiche {ref_id} ?")
                if st.button("Confirmer la suppression", key=f"conf_t_del_{ref_id}", type="primary"):
                    df_p = df_p.drop(idx)
                    df_p.to_csv(F_PIECES, index=False)
                    st.session_state[f"pop_a_{ref_id}"] = False
                    st.rerun()
            st.write("---")
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
# ONGLET 3 : COMMANDE FOURNISSEUR (FORMULAIRE FIXE)
# ---------------------------------------------------------------------
with t3:
    st.subheader("📥 Enregistrer une Vente ou une Entrée Fournisseur")
    ref_mouv = st.text_input("Référence de la pièce concernée :", key="r_mouv").strip().upper()
    nom_tiers = st.text_input("Nom du Client ou du Fournisseur :", value="Client comptoir", key="t_mouv").strip()
    qte_mouv = st.number_input("Quantité de pièces :", min_value=1, step=1, value=1, key="q_mouv")
    mode_reglement = st.radio("Mode de règlement (Pour les ventes uniquement) :", ["💵 Espèces", "💳 Carte Bancaire"], horizontal=True)
    
    col_v, col_a = st.columns(2)
    
    if col_v.button("💸 Valider la Vente (Sortie de stock)", use_container_width=True, key="btn_v_form"):
        if not ref_mouv or not nom_tiers:
            st.error("Veuillez remplir la référence et le nom du client.")
        elif ref_mouv not in df_p["Référence"].astype(str).values:
            st.error("Cette référence de pièce n'existe pas.")
        else:
            idx = df_p[df_p["Référence"] == ref_mouv].index
            stock_actuel = int(df_p.at[idx, "Quantité"])
            if stock_actuel < qte_mouv:
                st.error(f"Stock insuffisant ! Il ne reste que {stock_actuel} pièces.")
            else:
                df_p.at[idx, "Quantité"] -= qte_mouv
                df_p.to_csv(F_PIECES, index=False)
                pa_t = float(df_p.at[idx, "Prix Achat"] * qte_mouv)
                pv_t = float(df_p.at[idx, "Prix Vente"] * qte_mouv)
                nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_mouv, "Vente", int(qte_mouv), float(pa_t), float(pv_t), str(nom_tiers), str(mode_reglement)]], columns=df_m.columns)
                pd.concat([df_m, nouvel_hist], ignore_index=True).to_csv(F_MOUV, index=False)
                st.success("Vente enregistrée avec succès !")
                st.rerun()

    if col_a.button("📦 Valider la Livraison (Entrée de stock)", use_container_width=True, key="btn_a_form"):
        if not ref_mouv or not nom_tiers:
            st.error("Veuillez remplir la référence et le nom du fournisseur.")
        elif ref_mouv not in df_p["Référence"].astype(str).values:
            st.error("Cette référence de pièce n'existe pas.")
        else:
