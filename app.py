import streamlit as st
from groq import Groq

# Configuration de la page
st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="collapsed")

# --- INITIALISATION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "char_select" not in st.session_state: st.session_state.char_select = None

# --- DONNÉES DES PERSONNAGES ---
# Ici sont regroupées les infos pour l'affichage ET pour l'IA
personnages_data = {
    "Noah": {
        "img": "Noah.png",
        "accroche": "Regarde-moi dans les yeux quand je te parle.",
        "prompt": "Tu es Noah, quaterback star, distant au lycée mais attentionné et profond par SMS avec {{user}}..."
    },
    "Caelum": {
        "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
        "accroche": "Tu es sur mon chemin, humaine. Disparais.",
        "prompt": "Tu es Caelum, Prince des Ténèbres. Froid, arrogant, distant, fiancé de force, mais secrètement protecteur..."
    },
    # ... Ajoute les autres ici de la même manière
}

# --- PAGE D'ACCUEIL ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    cols = st.columns(4)
    
    # Liste des noms pour la boucle
    noms = ["Noah", "Caelum", "Lucas", "Ethan", "Léo", "Liam", "Alexei", "Killian"]
    
    for i, nom in enumerate(noms):
        with cols[i % 4]:
            # Utilise soit une URL soit un fichier local
            img = personnages_data.get(nom, {}).get("img", f"{nom}.png")
            st.image(img, use_container_width=True)
            st.subheader(nom)
            st.caption(personnages_data.get(nom, {}).get("accroche", "Prête à commencer ?"))
            
            if st.button(f"Chatter avec {nom}", key=f"btn_{nom}"):
                st.session_state.char_select = nom
                st.session_state.page = "chat"
                st.rerun()

# --- PAGE DE CHAT ---
elif st.session_state.page == "chat":
    st.title(f"Discussion avec {st.session_state.char_select}")
    if st.button("⬅ Retour au choix"):
        st.session_state.page = "home"
        st.rerun()
        
    # Ici tu inséreras la logique d'appel à Groq avec st.session_state.char_select
    st.write(f"Connexion avec l'IA pour {st.session_state.char_select} en cours...")
