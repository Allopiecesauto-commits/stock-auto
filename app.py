from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Stock Auto", layout="wide")

# Lien de votre Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1H4GYOMMqA6lGpbXhbQ-HrzFJAeoBjj7TdFcq_62nirg/edit?usp=sharing"

# Connexion aux Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE ---
def load_data():
    try:
        df_p = conn.read(spreadsheet=SHEET_URL, worksheet="Pieces", ttl=0)
        df_p = df_p.dropna(how="all")
    except Exception:
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
        df_v = conn.read(spreadsheet=SHEET_URL, worksheet="Ventes", ttl=0)
        df_v = df_v.dropna(how="all")
    except Exception:
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
    conn.update(
        spreadsheet=SHEET_URL, worksheet="Pieces", data=df_p, clear=True
    )


def save_ventes(df_v):
    conn.update(
        spreadsheet=SHEET_URL, worksheet="Ventes", data=df_v, clear=True
    )


# Chargement initial
df_p, df_v = load_data()

st.title("🚗 Gestion de Stock Auto")

t1, t2, t3 = st.tabs(
    [
        "📊 Accueil & Actions rapides",
        "📦 Créer Nouvelle Fiche",
        "📈 Historique & Bilan Mensuel",
    ]
)

if "filtre_alerte" not in st.session_state:
    st.session_state.filtre_alerte = False

if not df_p.empty:
    for idx, row in df_p.iterrows():
        r_id = str(row["Référence"])
        if f"pop_act_{r_id}" not in st.session_state:
            st.session_state[f"pop_act_{r_id}"] = False

