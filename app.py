import streamlit as st
import sqlite3
from groq import Groq
import os

# --- CONFIGURATION ---
client = Groq(api_key="TON_API_KEY") 
st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (user_pseudo TEXT, char_name TEXT, role TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS custom_characters (name TEXT PRIMARY KEY, prompt TEXT, start TEXT, visibility TEXT, image_path TEXT, creator TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_msg(pseudo, char, role, content):
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (pseudo, char, role, content))
    conn.commit()
    conn.close()

def load_msgs(pseudo, char):
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE user_pseudo=? AND char_name=?", (pseudo, char))
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in data]

# --- SIDEBAR (Navigation & Conversations) ---
st.sidebar.title("Storyia")
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.get("pseudo", "User"))

if st.sidebar.button("🏠 Accueil"): 
    st.session_state.current_chat = None
    st.session_state.page = "home"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Tes Conversations")

# Récupérer les personnages avec qui tu as déjà discuté
conn = sqlite3.connect('storyia_v3.db')
c = conn.cursor()
c.execute("SELECT DISTINCT char_name FROM messages WHERE user_pseudo=?", (st.session_state.pseudo,))
active_chats = [row[0] for row in c.fetchall()]
conn.close()

for char in active_chats:
    col1, col2 = st.sidebar.columns([4, 1])
    if col1.button(f"💬 {char}"):
        st.session_state.current_chat = char
        st.session_state.page = "chat"
        st.rerun()
    if col2.button("x", key=f"del_{char}"):
        # Logique pour "fermer" (revenir à l'accueil)
        st.session_state.current_chat = None
        st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("✨ Créer un personnage"): st.session_state.page = "create"; st.rerun()

# --- LOGIQUE DES PAGES ---
if "page" not in st.session_state: st.session_state.page = "home"

# --- PAGE CHAT (Principale) ---
if st.session_state.get("current_chat"):
    char_name = st.session_state.current_chat
    st.title(f"Chat avec {char_name}")
    
    with st.container(height=500):
        for msg in load_msgs(st.session_state.pseudo, char_name):
            if msg["role"] != "system":
                with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Répondre..."):
        save_msg(st.session_state.pseudo, char_name, "user", prompt)
        messages_db = load_msgs(st.session_state.pseudo, char_name)
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_db)
        save_msg(st.session_state.pseudo, char_name, "assistant", response.choices[0].message.content)
        st.rerun()

# --- PAGE ACCUEIL ---
elif st.session_state.page == "home":
    st.title("Choisis ton personnage")
    # (Mettre ici ta logique de CHARACTERS et SELECT custom_characters)
    # Dès qu'on clique sur "Chatter", on fait :
    # st.session_state.current_chat = name
    # st.rerun()
