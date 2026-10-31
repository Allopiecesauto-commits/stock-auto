import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", layout="wide")

F_PIECES, F_VENTES = "web_pieces.csv", "web_ventes.csv"

# Initialisation des fichiers avec les structures exactes
if not os.path.exists(F_PIECES):
    pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]).to_csv(F_PIECES, index=False)
if not os.path.exists(F_VENTES):
    pd.DataFrame(columns=["Date", "Référence", "Désignation", "Quantité", "Total Vente", "Tiers", "Paiement"]).to_csv(F_VENTES, index=False)

df_p = pd.read_csv(F_PIECES)
df_v = pd.read_csv(F_VENTES)

# Sécurité : Réinitialisation forcée si le fichier d'historique s'est décalé
if not df_v.empty and len(df_v.columns) != 7:
    df_v = pd.DataFrame(columns=["Date", "Référence", "Désignation", "Quantité", "Total Vente", "Tiers", "Paiement"])
    df_v.to_csv(F_VENTES, index=False)

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3 = st.tabs(["📊 Accueil & Actions rapides", "📦 Créer Nouvelle Fiche", "📈 Historique des Ventes"])

if "filtre_alerte" not in st.session_state:
    st.session_state.filtre_alerte = False

# Initialisation des états d'affichage
for idx, row in df_p.iterrows():
    r_id = str(row['Référence'])
    if f"pop_act_{r_id}" not in st.session_state:
        st.session_state[f"pop_act_{r_id}"] = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL & GESTION DU STOCK DIRECT (TRIÉ PAR CATÉGORIE)
# ---------------------------------------------------------------------
with t1:
    st.subheader("📋 Liste du stock et Actions en direct")
    
    # Boutons d'alerte et compteurs remis en place
    alt_df = df_p[df_p["Quantité"] <= df_p["Alerte Min"]] if not df_p.empty else pd.DataFrame()
    nb_alt = len(alt_df)
    
    c1, c2 = st.columns(2)
    if c1.button(f"📋 Total Références : {len(df_p)}", use_container_width=True, key="btn_tot_ref"):
        st.session_state.filtre_alerte = False
        st.rerun()
    if c2.button(f"⚠️ Alertes rupture : {nb_alt}", use_container_width=True, type="primary" if nb_alt > 0 else "secondary", key="btn_alt_ruf"):
        st.session_state.filtre_alerte = True
        st.rerun()

    # Application du filtre d'alerte rupture si cliqué
    df_affichage = alt_df if st.session_state.filtre_alerte else df_p.copy()

    if st.session_state.filtre_alerte:
        st.warning("🚨 Affichage des pièces en alerte rupture uniquement")

    # Barre de recherche de texte
    req = st.text_input("Rechercher (Réf ou Nom) :", key="search_bar").strip().upper()
    if req and not df_affichage.empty:
        df_affichage = df_affichage[df_affichage["Référence"].astype(str).str.contains(req, na=False) | df_affichage["Désignation"].astype(str).str.upper().str.contains(req, na=False)]
        
    # CLASSEMENT PAR ORDRE ALPHABÉTIQUE DES CATÉGORIES
    if not df_affichage.empty:
        df_affichage = df_affichage.sort_values(by=["Catégorie", "Référence"], ascending=[True, True])
        
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
            
            if col_r8.button("🛠️ Gérer / Vendre", key=f"btn_act_{ref_id}", use_container_width=True):
                st.session_state[f"pop_act_{ref_id}"] = not st.session_state[f"pop_act_{ref_id}"]
                
            if st.session_state[f"pop_act_{ref_id}"]:
                st.write("")
                st.markdown(f"⚙️ **PANNEAU DE CONFIGURATION DIRECTE : {ref_id}**")
                c_panel1, c_panel2 = st.columns(2)
                
                with c_panel1:
                    st.markdown("### 💸 Enregistrer une Vente rapide")
                    q_client = st.text_input("Nom du Client :", value="Client comptoir", key=f"qc_{ref_id}").strip()
                    q_vendu = st.number_input("Quantité à vendre :", min_value=1, max_value=int(row['Quantité']) if int(row['Quantité']) > 0 else 1, step=1, key=f"qv_{ref_id}")
                    q_paye = st.radio("Mode de règlement :", ["💵 Espèces", "💳 Carte Bancaire"], horizontal=True, key=f"qp_{ref_id}")
                    
                    if st.button("Confirmer la vente", key=f"conf_v_{ref_id}", type="primary", use_container_width=True):
                        if row['Quantité'] < q_vendu:
                            st.error("Stock insuffisant !")
                        else:
                            df_p.loc[df_p["Référence"] == ref_id, "Quantité"] -= q_vendu
                            df_p.to_csv(F_PIECES, index=False)
                            
                            tot_v = float(row["Prix Vente"] * q_vendu)
                            nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], int(q_vendu), float(tot_v), str(q_client), str(q_paye)]], columns=df_v.columns)
                            df_v = pd.concat([df_v, nouvel_hist], ignore_index=True)
                            df_v.to_csv(F_VENTES, index=False)
                            
                            st.session_state[f"pop_act_{ref_id}"] = False
                            st.success("Vente enregistrée !")
                            st.rerun()
                        
                with c_panel2:
                    st.markdown("### 📦 Ajuster les prix ou le stock")
                    n_pa = st.number_input("Prix d'Achat unitaire (€) :", min_value=0.0, value=float(row['Prix Achat']), step=0.5, key=f"pa_{ref_id}")
                    n_pv = st.number_input("Prix de Vente unitaire (€) :", min_value=0.0, value=float(row['Prix Vente']), step=0.5, key=f"pv_{ref_id}")
                    n_qt = st.number_input("Modifier le Stock (Ajustement) :", min_value=0, value=int(row['Quantité']), step=1, key=f"qt_{ref_id}")
                    
                    if st.button("💾 Sauvegarder les modifications", key=f"save_edit_{ref_id}", use_container_width=True):
                        df_p.loc[df_p["Référence"] == ref_id, ["Prix Achat", "Prix Vente", "Quantité"]] = [n_pa, n_pv, n_qt]
                        df_p.to_csv(F_PIECES, index=False)
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.success("Données enregistrées !")
                        st.rerun()
                        
                    if st.button("🗑️ Effacer la fiche produit", key=f"del_{ref_id}", type="secondary", use_container_width=True):
                        df_p = df_p[df_p["Référence"] != ref_id]
                        df_p.to_csv(F_PIECES, index=False)
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.success("Fiche produit effacée.")
                        st.rerun()
                st.write("---")
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
            st.error("Cette référence existe déjà !")
        else:
            nouvelle_ligne = pd.DataFrame([[ref_add, nom_add, cat_add, pa_add, pv_add, stock_add, seuil_add]], columns=df_p.columns)
            df_p = pd.concat([df_p, nouvelle_ligne], ignore_index=True)
            df_p.to_csv(F_PIECES, index=False)
            st.success("Nouvelle référence ajoutée au catalogue !")
            st.rerun()

# ---------------------------------------------------------------------
# ONGLET 3 : HISTORIQUE DES VENTES EN DIRECT (PLATE ET ANTI-PLANTAGE)
# ---------------------------------------------------------------------
with t3:
