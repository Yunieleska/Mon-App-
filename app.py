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

# Initialisation immédiate
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
    # Sécurité : on vérifie si le fichier existe
    if not os.path.exists('storyia.db'): return []
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    try:
        c.execute("SELECT DISTINCT char_name FROM messages WHERE user_pseudo=?", (pseudo,))
        data = c.fetchall()
        return [row[0] for row in data]
    except sqlite3.OperationalError:
        return [] # Retourne vide si la table n'est pas prête
    finally:
        conn.close()

# --- CONFIGURATION DES PERSONNALITÉS ---
CHARACTERS = {
    "Caelum": {"prompt": "Tu es Caelum, Prince des Ténèbres.", "start": "Tu es sur mon chemin, humaine."},
    "Noah": {"prompt": "Tu es Noah, quaterback star.", "start": "Hey... Le match était d'un ennui mortel."},
    "Ethan": {"prompt": "Tu es Ethan, Loup Alpha.", "start": "La forêt cache des prédateurs, reste près de moi."},
    "Léo": {"prompt": "Tu es Léo, streameur gaming.", "start": "Tu es enfin là !"},
    "Liam": {"prompt": "Tu es Liam, le grand frère.", "start": "Ne perturbe pas le calme de ma maison."},
    "Alexei": {"prompt": "Tu es Alexei, mafieux.", "start": "La mafia n'attend personne."},
    "Lucas": {"prompt": "Tu es Lucas, meilleur ami.", "start": "On squatte ton canapé ?"},
    "Killian": {"prompt": "Tu es Killian, motard.", "start": "Je t'ai sortie de là."}
}

personnages = [
    {"nom": "Caelum", "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "accroche": "Prince des Ténèbres"},
    {"nom": "Alexei", "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "accroche": "Le mafieux"},
    {"nom": "Killian", "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "accroche": "Le motard"},
    {"nom": "Noah", "img": "Noah.png", "accroche": "Le sportif"},
    {"nom": "Lucas", "img": "Lucas.png", "accroche": "Le meilleur ami"},
    {"nom": "Ethan", "img": "Ethan.png", "accroche": "Loup Alpha"},
    {"nom": "Léo", "img": "Léo.png", "accroche": "Le streameur"},
    {"nom": "Liam", "img": "Liam.png", "accroche": "Le protecteur"}
]

# --- SIDEBAR & SESSION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "pseudo" not in st.session_state: st.session_state.pseudo = "User"

st.sidebar.title("Mes Conversations")
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.pseudo)

if st.sidebar.button("➕ Nouvelle rencontre"):
    st.session_state.page = "home"
    st.rerun()

# Chargement sécurisé des chats
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
            if st.button(f"Chatter avec {p['nom']}", key=f"btn_{i}"):
                st.session_state.char_select = p["nom"]
                if not load_msgs(st.session_state.pseudo, p["nom"]):
                    save_msg(st.session_state.pseudo, p["nom"], "system", CHARACTERS[p["nom"]]["prompt"])
                    save_msg(st.session_state.pseudo, p["nom"], "assistant", CHARACTERS[p["nom"]]["start"])
                st.session_state.page = "chat"
                st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Discussion avec {st.session_state.char_select}")
    for msg in load_msgs(st.session_state.pseudo, st.session_state.char_select):
        if msg["role"] != "system":
            with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Répondre..."):
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        messages_db = load_msgs(st.session_state.pseudo, st.session_state.char_select)
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_db)
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", response.choices[0].message.content)
        st.rerun()
