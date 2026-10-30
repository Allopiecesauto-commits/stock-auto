import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", page_icon="🚗", layout="wide")

F_PIECES, F_MOUV = "web_pieces.csv", "web_mouvements.csv"

def charger_donnees():
    cols_pieces = ["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]
    cols_mouv = ["Date", "Référence", "Désignation", "Type", "Quantité", "Prix Achat Total", "Prix Vente Total", "Tiers", "Paiement"]
    
    if not os.path.exists(F_PIECES):
        pd.DataFrame(columns=cols_pieces).to_csv(F_PIECES, index=False)
    if not os.path.exists(F_MOUV):
        pd.DataFrame(columns=cols_mouv).to_csv(F_MOUV, index=False)
        
    df = pd.read_csv(F_PIECES)
    df_m = pd.read_csv(F_MOUV)
    
    df["Référence"] = df["Référence"].astype(str).str.upper().str.strip()
    df["Désignation"] = df["Désignation"].fillna("").astype(str)
    df["Catégorie"] = df["Catégorie"].fillna("").astype(str)
    df["Prix Achat"] = pd.to_numeric(df["Prix Achat"], errors='coerce').fillna(0.0).astype(float)
    df["Prix Vente"] = pd.to_numeric(df["Prix Vente"], errors='coerce').fillna(0.0).astype(float)
    df["Quantité"] = pd.to_numeric(df["Quantité"], errors='coerce').fillna(0).astype(int)
    df["Alerte Min"] = pd.to_numeric(df["Alerte Min"], errors='coerce').fillna(0).astype(int)
    
    return df, df_m

df_p, df_m = charger_donnees()

st.title("🚗 Stock Auto Privé")

# Ajout du nouvel onglet "Retour Fournisseur"
t1, t2, t3, t4, t5 = st.tabs(["📊 Accueil & Recherche", "📦 Ajouter / Modifier", "📥 Commande Fournisseur", "📤 Retour Fournisseur", "📈 Comptabilité & Bilans"])

if "filtre_alerte" not in st.session_state:
    st.session_state.filtre_alerte = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL
# ---------------------------------------------------------------------
with t1:
    alt_df = df_p[df_p["Quantité"] <= df_p["Alerte Min"]] if not df_p.empty else pd.DataFrame()
    nb_alt = len(alt_df)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"📋 Total Références : {len(df_p)}", use_container_width=True, key="btn_tot_ref"):
            st.session_state.filtre_alerte = False
            st.rerun()
    with c2:
        if st.button(f"⚠️ Alertes rupture : {nb_alt}", use_container_width=True, type="primary" if nb_alt > 0 else "secondary", key="btn_alt_ruf"):
            st.session_state.filtre_alerte = True
            st.rerun()

    df_affichage = alt_df if st.session_state.filtre_alerte else df_p

    if st.session_state.filtre_alerte:
        st.warning("🚨 Affichage des pièces en alerte rupture uniquement")

    req = st.text_input("Rechercher (Réf ou Nom) :", key="search_bar").strip().upper()
    if req and not df_affichage.empty:
        df_affichage = df_affichage[df_affichage["Référence"].str.contains(req, na=False) | df_affichage["Désignation"].str.upper().str.contains(req, na=False)]

    if not df_affichage.empty:
        st.write("---")
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([2, 2.5, 2, 1.2, 1.2, 1, 1, 4])
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
            
            col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7, col_r8 = st.columns([2, 2.5, 2, 1.2, 1.2, 1, 1, 4])
            col_r1.write(f"{prefix}{ref_id}")
            col_r2.write(row['Désignation'])
            col_r3.write(row['Catégorie'])
            col_r4.write(f"{row['Prix Achat']} €")
            col_r5.write(f"{row['Prix Vente']} €")
            col_r6.write(f"**{row['Quantité']}**")
            col_r7.write(str(row['Alerte Min']))
            
            # 4 Boutons d'action rapides (Ajout du bouton Retour Fournisseur)
            c_btn1, c_btn2, c_btn3, c_btn4 = col_r8.columns(4)
            if c_btn1.button("💸", key=f"btn_t_v_{ref_id}", help="Vendre"):
                st.session_state[f"pop_v_{ref_id}"] = not st.session_state.get(f"pop_v_{ref_id}", False)
                st.session_state[f"pop_e_{ref_id}"] = False
                st.session_state[f"pop_ret_{ref_id}"] = False
            if c_btn2.button("📥", key=f"btn_t_e_{ref_id}", help="Livraison Fournisseur"):
                st.session_state[f"pop_e_{ref_id}"] = not st.session_state.get(f"pop_e_{ref_id}", False)
                st.session_state[f"pop_v_{ref_id}"] = False
                st.session_state[f"pop_ret_{ref_id}"] = False
            if c_btn3.button("📤", key=f"btn_t_r_{ref_id}", help="Retour Marchandise"):
                st.session_state[f"pop_ret_{ref_id}"] = not st.session_state.get(f"pop_ret_{ref_id}", False)
                st.session_state[f"pop_v_{ref_id}"] = False
                st.session_state[f"pop_e_{ref_id}"] = False
            if c_btn4.button("❌", key=f"btn_t_a_{ref_id}", help="Supprimer la fiche"):
                st.session_state[f"pop_a_{ref_id}"] = not st.session_state.get(f"pop_a_{ref_id}", False)
            
            # Action de VENTE RAPIDE
            if st.session_state.get(f"pop_v_{ref_id}", False):
                st.info(f"💸 Vente rapide pour : {ref_id}")
                q_client = st.text_input("Nom du Client :", value="Client Comptoir", key=f"qc_{ref_id}").strip()
                q_vendu = st.number_input("Quantité à vendre :", min_value=1, max_value=int(row['Quantité']) if int(row['Quantité']) > 0 else 1, step=1, key=f"qv_{ref_id}")
                q_paye = st.radio("Mode de règlement :", ["💵 Espèces", "💳 Carte Bancaire"], horizontal=True, key=f"qp_{ref_id}")
                if st.button("Confirmer la vente", key=f"conf_v_action_{ref_id}", type="primary"):
                    if row['Quantité'] < q_vendu:
                        st.error("Stock insuffisant !")
                    else:
                        df_p.at[idx, "Quantité"] -= q_vendu
                        df_p.to_csv(F_PIECES, index=False)
                        pa_t = float(row["Prix Achat"] * q_vendu)
                        pv_t = float(row["Prix Vente"] * q_vendu)
                        n_mouv = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], "💸 Vente Client (Sortie)", int(q_vendu), float(pa_t), float(pv_t), str(q_client), str(q_paye)]], columns=df_m.columns)
                        df_m = pd.concat([df_m, n_mouv], ignore_index=True)
                        df_m.to_csv(F_MOUV, index=False)
                        st.session_state[f"pop_v_{ref_id}"] = False
                        st.rerun()

            # Action d'ENTRÉE STOCK FOURNISSEUR RAPIDE
            if st.session_state.get(f"pop_e_{ref_id}", False):
                st.success(f"📦 Arrivage fournisseur pour : {ref_id}")
                q_fourn = st.text_input("Nom du Fournisseur :", value="Fournisseur", key=f"qf_{ref_id}").strip()
                q_recu = st.number_input("Quantité de pièces reçues :", min_value=1, step=1, value=1, key=f"qr_{ref_id}")
                if st.button("Confirmer l'entrée stock", key=f"conf_e_action_{ref_id}", type="primary"):
                    df_p.at[idx, "Quantité"] += q_recu
                    df_p.to_csv(F_PIECES, index=False)
                    pa_t = float(row["Prix Achat"] * q_recu)
                    n_mouv = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], "📦 Commande Fournisseur (Entrée)", int(q_recu), float(pa_t), 0.0, str(q_fourn), "Fournisseur"]], columns=df_m.columns)
                    df_m = pd.concat([df_m, n_mouv], ignore_index=True)
                    df_m.to_csv(F_MOUV, index=False)
                    st.session_state[f"pop_e_{ref_id}"] = False
                    st.rerun()

            # ACTION RAPIDE RETOUR FOURNISSEUR (BOUTON CARTON)
            if st.session_state.get(f"pop_ret_{ref_id}", False):
                st.warning(f"📤 Enregistrer un retour marchandise pour : {ref_id}")
                r_fourn = st.text_input("Nom du Fournisseur concerné :", value="Fournisseur", key=f"rfourn_{ref_id}").strip()
                r_qte = st.number_input("Quantité à renvoyer :", min_value=1, max_value=int(row['Quantité']) if int(row['Quantité']) > 0 else 1, step=1, key=f"rqte_{ref_id}")
                r_prix = st.number_input("Prix d'achat unitaire remboursé (€) :", min_value=0.0, value=float(row['Prix Achat']), step=0.5, key=f"rprix_{ref_id}")
                if st.button("Confirmer le Retour Marchandise", key=f"conf_r_action_{ref_id}", type="primary"):
                    if row['Quantité'] < r_qte:
                        st.error("Impossible de renvoyer plus de pièces que vous n'en avez en stock !")
                    else:
                        df_p.at[idx, "Quantité"] -= r_qte
                        df_p.to_csv(F_PIECES, index=False)
                        valeur_remboursee = float(r_prix * r_qte)
                        n_mouv = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], "📤 Retour Fournisseur (Remboursement)", int(r_qte), valeur_remboursee, 0.0, str(r_fourn), "Retour Stock"]], columns=df_m.columns)
                        df_m = pd.concat([df_m, n_mouv], ignore_index=True)
                        df_m.to_csv(F_MOUV, index=False)
                        st.session_state[f"pop_ret_{ref_id}"] = False
                        st.success("Retour enregistré avec succès !")
                        st.rerun()

            if st.session_state.get(f"pop_a_{ref_id}", False):
                st.warning(f"Supprimer la fiche {ref_id} ?")
