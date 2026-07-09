import streamlit as st
import sqlite3
import hashlib
import os
import base64

# --- CONFIGURATION ---
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, "storyia_users.db")

# --- LISTE DES PERSONNAGES ---
# J'ai retiré 'Personnages/' car tes fichiers sont à la racine
# J'ai mis les noms exacts (avec .PNG et majuscules)
personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "type": "url"},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "type": "url"},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "type": "url"},
    {"nom": "Lucas", "img": "Lucas.PNG", "type": "file"},
    {"nom": "Ethan", "img": "Ethan.PNG", "type": "file"},
    {"nom": "Léo", "img": "Léo.PNG", "type": "file"},
    {"nom": "Liam", "img": "Liam.PNG", "type": "file"},
    {"nom": "Noah", "img": "Noah.PNG", "type": "file"}
]

# --- INITIALISATION ÉTATS ---
if "page" not in st.session_state: st.session_state.page = "home"
if "char_select" not in st.session_state: st.session_state.char_select = None
if "messages" not in st.session_state: st.session_state.messages = []

# --- STYLE CSS ---
st.set_page_config(page_title="Storyia", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: white; }
    .char-card { background: #1e2533; padding: 20px; border-radius: 20px; text-align: center; border: 1px solid #333; margin-bottom: 20px; }
    div.stButton > button { background-color: #ff4b4b !important; color: white !important; border-radius: 8px !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE NAVIGATION ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    cols = st.columns(4)
    for i, p in enumerate(personnages):
        with cols[i % 4]:
            st.markdown('<div class="char-card">', unsafe_allow_html=True)
            # Affichage image
            if p["type"] == "url":
                st.image(p["img"], use_container_width=True)
            else:
                # Vérification simple du fichier à la racine
                if os.path.exists(p["img"]):
                    st.image(p["img"], use_container_width=True)
                else:
                    st.error(f"Introuvable: {p['img']}")
            
            st.subheader(p["nom"])
            if st.button(f"Chatter avec {p['nom']}", key=f"btn_{i}"):
                st.session_state.char_select = p["nom"]
                st.session_state.page = "chat"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "chat":
    if st.button("← Retour à la sélection"):
        st.session_state.page = "home"
        st.rerun()
        
    st.title(f"Conversation avec {st.session_state.char_select}")
    
    # Zone de Chat
    for msg in st.session_state.messages:
        with st.chat_message("user"): st.write(msg)
    
    if prompt := st.chat_input(f"Dis quelque chose à {st.session_state.char_select}..."):
        st.session_state.messages.append(prompt)
        st.rerun()
