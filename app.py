import streamlit as st

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="collapsed")

# --- DONNÉES DES PERSONNAGES ---
personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "accroche": "Tu es sur mon chemin, humaine. Disparais."},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "accroche": "La mafia n'attend personne."},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "accroche": "On joue selon mes règles."},
    {"nom": "Noah", "img": "Noah.png", "accroche": "Regarde-moi dans les yeux quand je te parle."},
    {"nom": "Lucas", "img": "Lucas.png", "accroche": "Je t'attendais, tu es en retard."},
    {"nom": "Ethan", "img": "Ethan.png", "accroche": "Laisse tes problèmes à la porte."},
    {"nom": "Léo", "img": "Léo.png", "accroche": "Tu es enfin là, je m'impatientais."},
    {"nom": "Liam", "img": "Liam.png", "accroche": "Viens voir ce que je te réserve."}
]

# --- PAGE D'ACCUEIL ---
st.title("Choisis ton personnage")

cols = st.columns(4)
for i, p in enumerate(personnages):
    with cols[i % 4]:
        # Affiche l'image (URL ou locale)
        st.image(p["img"], use_container_width=True)
        st.subheader(p["nom"])
        st.caption(p["accroche"])
        
        if st.button(f"Chatter avec {p['nom']}", key=f"btn_{i}"):
            st.session_state.char_select = p["nom"]
            st.session_state.page = "chat"
            # Ici tu pourras plus tard ajouter st.rerun() pour basculer
            st.success(f"Mode chat activé pour {p['nom']} !")
