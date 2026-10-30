import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Stock Auto", page_icon="🚗", layout="centered")

F_PIECES, F_MOUV = "web_pieces.csv", "web_mouvements.csv"

def charger_donnees():
    if not os.path.exists(F_PIECES):
        pd.DataFrame(columns=["Référence", "Désignation", "Catégorie", "Prix Achat", "Prix Vente", "Quantité", "Alerte Min"]).to_csv(F_PIECES, index=False)
    if not os.path.exists(F_MOUV):
        pd.DataFrame(columns=["Date", "Référence", "Désignation", "Type", "Quantité"]).to_csv(F_MOUV, index=False)
    return pd.read_csv(F_PIECES), pd.read_csv(F_MOUV)

df_p, df_m = charger_donnees()

st.title("🚗 Stock Auto Privé")

t1, t2, t3 = st.tabs(["📊 Accueil & Recherche", "📦 Ajouter / Modifier", "🔄 Mouvements"])

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL
# ---------------------------------------------------------------------
with t1:
    c1, c2 = st.columns(2)
    c1.metric("Total Références", len(df_p))
    alt = len(df_p[df_p["Quantité"] <= df_p["Alerte Min"]]) if not df_p.empty else 0
    c2.metric("Alertes rupture", alt)

    req = st.text_input("Rechercher (Réf ou Nom) :").strip().upper()
    if req and not df_p.empty:
        res = df_p[df_p["Référence"].str.contains(req, na=False) | df_p["Désignation"].str.upper().str.contains(req, na=False)]
        st.dataframe(res, use_container_width=True)
    elif not df_p.empty:
        st.dataframe(df_p, use_container_width=True)

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER OU MODIFIER UNE RÉFÉRENCE
# ---------------------------------------------------------------------
with t2:
    st.subheader("Gestion des fiches articles")
    
    # Entrée de la référence pour décider si on ajoute ou modifie
    rf_gest = st.text_input("Saisir la Référence à gérer :").strip().upper()
    
    existe = False
    p_info = None
    idx_p = None
    
    if rf_gest and not df_p.empty and rf_gest in df_p["Référence"].values:
        existe = True
        idx_p = df_p[df_p["Référence"] == rf_gest].index[0]
        p_info = df_p.loc[idx_p]
        st.info(f"🔎 Référence trouvée. Mode modification activé pour : {p_info['Désignation']}")
    elif rf_gest:
        st.success("✨ Référence inconnue. Mode création activé.")

    if rf_gest:
        with st.form("f_add_edit", clear_on_submit=not existe):
            # Valeurs par défaut si modification
            val_nom = str(p_info["Désignation"]) if existe else ""
            val_cat = str(p_info["Catégorie"]) if existe else ""
            val_pa = float(p_info["Prix Achat"]) if existe else 0.0
            val_pv = float(p_info["Prix Vente"]) if existe else 0.0
            val_qt = int(p_info["Quantité"]) if existe else 0
            val_sl = int(p_info["Alerte Min"]) if existe else 0
            
            nm = st.text_input("Désignation / Nom :", value=val_nom).strip()
            ct = st.text_input("Catégorie :", value=val_cat).strip()
            
            col_a, col_b = st.columns(2)
            pa = col_a.number_input("Prix d'achat (€) :", min_value=0.0, step=0.5, value=val_pa)
            
            # On ne change pas le stock initial depuis ce formulaire si la pièce existe (on passe par l'onglet mouvement)
            if existe:
                col_a.write(f"**Stock actuel :** {val_qt} pcs")
                qt = val_qt
            else:
                qt = col_a.number_input("Stock Initial :", min_value=0, step=1, value=val_qt)
                
            pv = col_b.number_input("Prix de vente (€) :", min_value=0.0, step=0.5, value=val_pv)
            sl = col_b.number_input("Seuil alerte min :", min_value=0, step=1, value=val_sl)
            
            texte_bouton = "💾 Enregistrer les modifications" if existe else "➕ Créer la pièce"
            
            if st.form_submit_button(texte_bouton):
                if not nm:
                    st.error("Le nom de la pièce est obligatoire.")
                else:
                    if existe:
                        # Mise à jour
                        df_p.at[idx_p, "Désignation"] = nm
                        df_p.at[idx_p, "Catégorie"] = ct
                        df_p.at[idx_p, "Prix Achat"] = pa
                        df_p.at[idx_p, "Prix Vente"] = pv
                        df_p.at[idx_p, "Alerte Min"] = sl
                        st.success("Fiche de la pièce mise à jour avec succès !")
                    else:
                        # Création
                        nouvelle = pd.DataFrame([[rf_gest, nm, ct, pa, pv, qt, sl]], columns=df_p.columns)
                        df_p = pd.concat([df_p, nouvelle], ignore_index=True)
                        st.success("Nouvelle pièce ajoutée au catalogue !")
                        
                    df_p.to_csv(F_PIECES, index=False)
                    st.rerun()

# ---------------------------------------------------------------------
# ONGLET 3 : MOUVEMENTS
# ---------------------------------------------------------------------
with t3:
    st.subheader("Entrée / Sortie")
    rf_m = st.text_input("Référence de la pièce :").strip().upper()
    if rf_m:
        if not df_p.empty and rf_m in df_p["Référence"].values:
            idx_m = df_p[df_p["Référence"] == rf_m].index[0]
            p_inf = df_p.loc[idx_m]
            st.info(f"Pièce : {p_inf['Désignation']} | Stock actuel : {p_inf['Quantité']}")
            typ = st.radio("Opération :", ["💸 Vente Client (Sortie)", "📦 Arrivée Fournisseur (Entrée)"])
            q_m = st.number_input("Quantité :", min_value=1, step=1)
            
            if st.button("Valider"):
                ok = False
                if "Vente" in typ:
                    if p_inf['Quantité'] < q_m: st.error("Stock insuffisant !")
                    else:
                        df_p.at[idx_m, "Quantité"] -= q_m
                        ok = True
                else:
                    df_p.at[idx_m, "Quantité"] += q_m
                    ok = True
                if ok:
                    df_p.to_csv(F_PIECES, index=False)
                    df_m = pd.concat([df_m, pd.DataFrame([[datetime.now().strftime("%d/%m %H:%M"), rf_m, p_inf['Désignation'], typ, q_m]], columns=df_m.columns)], ignore_index=True)
                    df_m.to_csv(F_MOUV, index=False)
                    st.success("Stock mis à jour !")
                    st.rerun()
        else: st.error("Référence inconnue.")
