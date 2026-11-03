from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Stock Auto", layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzH7w2yTxxslMP0lAD45LslEJTZkcbSbXVyoPONJEeO8kWiS1rhZWSS6ORVzBAEM33BJQ/exec"


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE AVEC CACHE OPTIMISÉ ---
@st.cache_data(ttl=60)
def load_data():
    try:
        res_p = requests.get(f"{WEB_APP_URL}?sheet=Pieces", timeout=10)
        data_p = res_p.json()
        df_p = pd.DataFrame(data_p) if data_p else pd.DataFrame()
    except Exception:
        df_p = pd.DataFrame()

    if df_p.empty or not all(
        col in df_p.columns
        for col in [
            "Référence",
            "Désignation",
            "Catégorie",
            "Prix Achat",
            "Prix Vente",
            "Quantité",
            "Alerte Min",
        ]
    ):
        df_p = pd.DataFrame(
            columns=[
                "Référence",
                "Désignation",
                "Catégorie",
                "Prix Achat",
                "Prix Vente",
                "Quantité",
                "Alerte Min",
            ]
        )

    try:
        res_v = requests.get(f"{WEB_APP_URL}?sheet=Ventes", timeout=10)
        data_v = res_v.json()
        df_v = pd.DataFrame(data_v) if data_v else pd.DataFrame()
    except Exception:
        df_v = pd.DataFrame()

    if df_v.empty or not all(
        col in df_v.columns
        for col in [
            "Date",
            "Référence",
            "Désignation",
            "Quantité",
            "Total Vente",
            "Tiers",
            "Paiement",
        ]
    ):
        df_v = pd.DataFrame(
            columns=[
                "Date",
                "Référence",
                "Désignation",
                "Quantité",
                "Total Vente",
                "Tiers",
                "Paiement",
            ]
        )

    return df_p, df_v


def save_pieces(df_p):
    try:
        requests.post(
            WEB_APP_URL,
            json={"sheet": "Pieces", "rows": df_p.to_dict(orient="records")},
            timeout=10,
        )
        st.cache_data.clear()
    except Exception:
        pass


def save_ventes(df_v):
    try:
        requests.post(
            WEB_APP_URL,
            json={"sheet": "Ventes", "rows": df_v.to_dict(orient="records")},
            timeout=10,
        )
        st.cache_data.clear()
    except Exception:
        pass


df_p, df_v = load_data()

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3 = st.tabs(
    [
        "📦 Stock & Ventes",
        "➕ Ajouter une pièce",
        "📈 Historique & Bilan Mensuel",
    ]
)

