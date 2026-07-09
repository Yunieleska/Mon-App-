import streamlit as st
import os
import sqlite3
import hashlib
import base64
from groq import Groq

# ==========================================
# 0. INITIALISATION GÉNÉRALE
# ==========================================
if "authentifie" not in st.session_state: st.session_state.authentifie = False
if "username" not in st.session_state: st.session_state.username = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "personnage_actuel" not in st.session_state: st.session_state.personnage_actuel = None

# ==========================================
# 1. CONFIGURATION ET STYLE
# ==========================================
st.set_page_config(page_title="Storyia", layout="centered")

def get_base64_image():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "bg.png")
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

st.markdown(
    """
    <style>
    .stApp { background-color: #000000 !important; color: white; }
    .card-img { width: 100%; height: 250px; object-fit: cover; border-radius: 15px; margin-bottom: 5px; }
    .card-name { font-size: 17px; font-weight: 800; margin: 0; }
    .card-desc { font-size: 12px; color: #a0a0a0; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True
)

# ==========================================
# 2. GESTION BASE DE DONNÉES
# ==========================================
DB_FILE = "/tmp/storyia_users.db" if os.path.exists("/mount/src") else "storyia_users.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, security_question TEXT, security_answer TEXT)')
    conn.close()
init_db()

# ==========================================
# 3. ÉCRAN DE CONNEXION (SANS RECTANGLE VIDE)
# ==========================================
if not st.session_state.authentifie:
    image_base64 = get_base64_image()
    if image_base64:
        st.markdown(f'<div style="text-align: center; margin-bottom: 20px;"><img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 650px; border-radius: 14px;"></div>', unsafe_allow_html=True)
    
    st.title("Bienvenue sur Storyia")
    tab_login, tab_register = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
    with tab_login:
        u = st.text_input("Pseudo", key="log_u")
        p = st.text_input("Mot de passe", type="password", key="log_p")
        if st.button("Se connecter"): st.session_state.authentifie = True; st.session_state.username = u; st.rerun()
    with tab_register:
        st.write("Inscris-toi pour créer des histoires.")
    st.stop()

# ==========================================
# 4. SIDEBAR & CONFIG
# ==========================================
CATEGORIES = ["Mafieux", "Fantaisie", "Motard", "École"]
BASE_DIR = "Personnages"
os.makedirs(BASE_DIR, exist_ok=True)
for cat in CATEGORIES: os.makedirs(os.path.join(BASE_DIR, cat), exist_ok=True)

st.sidebar.markdown(f"### 👤 {st.session_state.username}")
if st.sidebar.button("Déconnexion"): st.session_state.authentifie = False; st.rerun()

with st.sidebar.expander("➕ Créer un personnage"):
    nom_p = st.text_input("Nom")
    cat_p = st.selectbox("Univers", CATEGORIES)
    bio_p = st.text_area("Description")
    if st.button("Sauvegarder"):
        with open(os.path.join(BASE_DIR, cat_p, f"{nom_p.strip()}.txt"), "w", encoding="utf-8") as f: f.write(bio_p)
        st.rerun()

# ==========================================
# 5. HUB (GRILLE SOCIAL MEDIA)
# ==========================================
if st.session_state.personnage_actuel is None:
    st.markdown("### ✨ Pour vous")
    tous = []
    for cat in CATEGORIES:
        for f in os.listdir(os.path.join(BASE_DIR, cat)):
            if f.endswith(".txt"): tous.append((cat, f))
    
    cols = st.columns(2)
    for i, (cat, f) in enumerate(tous):
        with open(os.path.join(BASE_DIR, cat, f), "r", encoding="utf-8", errors="ignore") as file: desc = file.read()
        with cols[i % 2]:
            st.markdown(f'<img src="https://picsum.photos/400/600?random={i}" class="card-img">', unsafe_allow_html=True)
            st.markdown(f'<p class="card-name">{f.replace(".txt", "")}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="card-desc">{cat} • {desc[:25]}...</p>', unsafe_allow_html=True)
            if st.button(f"Chatter", key=f"btn_{i}", use_container_width=True):
                st.session_state.personnage_actuel = f.replace(".txt", "")
                st.session_state.messages = [{"role": "system", "content": f"Tu es {f.replace('.txt', '')}. Contexte: {desc}"}]
                st.rerun()

# ==========================================
# 6. CHAT
# ==========================================
else:
    if st.button("⬅️ Retour"): st.session_state.personnage_actuel = None; st.rerun()
    st.header(f"🎭 Chat avec {st.session_state.personnage_actuel}")
    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            client = Groq(api_key="VOTRE_CLE_API_GROQ_ICI")
            res = client.chat.completions.create(messages=st.session_state.messages, model="llama-3.1-8b-instant").choices[0].message.content
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
