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
if "mode" not in st.session_state: st.session_state.mode = "login"

# LOGIQUE AUTHENTIFICATION
if not st.session_state.authentifie:
    st.title("Bienvenue sur Storyia")
    
    if st.session_state.mode == "login":
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
            
            if st.button("Mot de passe oublié ?"):
                st.session_state.mode = "recup"
                st.rerun()

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

    elif st.session_state.mode == "recup":
        st.subheader("Récupération de mot de passe")
        ru = st.text_input("Ton pseudo")
        conn = sqlite3.connect(DB_FILE)
        data = conn.execute('SELECT question, answer FROM users WHERE username=?', (ru.strip(),)).fetchone()
        
        if data:
            st.write(f"Question de sécurité : **{data[0]}**")
            ra = st.text_input("Ta réponse", type="password")
            nnp = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Réinitialiser"):
                if hash_pass(ra) == data[1]:
                    conn.execute('UPDATE users SET password=? WHERE username=?', (hash_pass(nnp), ru.strip()))
                    conn.commit()
                    st.success("Mot de passe mis à jour !")
                    st.session_state.mode = "login"
                    st.rerun()
                else:
                    st.error("Réponse incorrecte.")
        conn.close()
        if st.button("Retour à la connexion"):
            st.session_state.mode = "login"
            st.rerun()

else:
    st.write(f"Bonjour {st.session_state.username} ! Tu es connecté.")
    if st.button("Déconnexion"):
        st.session_state.authentifie = False
        st.rerun()
