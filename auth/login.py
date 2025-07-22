import streamlit as st
from database.queries import create_user, authenticate_user, email_existe

# Titre principal
st.title("🔐 Authentification - OCC Analyses App")

# Choix: Connexion ou Inscription
choix = st.radio("Choisissez une option :", ("Se connecter", "Créer un compte"), horizontal=True)

if choix == "Créer un compte":
    st.subheader("📝 Créer un compte utilisateur")
    nom = st.text_input("Nom complet")
    email = st.text_input("Adresse email")
    mot_de_passe = st.text_input("Mot de passe", type="password")
    confirmation = st.text_input("Confirmez le mot de passe", type="password")
    role = st.selectbox("Rôle", ["agent", "analyste", "admin"])

    if st.button("S'inscrire"):
        if mot_de_passe != confirmation:
            st.error("❌ Les mots de passe ne correspondent pas.")
        elif email_existe(email):
            st.warning("⚠️ Cet email est déjà utilisé.")
        else:
            if create_user(nom, email, mot_de_passe, role):
                st.success("✅ Compte créé avec succès. Vous pouvez maintenant vous connecter.")
            else:
                st.error("❌ Une erreur est survenue lors de la création du compte.")

else:
    st.subheader("🔓 Se connecter")
    email = st.text_input("Adresse email")
    mot_de_passe = st.text_input("Mot de passe", type="password")

    if st.button("Connexion"):
        user = authenticate_user(email, mot_de_passe)
        if user:
            st.session_state["auth"] = True
            st.session_state["user"] = user
            st.success(f"✅ Bienvenue {user['nom']} !")
            st.switch_page("pages/1_Accueil.py")
        else:
            st.error("❌ Email ou mot de passe incorrect.")
