# Page d'accueil (presentation + statistiques) 
import streamlit as st
import pandas as pd
import datetime as dt
from PIL import Image
from pathlib import Path
from database.queries import get_dashboard_stats, get_latest_analyses


st.set_page_config(
    page_title="Accueil - OCC Analyses",
    page_icon="🏠",
    layout="wide"
)

# Charger le CSS global
css_path = Path("assets/styles.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Charger le logo OCC
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("assets/logo_occ.png", width=250)
with col_title:
    st.title("Plateforme OCC - Analyses & Contrôles")

# Message de bienvenue personnalisé
nom_user = st.session_state.get("user", {}).get("nom", "")
if nom_user:
    st.success(f"👋 Bonjour {nom_user}, heureux de vous revoir sur la plateforme.")

# Date du jour
st.markdown(f"📅 **Date actuelle :** {dt.date.today().strftime('%d/%m/%Y')}")

# Ligne d'information
st.markdown("""
### 📊 Aperçu général des données
Ci-dessous, un résumé visuel des analyses enregistrées dans la base de données.
""")

data_stats = get_dashboard_stats()

# Affichage en grid de cartes (alignées de gauche à droite)
cols = st.columns(len(data_stats))
colors = ["#0d6efd", "#198754", "#dc3545", "#6f42c1", "#20c997"]
icons = ["📦", "✅", "❌", "📄", "👨‍🔬"]

for i, (label, value) in enumerate(data_stats.items()):
    with cols[i]:
        st.markdown(f"""
        <div class="card" style="background-color:{colors[i]};color:white;padding:1.5rem;border-radius:15px;">
            <div style="font-size:2rem;">{icons[i]}</div>
            <div style="font-size:1.2rem;font-weight:bold;">{label}</div>
            <div style="font-size:2rem;">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# Section complémentaire
st.markdown("""
---
### 📁 Dernières analyses enregistrées
(NB : ces données peuvent être dynamiques dans la version finale.)
""")

# Affichage de données
exemples = pd.DataFrame(get_latest_analyses(5))
st.dataframe(exemples, use_container_width=True)
