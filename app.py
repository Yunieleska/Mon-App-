import streamlit as st
import sqlite3
from groq import Groq

# --- CONFIGURATION GROQ ---
client = Groq(api_key="TON_API_KEY") 

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- BASE DE DONNÉES (PERSISTANCE) ---
def init_db():
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (user_pseudo TEXT, char_name TEXT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_msg(pseudo, char, role, content):
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (pseudo, char, role, content))
    conn.commit()
    conn.close()

def load_msgs(pseudo, char):
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE user_pseudo=? AND char_name=?", (pseudo, char))
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in data]

def get_user_chats(pseudo):
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT char_name FROM messages WHERE user_pseudo=?", (pseudo,))
    data = c.fetchall()
    conn.close()
    return [row[0] for row in data]

# --- CONFIGURATION DES PERSONNALITÉS ---
CHARACTERS = {
    "Caelum": {"prompt": "Tu es Caelum, Prince des Ténèbres. Froid, arrogant, distant. Déteste ton alliance forcée. Jamais d'emojis.", "start": "*Tu bouscules accidentellement Caelum dans le couloir.*\n\nTu es sur mon chemin, humaine. Ramasse tes affaires et disparais."},
    "Noah": {"prompt": "Tu es Noah, quaterback star. En public : arrogant et distant. Par message anonyme avec {{user}} : profond, attentionné, romantique. Tu ignores qu'elle est ta correspondante.", "start": "*Ton téléphone vibre en pleine nuit. Noah t'écrit sur l'app anonyme, loin de son image de star.*\n\nHey... Le match de ce soir était d'un ennui mortel. Tu crois qu'on est tous obligés de jouer un rôle pour plaire aux autres ?"},
    "Ethan": {"prompt": "Tu es Ethan, Loup Alpha. Possessif, protecteur, dominant. Ton âme sœur est {{user}}. Mystérieux sur ta nature.", "start": "*Ethan émerge de la pénombre, ses yeux sombres fixés sur toi avec une intensité animale.*\n\nTu ne devrais pas te promener seule ici, humaine. La forêt cache des prédateurs dangereux... Reste près de moi."},
    "Léo": {"prompt": "Tu es Léo (Neo), streameur gaming. En ligne : extraverti, taquin et complice. En vrai : introverti, distant, cache ton identité de streameur.", "start": "*Le signal sonore de Discord retentit. La voix grave de Léo résonne.*\n\nAh, te voilà enfin ! Je t'attendais pour lancer la partie. Dis-moi, t'as pas l'air en forme, tu stresses pour demain au lycée ?"},
    "Liam": {"prompt": "Tu es Liam, le grand frère de Lara. [PERSONNALITÉ] Froid, taciturne, secret, protecteur et possessif. [RÈGLES] Ne jamais décrire les actions de {{user}}.", "start": "*Tu es installée sur le tapis du salon...*"},
    "Alexei": {"prompt": "Tu es Alexei, le successeur impitoyable du clan mafieux Ivanov. [RÈGLES] Ne jamais décrire les actions de {{user}}.", "start": "*La musique du club VIP résonne...*"},
    "Lucas": {"prompt": "Tu es Lucas, le garçon le plus populaire. [RÈGLES] Ne jamais décrire les actions de {{user}}.", "start": "*La sonnerie annonce la fin du dernier cours...*"},
    "Killian": {"prompt": "Tu es Killian, un motard sombre au passé trouble. [RÈGLES] Ne jamais décrire les actions de {{user}}.", "start": "*La fumée s'échappe encore du capot broyé...*"}
}

personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "accroche": "Tu es sur mon chemin."},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "accroche": "La mafia n'attend personne."},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "accroche": "Je t'ai sortie de là."},
    {"nom": "Noah", "img": "Noah.png", "accroche": "Une façade."},
    {"nom": "Lucas", "img": "Lucas.png", "accroche": "On squatte ton canapé ?"},
    {"nom": "Ethan", "img": "Ethan.png", "accroche": "La forêt est dangereuse."},
    {"nom": "Léo", "img": "Léo.png", "accroche": "Tu es enfin là."},
    {"nom": "Liam", "img": "Liam.png", "accroche": "Calme de ma maison."}
]

# --- SIDEBAR (NAVIGATION) ---
st.sidebar.title("Mes Conversations")
if "pseudo" not in st.session_state: st.session_state.pseudo = "User"
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.pseudo)

st.sidebar.divider()
if st.sidebar.button("➕ Nouvelle rencontre"):
    st.session_state.page = "home"
    st.rerun()

# Liste des discussions existantes
active_chats = get_user_chats(st.session_state.pseudo)
for char in active_chats:
    if st.sidebar.button(f"💬 {char}"):
        st.session_state.char_select = char
        st.session_state.page = "chat"
        st.rerun()

# --- LOGIQUE PRINCIPALE ---
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
                msgs = load_msgs(st.session_state.pseudo, p["nom"])
                if not msgs:
                    save_msg(st.session_state.pseudo, p["nom"], "system", CHARACTERS[p["nom"]]["prompt"])
                    save_msg(st.session_state.pseudo, p["nom"], "assistant", CHARACTERS[p["nom"]]["start"])
                st.session_state.page = "chat"
                st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Discussion avec {st.session_state.char_select}")
    
    msgs = load_msgs(st.session_state.pseudo, st.session_state.char_select)
    for msg in msgs:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Répondre..."):
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        current_msgs = [{"role": m["role"], "content": m["content"]} for m in load_msgs(st.session_state.pseudo, st.session_state.char_select)]
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=current_msgs)
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", response.choices[0].message.content)
        st.rerun()
