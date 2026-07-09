import streamlit as st
import os
import sqlite3
import hashlib
import base64
from groq import Groq

# ==========================================
# 0. INITIALISATION STRICTE DU SESSION_STATE
# ==========================================
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "personnage_actuel" not in st.session_state:
    st.session_state.personnage_actuel = None

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="Storyia - AI Roleplay", layout="wide")

def get_base64_image():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "bg.png")
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

image_base64 = get_base64_image()

st.markdown(
    """
    <style>
    .stApp { background-color: #0B0E14 !important; }
    .stChatMessage { background-color: rgba(25, 30, 40, 0.6) !important; border: 1px solid rgba(255, 75, 75, 0.2); border-radius: 12px; padding: 12px; color: #ffffff !important; }
    .auth-container { background-color: #151922; padding: 30px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05); }
    .char-card-box { background: #181E2A; border: 1px solid #242F41; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .char-avatar-circle { width: 70px; height: 70px; background: #242F41; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; margin: 0 auto 12px auto; border: 2px solid #ff4b4b; }
    .char-title { color: #FFFFFF; font-size: 18px; font-weight: 600; margin-bottom: 6px; }
    .char-subtitle { color: #9CA3AF; font-size: 13px; line-height: 1.4; height: 40px; overflow: hidden; margin-bottom: 5px; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. GESTION DB & AUTH
# ==========================================
DB_FILE = "/tmp/storyia_users.db" if os.path.exists("/mount/src") else "storyia_users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit(); conn.close()

def hash_pass(p): return hashlib.sha256(str.encode(p)).hexdigest()

init_db()

# ==========================================
# 3. AUTH LOGIC
# ==========================================
if not st.session_state.authentifie:
    # BANNIÈRE UNIQUEMENT À LA CONNEXION
    if image_base64:
        st.markdown(f'<div style="text-align: center; margin-bottom: 20px;"><img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 650px; border-radius: 14px;"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    tab_login, tab_register = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
    with tab_login:
        username = st.text_input("Pseudo", key="log_u")
        password = st.text_input("Mot de passe", type="password", key="log_p")
        if st.button("Se connecter"):
            st.session_state.authentifie = True; st.session_state.username = username; st.rerun()
    with tab_register:
        st.write("Inscris-toi pour commencer.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# ==========================================
# 4. CONFIG API & DOSSIERS
# ==========================================
client = Groq(api_key="VOTRE_CLE_API_GROQ_ICI")
CATEGORIES = ["Mafieux", "Fantaisie", "Motard", "École"]
BASE_DIR = "Personnages"
if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)
for cat in CATEGORIES: os.makedirs(os.path.join(BASE_DIR, cat), exist_ok=True)

# ==========================================
# 5. SIDEBAR
# ==========================================
st.sidebar.markdown(f"### 👤 {st.session_state.username}")
if st.sidebar.button("🚪 Déconnexion"):
    st.session_state.authentifie = False; st.rerun()

with st.sidebar.expander("➕ Créer un personnage"):
    nom_p = st.text_input("Nom")
    cat_p = st.selectbox("Univers", CATEGORIES)
    bio_p = st.text_area("Description")
    if st.button("Sauvegarder"):
        with open(os.path.join(BASE_DIR, cat_p, f"{nom_p.strip()}.txt"), "w", encoding="utf-8") as f: f.write(bio_p)
        st.rerun()

# ==========================================
# 6. HUB GLOBAL
# ==========================================
if st.session_state.personnage_actuel is None:
    st.markdown("### ✨ Tous tes personnages")
    tous = []
    for cat in CATEGORIES:
        path_cat = os.path.join(BASE_DIR, cat)
        for f in os.listdir(path_cat):
            if f.endswith(".txt"): tous.append((cat, f))
    
    if not tous: st.info("Aucun personnage. Crée-en un dans la sidebar !")
    else:
        cols = st.columns(4)
        for i, (cat, f) in enumerate(tous):
            with open(os.path.join(BASE_DIR, cat, f), "r", encoding="utf-8", errors="ignore") as file: desc = file.read()
            with cols[i % 4]:
                st.markdown(f'<div class="char-card-box"><div class="char-avatar-circle">🎭</div><div class="char-title">{f.replace(".txt", "")}</div><div class="char-subtitle">{cat}</div></div>', unsafe_allow_html=True)
                if st.button(f"Chatter", key=f"btn_{f}_{i}"):
                    st.session_state.personnage_actuel = f.replace(".txt", "")
                    st.session_state.messages = [{"role": "system", "content": f"Tu es {f.replace('.txt', '')}. Contexte: {desc}"}]
                    st.rerun()

# ==========================================
# 7. CHAT
# ==========================================
else:
    if st.button("🏠 Retour au Hub"): st.session_state.personnage_actuel = None; st.rerun()
    st.markdown(f"## 🎭 Chat avec {st.session_state.personnage_actuel}")
    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            res = client.chat.completions.create(messages=st.session_state.messages, model="llama-3.1-8b-instant").choices[0].message.content
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
