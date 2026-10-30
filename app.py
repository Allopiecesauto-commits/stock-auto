import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", page_icon="🚗", layout="centered")

F_PIECES, F_MOUV = "web_pieces.csv", "web_mouvements.csv"

def charger_donnees():
    cols_pieces = ["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]
    if not os.path.exists(F_PIECES):
        pd.DataFrame(columns=cols_pieces).to_csv(F_PIECES, index=False)
        
    cols_mouv = ["Date", "Référence", "Désignation", "Type", "Quantité", "Prix Achat Total", "Prix Vente Total", "Tiers"]
    if not os.path.exists(F_MOUV):
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

t1, t2, t3, t4 = st.tabs(["📊 Accueil & Recherche", "📦 Ajouter / Modifier", "🔄 Journal Ventes & Fournisseurs", "📈 Comptabilité & Bilans"])

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
        for idx, row in df_affichage.iterrows():
            ref_id = row['Référence']
            prefix_status = "⚠️ " if row['Quantité'] <= row['Alerte Min'] else "✅ "
            
            with st.expander(f"{prefix_status} Réf: {ref_id} — {row['Désignation']}", expanded=True):
                col_i1, col_i2, col_i3 = st.columns(3)
                with col_i1:
                    st.write(f"**Catégorie :** {row['Catégorie']} | **Seuil Min :** {row['Alerte Min']}")
                    st.write(f"**Prix Achat :** {row['Prix Achat']}€ | **Prix Vente :** {row['Prix Vente']}€")
                with col_i2:
                    st.metric("En Stock", f"{row['Quantité']} pcs")
                with col_i3:
                    if st.button("💸 Vendre", key=f"btn_v_{ref_id}", use_container_width=True):
                        st.session_state[f"pop_v_{ref_id}"] = True
                    if st.button("❌ Suppr. Fiche", key=f"btn_a_{ref_id}", use_container_width=True, type="secondary"):
                        st.session_state[f"pop_a_{ref_id}"] = True
                
                if f"pop_v_{ref_id}" in st.session_state and st.session_state[f"pop_v_{ref_id}"]:
                    with st.form(f"quick_v_{ref_id}"):
                        st.write("### 💸 Vente rapide")
                        q_client = st.text_input("Nom du Client :", value="Client Comptoir").strip()
                        q_vendu = st.number_input("Quantité vendue :", min_value=1, max_value=int(row['Quantité']), step=1)
                        c_f1, c_f2 = st.columns(2)
                        if c_f1.form_submit_button("Valider"):
                            df_p.at[idx, "Quantité"] -= q_vendu
                            df_p.to_csv(F_PIECES, index=False)
                            n_mouv = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], "💸 Vente Client (Sortie)", q_vendu, float(row["Prix Achat"]*q_vendu), float(row["Prix Vente"]*q_vendu), q_client]], columns=df_m.columns)
                            df_m = pd.concat([df_m, n_mouv], ignore_index=True)
                            df_m.to_csv(F_MOUV, index=False)
                            st.session_state[f"pop_v_{ref_id}"] = False
                            st.rerun()
                        if c_f2.form_submit_button("Fermer"):
                            st.session_state[f"pop_v_{ref_id}"] = False
                            st.rerun()

                if f"pop_a_{ref_id}" in st.session_state and st.session_state[f"pop_a_{ref_id}"]:
                    st.warning(f"Supprimer définitivement la fiche de {ref_id} ?")
                    cd1, cd2 = st.columns(2)
                    if cd1.button("Confirmer", key=f"c_del_{ref_id}", type="primary"):
                        df_p = df_p.drop(idx)
                        df_p.to_csv(F_PIECES, index=False)
                        st.session_state[f"pop_a_{ref_id}"] = False
                        st.rerun()
                    if cd2.button("Retour", key=f"b_del_{ref_id}"):
                        st.session_state[f"pop_a_{ref_id}"] = False
                        st.rerun()
    else:
        st.write("Aucun article à afficher.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER OU MODIFIER
# ---------------------------------------------------------------------
with t2:
    st.subheader("Gestion des fiches articles")
    rf_gest = st.text_input("Saisir la Référence à gérer :").strip().upper()
    existe = False
    p_info = None
    if rf_gest and not df_p.empty and rf_gest in df_p["Référence"].values:
        existe = True
        p_info = df_p[df_p["Référence"] == rf_gest].iloc
        st.info(f"🔎 Référence existante : {p_info['Désignation']}")
    elif rf_gest:
        st.success("✨ Nouvelle référence détectée.")

    if rf_gest:
        with st.form("f_add_edit", clear_on_submit=not existe):
            val_nom = str(p_info["Désignation"]) if existe else ""
            val_cat = str(p_info["Catégorie"]) if existe else ""
            val_pa = float(p_info["Prix Achat"]) if existe else 0.0
            val_pv = float(p_info["Prix Vente"]) if existe else 0.0
            val_qt = int(p_info["Quantité"]) if existe else 0
            val_sl = int(p_info["Alerte Min"]) if existe else 0
            
            nm = st.text_input("Désignation / Nom :", value=val_nom).strip()
            ct = st.text_input("Catégorie :", value=val_cat).strip()
            col_a, col_b = st.columns(2)
            pa = col_a.number_input("Prix d'achat (€) :", min_value=0.0, value=val_pa)
            if existe:
                col_a.write(f"**Stock actuel :** {val_qt} pcs")
                qt = val_qt
            else:
                qt = col_a.number_input("Stock Initial :", min_value=0, value=val_qt)
            pv = col_b.number_input("Prix de vente (€) :", min_value=0.0, value=val_pv)
            sl = col_b.number_input("Seuil alerte min :", min_value=0, value=val_sl)
            
            if st.form_submit_button("✏️ Modifier" if existe else "➕ Créer"):
                if not nm: st.error("Le nom est obligatoire.")
                else:
                    if existe:
                        df_p.loc[df_p["Référence"] == rf_gest, ["Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Alerte Min"]] = [nm, ct, pa, pv, sl]
                    else:
                        df_p = pd.concat([df_p, pd.DataFrame([[rf_gest, nm, ct, pa, pv, qt, sl]], columns=df_p.columns)], ignore_index=True)
                    df_p.to_csv(F_PIECES, index=False)
                    st.rerun()

# ---------------------------------------------------------------------
# ONGLET 3 : JOURNAL DIRECTION DES OPÉRATIONS
# ---------------------------------------------------------------------
with t3:
    st.subheader(" Enregistrer une opération complète")
    rf_m = st.text_input("Référence de la pièce :", key="journal_ref").strip().upper()
    if rf_m and not df_p.empty and rf_m in df_p["Référence"].values:
        idx_m = df_p[df_p["Référence"] == rf_m].index
        p_inf = df_p.loc[idx_m]
        st.info(f"📦 Pièce : {p_inf['Désignation']} | Stock : {p_inf['Quantité']} pcs")
        typ = st.radio("Transaction :", ["💸 Vente Client (Sortie)", "📦 Commande Fournisseur (Entrée)"])
        tiers = st.text_input("Nom du Client / Fournisseur :").strip()
        q_m = st.number_input("Quantité :", min_value=1, step=1)
        
        if st.button("💾 Valider"):
            if not tiers: st.error("Le nom du tiers est obligatoire.")
            else:
                ok = False
                pa_t, pv_t = float(p_inf["Prix Achat"] * q_m), float(p_inf["Prix Vente"] * q_m)
                if "Vente" in typ:
                    if p_inf['Quantité'] < q_m: st.error("Stock insuffisant !")
                    else:
                        df_p.at[idx_m, "Quantité"] -= q_m
                        ok = True
                else:
                    df_p.at[idx_m, "Quantité"] += q_m
                    ok = True
