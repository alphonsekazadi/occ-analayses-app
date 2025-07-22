# Gestion utilisateurs, roles, audit (admin only) 
import streamlit as st
import pandas as pd

# Fonctions à implémenter / importer depuis database.queries
from database.queries import (
    list_utilisateurs,
    supprimer_utilisateur,
    reset_password_utilisateur,
)

st.set_page_config(page_title="Administration", page_icon="🛠️", layout="wide")

# CSS global
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Vérification des droits d'accès
if "auth" not in st.session_state or not st.session_state["auth"]:
    st.error("⛔ Vous devez être connecté pour accéder à cette page.")
    st.stop()

user = st.session_state["user"]
if user["role_id"] != 1:  # Supposons role_id 1 = admin
    st.error("⛔ Accès réservé à l'administrateur.")
    st.stop()

st.title("🛠️ Administration de la plateforme OCC Analyses")

# Onglets pour organiser la page
onglets = st.tabs(["Utilisateurs", "Audit (placeholder)"])

# ============================
# ONGLET UTILISATEURS
# ============================
with onglets[0]:
    st.subheader("👥 Gestion des utilisateurs")

    utilisateurs = list_utilisateurs()
    if not utilisateurs:
        st.warning("Aucun utilisateur trouvé.")
    else:
        df_users = pd.DataFrame(utilisateurs)
        st.dataframe(df_users, use_container_width=True)

        # Sélection utilisateur pour actions
        user_ids = [u["id"] for u in utilisateurs]
        choix_user = st.selectbox("Sélectionnez un utilisateur", user_ids, format_func=lambda x: f"ID {x}")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Supprimer", key="btn_suppr"):
                if supprimer_utilisateur(choix_user):
                    st.success("Utilisateur supprimé.")
                    st.experimental_rerun()
                else:
                    st.error("Erreur lors de la suppression.")
        with col_b:
            if st.button("🔑 Réinitialiser mot de passe", key="btn_reset"):
                if reset_password_utilisateur(choix_user):
                    st.info("Mot de passe réinitialisé (envoyé par e-mail).")
                else:
                    st.error("Erreur lors de la réinitialisation.")

# ============================
# ONGLET AUDIT (placeholder)
# ============================
with onglets[1]:
    st.subheader("📜 Journal des actions (à implémenter)")
    st.info("Module d'audit à venir.")
