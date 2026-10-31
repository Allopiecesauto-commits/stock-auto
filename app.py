import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", layout="wide")

F_PIECES, F_VENTES = "web_pieces.csv", "web_ventes.csv"

# Initialisation des deux fichiers de base
if not os.path.exists(F_PIECES):
    pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]).to_csv(F_PIECES, index=False)
if not os.path.exists(F_VENTES):
    pd.DataFrame(columns=["Date", "Référence", "Désignation", "Quantité", "Total Achat", "Total Vente", "Tiers", "Paiement"]).to_csv(F_VENTES, index=False)

df_p = pd.read_csv(F_PIECES)
df_v = pd.read_csv(F_VENTES)

if not df_v.empty and len(df_v.columns) != 8:
    df_v = pd.DataFrame(columns=["Date", "Référence", "Désignation", "Quantité", "Total Achat", "Total Vente", "Tiers", "Paiement"])
    df_v.to_csv(F_VENTES, index=False)

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3 = st.tabs(["📊 Accueil, Prix & Modifications", "📦 Créer Nouvelle Fiche", "📈 Bilan & Caisse"])

# Initialisation des états d'affichage
for idx, row in df_p.iterrows():
    r_id = str(row['Référence'])
    if f"pop_v_{r_id}" not in st.session_state:
        st.session_state[f"pop_v_{r_id}"] = False
    if f"pop_a_{r_id}" not in st.session_state:
        st.session_state[f"pop_a_{r_id}"] = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL, MODIFICATIONS EN DIRECT & VENTES
# ---------------------------------------------------------------------
with t1:
    st.subheader("Tableau de bord et modifications en direct")
    recherche = st.text_input("Saisir un nom ou une référence pour chercher :", key="main_search").strip().upper()
    
    df_affichage = df_p.copy()
    if recherche and not df_p.empty:
        df_affichage = df_p[df_p["Référence"].astype(str).str.contains(recherche, na=False) | df_affichage["Désignation"].astype(str).str.upper().str.contains(recherche, na=False)]
        
    if not df_affichage.empty:
        st.write("---")
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1.5, 1, 2.5])
        col_h1.markdown("**Référence**")
        col_h2.markdown("**Désignation**")
        col_h3.markdown("**Catégorie**")
        col_h4.markdown("**P. Achat (€)**")
        col_h5.markdown("**P. Vente (€)**")
        col_h6.markdown("**Stock Actuel**")
        col_h7.markdown("**Alerte**")
        col_h8.markdown("**Actions**")
        st.write("---")

        for idx, row in df_affichage.iterrows():
            ref_id = str(row['Référence'])
            prefix = "⚠️ " if row['Quantité'] <= row['Alerte Min'] else ""
            
            col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7, col_r8 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1.5, 1, 2.5])
            
            # Textes fixes non modifiables en direct
            col_r1.write(f"{prefix}{ref_id}")
            col_r2.write(row['Désignation'])
            col_r3.write(row['Catégorie'])
            
            # MODIFICATION DIRECTE : Cases numériques éditables directement dans la ligne
            n_pa = col_r4.number_input("Achat", min_value=0.0, value=float(row['Prix Achat']), step=0.5, key=f"pa_{ref_id}", label_visibility="collapsed")
            n_pv = col_r5.number_input("Vente", min_value=0.0, value=float(row['Prix Vente']), step=0.5, key=f"pv_{ref_id}", label_visibility="collapsed")
            n_qt = col_r6.number_input("Stock", min_value=0, value=int(row['Quantité']), step=1, key=f"qt_{ref_id}", label_visibility="collapsed")
            
            col_r7.write(str(row['Alerte Min']))
            
            # Boutons d'action rapides
            c_btn1, c_btn2, c_btn3 = col_r8.columns(3)
            
            # Bouton de vente rapide
            if c_btn1.button("💸", key=f"btn_v_{ref_id}", help="Enregistrer une vente"):
                st.session_state[f"pop_v_{ref_id}"] = not st.session_state[f"pop_v_{ref_id}"]
                
            # Bouton Disquette de sauvegarde des modifications de la ligne
            if c_btn2.button("💾", key=f"btn_s_{ref_id}", help="Sauvegarder les changements de prix/stock"):
                df_p.loc[df_p["Référence"] == ref_id, ["Prix Achat", "Prix Vente", "Quantité"]] = [n_pa, n_pv, n_qt]
                df_p.to_csv(F_PIECES, index=False)
                st.success(f"Fiche {ref_id} mise à jour !")
                st.rerun()
                
            # Bouton de suppression de la fiche
            if c_btn3.button("❌", key=f"btn_a_{ref_id}", help="Supprimer la fiche"):
                st.session_state[f"pop_a_{ref_id}"] = not st.session_state[f"pop_a_{ref_id}"]
                
            # Zone de Vente rapide déroulée
            if st.session_state[f"pop_v_{ref_id}"]:
                st.info(f"💸 Enregistrer une vente pour : {ref_id}")
                q_client = st.text_input("Nom du Client :", value="Client comptoir", key=f"qc_{ref_id}").strip()
                q_vendu = st.number_input("Quantité vendue :", min_value=1, max_value=int(row['Quantité']) if int(row['Quantité']) > 0 else 1, step=1, key=f"qv_{ref_id}")
                q_paye = st.radio("Mode de règlement :", ["💵 Espèces", "💳 Carte Bancaire"], horizontal=True, key=f"qp_{ref_id}")
                
                if st.button("Confirmer la vente", key=f"conf_v_{ref_id}", type="primary"):
                    if row['Quantité'] < q_vendu:
                        st.error("Stock insuffisant !")
                    elif not q_client:
                        st.error("Le nom du client est obligatoire.")
                    else:
                        df_p.loc[df_p["Référence"] == ref_id, "Quantité"] -= q_vendu
                        df_p.to_csv(F_PIECES, index=False)
                        pa_t = float(row["Prix Achat"] * q_vendu)
                        pv_t = float(row["Prix Vente"] * q_vendu)
                        nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], int(q_vendu), float(pa_t), float(pv_t), str(q_client), str(q_paye)]], columns=df_v.columns)
                        pd.concat([df_v, nouvel_hist], ignore_index=True).to_csv(F_VENTES, index=False)
                        st.session_state[f"pop_v_{ref_id}"] = False
                        st.success("Vente enregistrée !")
                        st.rerun()
                        
            if st.session_state[f"pop_a_{ref_id}"]:
                st.warning(f"Supprimer définitivement la fiche {ref_id} ?")
                if st.button("Confirmer la suppression", key=f"conf_del_{ref_id}", type="primary"):
                    df_p = df_p[df_p["Référence"] != ref_id]
                    df_p.to_csv(F_PIECES, index=False)
                    st.session_state[f"pop_a_{ref_id}"] = False
                    st.rerun()
            st.write("---")
    if df_affichage.empty:
        st.info("Aucun article trouvé dans votre stock.")

