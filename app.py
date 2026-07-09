import streamlit as st
import sqlite3
import hashlib
import os
import base64

# CONFIGURATION
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, "storyia_users.db")

# SUPPRESSION FORCEE DE LA BASE (Pour repartir à zéro)
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

def hash_pass(p):
    return hashlib.sha256(p.strip().encode('utf-8')).hexdigest()

def display_banner():
    dossier_actuel = os.getcwd()
    fichiers = os.listdir(dossier_actuel)
    image_nom = next((f for f in fichiers if f.lower() == "bg.png"), None)
    
    if image_nom:
        image_path = os.path.join(dossier_actuel, image_nom)
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{data}" style="width:100%; max-width:600px; border-radius:15px;"></div>', unsafe_allow_html=True)

# CONFIG PAGE
st.set_page_config(page_title="Storyia", layout="wide")
st.markdown("""<style>.stApp { background-color: #0B0E14 !important; color: white; }</style>""", unsafe_allow_html=True)

display_banner()

# INITIALISATION BASE (sera recréée propre à chaque démarrage)
conn = sqlite3.connect(DB_FILE)
conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, question TEXT, answer TEXT)')
conn.commit(); conn.close()

if "authentifie" not in st.session_state: st.session_state.authentifie = False

# LOGIQUE DE CONNEXION
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
            else: st.error("Identifiants incorrects. Inscris-toi d'abord.")

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
                st.success("Compte créé ! Connecte-toi maintenant.")
            except: st.error("Erreur : Pseudo déjà pris.")
            conn.close()
else:
    st.write(f"Bonjour {st.session_state.username} !")
    if st.button("Déconnexion"):
        st.session_state.authentifie = False
        st.rerun()
