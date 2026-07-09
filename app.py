import streamlit as st
import os
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Storyia", layout="wide")

# --- FONCTION POUR CHARGER LES IMAGES ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

# --- LISTE DES PERSONNAGES ---
# Remplace par les noms exacts de tes fichiers (sensible à la casse !)
personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "type": "url"},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "type": "url"},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "type": "url"},
    {"nom": "Lucas", "img": get_image_base64("Lucas.PNG"), "type": "base64"},
    {"nom": "Ethan", "img": get_image_base64("Ethan.PNG"), "type": "base64"},
    {"nom": "Léo", "img": get_image_base64("Léo.PNG"), "type": "base64"},
    {"nom": "Liam", "img": get_image_base64("Liam.PNG"), "type": "base64"},
    {"nom": "Noah", "img": get_image_base64("Noah.PNG"), "type": "base64"}
]

# --- INITIALISATION ÉTATS ---
if "page" not in st.session_state: st.session_state.page = "home"
if "char_select" not in st.session_state: st.session_state.char_select = None
if "messages" not in st.session_state: st.session_state.messages = []

# --- STYLE CSS ---
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
            elif p["type"] == "base64" and p["img"]:
                st.markdown(f'<img src="{p["img"]}" style="width:100%; border-radius:15px;">', unsafe_allow_html=True)
            else:
                st.error(f"Image introuvable")
            
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
    for msg in st.session_state.messages:
        with st.chat_message("user"): st.write(msg)
    if prompt := st.chat_input("Dis quelque chose..."):
        st.session_state.messages.append(prompt)
        st.rerun()
