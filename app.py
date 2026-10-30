import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", page_icon="🚗", layout="wide")

F_PIECES, F_MOUV = "web_pieces.csv", "web_mouvements.csv"

def charger_donnees():
    cols_pieces = ["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]
    if not os.path.exists(F_PIECES):
        pd.DataFrame(columns=cols_pieces).to_csv(F_PIECES, index=False)
        
    cols_mouv = ["Date", "Référence", "Désignation", "Type", "Quantité", "Prix Achat Total", "Prix Vente Total", "Tiers", "Paiement"]
    
    if os.path.exists(F_MOUV):
        try:
            test_df = pd.read_csv(F_MOUV)
            if "Paiement" not in test_df.columns or test_df.empty:
                pd.DataFrame(columns=cols_mouv).to_csv(F_MOUV, index=False)
        except:
            pd.DataFrame(columns=cols_mouv).to_csv(F_MOUV, index=False)
    else:
        pd.DataFrame(columns=cols_mouv).to_csv(F_MOUV, index=False)
        
    df = pd.read_csv(F_PIECES)
    df_m = pd.read_csv(F_MOUV)
    
    df["Référence"] = df["Référence"].astype(str).str.upper()
    df["Désignation"] = df["Désignation"].fillna("").astype(str)
    df["Catégorie"] = df["Catégorie"].fillna("").astype(str)
    df["Prix Achat"] = pd.to_numeric(df["Prix Achat"], errors='coerce').fillna(0.0).astype(float)
    df["Prix Vente"] = pd.to_numeric(df["Prix Vente"], errors='coerce').fillna(0.0).astype(float)
    df["Quantité"] = pd.to_numeric(df["Quantité"], errors='coerce').fillna(0).astype(int)
    df["Alerte Min"] = pd.to_numeric(df["Alerte Min"], errors='coerce').fillna(0).astype(int)
    
    return df, df_m

df_p, df_m = charger_donnees()

st.title("🚗 Stock Auto Privé")

t1, t2, t3, t4 = st.tabs(["📊 Accueil & Recherche", "📦 Ajouter / Modifier", "🔄 Commande Fournisseur", "📈 Comptabilité & Bilans"])

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
        if st.button(f"📋 Total Références : {len(df_p)}", use_container_width=True):
            st.session_state.filtre_alerte = False
            st.rerun()
    with c2:
        if st.button(f"⚠️ Alertes rupture : {nb_alt}", use_container_width=True, type="primary" if nb_alt > 0 else "secondary"):
            st.session_state.filtre_alerte = True
            st.rerun()

    df_affichage = alt_df if st.session_state.filtre_alerte else df_p

    if st.session_state.filtre_alerte:
        st.warning("🚨 Affichage des pièces en alerte rupture uniquement")

    req = st.text_input("Rechercher (Réf ou Nom) :").strip().upper()
    if req and not df_affichage.empty:
        df_affichage = df_affichage[df_affichage["Référence"].str.contains(req, na=False) | df_affichage["Désignation"].str.upper().str.contains(req, na=False)]

    if not df_affichage.empty:
        st.write("---")
        
        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([2, 3, 2, 1.5, 1.5, 1.2, 1.2, 3.5])
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
            
            col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7, col_r8 = st.columns([2, 3, 2, 1.5, 1.5, 1.2, 1.2, 3.5])
            col_r1.write(f"{prefix}{ref_id}")
            col_r2.write(row['Désignation'])
            col_r3.write(row['Catégorie'])
            col_r4.write(f"{row['Prix Achat']} €")
            col_r5.write(f"{row['Prix Vente']} €")
            col_r6.write(f"**{row['Quantité']}**")
            col_r7.write(str(row['Alerte Min']))
            
            c_btn1, c_btn2, c_btn3 = col_r8.columns(3)
            if c_btn1.button("💸", key=f"btn_t_v_{ref_id}", help="Vendre"):
                st.session_state[f"pop_v_{ref_id}"] = True
                st.session_state[f"pop_e_{ref_id}"] = False
            if c_btn2.button("📦", key=f"btn_t_e_{ref_id}", help="Ajouter du Stock (Fournisseur)"):
                st.session_state[f"pop_e_{ref_id}"] = True
                st.session_state[f"pop_v_{ref_id}"] = False
            if c_btn3.button("❌", key=f"btn_t_a_{ref_id}", help="Supprimer la fiche"):
                st.session_state[f"pop_a_{ref_id}"] = True
            
            if f"pop_v_{ref_id}" in st.session_state and st.session_state[f"pop_v_{ref_id}"]:
                with st.form(f"quick_v_{ref_id}"):
                    st.info(f"💸 Vente rapide pour : {ref_id}")
                    q_client = st.text_input("Nom du Client :", value="Client Comptoir").strip()
                    q_vendu = st.number_input("Quantité à vendre :", min_value=1, max_value=int(row['Quantité']) if int(row['Quantité']) > 0 else 1, step=1)
                    q_paye = st.radio("Mode de règlement :", ["💵 Espèces", "💳 Carte Bancaire"], horizontal=True)
                    cf1, cf2 = st.columns(2)
                    if cf1.form_submit_button("Valider la vente"):
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
                    if cf2.form_submit_button("Fermer"):
                        st.session_state[f"pop_v_{ref_id}"] = False
                        st.rerun()

            if f"pop_e_{ref_id}" in st.session_state and st.session_state[f"pop_e_{ref_id}"]:
                with st.form(f"quick_e_{ref_id}"):
                    st.success(f"📦 Arrivage fournisseur pour : {ref_id}")
                    q_fourn = st.text_input("Nom du Fournisseur :", value="Fournisseur").strip()
                    q_recu = st.number_input("Quantité de pièces reçues :", min_value=1, step=1, value=1)
                    ce1, ce2 = st.columns(2)
                    if ce1.form_submit_button("Valider l'entrée"):
                        df_p.at[idx, "Quantité"] += q_recu
                        df_p.to_csv(F_PIECES, index=False)
                        pa_t = float(row["Prix Achat"] * q_recu)
                        n_mouv = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], "📦 Commande Fournisseur (Entrée)", int(q_recu), float(pa_t), 0.0, str(q_fourn), "Fournisseur"]], columns=df_m.columns)
                        df_m = pd.concat([df_m, n_mouv], ignore_index=True)
                        df_m.to_csv(F_MOUV, index=False)
                        st.session_state[f"pop_e_{ref_id}"] = False
                        st.rerun()
                    if ce2.form_submit_button("Fermer"):
                        st.session_state[f"pop_e_{ref_id}"] = False
                        st.rerun()

            if f"pop_a_{ref_id}" in st.session_state and st.session_state[f"pop_a_{ref_id}"]:
                st.warning(f"Supprimer définitivement la fiche {ref_id} ?")
                cd1, cd2 = st.columns(2)
                if cd1.button("Confirmer", key=f"conf_t_del_{ref_id}", type="primary"):
                    df_p = df_p.drop(idx)
                    df_p.to_csv(F_PIECES, index=False)
                    st.session_state[f"pop_a_{ref_id}"] = False
                    st.rerun()
                if cd2.button("Retour", key=f"back_t_del_{ref_id}"):
                    st.session_state[f"pop_a_{ref_id}"] = False
                    st.rerun()
            st.write("---")
    else:
        st.write("Aucun article à afficher.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER OU MODIFIER (RÉPARÉ INDÉSTRUCTIBLE)
# ---------------------------------------------------------------------
with t2:
    st.subheader("Gestion des fiches articles")
    rf_gest = st.text_input("Saisir la Référence à gérer :", key="txt_gest_ref").strip().upper()
    existe = False
    
    val_nom, val_cat, val_pa, val_pv, val_qt, val_sl = "", "", 0.0, 0.0, 0, 0
    
    if rf_gest and not df_p.empty and rf_gest in df_p["Référence"].values:
        existe = True
        # Extraction de la ligne de données en mode dictionnaire pur pour éliminer le bug d'index mobile
        match_rows = df_p[df_p["Référence"] == rf_gest]
        if not match_rows.empty:
            p_row = match_rows.iloc[0]
            st.info(f"🔎 Référence existante trouvée : {p_row['Désignation']}")
            val_nom = str(p_row["Désignation"])
            val_cat = str(p_row["Catégorie"])
            val_pa = float(p_row["Prix Achat"])
            val_pv = float(p_row["Prix Vente"])
            val_qt = int(p_row["Quantité"])
