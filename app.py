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

# --- FONCTIONS UTILES ---
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

# --- DONNÉES PAR DÉFAUT ---
# Si tu n'as pas les images locales, l'app utilisera une image par défaut.
# Assure-toi que tes fichiers .png sont bien dans un dossier nommé "images" à côté de app.py
CHARACTERS = {
    "Caelum": {"img": "https://i.pinimg.com/1200x/21/90/e3/2190e375ce1e7be5bb2e8106de99b9df.jpg", "prompt": "Tu es Caelum, Prince des Ténèbres.", "start": "Tu es sur mon chemin, humaine.", "accroche": "Tu es sur mon chemin."},
    "Noah": {"img": "https://i.pinimg.com/736x/3a/ec/bd/3aecbd.jpg", "prompt": "Tu es Noah, quaterback star.", "start": "Dis, tu crois qu'on est tous obligés de jouer un rôle ?", "accroche": "Une façade."},
    "Ethan": {"img": "https://i.pinimg.com/736x/39/9f/5d/399f5d.jpg", "prompt": "Tu es Ethan, Loup Alpha.", "start": "La forêt cache des prédateurs... Reste près de moi.", "accroche": "La forêt est dangereuse."},
    "Léo": {"img": "https://i.pinimg.com/736x/3a/0b/df/3a0bdf.jpg", "prompt": "Tu es Léo, streameur.", "start": "Ah, te voilà enfin ! Prête à détruire l'équipe d'en face ?", "accroche": "Tu es enfin là."},
    "Liam": {"img": "https://i.pinimg.com/736x/3a/78/bc/3a78bc.jpg", "prompt": "Tu es Liam, le grand frère.", "start": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit.", "accroche": "Calme de ma maison."},
    "Alexei": {"img": "https://i.pinimg.com/736x/9c/46/99/9c4699b3c19b43c4c910c1a018210431.jpg", "prompt": "Tu es Alexei, mafieux.", "start": "Regardez qui s'est perdue sur mon territoire.", "accroche": "La mafia n'attend personne."},
    "Lucas": {"img": "https://i.pinimg.com/736x/39/36/24/393624.jpg", "prompt": "Tu es Lucas, populaire.", "start": "Hey, on s'esquive et on va squatter ton canapé ?", "accroche": "On squatte ton canapé ?"},
    "Killian": {"img": "https://i.pinimg.com/736x/2d/d2/a6/2dd2a6a826b7c58984f44ae0dddf0678.jpg", "prompt": "Tu es Killian, motard.", "start": "Respire, c'est fini... T'as pas changé.", "accroche": "Je t'ai sortie de là."}
}

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "home"
st.sidebar.title("Storyia")
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo", "User")
if st.sidebar.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()

# --- PAGE ACCUEIL ---
if st.session_state.page == "home":
    st.title("Choisis ton personnage")
    cols = st.columns(4)
    idx = 0
    for name, data in CHARACTERS.items():
        with cols[idx % 4]:
            st.image(data["img"], use_container_width=True)
            st.subheader(name)
            st.caption(data["accroche"])
            if st.button(f"Chatter avec {name}", key=name):
                st.session_state.char_select = name
                # Initialisation message si vide
                if not load_msgs(st.session_state.pseudo, name):
                    save_msg(st.session_state.pseudo, name, "system", data["prompt"])
                    save_msg(st.session_state.pseudo, name, "assistant", data["start"])
                st.session_state.page = "chat"
                st.rerun()
        idx += 1

# --- PAGE CHAT ---
elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    for msg in load_msgs(st.session_state.pseudo, st.session_state.char_select):
        if msg["role"] != "system":
            with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Répondre..."):
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        messages_db = load_msgs(st.session_state.pseudo, st.session_state.char_select)
        
        with st.spinner("Caelum réfléchit..."):
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_db)
            answer = response.choices[0].message.content
            save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", answer)
        st.rerun()
