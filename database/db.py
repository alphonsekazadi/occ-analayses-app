# Connexion MySQL 
import mysql.connector
import streamlit as st

# Informations de connexion 
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "occ_analyses"

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        return None
