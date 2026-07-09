import streamlit as st
import sqlite3
import hashlib
import os
import base64

# CONFIGURATION
DB_FILE = "storyia_users.db"

def hash_pass(p):
    return hashlib.sha256(p.strip().encode('utf-8')).hexdigest()

def display_banner():
    # Correction : on cherche maintenant 'bg.png'
    dossier_actuel = os.getcwd()
    fichiers = os.listdir(dossier_actuel)
    
    # Cherche une correspondance insensible à la casse pour 'bg.png'
    image_nom = next((f for f in fichiers if f.lower() == "bg.png"), None)
    
    if image_nom:
        image_path = os.path.join(dossier_actuel, image_nom)
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{data}" style="width:100%; max-width:600px; border-radius:15px;"></div>', unsafe_allow_html=True)
    else:
        st.warning(f"Fichier 'bg.png' non trouvé dans : {dossier_actuel}. Fichiers présents : {fichiers}")

# CONFIG PAGE
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

# AFFICHAGE
display_banner()

if "authentifie" not in st.session_state: st.session_state.authentifie = False
if "mode" not in st.session_state: st.session_state.mode = "login"

# LOGIQUE
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
                else: st.error("Identifiants incorrects.")
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
                    st.success("Compte créé ! Connecte-toi.")
                except: st.error("Pseudo déjà pris.")
                conn.close()
    elif st.session_state.mode == "recup":
        st.subheader("Récupération de mot de passe")
        ru = st.text_input("Ton pseudo")
        conn = sqlite3.connect(DB_FILE)
        data = conn.execute('SELECT question, answer FROM users WHERE username=?', (ru.strip(),)).fetchone()
        conn.close()
        if data:
            st.write(f"Question : **{data[0]}**")
            ra = st.text_input("Ta réponse", type="password")
            nnp = st.text_input("Nouveau mot de passe", type="password")
            if st.button("Valider la récupération"):
                if hash_pass(ra) == data[1]:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute('UPDATE users SET password=? WHERE username=?', (hash_pass(nnp), ru.strip()))
                    conn.commit(); conn.close()
                    st.success("Mot de passe mis à jour !")
                    st.session_state.mode = "login"; st.rerun()
                else: st.error("Réponse incorrecte.")
        if st.button("Retour à la connexion"):
            st.session_state.mode = "login"; st.rerun()
else:
    st.write(f"Bonjour {st.session_state.username} !")
    if st.button("Déconnexion"):
        st.session_state.authentifie = False; st.rerun()
