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
if "mode" not in st.session_state: st.session_state.mode = "login"

st.set_page_config(page_title="Storyia", layout="wide")

# ==========================================
# 1. DESIGN ET FONCTIONS
# ==========================================
def get_base64_image():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.png")
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def hash_pass(p): return hashlib.sha256(str.encode(p.strip())).hexdigest()

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14 !important; color: white; }
    div.stButton > button { background-color: #1e2533 !important; color: white !important; border: 1px solid #ff4b4b !important; border-radius: 8px !important; }
    div.stButton > button:hover { background-color: #ff4b4b !important; }
    .card-img { width: 100%; height: 250px; object-fit: cover; border-radius: 15px; }
    .card-name { font-size: 17px; font-weight: 800; margin: 10px 0 0 0; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE DONNÉES
# ==========================================
DB_FILE = "storyia_users.db"
conn = sqlite3.connect(DB_FILE)
conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, question TEXT, answer TEXT)')
conn.commit(); conn.close()

# ==========================================
# 3. PAGE DE CONNEXION / INSCRIPTION / RÉCUPÉRATION
# ==========================================
if not st.session_state.authentifie:
    img = get_base64_image()
    if img: st.markdown(f'<div style="text-align:center; margin-bottom: 20px;"><img src="data:image/png;base64,{img}" style="width:100%; max-width:600px; border-radius:15px;"></div>', unsafe_allow_html=True)
    
    st.title("Bienvenue sur Storyia")
    
    if st.session_state.mode == "login":
        tab1, tab2 = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
        with tab1:
            u = st.text_input("Pseudo", key="login_u")
            p = st.text_input("Mot de passe", type="password", key="login_p")
            if st.button("Se connecter", use_container_width=True):
                conn = sqlite3.connect(DB_FILE)
                user = conn.execute('SELECT username FROM users WHERE username=? AND password=?', (u.strip(), hash_pass(p))).fetchone()
                conn.close()
                if user: st.session_state.authentifie = True; st.session_state.username = user[0]; st.rerun()
                else: st.error("Identifiants incorrects.")
            if st.button("Mot de passe oublié ?"): st.session_state.mode = "recup"; st.rerun()
            
        with tab2:
            nu = st.text_input("Nouveau pseudo", key="reg_u")
            np = st.text_input("Nouveau mot de passe", type="password", key="reg_p")
            q = st.selectbox("Question de sécurité", ["Nom du premier animal ?", "Ville de naissance ?", "Nom jeune fille mère ?"])
            a = st.text_input("Réponse", type="password")
            if st.button("Créer mon compte", use_container_width=True):
                try:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute('INSERT INTO users VALUES (?,?,?,?)', (nu.strip(), hash_pass(np), q, hash_pass(a)))
                    conn.commit(); conn.close()
                    st.success("Compte créé !"); st.rerun()
                except: st.error("Pseudo déjà pris.")

    elif st.session_state.mode == "recup":
        st.subheader("Récupération")
        ru = st.text_input("Ton pseudo")
        conn = sqlite3.connect(DB_FILE)
        data = conn.execute('SELECT question, answer FROM users WHERE username=?', (ru.strip(),)).fetchone()
        if data:
            st.write(f"Question : {data[0]}")
            ra = st.text_input("Réponse", type="password")
            nnp = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Valider"):
                if hash_pass(ra) == data[1]:
                    conn.execute('UPDATE users SET password=? WHERE username=?', (hash_pass(nnp), ru.strip()))
                    conn.commit(); st.success("Mot de passe mis à jour !"); st.session_state.mode = "login"; st.rerun()
                else: st.error("Réponse incorrecte.")
        conn.close()
        if st.button("Retour"): st.session_state.mode = "login"; st.rerun()
    st.stop()

# ==========================================
# 4. HUB PRINCIPAL
# ==========================================
st.sidebar.button("Déconnexion", on_click=lambda: setattr(st.session_state, 'authentifie', False) or st.rerun())
st.header("✨ Pour vous")
# ... (le reste de ton code hub/chat reste inchangé)
