import streamlit as st
import sqlite3
import hashlib
import os
import base64

# CONFIGURATION
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, "storyia_users.db")

# --- LISTE DE TES PERSONNAGES ---
# J'ai ajouté une clé 'type' pour distinguer les liens internet des fichiers locaux
personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "type": "url"},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "type": "url"},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "type": "url"},
    {"nom": "Lucas", "img": "lucas.png", "type": "file"},
    {"nom": "Ethan", "img": "ethan.png", "type": "file"},
    {"nom": "Léo", "img": "léo.png", "type": "file"},
    {"nom": "Liam", "img": "liam.png", "type": "file"},
    {"nom": "Noah", "img": "noah.png", "type": "file"}
]

def hash_pass(p):
    return hashlib.sha256(p.strip().encode('utf-8')).hexdigest()

def display_banner():
    if os.path.exists("bg.png"):
        with open("bg.png", "rb") as f:
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

# LOGIQUE DE CONNEXION (Simplifiée pour tester l'affichage)
if "authentifie" not in st.session_state: st.session_state.authentifie = False

if not st.session_state.authentifie:
    st.title("Bienvenue sur Storyia")
    if st.button("Connexion Test"): st.session_state.authentifie = True
else:
    st.title("Choisis ton personnage")
    cols = st.columns(4)
    for i, p in enumerate(personnages):
        with cols[i % 4]:
            st.markdown('<div class="char-card">', unsafe_allow_html=True)
            try:
                # Si c'est un fichier, on vérifie s'il existe avant d'afficher
                if p["type"] == "file":
                    if os.path.exists(p["img"]):
                        st.image(p["img"], use_container_width=True)
                    else:
                        st.error(f"Fichier introuvable: {p['img']}")
                else:
                    st.image(p["img"], use_container_width=True)
            except Exception as e:
                st.write(f"Erreur : {e}")
            
            st.subheader(p["nom"])
            st.button(f"Chatter", key=f"btn_{i}")
            st.markdown('</div>', unsafe_allow_html=True)
            
    if st.button("Déconnexion"):
        st.session_state.authentifie = False
        st.rerun()
