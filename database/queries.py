from pathlib import Path
import uuid
import base64
import os
import mysql.connector
from datetime import date, datetime
import random
from database.db import get_connection
from auth.security import hash_password, verify_password

# Ces imports servent à la génération PDF / QR Code
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import qrcode

# -------------------------------------------------------------
# Requêtes SQL OCC Analyses (version simplifiée)
# -------------------------------------------------------------

# === UTILISATEURS ========================================================

def _get_role_id(role_name: str, cursor) -> int:
    cursor.execute("SELECT id FROM roles WHERE nom = %s", (role_name,))
    row = cursor.fetchone()
    return row[0] if row else 2


def create_user(nom: str, email: str, mot_de_passe: str, role_name: str = "agent") -> bool:
    hashed = hash_password(mot_de_passe)
    conn = get_connection(); ok = False
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM utilisateurs WHERE email=%s", (email,))
            if cur.fetchone():
                return False
            role_id = _get_role_id(role_name, cur)
            cur.execute(
                "INSERT INTO utilisateurs (nom,email,mot_de_passe_hash,role_id) VALUES (%s,%s,%s,%s)",
                (nom, email, hashed, role_id),
            ); conn.commit(); ok = True
        except mysql.connector.Error as e:
            print("create_user:", e)
        finally:
            cur.close(); conn.close()
    return ok


def authenticate_user(email: str, pwd: str):
    conn = get_connection(); user=None
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM utilisateurs WHERE email=%s AND est_actif=1", (email,))
        row = cur.fetchone(); cur.close(); conn.close()
        if row and verify_password(pwd, row["mot_de_passe_hash"]):
            user = row
    return user


def email_existe(email: str) -> bool:
    conn = get_connection(); ex=False
    if conn:
        cur = conn.cursor(); cur.execute("SELECT 1 FROM utilisateurs WHERE email=%s", (email,)); ex=cur.fetchone() is not None
        cur.close(); conn.close()
    return ex
# === ADMIN – UTILISATEURS ===============================================

def list_utilisateurs():
    """
    Retourne la liste des utilisateurs : id, nom, email, rôle, actif.
    """
    conn = get_connection()
    result = []
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT u.id, u.nom, u.email, r.nom AS role, u.est_actif
                FROM utilisateurs u
                LEFT JOIN roles r ON r.id = u.role_id
                ORDER BY u.id
                """
            )
            result = cur.fetchall()
        except mysql.connector.Error as e:
            print("MySQL list_utilisateurs:", e)
        finally:
            cur.close()
            conn.close()
    return result


def supprimer_utilisateur(user_id: int) -> bool:
    """
    Supprime totalement un compte utilisateur.
    (À sécuriser en production : désactivation plutôt que delete.)
    """
    conn = get_connection()
    ok = False
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM utilisateurs WHERE id = %s", (user_id,))
            conn.commit()
            ok = True
        except mysql.connector.Error as e:
            print("MySQL supprimer_utilisateur:", e)
        finally:
            cur.close()
            conn.close()
    return ok


def reset_password_utilisateur(user_id: int) -> bool:
    """
    Réinitialise le mot de passe d’un compte à « admin123 ».
    (À remplacer par un envoi de lien de réinitialisation en production.)
    """
    tmp_hash = hash_password("admin123")
    conn = get_connection()
    ok = False
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE utilisateurs SET mot_de_passe_hash = %s WHERE id = %s",
                (tmp_hash, user_id),
            )
            conn.commit()
            ok = True
        except mysql.connector.Error as e:
            print("MySQL reset_password_utilisateur:", e)
        finally:
            cur.close()
            conn.close()
    return ok


# === PRODUITS / LABOS ====================================================
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

def add_analyse(produit_id: int, type_analyse: str, resultat: str, date_analyse: date,
                laboratoire_id: int, agent_id: int, fichier):
    chemin_pdf = _save_uploaded_file(fichier)
    conn = get_connection(); ok=False
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO analyses (produit_id,type_analyse,resultat,date_analyse,laboratoire_id,agent_id,fichier_rapport) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (produit_id, type_analyse, resultat, date_analyse, laboratoire_id, agent_id, chemin_pdf)
            ); conn.commit(); ok=True
        except mysql.connector.Error as e:
            print("MySQL add_analyse:", e)
        finally:
            cur.close(); conn.close()
    return ok


def get_all_analyses():
    conn = get_connection(); res=[]
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT a.id AS `ID Analyse`, p.nom AS `Produit`, a.type_analyse AS `Type`, a.resultat AS `Résultat`,
                   DATE_FORMAT(a.date_analyse,'%d/%m/%Y') AS `Date`, l.nom AS `Laboratoire`, u.nom AS `Analyste`
            FROM analyses a
            JOIN produits p ON p.id=a.produit_id
            LEFT JOIN laboratoires l ON l.id=a.laboratoire_id
            LEFT JOIN utilisateurs u ON u.id=a.agent_id
            ORDER BY a.date_analyse DESC, a.id DESC
            """
        ); res=cur.fetchall(); cur.close(); conn.close()
    return res