# ---------------------------------------------------------------------
# ONGLET 1 : STOCK & ACTIONS EN DIRECT & MODIFICATION COMPLÈTE
# ---------------------------------------------------------------------
with t1:
    st.subheader("📋 Liste du stock et Actions en direct")

    if not df_p.empty:
        # --- GESTION DES ALERTES DE STOCK ---
        df_p_alert = df_p.copy()
        df_p_alert["Qte_Num"] = (
            pd.to_numeric(df_p_alert["Quantité"], errors="coerce").fillna(0)
        )
        df_p_alert["Seuil_Num"] = (
            pd.to_numeric(df_p_alert["Alerte Min"], errors="coerce").fillna(0)
        )
        alertes = df_p_alert[df_p_alert["Qte_Num"] <= df_p_alert["Seuil_Num"]]

        if not alertes.empty:
            st.warning(
                f"⚠️ Attention : {len(alertes)} pièce(s) ont atteint ou sont sous"
                " leur seuil d'alerte minimal !"
            )
            for _, a_row in alertes.iterrows():
                st.markdown(
                    f"- 🔴 **{a_row['Référence']}** ({a_row['Désignation']}) :"
                    f" Stock actuel = **{a_row['Quantité']}** (Seuil :"
                    f" {a_row['Alerte Min']})"
                )
            st.write("---")

        req = (
            st.text_input("Rechercher (Réf ou Nom) :", key="search_bar")
            .strip()
            .upper()
        )
        df_affichage = df_p.copy()
        if req:
            df_affichage = df_affichage[
                df_affichage["Référence"].astype(str).str.contains(req, na=False)
                | df_affichage["Désignation"]
                .astype(str)
                .str.upper()
                .str.contains(req, na=False)
            ]

        for idx, row in df_affichage.iterrows():
            ref_id = str(row["Référence"])
            unique_key = f"{ref_id}_{idx}"
            qte_actuelle = (
                float(row["Quantité"])
                if str(row["Quantité"]).strip() != ""
                else 0.0
            )

            if f"pop_act_{unique_key}" not in st.session_state:
                st.session_state[f"pop_act_{unique_key}"] = False

            col_r1, col_r2, col_r3, col_r4, col_r5, col_r6 = st.columns(
                [1.5, 2.5, 1.2, 1.2, 1.2, 2]
            )
            col_r1.write(f"**{ref_id}**")
            col_r2.write(row["Désignation"])
            col_r3.write(f"{row['Prix Vente']} €")
            col_r4.write(f"{row['Quantité']} pcs")

            if col_r6.button(
                "🛠️ Gérer / Vendre",
                key=f"btn_act_{unique_key}",
                use_container_width=True,
            ):
                st.session_state[f"pop_act_{unique_key}"] = not st.session_state[
                    f"pop_act_{unique_key}"
                ]

            if st.session_state.get(f"pop_act_{unique_key}", False):
                st.write("")
                st.markdown(
                    f"⚙️ **CONFIGURATION DE LA PIÈCE : {ref_id}**"
                )
                c_p1, c_p2 = st.columns(2)

                # Colonne 1 : Ventes
                with c_p1:
                    st.markdown("### 💸 Enregistrer une Vente")
                    q_client = st.text_input(
                        "Client :",
                        value="Client comptoir",
                        key=f"qc_{unique_key}",
                    )
                    q_vendu = st.number_input(
                        "Quantité vendue :",
                        min_value=1,
                        max_value=int(qte_actuelle)
                        if int(qte_actuelle) > 0
                        else 1,
                        step=1,
                        key=f"qv_{unique_key}",
                    )
                    q_paye = st.radio(
                        "Paiement :",
                        ["💵 Espèces", "💳 Carte Bancaire"],
                        horizontal=True,
                        key=f"qp_{unique_key}",
                    )

                    if st.button(
                        "Confirmer la vente",
                        key=f"conf_v_{unique_key}",
                        type="primary",
                    ):
                        if qte_actuelle < q_vendu:
                            st.error("Stock insuffisant !")
                        else:
                            for i, p_row in df_p.iterrows():
                                if str(p_row["Référence"]) == ref_id:
                                    df_p.at[i, "Quantité"] = (
                                        float(p_row["Quantité"]) - q_vendu
                                    )
                                    break
                            save_pieces(df_p)

                            tot_v = float(row["Prix Vente"]) * float(q_vendu)
                            nouvel_hist = pd.DataFrame(
                                [
                                    [
                                        datetime.now().strftime("%Y-%m-%d"),
                                        ref_id,
                                        row["Désignation"],
                                        int(q_vendu),
                                        float(tot_v),
                                        str(q_client),
                                        str(q_paye),
                                    ]
                                ],
                                columns=df_v.columns,
                            )
                            df_v = pd.concat(
                                [df_v, nouvel_hist], ignore_index=True
                            )
                            save_ventes(df_v)

                            st.session_state[f"pop_act_{unique_key}"] = False
                            st.success("Vente enregistrée !")
                            st.rerun()

                # Colonne 2 : Modification des infos et stock
                with c_p2:
                    st.markdown("### ✏️ Modifier la fiche & Stock")

                    edit_ref = st.text_input(
                        "Référence :",
                        value=str(row["Référence"]),
                        key=f"edit_ref_{unique_key}",
                    )
                    edit_nom = st.text_input(
                        "Désignation :",
                        value=str(row["Désignation"]),
                        key=f"edit_nom_{unique_key}",
                    )
                    edit_cat = st.text_input(
                        "Catégorie :",
                        value=str(row.get("Catégorie", "")),
                        key=f"edit_cat_{unique_key}",
                    )

                    col_pa, col_pv = st.columns(2)
                    with col_pa:
                        edit_pa = st.number_input(
                            "Prix Achat (€) :",
                            min_value=0.0,
                            value=float(row["Prix Achat"])
                            if str(row["Prix Achat"]).strip() != ""
                            else 0.0,
                            step=0.5,
                            key=f"edit_pa_{unique_key}",
                        )
                    with col_pv:
                        edit_pv = st.number_input(
                            "Prix Vente (€) :",
                            min_value=0.0,
                            value=float(row["Prix Vente"])
                            if str(row["Prix Vente"]).strip() != ""
                            else 0.0,
                            step=0.5,
                            key=f"edit_pv_{unique_key}",
                        )

                    col_q, col_s = st.columns(2)
                    with col_q:
                        edit_qte = st.number_input(
                            "Quantité :",
                            min_value=0,
                            value=int(qte_actuelle),
                            step=1,
                            key=f"edit_qte_{unique_key}",
                        )
                    with col_s:
                        edit_seuil = st.number_input(
                            "Seuil alerte :",
                            min_value=0,
                            value=int(row["Alerte Min"])
                            if str(row["Alerte Min"]).strip() != ""
                            else 0,
                            step=1,
                            key=f"edit_seuil_{unique_key}",
                        )

                    if st.button(
                        "💾 Enregistrer les modifications",
                        key=f"save_all_{unique_key}",
                        type="primary",
                    ):
                        df_p.at[idx, "Référence"] = edit_ref.strip().upper()
                        df_p.at[idx, "Désignation"] = edit_nom.strip()
                        df_p.at[idx, "Catégorie"] = edit_cat.strip()
                        df_p.at[idx, "Prix Achat"] = edit_pa
                        df_p.at[idx, "Prix Vente"] = edit_pv
                        df_p.at[idx, "Quantité"] = edit_qte
                        df_p.at[idx, "Alerte Min"] = edit_seuil

                        save_pieces(df_p)
                        st.session_state[f"pop_act_{unique_key}"] = False
                        st.success("Fiche mise à jour avec succès !")
                        st.rerun()

                    if st.button(
                        "🗑️ Supprimer la pièce",
                        key=f"del_{unique_key}",
                        type="secondary",
                    ):
                        df_p = df_p[df_p.index != idx]
                        save_pieces(df_p)
                        st.session_state[f"pop_act_{unique_key}"] = False
                        st.success("Pièce supprimée.")
                        st.rerun()
                st.write("---")
            st.write("---")
    else:
        st.info("Aucun article dans la base. Utilisez l'onglet 'Ajouter une pièce'.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER UNE NOUVELLE FICHE PRODUIT
# ---------------------------------------------------------------------
with t2:
    st.subheader("📦 Ajouter une nouvelle référence")
    r_add = st.text_input("Référence :").strip().upper()
    n_add = st.text_input("Désignation :").strip()
    c_add = st.text_input("Catégorie :").strip()
    pa_add = st.number_input("Prix d'achat (€) :", min_value=0.0, step=0.5)
    pv_add = st.number_input("Prix de vente (€) :", min_value=0.0, step=0.5)
    stock_add = st.number_input("Quantité initiale :", min_value=0, step=1)
    seuil_add = st.number_input("Seuil d'alerte :", min_value=0, step=1)

    if st.button("➕ Enregistrer la pièce", type="primary"):
        if r_add and n_add:
            nouvelle_ligne = pd.DataFrame(
                [[
                    r_add,
                    n_add,
                    c_add,
                    pa_add,
                    pv_add,
                    stock_add,
                    seuil_add,
                ]],
                columns=df_p.columns,
            )
            df_p = pd.concat([df_p, nouvelle_ligne], ignore_index=True)
            save_pieces(df_p)
            st.success("Pièce ajoutée avec succès !")
            st.rerun()
        else:
            st.error("La référence et la désignation sont obligatoires.")

# ---------------------------------------------------------------------
# ONGLET 3 : HISTORIQUE & BILAN MENSUEL
# ---------------------------------------------------------------------
with t3:
    st.subheader("📊 Bilan Financier et Historique des Ventes")

    if not df_v.empty:
        df_v_calc = df_v.copy()
        df_v_calc["Date"] = pd.to_datetime(df_v_calc["Date"], errors="coerce")
        df_v_calc["Mois"] = df_v_calc["Date"].dt.strftime("%Y-%m")

        if not df_p.empty and "Prix Achat" in df_p.columns:
            df_v_merged = df_v_calc.merge(
                df_p[["Référence", "Prix Achat"]], on="Référence", how="left"
            )
        else:
            df_v_merged = df_v_calc.copy()
            df_v_merged["Prix Achat"] = 0.0

        df_v_merged["Prix Achat"] = (
            df_v_merged["Prix Achat"].fillna(0).astype(float)
        )
        df_v_merged["Quantité"] = pd.to_numeric(
            df_v_merged["Quantité"], errors="coerce"
        ).fillna(0)
        df_v_merged["Coût Achat"] = (
            df_v_merged["Quantité"] * df_v_merged["Prix Achat"]
        )
        df_v_merged["Total Vente"] = pd.to_numeric(
            df_v_merged["Total Vente"], errors="coerce"
        ).fillna(0)

        bilan_mensuel = (
            df_v_merged.groupby("Mois")
            .agg(
                Ventes_CA=("Total Vente", "sum"),
                Depenses_Achats=("Coût Achat", "sum"),
                Nombre_Ventes=("Référence", "count"),
            )
            .reset_index()
        )
        bilan_mensuel["Benefice"] = (
            bilan_mensuel["Ventes_CA"] - bilan_mensuel["Depenses_Achats"]
        )
        bilan_mensuel = bilan_mensuel.sort_values(by="Mois", ascending=False)

        bilans_affiche = bilan_mensuel.rename(
            columns={
                "Mois": "Mois",
                "Ventes_CA": "Chiffre d'Affaires (€)",
                "Depenses_Achats": "Coût des Achats (€)",
                "Nombre_Ventes": "Nb Ventes",
                "Benefice": "Bénéfice Net (€)",
            }
        )

        st.dataframe(bilans_affiche, use_container_width=True, hide_index=True)

        st.write("---")
        ca_total = df_v["Total Vente"].astype(float).sum()
        m1, m2 = st.columns(2)
        m1.metric("💰 Chiffre d'Affaires Total", f"{ca_total:.2f} €")
        m2.metric("🧾 Nombre Total de Ventes", len(df_v))

        st.write("---")
        st.subheader("Historique détaillé")
        for idx, row in df_v.iloc[::-1].iterrows():
            col_h1, col_h2, col_h3, col_h4 = st.columns(
                [1.5, 2.5, 1.5, 1.5]
            )
            col_h1.write(str(row["Date"]))
            col_h2.write(f"{row['Référence']} - {row['Désignation']}")
            col_h3.write(f"{row['Total Vente']} €")
            if col_h4.button("↩️ Annuler", key=f"cancel_v_{idx}"):
                ref_annul = str(row["Référence"])
                qte_annul = int(row["Quantité"])
                for i, p_row in df_p.iterrows():
                    if str(p_row["Référence"]) == ref_annul:
                        df_p.at[i, "Quantité"] = (
                            int(p_row["Quantité"]) + qte_annul
                        )
                        break
                save_pieces(df_p)
                df_v = df_v.drop(idx)
                save_ventes(df_v)
                st.success("Vente annulée et stock remis à jour !")
                st.rerun()
            st.write("---")
    else:
        st.info("Aucune vente enregistrée pour le moment.")
