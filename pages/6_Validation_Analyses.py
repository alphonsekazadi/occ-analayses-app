import streamlit as st
from database.queries import get_analyses_non_validees, valider_analyse
from datetime import datetime

st.set_page_config(page_title="Validation des Analyses", page_icon="✅")

st.title("✅ Validation des analyses de produits")

# CSS personnalisé
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Vérifier si l'utilisateur est connecté et autorisé
if "auth" not in st.session_state or not st.session_state["auth"]:
    st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
    st.stop()

user = st.session_state["user"]
if user["role_id"] not in [1, 3]:  # 2 = analyste, 3 = admin (à adapter selon votre DB)
    st.error("⛔ Accès refusé. Cette page est réservée aux analystes ou admins.")
    st.stop()

# Récupérer les analyses non encore validées
analyses = get_analyses_non_validees()

if not analyses:
    st.info("🎉 Toutes les analyses ont déjà été validées.")
    st.stop()

st.markdown("### Analyses en attente de validation")

for analyse in analyses:
    with st.expander(f"🔬 Analyse ID {analyse['id']} – Produit : {analyse['produit']} ({analyse['laboratoire']})"):
        st.markdown(f"**Date :** {analyse['date_analyse']}  ")
        st.markdown(f"**Analyste :** {analyse['analyste']}  ")
        st.markdown(f"**Résultat :** {analyse['resultat']}  ")
        #st.markdown(f"**Observations :** {analyse['observation']}")

        if st.button("✅ Valider cette analyse", key=f"valider_{analyse['id']}"):
            if valider_analyse(analyse['id'], user['id']):
                st.success(f"Analyse ID {analyse['id']} validée avec succès. Certificat généré.")
                st.rerun()
            else:
                st.error("Une erreur s'est produite lors de la validation.")