def get_products():
    conn = get_connection(); res=[]
    if conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT id, nom FROM produits ORDER BY nom"); res=cur.fetchall(); cur.close(); conn.close()
    return res


def get_laboratories():
    conn = get_connection(); res=[]
    if conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT id, nom FROM laboratoires ORDER BY nom"); res=cur.fetchall(); cur.close(); conn.close()
    return res

# === ANALYSES ============================================================

def get_analyses_non_validees():
    conn = get_connection(); res=[]
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT a.id, p.nom AS produit, a.resultat,
                   DATE_FORMAT(a.date_analyse,'%d/%m/%Y') AS date_analyse,
                   l.nom AS laboratoire, u.nom AS analyste
            FROM analyses a
            JOIN produits p ON p.id=a.produit_id
            LEFT JOIN laboratoires l ON l.id=a.laboratoire_id
            LEFT JOIN utilisateurs u ON u.id=a.agent_id
            WHERE a.id NOT IN (SELECT analyse_id FROM certificats)
            ORDER BY a.date_analyse DESC
            """
        ); res = cur.fetchall(); cur.close(); conn.close()
    return res

# === CERTIFICATS (validation + PDF) ======================================

def _generate_qr(data: str, dest_path: Path):
    qr_img = qrcode.make(data)
    qr_img.save(dest_path)


def _generate_pdf(cert_num: str, analyse: dict, pdf_path: Path, qr_path: Path):
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "Office Congolais de Contrôle (OCC)")
    c.setFont("Helvetica", 12)
    c.drawString(40, height - 80, f"Certificat d'analyse – N° {cert_num}")

    y = height - 130
    for lbl, val in [
        ("Produit", analyse["produit"]),
        ("Résultat", analyse["resultat"]),
        ("Date analyse", analyse["date_analyse"]),
        ("Laboratoire", analyse["laboratoire"]),
        ("Analyste", analyse["analyste"]),
    ]:
        c.drawString(40, y, f"{lbl} : {val}")
        y -= 20

    c.drawImage(str(qr_path), 400, y + 60, width=120, height=120)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 40, "Ce certificat a été généré automatiquement le " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    c.save()


def valider_analyse(analyse_id: int, superviseur_id: int) -> bool:
    """Valide une analyse -> génère PDF + enregistrement certificat."""
    conn = get_connection(); ok=False
    if not conn:
        return False
    try:
        cur = conn.cursor(dictionary=True)
        # Récupérer infos analyse
        cur.execute(
            """
            SELECT a.id, p.nom AS produit, a.resultat,
                   DATE_FORMAT(a.date_analyse,'%d/%m/%Y') AS date_analyse,
                   l.nom AS laboratoire, u.nom AS analyste
            FROM analyses a
            JOIN produits p ON p.id=a.produit_id
            LEFT JOIN laboratoires l ON l.id=a.laboratoire_id
            LEFT JOIN utilisateurs u ON u.id=a.agent_id
            WHERE a.id=%s
            """,
            (analyse_id,),
        )
        analyse = cur.fetchone()
        if not analyse:
            return False

        # Préparer num cert + chemins
        cert_num = f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}"
        cert_dir = Path("certificats"); cert_dir.mkdir(exist_ok=True)
        pdf_path = cert_dir / f"{cert_num}.pdf"
        qr_path = cert_dir / f"{cert_num}.png"

        # Génération QR et PDF
        _generate_qr(cert_num, qr_path)
        _generate_pdf(cert_num, analyse, pdf_path, qr_path)

        # Enregistrement DB (table certificats)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO certificats (numero_certificat, analyse_id, date_emission, superviseur_id, chemin_pdf, qr_data, statut)
            VALUES (%s, %s, NOW(), %s, %s, %s, 'emis')
            """,
            (cert_num, analyse_id, superviseur_id, str(pdf_path), cert_num),
        ); conn.commit(); ok=True
    except mysql.connector.Error as e:
        print("valider_analyse:", e)
    finally:
        cur.close(); conn.close()
    return ok

