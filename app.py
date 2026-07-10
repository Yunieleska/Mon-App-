import streamlit as st
import sqlite3
from groq import Groq
import os

# --- CONFIGURATION ---
client = Groq(api_key="TON_API_KEY") 
st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('storyia_v4.db') # On passe à la v4 pour forcer le reset
    c = conn.cursor()
    # Table messages
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (user_pseudo TEXT, char_name TEXT, role TEXT, content TEXT)''')
    # Table personnages
    c.execute('''CREATE TABLE IF NOT EXISTS custom_characters 
                 (name TEXT PRIMARY KEY, prompt TEXT, start TEXT, visibility TEXT, image_path TEXT, creator TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_msg(pseudo, char, role, content):
    conn = sqlite3.connect('storyia_v4.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (pseudo, char, role, content))
    conn.commit()
    conn.close()

def load_msgs(pseudo, char):
    conn = sqlite3.connect('storyia_v4.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE user_pseudo=? AND char_name=?", (pseudo, char))
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in data]

def get_user_chats(pseudo):
    conn = sqlite3.connect('storyia_v4.db')
    c = conn.cursor()
    try:
        c.execute("SELECT DISTINCT char_name FROM messages WHERE user_pseudo=?", (pseudo,))
        data = c.fetchall()
        return [row[0] for row in data]
    except: return []
    finally: conn.close()

# --- SIDEBAR & NAVIGATION ---
st.sidebar.title("Storyia")
if "pseudo" not in st.session_state: st.session_state.pseudo = "User"
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.pseudo)

if st.sidebar.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()
if st.sidebar.button("👤 Mon Profil"): st.session_state.page = "profile"; st.rerun()
if st.sidebar.button("✨ Créer un personnage"): st.session_state.page = "create"; st.rerun()

# --- LOGIQUE DES PAGES ---
if "page" not in st.session_state: st.session_state.page = "home"

if st.session_state.page == "profile":
    st.title("Ton Profil")
    conn = sqlite3.connect('storyia_v4.db')
    c = conn.cursor()
    c.execute("SELECT name, visibility FROM custom_characters WHERE creator=?", (st.session_state.pseudo,))
    my_chars = c.fetchall()
    conn.close()
    for char in my_chars:
        st.write(f"- **{char[0]}** (Visibilité: {char[1]})")

elif st.session_state.page == "create":
    st.title("Créer ton personnage")
    with st.form("create_char"):
        name = st.text_input("Nom")
        prompt = st.text_area("Prompt système")
        start = st.text_area("Phrase d'accroche")
        vis = st.selectbox("Visibilité", ["Privé", "Public"])
        if st.form_submit_button("Sauvegarder"):
            conn = sqlite3.connect('storyia_v4.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO custom_characters VALUES (?, ?, ?, ?, ?, ?)", 
                      (name, prompt, start, vis, "", st.session_state.pseudo))
            conn.commit()
            conn.close()
            st.success("Personnage créé !")

elif st.session_state.page == "home":
    st.title("Choisis ton personnage")
    conn = sqlite3.connect('storyia_v4.db')
    c = conn.cursor()
    c.execute("SELECT name, prompt, start FROM custom_characters WHERE visibility='Public'")
    chars = c.fetchall()
    conn.close()
    for row in chars:
        if st.button(f"Chatter avec {row[0]}"):
            st.session_state.char_select = row[0]
            st.session_state.page = "chat"
            st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    if prompt := st.chat_input("Répondre..."):
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        messages_db = load_msgs(st.session_state.pseudo, st.session_state.char_select)
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_db)
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", response.choices[0].message.content)
        st.rerun()
