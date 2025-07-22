from pathlib import Path
import uuid
import mysql.connector
from datetime import date
from database.db import get_connection
from auth.security import hash_password, verify_password

# -------------------------------------------------------------
# Requêtes SQL centralisées pour OCC Analyses
# -------------------------------------------------------------
# Tables utilisées (schéma résumé) :
#   - utilisateurs(id, nom, email, mot_de_passe_hash, role_id, est_actif)
#   - roles(id, nom)
#   - produits(id, nom, ...)
#   - laboratoires(id, nom, ...)
#   - analyses(id, produit_id, type_analyse, resultat, date_analyse, laboratoire_id, agent_id, fichier_rapport)
# -------------------------------------------------------------

# === UTILISATEURS ========================================================

def _get_role_id(role_name: str, cursor) -> int:
    cursor.execute("SELECT id FROM roles WHERE nom = %s", (role_name,))
    row = cursor.fetchone()
    return row[0] if row else 2  # 2 = agent par défaut


def create_user(nom: str, email: str, mot_de_passe: str, role_name: str = "agent") -> bool:
    """Crée un utilisateur ; renvoie True si succès."""
    hashed = hash_password(mot_de_passe)
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM utilisateurs WHERE email = %s", (email,))
        if cur.fetchone():
            return False  # email déjà pris
        role_id = _get_role_id(role_name, cur)
        cur.execute(
            """
            INSERT INTO utilisateurs (nom, email, mot_de_passe_hash, role_id)
            VALUES (%s, %s, %s, %s)
            """,
            (nom, email, hashed, role_id),
        )
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print("MySQL create_user:", e)
        return False
    finally:
        cur.close()
        conn.close()


def authenticate_user(email: str, mot_de_passe: str):
    """Renvoie un dict utilisateur si auth OK, sinon None."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, nom, email, mot_de_passe_hash, role_id FROM utilisateurs WHERE email = %s AND est_actif = 1",
            (email,),
        )
        user = cur.fetchone()
        if user and verify_password(mot_de_passe, user["mot_de_passe_hash"]):
            return user
    except mysql.connector.Error as e:
        print("MySQL authenticate_user:", e)
    finally:
        cur.close()
        conn.close()
    return None


def email_existe(email: str) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM utilisateurs WHERE email = %s", (email,))
        return cur.fetchone() is not None
    finally:
        cur.close()
        conn.close()

# === PRODUITS & LABORATOIRES ============================================

def get_products():
    """Renvoie une liste de dicts {'id': int, 'nom': str}."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nom FROM produits ORDER BY nom")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def get_laboratories():
    """Renvoie une liste de dicts {'id': int, 'nom': str}."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nom FROM laboratoires ORDER BY nom")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

# === ANALYSES ============================================================

def _save_uploaded_file(uploaded_file) -> str | None:
    """Enregistre le PDF uploadé et renvoie le chemin relatif, ou None."""
    if uploaded_file is None:
        return None
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    unique_name = f"{uuid.uuid4()}.pdf"
    dest = uploads_dir / unique_name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


def add_analyse(
    produit_id: int,
    type_analyse: str,
    resultat: str,
    date_analyse: date,
    laboratoire_id: int,
    agent_id: int,
    fichier,
) -> bool:
    """Insère une analyse et renvoie True si succès."""
    chemin_pdf = _save_uploaded_file(fichier)
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO analyses (produit_id, type_analyse, resultat, date_analyse, laboratoire_id, agent_id, fichier_rapport)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                produit_id,
                type_analyse,
                resultat,
                date_analyse,
                laboratoire_id,
                agent_id,
                chemin_pdf,
            ),
        )
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print("MySQL add_analyse:", e)
        return False
    finally:
        cur.close()
        conn.close()