# === CERTIFICATS DISPONIBLES ============================================

def get_certificats_disponibles():
    conn = get_connection(); res=[]
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT c.id, c.numero_certificat, c.chemin_pdf,
                   p.nom               AS produit,
                   DATE_FORMAT(a.date_analyse,'%d/%m/%Y') AS date_analyse,
                   l.nom               AS laboratoire,
                   u.nom               AS analyste
            FROM certificats c
            JOIN analyses a ON a.id=c.analyse_id
            JOIN produits  p ON p.id=a.produit_id
            LEFT JOIN laboratoires l ON l.id=a.laboratoire_id
            LEFT JOIN utilisateurs u ON u.id=a.agent_id
            WHERE c.statut='emis'
            ORDER BY c.date_emission DESC
            """,
        ); rows=cur.fetchall(); cur.close(); conn.close()
        for row in rows:
            pdf_path = row["chemin_pdf"]
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, "rb") as f:
                    row["fichier_base64"] = base64.b64encode(f.read()).decode()
                    row["nom_fichier"] = Path(pdf_path).name
            else:
                row["fichier_base64"] = ""
                row["nom_fichier"] = "certificat.pdf"
            res.append(row)
    return res
# === DASHBOARD STATS & LATEST ===========================================

def get_dashboard_stats():
    """Renvoie un dict de statistiques pour le tableau de bord."""
    conn = get_connection()
    stats = {
        "Analyses totales": 0,
        "Produits validés": 0,
        "Produits rejetés": 0,
        "Certificats générés": 0,
        "Analystes actifs": 0,
    }
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM analyses")
            stats["Analyses totales"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM analyses WHERE resultat LIKE '%Conforme%'")
            stats["Produits validés"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM analyses WHERE resultat LIKE '%Non Conforme%'")
            stats["Produits rejetés"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM certificats WHERE statut='emis'")
            stats["Certificats générés"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM utilisateurs WHERE role_id = 2 AND est_actif = 1")
            stats["Analystes actifs"] = cur.fetchone()[0]
        except mysql.connector.Error as e:
            print("get_dashboard_stats :", e)
        finally:
            cur.close()
            conn.close()
    return stats


def get_latest_analyses(limit: int = 5):
    """Retourne les 'limit' dernières analyses."""
    conn = get_connection()
    rows = []
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT a.id AS `ID Analyse`,
                   p.nom AS Produit,
                   a.resultat AS Résultat,
                   DATE_FORMAT(a.date_analyse, '%d/%m/%Y') AS Date,
                   u.nom AS Responsable
            FROM analyses a
            JOIN produits p ON p.id = a.produit_id
            LEFT JOIN utilisateurs u ON u.id = a.agent_id
            ORDER BY a.date_analyse DESC, a.id DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    return rows
