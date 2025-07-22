# Generation et affichage des certificats 
import streamlit as st
from database.queries import get_certificats_disponibles
import base64

st.set_page_config(page_title="📜 Certificats - OCC Analyses App", page_icon="📜")

st.title("📜 Certificats des Analyses")

# CSS personnalisé
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Chargement des certificats disponibles
certificats = get_certificats_disponibles()

if not certificats:
    st.info("Aucun certificat disponible pour le moment.")
else:
    st.subheader("📄 Liste des certificats disponibles")
    for cert in certificats:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Produit :** {cert['produit']}")
                st.markdown(f"**Date d'analyse :** {cert['date_analyse']}")
                st.markdown(f"**Laboratoire :** {cert['laboratoire']}")
                st.markdown(f"**Analyste :** {cert['analyste']}")
            with col2:
                bouton_dl = st.download_button(
                    label="📥 Télécharger",
                    data=base64.b64decode(cert['fichier_base64']),
                    file_name=cert['nom_fichier'],
                    mime="application/pdf",
                    key=cert['id']
                )
