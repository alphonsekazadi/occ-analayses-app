import streamlit as st
from pathlib import Path

# Configuration globale de la page
st.set_page_config(
    page_title="OCC Analyses – Plateforme",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Charger le CSS global s’il existe
css_path = Path("assets/styles.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Vérifier l’état de connexion
if "auth" not in st.session_state:
    st.session_state["auth"] = False

# Rediriger vers login si non authentifié
if not st.session_state["auth"]:
    st.switch_page("pages/0_Login.py")
else:
    st.switch_page("pages/1_Accueil.py")
