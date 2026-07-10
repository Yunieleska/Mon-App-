import streamlit as st
import sqlite3
from groq import Groq
import os

# --- CONFIGURATION ---
client = Groq(api_key="TON_API_KEY") 
st.set_page_config(page_title="Storyia", layout="wide")

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

def get_user_chats(pseudo):
    if not os.path.exists('storyia_v3.db'): return []
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    try:
        c.execute("SELECT DISTINCT char_name FROM messages WHERE user_pseudo=?", (pseudo,))
        data = c.fetchall()
        return [row[0] for row in data]
    except: return []
    finally: conn.close()

# --- DONNÉES ---
CHARACTERS = {
    "Caelum": {"img": "https://i.pinimg.com/1200x/21/90/e3/2190e375ce1e7be5bb2e8106de99b9df.jpg", "prompt": "Tu es Caelum.", "start": "Salut.", "accroche": "Ténèbres."},
    "Noah": {"img": "https://i.pinimg.com/736x/3a/ec/bd/3aecbd.jpg", "prompt": "Tu es Noah.", "start": "Hey.", "accroche": "Quaterback."},
    "Ethan": {"img": "https://i.pinimg.com/736x/39/9f/5d/399f5d.jpg", "prompt": "Tu es Ethan.", "start": "Bonjour.", "accroche": "Loup."},
    "Léo": {"img": "https://i.pinimg.com/736x/3a/0b/df/3a0bdf.jpg", "prompt": "Tu es Léo.", "start": "Yo.", "accroche": "Gamer."},
    "Liam": {"img": "https://i.pinimg.com/736x/3a/78/bc/3a78bc.jpg", "prompt": "Tu es Liam.", "start": "Hello.", "accroche": "Frère."},
    "Alexei": {"img": "https://i.pinimg.com/736x/9c/46/99/9c4699b3c19b43c4c910c1a018210431.jpg", "prompt": "Tu es Alexei.", "start": "Bienvenue.", "accroche": "Mafia."},
    "Lucas": {"img": "https://i.pinimg.com/736x/39/36/24/393624.jpg", "prompt": "Tu es Lucas.", "start": "Salut.", "accroche": "Populaire."},
    "Killian": {"img": "https://i.pinimg.com/736x/2d/d2/a6/2dd2a6a826b7c58984f44ae0dddf0678.jpg", "prompt": "Tu es Killian.", "start": "Salut.", "accroche": "Motard."}
}

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "home"
st.sidebar.title("Storyia")
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo", "User")
if st.sidebar.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()

# --- PAGE ACCUEIL ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    
    # Fusion des persos par défaut et créés
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute("SELECT name, prompt, start, image_path FROM custom_characters")
    customs = {row[0]: {"img": row[3], "prompt": row[1], "start": row[2], "accroche": row[2]} for row in c.fetchall()}
    conn.close()
    
    all_chars = {**CHARACTERS, **customs}
    
    cols = st.columns(4)
    for idx, (name, data) in enumerate(all_chars.items()):
        with cols[idx % 4]:
            # Chargement image sécurisé
            try:
                st.image(data["img"], use_container_width=True)
            except:
                st.warning("Image indisponible")
            
            st.subheader(name)
            if st.button(f"Chatter avec {name}", key=name):
                st.session_state.char_select = name
                st.session_state.page = "chat"
                st.rerun()

# --- PAGE CHAT ---
elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    if st.button("⬅️ Retour"): st.session_state.page = "home"; st.rerun()
    
    for msg in load_msgs(st.session_state.pseudo, st.session_state.char_select):
        if msg["role"] != "system":
            with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Répondre..."):
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        messages_db = load_msgs(st.session_state.pseudo, st.session_state.char_select)
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_db)
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", response.choices[0].message.content)
        st.rerun()
