import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Stock Auto", layout="wide")

F_PIECES = "web_pieces.csv"

# Un seul fichier ultra-simple pour le stock
if not os.path.exists(F_PIECES):
    pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]).to_csv(F_PIECES, index=False)

df_p = pd.read_csv(F_PIECES)

st.title("🚗 Gestion de Stock Auto")

t1, t2 = st.tabs(["📊 Accueil & Actions rapides", "📦 Créer Nouvelle Fiche"])

# Initialisation des états d'affichage
for idx, row in df_p.iterrows():
    r_id = str(row['Référence'])
    if f"pop_act_{r_id}" not in st.session_state:
        st.session_state[f"pop_act_{r_id}"] = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL & GESTION DU STOCK DIRECT
# ---------------------------------------------------------------------
with t1:
    st.subheader("📋 Liste du stock et Actions en direct")
    recherche = st.text_input("Saisir un nom ou une référence pour chercher :", key="main_search").strip().upper()
    
    df_affichage = df_p.copy()
    if recherche and not df_p.empty:
        df_affichage = df_p[df_p["Référence"].astype(str).str.contains(recherche, na=False) | df_p["Désignation"].astype(str).str.upper().str.contains(recherche, na=False)]
        
    if not df_affichage.empty:
        st.write("---")
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([1.5, 2.5, 1.5, 1.2, 1.2, 1.2, 1.2, 2])
        col_h1.markdown("**Référence**")
        col_h2.markdown("**Désignation**")
        col_h3.markdown("**Catégorie**")
        col_h4.markdown("**P. Achat**")
        col_h5.markdown("**P. Vente**")
        col_h6.markdown("**En Stock**")
        col_h7.markdown("**Seuil Alerte**")
        col_h8.markdown("**Gérer la pièce**")
        st.write("---")

        for idx, row in df_affichage.iterrows():
            ref_id = str(row['Référence'])
            prefix = "⚠️ " if row['Quantité'] <= row['Alerte Min'] else "✅ "
            
            col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7, col_r8 = st.columns([1.5, 2.5, 1.5, 1.2, 1.2, 1.2, 1.2, 2])
            col_r1.write(f"{prefix}{ref_id}")
            col_r2.write(row['Désignation'])
            col_r3.write(row['Catégorie'])
            col_r4.write(f"{row['Prix Achat']} €")
            col_r5.write(f"{row['Prix Vente']} €")
            col_r6.write(f"**{row['Quantité']} pcs**")
            col_r7.write(f"{row['Alerte Min']} pcs")
            
            if col_r8.button("🛠️ Gérer la pièce", key=f"btn_act_{ref_id}", use_container_width=True):
                st.session_state[f"pop_act_{ref_id}"] = not st.session_state[f"pop_act_{ref_id}"]
                
            if st.session_state[f"pop_act_{ref_id}"]:
                st.write("")
                st.markdown(f"⚙️ **PANNEAU DE CONFIGURATION DIRECTE : {ref_id}**")
                c_panel1, c_panel2 = st.columns(2)
                
                with c_panel1:
                    st.markdown("### 📥 Enregistrer une Vente ou Ajuster les prix")
                    n_pa = st.number_input("Prix d'Achat unitaire (€) :", min_value=0.0, value=float(row['Prix Achat']), step=0.5, key=f"pa_{ref_id}")
                    n_pv = st.number_input("Prix de Vente unitaire (€) :", min_value=0.0, value=float(row['Prix Vente']), step=0.5, key=f"pv_{ref_id}")
                    n_qt = st.number_input("Modifier le Stock (Vente ou Arrivage) :", min_value=0, value=int(row['Quantité']), step=1, key=f"qt_{ref_id}")
                    
                    if st.button("💾 Sauvegarder les modifications", key=f"save_edit_{ref_id}", type="primary", use_container_width=True):
                        df_p.loc[df_p["Référence"] == ref_id, ["Prix Achat", "Prix Vente", "Quantité"]] = [n_pa, n_pv, n_qt]
                        df_p.to_csv(F_PIECES, index=False)
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.success("Données enregistrées avec succès !")
                        st.rerun()
                        
                with c_panel2:
                    st.markdown("### ❌ Supprimer définitivement")
                    st.write("Retirer cette pièce de votre catalogue magasin.")
                    if st.button("🗑️ Effacer la fiche produit", key=f"del_{ref_id}", type="secondary", use_container_width=True):
                        df_p = df_p[df_p["Référence"] != ref_id]
                        df_p.to_csv(F_PIECES, index=False)
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.success("Fiche produit effacée.")
                        st.rerun()
                st.write("---")
    if df_affichage.empty:
        st.info("Aucun article trouvé.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER UNE NOUVELLE FICHE PRODUIT BLANCHE
# ---------------------------------------------------------------------
with t2:
    st.subheader("📦 Ajouter une nouvelle référence au magasin")
    ref_add = st.text_input("Référence de la pièce (Ex: 70AH) :", key="r_add").strip().upper()
    nom_add = st.text_input("Nom / Désignation de la pièce :", key="n_add").strip()
    cat_add = st.text_input("Catégorie (Ex: Batterie) :", key="c_add").strip()
    col_c1, col_c2 = st.columns(2)
    pa_add = col_c1.number_input("Prix d'achat unitaire (€) :", min_value=0.0, step=0.5, key="pa_add_f")
    pv_add = col_c2.number_input("Prix de vente unitaire (€) :", min_value=0.0, step=0.5, key="pv_add_f")
    stock_add = col_c1.number_input("Stock de départ reçu :", min_value=0, step=1, key="s_add_f")
    seuil_add = col_c2.number_input("Seuil d'alerte minimum :", min_value=0, step=1, key="seuil_add_f")
    
    if st.button("➕ Créer la pièce et l'ajouter au magasin", type="primary", use_container_width=True):
        if not ref_add or not nom_add:
            st.error("La Référence et le Nom de la pièce sont obligatoires.")
        elif ref_add in df_p["Référence"].astype(str).values:
            st.error("Cette référence existe déjà ! Modifiez son stock directement dans le premier onglet.")
        else:
            nouvelle_ligne = pd.DataFrame([[ref_add, nom_add, cat_add, pa_add, pv_add, stock_add, seuil_add]], columns=df_p.columns)
            df_p = pd.concat([df_p, nouvelle_ligne], ignore_index=True)
            df_p.to_csv(F_PIECES, index=False)
            st.success("Nouvelle référence ajoutée avec succès au catalogue !")
            st.rerun()
