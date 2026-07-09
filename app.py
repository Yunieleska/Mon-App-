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
# 1. FONCTIONS & DESIGN
# ==========================================
def get_base64_image():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.png")
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: white; }
    .card-img { width: 100%; height: 250px; object-fit: cover; border-radius: 15px; }
    .card-name { font-size: 17px; font-weight: 800; margin: 10px 0 0 0; }
    .card-desc { font-size: 12px; color: #a0a0a0; margin-bottom: 10px; }
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
# 3. PAGE DE CONNEXION / INSCRIPTION
# ==========================================
if not st.session_state.authentifie:
    img = get_base64_image()
    if img: st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{img}" style="width:100%; max-width:600px; border-radius:15px;"></div>', unsafe_allow_html=True)
    
    st.title("Bienvenue sur Storyia")
    tab1, tab2 = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
    
    with tab1:
        u = st.text_input("Pseudo", key="login_u")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter"):
            conn = sqlite3.connect(DB_FILE)
            user = conn.execute('SELECT username FROM users WHERE username=? AND password=?', (u, hash_pass(p))).fetchone()
            conn.close()
            if user: st.session_state.authentifie = True; st.session_state.username = user[0]; st.rerun()
            else: st.error("Identifiants incorrects.")
            
    with tab2:
        nu = st.text_input("Nouveau pseudo", key="reg_u")
        np = st.text_input("Nouveau mot de passe", type="password", key="reg_p")
        q = st.text_input("Question de sécurité")
        a = st.text_input("Réponse")
        if st.button("Créer mon compte"):
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.execute('INSERT INTO users VALUES (?,?,?,?)', (nu, hash_pass(np), q, a))
                conn.commit(); conn.close()
                st.success("Compte créé ! Connecte-toi.")
            except: st.error("Pseudo déjà pris.")
    st.stop()

# ==========================================
# 4. HUB PRINCIPAL (GRILLE)
# ==========================================
CATEGORIES = ["Mafieux", "Fantaisie", "Motard", "École"]
BASE_DIR = "Personnages"
os.makedirs(BASE_DIR, exist_ok=True)
for c in CATEGORIES: os.makedirs(os.path.join(BASE_DIR, c), exist_ok=True)

if st.sidebar.button("Déconnexion"): st.session_state.authentifie = False; st.rerun()

if st.session_state.personnage_actuel is None:
    st.header("✨ Pour vous")
    tous = [(c, f) for c in CATEGORIES for f in os.listdir(os.path.join(BASE_DIR, c)) if f.endswith(".txt")]
    cols = st.columns(4)
    for i, (cat, f) in enumerate(tous):
        with cols[i % 4]:
            st.markdown(f'<img src="https://picsum.photos/400/600?random={i}" class="card-img">', unsafe_allow_html=True)
            st.markdown(f'<p class="card-name">{f.replace(".txt", "")}</p>', unsafe_allow_html=True)
            if st.button(f"Chatter", key=f"btn_{i}", use_container_width=True):
                st.session_state.personnage_actuel = f.replace(".txt", "")
                st.rerun()
else:
    if st.button("⬅️ Retour"): st.session_state.personnage_actuel = None; st.rerun()
    st.header(f"Discussion avec {st.session_state.personnage_actuel}")
    if prompt := st.chat_input():
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"): st.markdown("Réponse de l'IA...")
