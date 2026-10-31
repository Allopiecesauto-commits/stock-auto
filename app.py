import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", layout="wide")

F_PIECES, F_VENTES = "web_pieces.csv", "web_ventes.csv"

# Initialisation des deux seuls fichiers nécessaires
if not os.path.exists(F_PIECES):
    pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]).to_csv(F_PIECES, index=False)
if not os.path.exists(F_VENTES):
    pd.DataFrame(columns=["Date", "Référence", "Désignation", "Quantité", "Total Achat", "Total Vente", "Tiers", "Paiement"]).to_csv(F_VENTES, index=False)

df_p = pd.read_csv(F_PIECES)
df_v = pd.read_csv(F_VENTES)

# Sécurité : Recréation propre de l'historique si la structure a changé
if not df_v.empty and len(df_v.columns) != 8:
    df_v = pd.DataFrame(columns=["Date", "Référence", "Désignation", "Quantité", "Total Achat", "Total Vente", "Tiers", "Paiement"])
    df_v.to_csv(F_VENTES, index=False)

st.title("🚗 Gestion de Stock Auto")

# Uniquement 3 onglets essentiels maintenant
t1, t2, t3 = st.tabs(["📊 Accueil & Ventes", "📦 Créer / Modifier Fiche", "📈 Bilan & Caisse"])

# Initialisation des états d'affichage
for idx, row in df_p.iterrows():
    r_id = str(row['Référence'])
    if f"pop_v_{r_id}" not in st.session_state:
        st.session_state[f"pop_v_{r_id}"] = False
    if f"pop_a_{r_id}" not in st.session_state:
        st.session_state[f"pop_a_{r_id}"] = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL & COMPTOIR DE VENTE DIRECT
# ---------------------------------------------------------------------
with t1:
    st.subheader("Liste du stock en magasin")
    recherche = st.text_input("Saisir un nom ou une référence pour chercher :", key="main_search").strip().upper()
    
    df_affichage = df_p.copy()
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
            ref_id = str(row['Référence'])
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
            if c_btn1.button("💸", key=f"btn_t_v_{ref_id}", help="Vendre"):
                st.session_state[f"pop_v_{ref_id}"] = not st.session_state[f"pop_v_{ref_id}"]
            if c_btn2.button("❌", key=f"btn_t_a_{ref_id}", help="Supprimer la fiche"):
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
                        # Mise à jour du stock
                        df_p.at[idx, "Quantité"] -= q_vendu
                        df_p.to_csv(F_PIECES, index=False)
                        
                        pa_t = float(row["Prix Achat"] * q_vendu)
                        pv_t = float(row["Prix Vente"] * q_vendu)
                        
                        # Enregistrement propre dans le fichier des ventes
                        nouvel_hist = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), ref_id, row['Désignation'], int(q_vendu), float(pa_t), float(pv_t), str(q_client), str(q_paye)]], columns=df_v.columns)
                        pd.concat([df_v, nouvel_hist], ignore_index=True).to_csv(F_VENTES, index=False)
                        
                        st.session_state[f"pop_v_{ref_id}"] = False
                        st.success("Vente enregistrée !")
                        st.rerun()
                        
            if st.session_state[f"pop_a_{ref_id}"]:
                st.warning(f"Supprimer définitivement la fiche {ref_id} ?")
                if st.button("Confirmer la suppression", key=f"conf_t_del_{ref_id}", type="primary"):
                    df_p = df_p.drop(idx)
                    df_p.to_csv(F_PIECES, index=False)
                    st.session_state[f"pop_a_{ref_id}"] = False
                    st.rerun()
            st.write("---")
    if df_affichage.empty:
        st.info("Aucun article trouvé dans votre stock.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER OU MODIFIER UNE PIÈCE (OU ENTRÉE DE LIVRAISON)
# ---------------------------------------------------------------------
with t2:
    st.subheader("📦 Créer, Modifier une pièce ou Ajuster le stock")
    st.write("Entrez une référence : si elle existe déjà, vous pourrez modifier son stock actuel ou ses prix.")
    
    ref_add = st.text_input("Référence de la pièce (Ex: 70AH) :", key="r_add").strip().upper()
    
    val_nom, val_cat, val_pa, val_pv, val_qt, val_sl = "", "", 0.0, 0.0, 0, 0
    existe = False
    
    if ref_add and not df_p.empty and ref_add in df_p["Référence"].astype(str).values:
        existe = True
        p_row = df_p[df_p["Référence"] == ref_add].iloc[0]
        st.info(f"🔎 Pièce trouvée dans le stock : {p_row['Désignation']}")
        val_nom = str(p_row["Désignation"])
        val_cat = str(p_row["Catégorie"])
        val_pa = float(p_row["Prix Achat"])
        val_pv = float(p_row["Prix Vente"])
        val_qt = int(p_row["Quantité"])
        val_sl = int(p_row["Alerte Min"])

    nom_add = st.text_input("Nom / Désignation de la pièce :", value=val_nom, key="n_add").strip()
    cat_add = st.text_input("Catégorie (Ex: Batterie) :", value=val_cat, key="c_add").strip()
    col_a, col_b = st.columns(2)
    pa_add = col_a.number_input("Prix d'achat unitaire (€) :", min_value=0.0, step=0.5, value=val_pa, key="pa_add")
    pv_add = col_b.number_input("Prix de vente unitaire (€) :", min_value=0.0, step=0.5, value=val_pv, key="pv_add")
    
    stock_add = col_a.number_input("Stock Total disponible en magasin :", min_value=0, step=1, value=val_qt, key="s_add")
    seuil_add = col_b.number_input("Seuil d'alerte minimum (Alerte rupture) :", min_value=0, step=1, value=val_sl, key="seuil_add")
    
    st.write("")
    if st.button("💾 Enregistrer et mettre à jour le catalogue", type="primary", use_container_width=True):
        if not ref_add or not nom_add:
            st.error("La Référence et le Nom de la pièce sont obligatoires.")
        else:
            if existe:
                df_p.loc[df_p["Référence"] == ref_add, ["Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]] = [nom_add, cat_add, pa_add, pv_add, stock_add, seuil_add]
                st.success("Fiche produit et stock mis à jour !")
            if not existe:
                nouvelle_ligne = pd.DataFrame([[ref_add, nom_add, cat_add, pa_add, pv_add, stock_add, seuil_add]], columns=df_p.columns)
                df_p = pd.concat([df_p, nouvelle_ligne], ignore_index=True)
                st.success("Nouvelle référence ajoutée avec succès au magasin !")
            df_p.to_csv(F_PIECES, index=False)
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
