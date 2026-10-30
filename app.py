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

    req = st.text_input("Rechercher (Réf ou Nom) :", key="search_bar").strip().upper()
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
            if c_btn1.button("💸", key=f"btn_t_v_{ref_id}"):
                st.session_state[f"pop_v_{ref_id}"] = not st.session_state.get(f"pop_v_{ref_id}", False)
                st.session_state[f"pop_e_{ref_id}"] = False
            if c_btn2.button("📦", key=f"btn_t_e_{ref_id}"):
                st.session_state[f"pop_e_{ref_id}"] = not st.session_state.get(f"pop_e_{ref_id}", False)
                st.session_state[f"pop_v_{ref_id}"] = False
            if c_btn3.button("❌", key=f"btn_t_a_{ref_id}"):
                st.session_state[f"pop_a_{ref_id}"] = not st.session_state.get(f"pop_a_{ref_id}", False)
            
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

            if st.session_state.get(f"pop_a_{ref_id}", False):
                st.warning(f"Supprimer la fiche {ref_id} ?")
                if st.button("Confirmer la suppression", key=f"conf_t_del_{ref_id}", type="primary"):
                    df_p = df_p.drop(idx)
                    df_p.to_csv(F_PIECES, index=False)
                    st.session_state[f"pop_a_{ref_id}"] = False
                    st.rerun()
            st.write("---")
    else:
        st.write("Aucun article à afficher.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER OU MODIFIER (BOUTONS FORCE FIXES SANS CONDITIONS)
# ---------------------------------------------------------------------
with t2:
    st.subheader("Gestion des fiches articles")
    rf_gest = st.text_input("Saisir la Référence à gérer :", key="txt_gest_ref").strip().upper()
    
    val_nom, val_cat, val_pa, val_pv, val_qt, val_sl = "", "", 0.0, 0.0, 0, 0
    existe = False
    
    if rf_gest and not df_p.empty and rf_gest in df_p["Référence"].values:
        existe = True
        p_row = df_p[df_p["Référence"] == rf_gest].iloc
        st.info(f"🔎 Référence trouvée dans votre stock : {p_row['Désignation']}")
        val_nom = str(p_row["Désignation"])
        val_cat = str(p_row["Catégorie"])
        val_pa = float(p_row["Prix Achat"])
        val_pv = float(p_row["Prix Vente"])
        val_qt = int(p_row["Quantité"])
        val_sl = int(p_row["Alerte Min"])
    elif rf_gest:
        st.success("✨ Nouvelle référence détectée. Remplissez les cases ci-dessous :")

    nm = st.text_input("Désignation / Nom de la pièce :", value=val_nom, key="input_nm").strip()
    ct = st.text_input("Catégorie :", value=val_cat, key="input_ct").strip()
    col_a, col_b = st.columns(2)
    pa = col_a.number_input("Prix d'achat (€) :", min_value=0.0, value=val_pa, key="input_pa")
    
    if existe:
        col_a.write(f"**Stock actuel en magasin :** {val_qt} pcs")
        qt = val_qt
    else:
        qt = col_a.number_input("Stock Initial :", min_value=0, value=val_qt, key="input_qt")
        
    pv = col_b.number_input("Prix de vente (€) :", min_value=0.0, value=val_pv, key="input_pv")
    sl = col_b.number_input("Seuil alerte min :", min_value=0, value=val_sl, key="input_sl")
    
    st.write("")
    
    # Bouton d'action TOUJOURS visible de manière fixe en bas du formulaire
    if existe:
        if st.button("✏️ Enregistrer les modifications de la pièce", key="btn_mod_secure", type="primary", use_container_width=True):
            if not rf_gest or not nm:
