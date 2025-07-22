# Enregistrement d'une analyse 
import streamlit as st
from pathlib import Path
import datetime as dt
from database.queries import (
    get_products,
    get_laboratories,
    add_analyse,
)

# -------------------------------------------------------------
# Page 2 - Enregistrement d'une nouvelle analyse
# -------------------------------------------------------------
# Affiche un formulaire simple et professionnel pour encoder
# un nouveau résultat d'analyse dans la base de données.
# -------------------------------------------------------------

st.set_page_config(page_title="Ajouter une analyse", page_icon="🧪", layout="wide")

# Injecter le CSS global
css_path = Path("assets/styles.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Vérification d'authentification
if not st.session_state.get("auth", False):
    st.error("Vous devez être connecté pour accéder à cette page.")
    st.stop()

st.title("🧪 Ajouter une nouvelle analyse de produit")

# Charger les listes de produits et laboratoires
produits = get_products()  # retourne [{'id':1,'nom': 'Farine'}, ...]
laboratoires = get_laboratories()  # retourne [{'id':1,'nom': 'DIV LABO'}, ...]

# Disposition en grille (2 colonnes)
col1, col2 = st.columns(2)

with col1:
    produit_select = st.selectbox(
        "Produit",
        options=[p["nom"] for p in produits] if produits else ["Aucun produit"],
    )
    type_analyse = st.text_input("Type d'analyse (ex. pH, humidité...)")
    date_analyse = st.date_input("Date de l'analyse", value=dt.date.today())

with col2:
    laboratoire_select = st.selectbox(
        "Laboratoire / Division",
        options=[l["nom"] for l in laboratoires] if laboratoires else ["Aucun labo"],
    )
    resultat = st.text_area("Résultat / Conclusion", height=150)
    fichier = st.file_uploader("Joindre le rapport PDF (optionnel)", type=["pdf"])

# Bouton d'enregistrement
if st.button("💾 Enregistrer l'analyse"):
    if not (produit_select and type_analyse and resultat):
        st.warning("Veuillez remplir tous les champs obligatoires : produit, type d'analyse et résultat.")
    else:
        # Récupérer les IDs à partir des sélections
        produit_id = next((p["id"] for p in produits if p["nom"] == produit_select), None)
        labo_id = next((l["id"] for l in laboratoires if l["nom"] == laboratoire_select), None)
        if add_analyse(
            produit_id=produit_id,
            type_analyse=type_analyse,
            resultat=resultat,
            date_analyse=date_analyse,
            laboratoire_id=labo_id,
            agent_id=st.session_state["user"]["id"],
            fichier=fichier,
        ):
            st.success("Analyse enregistrée avec succès !")
        else:
            st.error("Une erreur est survenue lors de l'enregistrement.")
