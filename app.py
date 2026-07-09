import streamlit as st
import os
import sqlite3
import hashlib
import base64

# --- LIGNE DE SECOURS (Si erreur persistante, enleve le '#' devant la ligne suivante pour reset) ---
# os.remove("storyia_users.db")

# CONFIGURATION
DB_FILE = "storyia_users.db"

# HASHAGE (fixé en utf-8 pour la cohérence)
def hash_pass(p):
    return hashlib.sha256(p.strip().encode('utf-8')).hexdigest()

# AFFICHAGE BANNIÈRE (Utilise fond.png)
def display_banner():
    if os.path.exists("fond.png"):
        with open("fond.png", "rb") as f:
            data = base64.b64encode(f.read()).decode()
            st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{data}" style="width:100%; max-width:600px; border-radius:15px;"></div>', unsafe_allow_html=True)

# CONFIGURATION PAGE
st.set_page_config(page_title="Storyia", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14 !important; color: white; }
    div.stButton > button { background-color: #1e2533 !important; color: white !important; border: 1px solid #ff4b4b !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

# BASE DE DONNÉES
conn = sqlite3.connect(DB_FILE)
conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, question TEXT, answer TEXT)')
conn.commit(); conn.close()

# SESSION
if "authentifie" not in st.session_state: st.session_state.authentifie = False

# LOGIQUE
if not st.session_state.authentifie:
    display_banner()
    st.title("Bienvenue sur Storyia")
    
    tab1, tab2 = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
    with tab1:
        u = st.text_input("Pseudo", key="login_u")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter"):
            conn = sqlite3.connect(DB_FILE)
            user = conn.execute('SELECT username FROM users WHERE username=? AND password=?', (u.strip(), hash_pass(p))).fetchone()
            conn.close()
            if user:
                st.session_state.authentifie = True
                st.session_state.username = user[0]
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with tab2:
        nu = st.text_input("Nouveau pseudo", key="reg_u")
        np = st.text_input("Nouveau mot de passe", type="password", key="reg_p")
        if st.button("S'inscrire"):
            conn = sqlite3.connect(DB_FILE)
            try:
                conn.execute('INSERT INTO users VALUES (?,?,?,?)', (nu.strip(), hash_pass(np), "Q", "A"))
                conn.commit()
                st.success("Compte créé ! Connecte-toi.")
            except: st.error("Pseudo déjà pris.")
            conn.close()
else:
    st.write(f"Bonjour {st.session_state.username} !")
    if st.button("Déconnexion"):
        st.session_state.authentifie = False
        st.rerun()
