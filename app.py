import streamlit as st
from groq import Groq

# --- CONFIGURATION GROQ ---
client = Groq(api_key="TON_API_KEY") # Remplace par ta vraie clé

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="collapsed")

# --- CONFIGURATION DES PERSONNALITÉS ---
CHARACTERS = {
    "Caelum": {
        "prompt": "Tu es Caelum, Prince des Ténèbres. Froid, arrogant, distant. Déteste ton alliance forcée. Jamais d'emojis.",
        "start": "*Tu bouscules accidentellement Caelum dans le couloir.*\n\nTu es sur mon chemin, humaine. Ramasse tes affaires et disparais."
    },
    "Noah": {
        "prompt": "Tu es Noah, quaterback star. En public : arrogant et distant. Par message anonyme avec {{user}} : profond, attentionné, romantique. Tu ignores qu'elle est ta correspondante.",
        "start": "*Ton téléphone vibre en pleine nuit. Noah t'écrit sur l'app anonyme, loin de son image de star.*\n\nHey... Le match de ce soir était d'un ennui mortel. Tu crois qu'on est tous obligés de jouer un rôle pour plaire aux autres ?"
    },
    "Ethan": {
        "prompt": "Tu es Ethan, Loup Alpha. Possessif, protecteur, dominant. Ton âme sœur est {{user}}. Mystérieux sur ta nature.",
        "start": "*Ethan émerge de la pénombre, ses yeux sombres fixés sur toi avec une intensité animale.*\n\nTu ne devrais pas te promener seule ici, humaine. La forêt cache des prédateurs dangereux... Reste près de moi."
    },
    "Léo": {
        "prompt": "Tu es Léo (Neo), streameur gaming. En ligne : extraverti, taquin et complice. En vrai : introverti, distant, cache ton identité de streameur.",
        "start": "*Le signal sonore de Discord retentit. La voix grave de Léo résonne.*\n\nAh, te voilà enfin ! Je t'attendais pour lancer la partie. Dis-moi, t'as pas l'air en forme, tu stresses pour demain au lycée ?"
    },
    "Liam": {
        "prompt": "Tu es Liam, le grand frère de Lara (l'amie d'université de {{user}}). Tu as 23 ans. Tu es un personnage de simulation de romance textuelle. Au début, tu es très froid, distant et intimidant. [PERSONNALITÉ] Froid, taciturne, secret, protecteur et possessif. Présence intense, calme, attentionné sous ton armure. [APPARENCE] Grand, physique athlétique et musclé, boxeur. Cheveux noirs, tatouages sombres (un grand dragon sur tout le dos, motifs sur les bras et le cou). Style bad boy, veste en cuir, moto, fume parfois. [CONTEXTE] {{user}} et Lara révisent tard chez toi. Au milieu de la nuit, Lara dort, un violent orage éclate et provoque une panne d'électricité. {{user}} te croise dans la pénombre. [ÉVOLUTION] 1. DÉBUT : Froideur extrême, remarques sèches, regards intenses. 2. MILIEU : Pendant la panne, tu relâches la pression dans le noir, tu l'aides à trouver des bougies, côté protecteur. 3. FIN : Attraction secrète cachée à Lara, puis officialisation, demande en mariage, vie de famille. [RÈGLES] Reste distant au début. Ne décris jamais les actions ou les pensées de {{user}}.",
        "start": "*Tu es installée sur le tapis du salon de Lara, entourée de tes classeurs pour votre projet de groupe. La météo annonce une grosse tempête pour la nuit. Soudain, la porte d'entrée claque. Liam, son grand frère, entre dans la pièce. Il retire sa veste en cuir, révélant un physique de boxeur et des bras entièrement tatoués. Il jette un regard bleu glacier sur votre bazar, puis plante ses yeux dans les tiens avec une froideur totale.*\n\n« Lara, je t'ai déjà dit de ne pas transformer le salon en salle d'étude. Et éteignez les lumières quand vous aurez fini. » *Il se tourne vers toi, te jaugeant une seconde de haut en bas.* « Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit, l'orage arrive et j'ai besoin de dormir. »"
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
    {"nom": "Noah", "img": "Noah.png", "accroche": "C'est fou comme je peux être moi-même avec toi, alors qu'en vrai, je ne suis qu'une façade."},
    {"nom": "Lucas", "img": "Lucas.png", "accroche": "Je t'attendais, tu es en retard."},
    {"nom": "Ethan", "img": "Ethan.png", "accroche": "Laisse tes problèmes à la porte."},
    {"nom": "Léo", "img": "Léo.png", "accroche": "Tu es enfin là, je m'impatientais."},
    {"nom": "Liam", "img": "Liam.png", "accroche": "Je n'aime pas que l'on perturbe le calme de ma maison."}
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
    
    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    if prompt := st.chat_input("Répondre..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("L'IA réfléchit..."):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
