import streamlit as st

# --- CONFIGURATION ---
st.set_page_config(page_title="Storyia", layout="wide")

# --- LISTE DES PERSONNAGES ---
# Puisque tes fichiers sont dans ton dépôt GitHub, on les appelle directement par leur nom.
# Streamlit les trouvera automatiquement s'ils sont à la racine.
personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg"},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg"},
    {"nom": "Lucas", "img": "Lucas.png"}, 
    {"nom": "Ethan", "img": "Ethan.png"},
    {"nom": "Léo", "img": "Léo.png"},
    {"nom": "Liam", "img": "Liam.png"},
    {"nom": "Noah", "img": "Noah.png"}
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

# --- LOGIQUE ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    cols = st.columns(4)
    for i, p in enumerate(personnages):
        with cols[i % 4]:
            st.markdown('<div class="char-card">', unsafe_allow_html=True)
            # Affichage de l'image
            st.image(p["img"], use_container_width=True)
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
    
    # Affichage de l'historique des messages
    for msg in st.session_state.messages:
        with st.chat_message("user"): st.write(msg)
    
    # Input utilisateur
    if prompt := st.chat_input("Dis quelque chose..."):
        st.session_state.messages.append(prompt)
        st.rerun()
