import streamlit as st
import os
import sqlite3
import hashlib
import base64

# ==========================================
# 0. INITIALISATION
# ==========================================
if "authentifie" not in st.session_state: st.session_state.authentifie = False
if "username" not in st.session_state: st.session_state.username = ""
if "mode" not in st.session_state: st.session_state.mode = "login"

st.set_page_config(page_title="Storyia", layout="wide")

# ==========================================
# 1. DESIGN & HASH
# ==========================================
def hash_pass(p): 
    # On utilise un hash simple, identique partout
    return hashlib.sha256(p.strip().encode()).hexdigest()

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14 !important; color: white; }
    div.stButton > button { background-color: #1e2533 !important; color: white !important; border: 1px solid #ff4b4b !important; border-radius: 8px !important; }
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
# 3. LOGIQUE
# ==========================================
if not st.session_state.authentifie:
    st.title("Bienvenue sur Storyia")
    
    if st.session_state.mode == "login":
        tab1, tab2 = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
        with tab1:
            u = st.text_input("Pseudo", key="login_u")
            p = st.text_input("Mot de passe", type="password", key="login_p")
            if st.button("Se connecter"):
                conn = sqlite3.connect(DB_FILE)
                # On cherche le user AVEC le hash du mot de passe
                cur = conn.execute('SELECT username FROM users WHERE username=? AND password=?', (u.strip(), hash_pass(p)))
                user = cur.fetchone()
                conn.close()
                if user: 
                    st.session_state.authentifie = True
                    st.session_state.username = user[0]
                    st.rerun()
                else: st.error("Identifiants incorrects.")
            
        with tab2:
            nu = st.text_input("Nouveau pseudo", key="reg_u")
            np = st.text_input("Nouveau mot de passe", type="password", key="reg_p")
            q = st.selectbox("Question", ["Animal ?", "Ville ?", "Mère ?"])
            a = st.text_input("Réponse", type="password")
            if st.button("Créer mon compte"):
                try:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute('INSERT INTO users VALUES (?,?,?,?)', (nu.strip(), hash_pass(np), q, hash_pass(a)))
                    conn.commit(); conn.close()
                    st.success("Compte créé ! Connecte-toi.")
                except: st.error("Pseudo déjà pris.")
    st.stop()