# ---------------------------------------------------------------------
# ONGLET 1 : ACCUEIL & GESTION DU STOCK DIRECT
# ---------------------------------------------------------------------
with t1:
    st.subheader("📋 Liste du stock et Actions en direct")

    alt_df = (
        df_p[
            pd.to_numeric(df_p["Quantité"], errors="coerce").fillna(0)
            <= pd.to_numeric(df_p["Alerte Min"], errors="coerce").fillna(0)
        ]
        if not df_p.empty
        else pd.DataFrame()
    )
    nb_alt = len(alt_df)

    c1, c2 = st.columns(2)
    if c1.button(
        f"📋 Total Références : {len(df_p)}",
        use_container_width=True,
        key="btn_tot_ref",
    ):
        st.session_state.filtre_alerte = False
        st.rerun()
    if c2.button(
        f"⚠️ Alertes rupture : {nb_alt}",
        use_container_width=True,
        type="primary" if nb_alt > 0 else "secondary",
        key="btn_alt_ruf",
    ):
        st.session_state.filtre_alerte = True
        st.rerun()

    df_affichage = alt_df if st.session_state.filtre_alerte else df_p.copy()

    if st.session_state.filtre_alerte:
        st.warning("🚨 Affichage des pièces en alerte rupture uniquement")

    req = st.text_input("Rechercher (Réf ou Nom) :", key="search_bar").strip().upper()
    if req and not df_affichage.empty:
        df_affichage = df_affichage[
            df_affichage["Référence"].astype(str).str.contains(req, na=False)
            | df_affichage["Désignation"]
            .astype(str)
            .str.upper()
            .str.contains(req, na=False)
        ]

    if not df_affichage.empty:
        df_affichage = df_affichage.sort_values(
            by=["Catégorie", "Référence"], ascending=[True, True]
        )

        st.write("---")
        (
            col_h1,
            col_h2,
            col_h3,
            col_h4,
            col_h5,
            col_h6,
            col_h7,
            col_h8,
        ) = st.columns([1.5, 2.5, 1.5, 1.2, 1.2, 1.2, 1.2, 2])
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
            ref_id = str(row["Référence"])
            qte_actuelle = float(row["Quantité"])
            seuil_min = float(row["Alerte Min"])

            prefix = "⚠️ " if qte_actuelle <= seuil_min else "✅ "

            (
                col_r1,
                col_r2,
                col_r3,
                col_r4,
                col_r5,
                col_r6,
                col_r7,
                col_r8,
            ) = st.columns([1.5, 2.5, 1.5, 1.2, 1.2, 1.2, 1.2, 2])
            col_r1.write(f"{prefix}{ref_id}")
            col_r2.write(row["Désignation"])
            col_r3.write(row["Catégorie"])
            col_r4.write(f"{row['Prix Achat']} €")
            col_r5.write(f"{row['Prix Vente']} €")
            col_r6.write(f"**{row['Quantité']} pcs**")
            col_r7.write(f"{row['Alerte Min']} pcs")

            if col_r8.button(
                "🛠️ Gérer / Vendre",
                key=f"btn_act_{ref_id}",
                use_container_width=True,
            ):
                st.session_state[f"pop_act_{ref_id}"] = not st.session_state[
                    f"pop_act_{ref_id}"
                ]

            if st.session_state.get(f"pop_act_{ref_id}", False):
                st.write("")
                st.markdown(
                    f"⚙️ **PANNEAU DE CONFIGURATION DIRECTE : {ref_id}**"
                )
                c_panel1, c_panel2 = st.columns(2)

                with c_panel1:
                    st.markdown("### 💸 Enregistrer une Vente rapide")
                    q_client = st.text_input(
                        "Nom du Client :",
                        value="Client comptoir",
                        key=f"qc_{ref_id}",
                    ).strip()
                    max_qte = int(qte_actuelle) if int(qte_actuelle) > 0 else 1
                    q_vendu = st.number_input(
                        "Quantité à vendre :",
                        min_value=1,
                        max_value=max_qte,
                        step=1,
                        key=f"qv_{ref_id}",
                    )
                    q_paye = st.radio(
                        "Mode de règlement :",
                        ["💵 Espèces", "💳 Carte Bancaire"],
                        horizontal=True,
                        key=f"qp_{ref_id}",
                    )

                    col_v1, col_v2 = st.columns(2)
                    if col_v1.button(
                        "Confirmer la vente",
                        key=f"conf_v_{ref_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        if qte_actuelle < q_vendu:
                            st.error("Stock insuffisant !")
                        else:
                            df_p.loc[
                                df_p["Référence"].astype(str) == ref_id,
                                "Quantité",
                            ] = (qte_actuelle - q_vendu)
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

                            st.session_state[f"pop_act_{ref_id}"] = False
                            st.success("Vente enregistrée !")
                            st.rerun()

                    if col_v2.button(
                        "❌ Annuler",
                        key=f"cancel_action_{ref_id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.rerun()

                with c_panel2:
                    st.markdown("### 📦 Ajuster les prix ou le stock")
                    n_pa = st.number_input(
                        "Prix d'Achat unitaire (€) :",
                        min_value=0.0,
                        value=float(row["Prix Achat"]),
                        step=0.5,
                        key=f"pa_{ref_id}",
                    )
                    n_pv = st.number_input(
                        "Prix de Vente unitaire (€) :",
                        min_value=0.0,
                        value=float(row["Prix Vente"]),
                        step=0.5,
                        key=f"pv_{ref_id}",
                    )
                    n_qt = st.number_input(
                        "Modifier le Stock (Ajustement) :",
                        min_value=0,
                        value=int(qte_actuelle),
                        step=1,
                        key=f"qt_{ref_id}",
                    )

                    col_s1, col_s2 = st.columns(2)
                    if col_s1.button(
                        "💾 Sauvegarder",
                        key=f"save_edit_{ref_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        df_p.loc[
                            df_p["Référence"].astype(str) == ref_id,
                            ["Prix Achat", "Prix Vente", "Quantité"],
                        ] = [n_pa, n_pv, n_qt]
                        save_pieces(df_p)
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.success("Modifications enregistrées !")
                        st.rerun()

                    if col_s2.button(
                        "❌ Annuler",
                        key=f"cancel_edit_{ref_id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.rerun()

                    if st.button(
                        "🗑️ Effacer la fiche produit",
                        key=f"del_{ref_id}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        df_p = df_p[df_p["Référence"].astype(str) != ref_id]
                        save_pieces(df_p)
                        st.session_state[f"pop_act_{ref_id}"] = False
                        st.success("Fiche produit effacée.")
                        st.rerun()
                st.write("---")
            st.write("---")
    else:
        st.info("Aucun article trouvé dans la base.")

# ---------------------------------------------------------------------
# ONGLET 2 : AJOUTER UNE NOUVELLE FICHE PRODUIT
# ---------------------------------------------------------------------
with t2:
    st.subheader("📦 Ajouter une nouvelle référence au magasin")
    ref_add = (
        st.text_input("Référence de la pièce (Ex: 70AH) :", key="r_add")
        .strip()
        .upper()
    )
    nom_add = st.text_input(
        "Nom / Désignation de la pièce :", key="n_add"
    ).strip()
    cat_add = st.text_input("Catégorie (Ex: Batterie) :", key="c_add").strip()
    col_c1, col_c2 = st.columns(2)
    pa_add = col_c1.number_input(
        "Prix d'achat unitaire (€) :", min_value=0.0, step=0.5, key="pa_add_f"
    )
    pv_add = col_c2.number_input(
        "Prix de vente unitaire (€) :", min_value=0.0, step=0.5, key="pv_add_f"
    )
    stock_add = col_c1.number_input(
        "Stock de départ reçu :", min_value=0, step=1, key="s_add_f"
    )
    seuil_add = col_c2.number_input(
        "Seuil d'alerte minimum :", min_value=0, step=1, key="seuil_add_f"
    )

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button(
        "➕ Créer la pièce et l'ajouter",
        type="primary",
        use_container_width=True,
    ):
        if not ref_add or not nom_add:
            st.error("La Référence et le Nom de la pièce sont obligatoires.")
        elif ref_add in df_p["Référence"].astype(str).values:
            st.error("Cette référence existe déjà !")
        else:
            nouvelle_ligne = pd.DataFrame(
                [[
                    ref_add,
                    nom_add,
                    cat_add,
                    pa_add,
                    pv_add,
                    stock_add,
                    seuil_add,
                ]],
                columns=df_p.columns,
            )
            df_p = pd.concat([df_p, nouvelle_ligne], ignore_index=True)
            save_pieces(df_p)
            st.success("Nouvelle référence ajoutée au catalogue !")
            st.rerun()

    if col_btn2.button("❌ Annuler / Réinitialiser", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------
# ONGLET 3 : HISTORIQUE DES VENTES & BILAN MENSUEL
# ---------------------------------------------------------------------
with t3:
    st.subheader("📊 Bilan Financier par Mois (Ventes & Dépenses)")

    if not df_v.empty:
        df_v_calc = df_v.copy()
        df_v_calc["Date"] = pd.to_datetime(df_v_calc["Date"], errors="coerce")
        df_v_calc["Mois"] = df_v_calc["Date"].dt.strftime("%Y-%m")

        df_v_merged = df_v_calc.merge(
            df_p[["Référence", "Prix Achat"]], on="Référence", how="left"
        )
        df_v_merged["Prix Achat"] = (
            df_v_merged["Prix Achat"].fillna(0).astype(float)
        )
        df_v_merged["Coût Achat"] = df_v_merged["Quantité"].astype(
            float
        ) * df_v_merged["Prix Achat"]
        df_v_merged["Total Vente"] = df_v_merged["Total Vente"].astype(float)

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

        st.dataframe(
            bilan_mensuel.rename(
                columns={
                    "Mois": "Mois",
                    "Ventes_CA": "Chiffre d'Affaires (€)",
                    "Depenses_Achats": "Coût des Achats (€)",
                    "Nombre_Ventes": "Nb Ventes",
                    "Benefice": "Bénéfice Net (€)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.write("---")
        st.subheader("📈 Historique détaillé des Ventes & Annulation")
        st.info(
            "💡 En cliquant sur '↩️ Annuler', la vente est supprimée et les articles sont automatiquement remis dans le stock !"
        )

        ca_total = df_v["Total Vente"].astype(float).sum()
        marge_totale = (
            df_v_merged["Total Vente"].sum() - df_v_merged["Coût Achat"].sum()
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Chiffre d'Affaires Total", f"{ca_total:.2f} €")
        m2.metric("📈 Marge / Bénéfice Total", f"{marge_totale:.2f} €")
        m3.metric("🧾 Nombre Total de Ventes", len(df_v))

        st.write("---")
        (
            col_h1,
            col_h2,
            col_h3,
            col_h4,
            col_h5,
            col_h6,
            col_h7,
        ) = st.columns([1.2, 1.5, 2.5, 1.0, 1.2, 1.5, 1.5])
        col_h1.markdown("**Date**")
        col_h2.markdown("**Référence**")
        col_h3.markdown("**Désignation**")
        col_h4.markdown("**Qté**")
        col_h5.markdown("**Total**")
        col_h6.markdown("**Client / Reglt**")
        col_h7.markdown("**Action**")
        st.write("---")

        for idx, row in df_v.iloc[::-1].iterrows():
            (
                col_r1,
                col_r2,
                col_r3,
                col_r4,
                col_r5,
                col_r6,
                col_r7,
            ) = st.columns([1.2, 1.5, 2.5, 1.0, 1.2, 1.5, 1.5])
            col_r1.write(str(row["Date"]))
            col_r2.write(str(row["Référence"]))
            col_r3.write(str(row["Désignation"]))
            col_r4.write(f"{row['Quantité']} pcs")
            col_r5.write(f"{float(row['Total Vente']):.2f} €")
            col_r6.write(f"{row['Tiers']}\n({row['Paiement']})")

            if col_r7.button("↩️ Annuler", key=f"cancel_v_{idx}"):
                ref_annul = str(row["Référence"])
                qte_annul = int(row["Quantité"])

                if ref_annul in df_p["Référence"].astype(str).values:
                    df_p.loc[
                        df_p["Référence"].astype(str) == ref_annul, "Quantité"
                    ] = (
                        df_p.loc[
                            df_p["Référence"].astype(str) == ref_annul,
                            "Quantité",
                        ].astype(int)
                        + qte_annul
                    )
                    save_pieces(df_p)

                df_v = df_v.drop(idx)
                save_ventes(df_v)

                st.success(
                    "Vente annulée avec succès : stock réincrémenté et Google Sheets mis à jour !"
                )
                st.rerun()
            st.write("---")
    else:
        st.info("Aucune vente enregistrée pour le moment.")
