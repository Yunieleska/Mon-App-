import streamlit as st
import sqlite3
import hashlib
import os
import base64

# CONFIGURATION
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, "storyia_users.db")

# --- LISTE DE TES PERSONNAGES ---
personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg"},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg"},
    {"nom": "Lucas", "img": "https://i.ibb.co/37456J5z/9mF2wXbL.jpg"},
    {"nom": "Ethan", "img": "https://i.pinimg.com/736x/2a/5a/53/2a5a53856b3e34b9d0737a42a222383c.jpg"},
    {"nom": "Léo", "img": "https://i.pinimg.com/736x/e4/f9/52/e4f952136e05f6e87398912e6971936c.jpg"},
    {"nom": "Liam", "img": "https://i.pinimg.com/736x/07/77/65/077765103a8848d7d8e6c4664879d72e.jpg"}
]

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
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14 !important; color: white; }
    .char-card { background: #1e2533; padding: 15px; border-radius: 15px; margin-bottom: 20px; text-align: center; }
    div.stButton > button { background-color: #ff4b4b !important; color: white !important; border: none !important; border-radius: 8px !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

display_banner()

# INITIALISATION BASE
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
        if st.button("Se connecter", key="btn_login"):
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
        q = st.selectbox("Question", ["Animal ?", "Ville ?", "Mère ?"])
        a = st.text_input("Réponse", type="password")
        if st.button("S'inscrire", key="btn_signup"):
            conn = sqlite3.connect(DB_FILE)
            try:
                conn.execute('INSERT INTO users VALUES (?,?,?,?)', (nu.strip(), hash_pass(np), q, hash_pass(a)))
                conn.commit()
                st.success("Inscription réussie !")
            except Exception as e: st.error(f"Erreur : {e}")
            conn.close()
else:
    st.title("Choisis ton personnage")
    cols = st.columns(3)
    for i, p in enumerate(personnages):
        with cols[i % 3]:
            st.markdown('<div class="char-card">', unsafe_allow_html=True)
            try:
                st.image(p["img"], use_container_width=True)
            except:
                st.write("Image non disponible")
            st.subheader(p["nom"])
            if st.button(f"Chatter", key=f"btn_{i}"):
                st.write(f"Démarrage de l'aventure avec {p['nom']}...")
            st.markdown('</div>', unsafe_allow_html=True)
            
    if st.button("Déconnexion"):
        st.session_state.authentifie = False
        st.rerun()
