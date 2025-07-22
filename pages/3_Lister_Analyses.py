# Tableau de bord des analyses 
import streamlit as st
import pandas as pd
from database.queries import get_all_analyses

st.set_page_config(page_title="Liste des Analyses", page_icon="📋")

# CSS personnalisé
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Titre principal
st.title("📋 Liste des Analyses")

# Vérification connexion utilisateur
if "auth" not in st.session_state or not st.session_state.auth:
    st.error("⛔ Veuillez vous connecter pour accéder à cette page.")
    st.stop()

# Chargement des analyses
analyses = get_all_analyses()

if not analyses:
    st.warning("Aucune analyse enregistrée pour le moment.")
else:
    df = pd.DataFrame(analyses)

    # Affichage dans un tableau stylisé
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Option de filtre par produit ou analyste (facultatif)
    with st.expander("🔍 Filtres avancés"):
        produit_filter = st.text_input("Filtrer par produit")
        analyste_filter = st.text_input("Filtrer par analyste")

        if produit_filter or analyste_filter:
            df = df[
                df["Produit"].str.contains(produit_filter, case=False, na=False) &
                df["Analyste"].str.contains(analyste_filter, case=False, na=False)
            ]
            st.dataframe(df, use_container_width=True, hide_index=True)

    # Téléchargement CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger en CSV",
        data=csv,
        file_name="analyses_occ.csv",
        mime="text/csv"
    )
