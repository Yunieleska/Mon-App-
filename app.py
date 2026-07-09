import streamlit as st
import sqlite3
import hashlib
import os

# CONFIGURATION
DB_FILE = "storyia_users.db"

# HASHAGE UNIQUE ET FIXE
def hash_pass(p):
    return hashlib.sha256(p.strip().encode('utf-8')).hexdigest()

# INITIALISATION DE LA BASE
conn = sqlite3.connect(DB_FILE)
conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, question TEXT, answer TEXT)')
conn.commit()
conn.close()

# CONFIGURATION PAGE
st.set_page_config(page_title="Storyia", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14 !important; color: white; }
    div.stButton > button { background-color: #1e2533 !important; color: white !important; border: 1px solid #ff4b4b !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

# GESTION SESSION
if "authentifie" not in st.session_state: st.session_state.authentifie = False

# LOGIQUE AUTHENTIFICATION
if not st.session_state.authentifie:
    st.title("Bienvenue sur Storyia")
    tab1, tab2 = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
    
    with tab1:
        u = st.text_input("Pseudo", key="log_u")
        p = st.text_input("Mot de passe", type="password", key="log_p")
        if st.button("Se connecter"):
            conn = sqlite3.connect(DB_FILE)
            user = conn.execute('SELECT username FROM users WHERE username=? AND password=?', (u.strip(), hash_pass(p))).fetchone()
            conn.close()
            if user: 
                st.session_state.authentifie = True
                st.session_state.username = user[0]
                st.rerun()
            else: 
                st.error("Identifiants incorrects.")

    with tab2:
        nu = st.text_input("Nouveau pseudo", key="reg_u")
        np = st.text_input("Nouveau mot de passe", type="password", key="reg_p")
        q = st.selectbox("Question", ["Animal ?", "Ville ?", "Mère ?"])
        a = st.text_input("Réponse", type="password")
        if st.button("S'inscrire"):
            conn = sqlite3.connect(DB_FILE)
            try:
                conn.execute('INSERT INTO users VALUES (?,?,?,?)', (nu.strip(), hash_pass(np), q, hash_pass(a)))
                conn.commit()
                st.success("Compte créé ! Tu peux te connecter.")
            except: 
                st.error("Erreur : Ce pseudo est déjà pris.")
            conn.close()
else:
    st.write(f"Bonjour {st.session_state.username} ! Tu es connecté.")
    if st.button("Déconnexion"):
        st.session_state.authentifie = False
        st.rerun()