# ---------------------------------------------------------------------
# ONGLET 2 : RESTE UNIQUEMENT POUR CRÉER UNE NOUVELLE RÉFÉRENCE BLANCHE
# ---------------------------------------------------------------------
with t2:
    st.subheader("📦 Ajouter une nouvelle référence au magasin")
    ref_add = st.text_input("Référence de la pièce (Ex: 70AH) :", key="r_add").strip().upper()
    nom_add = st.text_input("Nom / Désignation de la pièce :", key="n_add").strip()
    cat_add = st.text_input("Catégorie (Ex: Batterie) :", key="c_add").strip()
    col_c1, col_c2 = st.columns(2)
    pa_add = col_c1.number_input("Prix d'achat unitaire (€) :", min_value=0.0, step=0.5, key="pa_add_f")
    pv_add = col_c2.number_input("Prix de vente unitaire (€) :", min_value=0.0, step=0.5, key="pv_add_f")
    stock_add = col_c1.number_input("Stock Initial reçu :", min_value=0, step=1, key="s_add_f")
    seuil_add = col_c2.number_input("Seuil d'alerte minimum :", min_value=0, step=1, key="seuil_add_f")
    
    if st.button("➕ Créer la pièce et l'ajouter au magasin", type="primary", use_container_width=True):
        if not ref_add or not nom_add:
            st.error("La Référence et le Nom de la pièce sont obligatoires.")
        elif ref_add in df_p["Référence"].astype(str).values:
            st.error("Cette référence existe déjà ! Modifiez-la directement sur le premier onglet.")
        else:
            nouvelle_ligne = pd.DataFrame([[ref_add, nom_add, cat_add, pa_add, pv_add, stock_add, seuil_add]], columns=df_p.columns)
            df_p = pd.concat([df_p, nouvelle_ligne], ignore_index=True)
            df_p.to_csv(F_PIECES, index=False)
            st.success("Nouvelle référence ajoutée avec succès !")
            st.rerun()

# ---------------------------------------------------------------------
# ONGLET 3 : COMPTABILITÉ & CAISSE DU JOUR
# ---------------------------------------------------------------------
with t3:
    st.subheader("📈 Synthèse de la caisse et des bénéfices")
    if not df_v.empty:
        df_v["Quantité"] = pd.to_numeric(df_v["Quantité"], errors='coerce').fillna(0).astype(int)
        df_v["Total Achat"] = pd.to_numeric(df_v["Total Achat"], errors='coerce').fillna(0.0).astype(float)
        df_v["Total Vente"] = pd.to_numeric(df_v["Total Vente"], errors='coerce').fillna(0.0).astype(float)
        
        dates_uniques = df_v["Date"].unique()
        lignes_bilan = []
        for d in dates_uniques:
            df_jour = df_v[df_v["Date"] == d]
            q_v = int(df_jour["Quantité"].sum())
            e_v = float(df_jour[df_jour["Paiement"] == "💵 Espèces"]["Total Vente"].sum())
            c_v = float(df_jour[df_jour["Paiement"] == "💳 Carte Bancaire"]["Total Vente"].sum())
            tot_ca = float(df_jour["Total Vente"].sum())
            tot_pa = float(df_jour["Total Achat"].sum())
            benef = tot_ca - tot_pa
            lignes_bilan.append([d, q_v, e_v, c_v, tot_ca, benef])
            
