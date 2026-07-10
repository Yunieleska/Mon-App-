import streamlit as st
import sqlite3
from groq import Groq
import os

# --- CONFIGURATION ---
client = Groq(api_key="TON_API_KEY") 
st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- BASE DE DONNÉES ---
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
    if not os.path.exists('storyia.db'): return []
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    try:
        c.execute("SELECT DISTINCT char_name FROM messages WHERE user_pseudo=?", (pseudo,))
        data = c.fetchall()
        return [row[0] for row in data]
    except: return []
    finally: conn.close()

# --- CONFIGURATION DES PERSONNALITÉS ---
CHARACTERS = {
    "Caelum": {"prompt": "Tu es Caelum, Prince des Ténèbres. Froid, arrogant, distant. Déteste ton alliance forcée.", "start": "*Tu bouscules accidentellement Caelum dans le couloir.*\n\nTu es sur mon chemin, humaine. Ramasse tes affaires et disparais."},
    "Noah": {"prompt": "Tu es Noah, quaterback star. En public : arrogant. Par message anonyme : profond, attentionné.", "start": "*Ton téléphone vibre en pleine nuit.*\n\nHey... Le match de ce soir était d'un ennui mortel. Tu crois qu'on est tous obligés de jouer un rôle ?"},
    "Ethan": {"prompt": "Tu es Ethan, Loup Alpha. Possessif, protecteur, dominant. Ton âme sœur est {{user}}.", "start": "*Ethan émerge de la pénombre.*\n\nTu ne devrais pas te promener seule ici, humaine. La forêt cache des prédateurs... Reste près de moi."},
    "Léo": {"prompt": "Tu es Léo (Neo), streameur gaming. En ligne : extraverti. En vrai : introverti, distant.", "start": "*Le signal sonore de Discord retentit.*\n\nAh, te voilà enfin ! Je t'attendais pour lancer la partie. Tu stresses pour demain au lycée ?"},
    "Liam": {"prompt": "Tu es Liam, le grand frère. Froid, taciturne, secret, protecteur.", "start": "*Tu es installée sur le tapis du salon de Lara.*\n\nLara, je t'ai dit de ne pas transformer le salon en salle d'étude. Salut, l'amie de ma sœur."},
    "Alexei": {"prompt": "Tu es Alexei, le successeur impitoyable du clan mafieux Ivanov.", "start": "*La musique du club VIP résonne.*\n\nRegardez qui s'est perdue sur mon territoire. La petite princesse des Volkov..."},
    "Lucas": {"prompt": "Tu es Lucas, le garçon le plus populaire. Chaleureux, charismatique, protecteur.", "start": "*La sonnerie annonce la fin du dernier cours.*\n\nHey, ma partenaire préférée ! On s'esquive et on va squatter ton canapé comme d'habitude ?"},
    "Killian": {"prompt": "Tu es Killian, un motard sombre au passé trouble. Taciturne, secret, protecteur.", "start": "*La fumée s'échappe encore du capot broyé.*\n\nRespire, c'est fini... T'as pas changé, toujours aussi maladroite."}
}

personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "accroche": "Tu es sur mon chemin, humaine."},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "accroche": "La mafia n'attend personne."},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "accroche": "Je t'ai sortie de là."},
    {"nom": "Noah", "img": "Noah.png", "accroche": "C'est fou comme je peux être moi-même avec toi."},
    {"nom": "Lucas", "img": "Lucas.png", "accroche": "On s'esquive et on va squatter ton canapé ?"},
    {"nom": "Ethan", "img": "Ethan.png", "accroche": "Tu es nouvelle en ville, n'est-ce pas ?"},
    {"nom": "Léo", "img": "Léo.png", "accroche": "Tu es enfin là, je m'impatientais."},
    {"nom": "Liam", "img": "Liam.png", "accroche": "Je n'aime pas que l'on perturbe le calme."}
]

# --- SIDEBAR (NAVIGATION) ---
st.sidebar.title("Mes Conversations")
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.get("pseudo", "User"))

if st.sidebar.button("➕ Nouvelle rencontre"):
    st.session_state.page = "home"
    st.rerun()

st.sidebar.markdown("---")
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
                if not load_msgs(st.session_state.pseudo, p["nom"]):
                    save_msg(st.session_state.pseudo, p["nom"], "system", CHARACTERS[p["nom"]]["prompt"])
                    save_msg(st.session_state.pseudo, p["nom"], "assistant", CHARACTERS[p["nom"]]["start"])
                st.session_state.page = "chat"
                st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Discussion avec {st.session_state.char_select}")
    
    # Fenêtre de discussion stylisée
    with st.container(border=True, height=500):
        for msg in load_msgs(st.session_state.pseudo, st.session_state.char_select):
            if msg["role"] != "system":
                with st.chat_message(msg["role"]): 
                    st.write(msg["content"])
    
    # Input en bas
    if prompt := st.chat_input("Répondre à " + st.session_state.char_select + "..."):
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        messages_db = load_msgs(st.session_state.pseudo, st.session_state.char_select)
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_db)
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", response.choices[0].message.content)
        st.rerun()
