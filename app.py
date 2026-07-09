import streamlit as st
from groq import Groq

# --- CONFIGURATION GROQ ---
client = Groq(api_key="TON_API_KEY") # Remplace par ta vraie clé

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="collapsed")

# --- CONFIGURATION DES PERSONNALITÉS ---
CHARACTERS = {
    "Caelum": {
        "prompt": "Tu es Caelum, Prince des Ténèbres. Froid, arrogant, distant. Déteste ton alliance forcée. Jamais d'emojis.",
        "start": "Tu es sur mon chemin, humaine. Ramasse tes affaires et disparais."
    },
    "Noah": {
        "prompt": "Tu es Noah, quaterback star. Arrogant en public, profond et romantique par SMS secret avec {{user}}.",
        "start": "Hé, je t'ai vue au lycée... Je ne sais pas pourquoi je t'écris, mais ton regard m'a intrigué."
    },
    "Ethan": {
        "prompt": "Tu es Ethan, Loup Alpha. Possessif, protecteur, dominant. Ton âme sœur est {{user}}. Mystérieux sur ta nature.",
        "start": "Tu ne devrais pas te promener seule ici, humaine. La forêt cache des prédateurs dangereux... Reste près de moi."
    }
}

# --- INITIALISATION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "char_select" not in st.session_state: st.session_state.char_select = None

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

# --- LOGIQUE DE NAVIGATION ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    cols = st.columns(4)
    for i, p in enumerate(personnages):
        with cols[i % 4]:
            st.image(p["img"], use_container_width=True)
            st.subheader(p["nom"])
            st.caption(p["accroche"])
            if st.button(f"Chatter avec {p['nom']}", key=f"btn_{i}"):
                st.session_state.char_select = p["nom"]
                if p["nom"] in CHARACTERS:
                    st.session_state.messages = [
                        {"role": "system", "content": CHARACTERS[p["nom"]]["prompt"]},
                        {"role": "assistant", "content": CHARACTERS[p["nom"]]["start"]}
                    ]
                else:
                    st.session_state.messages = [{"role": "assistant", "content": "Bonjour."}]
                st.session_state.page = "chat"
                st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    if st.button("⬅ Retour"):
        st.session_state.page = "home"
        st.rerun()
    
    # Affichage de l'historique
    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    # Saisie utilisateur et appel Groq
    if prompt := st.chat_input("Répondre..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Appel API Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
