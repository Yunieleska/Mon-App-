import streamlit as st
import sqlite3
from groq import Groq

# --- CONFIGURATION ---
client = Groq(api_key="TON_API_KEY") 
st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="collapsed")

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (user_id TEXT, char_name TEXT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_message(user_id, char_name, role, content):
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (user_id, char_name, role, content))
    conn.commit()
    conn.close()

def get_messages(user_id, char_name):
    conn = sqlite3.connect('storyia.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE user_id=? AND char_name=?", (user_id, char_name))
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in data]

# --- CONFIGURATION PERSONNALITÉS (Abrégée pour l'exemple) ---
CHARACTERS = {
    "Killian": {
        "prompt": "Tu es Killian, motard sombre...", 
        "start": "*La fumée s'échappe...* « Respire, c'est fini... »"
    },
    # Ajoute les autres ici...
}

# --- INITIALISATION ---
if "user_id" not in st.session_state:
    st.session_state.user_id = st.text_input("Entre ton pseudo pour commencer :", value="Utilisateur1")
if "page" not in st.session_state: st.session_state.page = "home"

# --- LOGIQUE ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    # ... (ton code de colonnes et boutons reste identique)
    if st.button("Chatter avec Killian"):
        st.session_state.char_select = "Killian"
        # Vérifier si on a déjà des messages en base
        history = get_messages(st.session_state.user_id, "Killian")
        if not history:
            save_message(st.session_state.user_id, "Killian", "system", CHARACTERS["Killian"]["prompt"])
            save_message(st.session_state.user_id, "Killian", "assistant", CHARACTERS["Killian"]["start"])
        st.session_state.page = "chat"
        st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    
    # Affichage
    messages = get_messages(st.session_state.user_id, st.session_state.char_select)
    for msg in messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
            
    # Input
    if prompt := st.chat_input("Répondre..."):
        save_message(st.session_state.user_id, st.session_state.char_select, "user", prompt)
        
        # Appel API
        current_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        current_messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=current_messages)
        reply = response.choices[0].message.content
        
        save_message(st.session_state.user_id, st.session_state.char_select, "assistant", reply)
        st.rerun()
