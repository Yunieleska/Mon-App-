import streamlit as st

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="collapsed")

# --- CONFIGURATION DES PERSONNALITÉS ---
# C'est ici que l'on stocke les prompts système pour Groq
CHARACTERS = {
    "Caelum": {
        "prompt": "Tu es Caelum, Prince des Ténèbres. Froid, arrogant, distant, aristocratique. Tu détestes ton engagement politique forcé. Parle de manière calme et tranchante. JAMAIS d'emojis.",
        "start_msg": "*Tu bouscules accidentellement Caelum dans le couloir. Il te regarde de haut avec une indifférence totale.* \n\nTu es sur mon chemin, humaine. Ramasse tes affaires et disparais."
    },
    "Noah": {
        "prompt": "Tu es Noah, quaterback star. Arrogant en public, profond et attentionné par SMS anonyme avec {{user}}.",
        "start_msg": "Hé, je t'ai vue au lycée tout à l'heure... Je ne sais pas pourquoi je t'écris, mais ton regard m'a intrigué."
    },
    "Ethan": {
        "prompt": "Tu es Ethan, Loup Alpha. Possessif, protecteur, dominant. Tu as reconnu ton âme sœur en {{user}}. Ne révèle pas ta nature immédiatement, reste mystérieux.",
        "start_msg": "*Ethan émerge de la pénombre, ses yeux sombres fixés sur toi avec une intensité animale.*\n\nTu ne devrais pas te promener seule ici, humaine. La forêt cache des prédateurs dangereux... Reste près de moi."
    }
}

# --- INITIALISATION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "char_select" not in st.session_state: st.session_state.char_select = None

# --- PAGE D'ACCUEIL ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    personnages = [
        {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "accroche": "Tu es sur mon chemin, humaine. Disparais."},
        {"nom": "Noah", "img": "Noah.png", "accroche": "Regarde-moi dans les yeux quand je te parle."},
        {"nom": "Ethan", "img": "Ethan.png", "accroche": "Laisse tes problèmes à la porte."},
        {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "accroche": "La mafia n'attend personne."}
    ]
    
    cols = st.columns(4)
    for i, p in enumerate(personnages):
        with cols[i % 4]:
            st.image(p["img"], use_container_width=True)
            st.subheader(p["nom"])
            st.caption(p["accroche"])
            if st.button(f"Chatter avec {p['nom']}", key=f"btn_{i}"):
                st.session_state.char_select = p["nom"]
                st.session_state.page = "chat"
                # Initialisation de l'historique avec le bon prompt
                st.session_state.messages = [
                    {"role": "system", "content": CHARACTERS[p["nom"]]["prompt"]},
                    {"role": "assistant", "content": CHARACTERS[p["nom"]]["start_msg"]}
                ]
                st.rerun()

# --- PAGE DE CHAT ---
elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    if st.button("⬅ Retour"):
        st.session_state.page = "home"
        st.rerun()
    
    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    if prompt := st.chat_input("Répondre..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
