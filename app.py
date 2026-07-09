import streamlit as st
import os
import sqlite3
import hashlib
import base64
from groq import Groq

# ==========================================
# 0. INITIALISATION DU SESSION_STATE
# ==========================================
if "authentifie" not in st.session_state: st.session_state.authentifie = False
if "username" not in st.session_state: st.session_state.username = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "personnage_actuel" not in st.session_state: st.session_state.personnage_actuel = None

# ==========================================
# 1. CONFIGURATION & DESIGN
# ==========================================
st.set_page_config(page_title="Storyia - AI Roleplay", layout="wide")

def get_base64_image():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.png")
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

image_base64 = get_base64_image()

st.markdown(
    """
    <style>
    .stApp { background-color: #0B0E14 !important; }
    .auth-container { background-color: #151922; padding: 30px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05); }
    .char-card-box { background: #181E2A; border: 1px solid #242F41; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; color: white; }
    .char-title { font-size: 18px; font-weight: bold; margin-bottom: 2px; }
    .char-category { font-size: 13px; color: #ff4b4b; font-weight: 500; margin-bottom: 15px; display: block; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. AUTHENTIFICATION
# ==========================================
DB_FILE = "/tmp/storyia_users.db" if os.path.exists("/mount/src") else "storyia_users.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.close()
init_db()

if not st.session_state.authentifie:
    if image_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 600px; border-radius: 10px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Connexion / Inscription"):
        st.session_state.authentifie = True; st.session_state.username = u; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# ==========================================
# 3. SIDEBAR & CRÉATION
# ==========================================
CATEGORIES = ["Mafieux", "Fantaisie", "Motard", "École"]
BASE_DIR = "Personnages"
os.makedirs(BASE_DIR, exist_ok=True)
for cat in CATEGORIES: os.makedirs(os.path.join(BASE_DIR, cat), exist_ok=True)

st.sidebar.markdown(f"### 👤 {st.session_state.username}")
if st.sidebar.button("🚪 Déconnexion"): st.session_state.authentifie = False; st.rerun()
with st.sidebar.expander("➕ Créer un personnage"):
    nom = st.text_input("Nom")
    cat = st.selectbox("Univers", CATEGORIES)
    bio = st.text_area("Description")
    if st.button("Sauvegarder"):
        with open(os.path.join(BASE_DIR, cat, f"{nom.strip()}.txt"), "w", encoding="utf-8") as f: f.write(bio)
        st.rerun()

# ==========================================
# 4. HUB GLOBAL
# ==========================================
if st.session_state.personnage_actuel is None:
    st.markdown("### ✨ Tous tes personnages")
    tous = []
    for cat in CATEGORIES:
        for f in os.listdir(os.path.join(BASE_DIR, cat)):
            if f.endswith(".txt"): tous.append((cat, f))
    
    cols = st.columns(4)
    for i, (cat, f) in enumerate(tous):
        with cols[i % 4]:
            st.markdown(f'''
                <div class="char-card-box">
                    <div class="char-title">{f.replace(".txt", "")}</div>
                    <div class="char-category">{cat}</div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button(f"Chatter", key=f"btn_{i}"):
                st.session_state.personnage_actuel = f.replace(".txt", "")
                st.session_state.messages = [{"role": "system", "content": f"Tu es {f.replace('.txt', '')} dans l'univers {cat}."}]
                st.rerun()

# ==========================================
# 5. CHAT
# ==========================================
else:
    if st.button("⬅️ Retour"): st.session_state.personnage_actuel = None; st.rerun()
    st.markdown(f"## 💬 {st.session_state.personnage_actuel}")
    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            res = Groq(api_key="VOTRE_CLE_API_GROQ_ICI").chat.completions.create(
                messages=st.session_state.messages, model="llama-3.1-8b-instant"
            ).choices[0].message.content
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
