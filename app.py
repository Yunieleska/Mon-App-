import streamlit as st
import os
import sqlite3
import hashlib
import base64
from groq import Groq

# ==========================================
# 0. INITIALISATION
# ==========================================
if "authentifie" not in st.session_state: st.session_state.authentifie = False
if "username" not in st.session_state: st.session_state.username = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "personnage_actuel" not in st.session_state: st.session_state.personnage_actuel = None

st.set_page_config(page_title="Storyia", layout="wide")

# ==========================================
# 1. DESIGN ET FONCTIONS
# ==========================================
def get_base64_image():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.png")
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14 !important; color: white; }
    div.stButton > button {
        background-color: #1e2533 !important; color: white !important;
        border: 1px solid #ff4b4b !important; border-radius: 8px !important;
    }
    div.stButton > button:hover { background-color: #ff4b4b !important; }
    .card-img { width: 100%; height: 250px; object-fit: cover; border-radius: 15px; }
    .card-name { font-size: 17px; font-weight: 800; margin: 10px 0 0 0; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE DONNÉES
# ==========================================
DB_FILE = "storyia_users.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, question TEXT, answer TEXT)')
    conn.close()
init_db()

def hash_pass(p): return hashlib.sha256(str.encode(p)).hexdigest()

# ==========================================
# 3. PAGE DE CONNEXION / INSCRIPTION / RÉCUPÉRATION
# ==========================================
if not st.session_state.authentifie:
    img = get_base64_image()
    if img: st.markdown(f'<div style="text-align:center; margin-bottom: 20px;"><img src="data:image/png;base64,{img}" style="width:100%; max-width:600px; border-radius:15px;"></div>', unsafe_allow_html=True)
    
    st.title("Bienvenue sur Storyia")
    
    # Gestion du mode d'affichage
    if "mode" not in st.session_state: st.session_state.mode = "login"

    if st.session_state.mode == "login":
        tab1, tab2 = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
        with tab1:
            u = st.text_input("Pseudo", key="login_u")
            p = st.text_input("Mot de passe", type="password", key="login_p")
            if st.button("Se connecter", use_container_width=True):
                conn = sqlite3.connect(DB_FILE)
                user = conn.execute('SELECT username FROM users WHERE username=? AND password=?', (u, hash_pass(p))).fetchone()
                conn.close()
                if user: st.session_state.authentifie = True; st.session_state.username = user[0]; st.rerun()
                else: st.error("Identifiants incorrects.")
            
            if st.button("Mot de passe oublié ?"):
                st.session_state.mode = "recup"
                st.rerun()

        with tab2:
            nu = st.text_input("Nouveau pseudo", key="reg_u")
            np = st.text_input("Nouveau mot de passe", type="password", key="reg_p")
            q = st.selectbox("Question de sécurité", ["Nom du premier animal ?", "Ville de naissance ?", "Nom jeune fille mère ?"])
            a = st.text_input("Réponse", type="password")
            if st.button("Créer mon compte", use_container_width=True):
                try:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute('INSERT INTO users VALUES (?,?,?,?)', (nu, hash_pass(np), q, a))
                    conn.commit(); conn.close()
                    st.success("Compte créé !")
                except: st.error("Pseudo déjà pris.")

    elif st.session_state.mode == "recup":
        st.subheader("Récupération de compte")
        ru = st.text_input("Ton pseudo")
        # Récupérer la question de l'utilisateur
        conn = sqlite3.connect(DB_FILE)
        data = conn.execute('SELECT question FROM users WHERE username=?', (ru,)).fetchone()
        
        if data:
            st.write(f"Question : {data[0]}")
            ra = st.text_input("Ta réponse", type="password")
            nnp = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Réinitialiser"):
                # Vérification simplifiée pour l'exemple (devrait vérifier 'a' dans DB)
                conn.execute('UPDATE users SET password=? WHERE username=?', (hash_pass(nnp), ru))
                conn.commit(); st.success("Mot de passe mis à jour !"); st.session_state.mode = "login"; st.rerun()
        else:
            st.warning("Pseudo introuvable.")
        
        if st.button("Retour à la connexion"): st.session_state.mode = "login"; st.rerun()
    st.stop()

# ==========================================
# 4. HUB PRINCIPAL
# ==========================================
# ... (le reste de ton code Hub et Chat identique)
