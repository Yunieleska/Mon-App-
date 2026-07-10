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
    # Table pour les persos créés par l'utilisateur
    c.execute('''CREATE TABLE IF NOT EXISTS custom_characters 
                 (name TEXT PRIMARY KEY, prompt TEXT, start TEXT, visibility TEXT)''')
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

# --- PERSONNALITÉS ---
CHARACTERS = {
    "Caelum": {"prompt": "Tu es Caelum, Prince des Ténèbres. Froid, arrogant, distant.", "start": "*Tu bouscules accidentellement Caelum.*\n\nTu es sur mon chemin, humaine."},
    "Noah": {"prompt": "Tu es Noah, quaterback star.", "start": "*Ton téléphone vibre.*\n\nHey... Le match était d'un ennui mortel."},
    "Ethan": {"prompt": "Tu es Ethan, Loup Alpha.", "start": "*Ethan émerge de la pénombre.*\n\nLa forêt cache des prédateurs... Reste près de moi."},
    "Léo": {"prompt": "Tu es Léo, streameur.", "start": "*Discord retentit.*\n\nTu es enfin là !"},
    "Liam": {"prompt": "Tu es Liam, le grand frère.", "start": "*Tu es sur le tapis du salon.*\n\nSalut, l'amie de ma sœur."},
    "Alexei": {"prompt": "Tu es Alexei, mafieux.", "start": "*Musique club VIP.*\n\nRegardez qui s'est perdue sur mon territoire."},
    "Lucas": {"prompt": "Tu es Lucas, populaire.", "start": "*Fin des cours.*\n\nOn va squatter ton canapé ?"},
    "Killian": {"prompt": "Tu es Killian, motard.", "start": "*Capot broyé.*\n\nRespire, c'est fini."}
}

# --- SIDEBAR ---
st.sidebar.title("Storyia")
if "pseudo" not in st.session_state: st.session_state.pseudo = "User"
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.pseudo)

if st.sidebar.button("➕ Nouvelle rencontre"):
    st.session_state.page = "home"
    st.rerun()

if st.sidebar.button("✨ Créer un personnage"):
    st.session_state.page = "create"
    st.rerun()

st.sidebar.markdown("---")
active_chats = get_user_chats(st.session_state.pseudo)
for char in active_chats:
    if st.sidebar.button(f"💬 {char}"):
        st.session_state.char_select = char
        st.session_state.page = "chat"
        st.rerun()

# --- LOGIQUE ---
if st.session_state.page == "create":
    st.title("Créer ton personnage")
    with st.form("create_char"):
        name = st.text_input("Nom du personnage")
        prompt = st.text_area("Prompt système (personnalité)")
        start = st.text_area("Phrase d'accroche")
        vis = st.selectbox("Visibilité", ["Privé", "Public"])
        if st.form_submit_button("Sauvegarder"):
            conn = sqlite3.connect('storyia.db')
            c = conn.cursor()
            c.execute("INSERT INTO custom_characters VALUES (?, ?, ?, ?)", (name, prompt, start, vis))
            conn.commit()
            conn.close()
            st.success(f"{name} a été créé !")

elif st.session_state.page == "home":
    st.title("Choisis ton personnage")
    # Affichage des persos (défaut + custom)
    cols = st.columns(4)
    all_chars = list(CHARACTERS.keys())
    # Ajout des persos custom ici si besoin...
    for i, name in enumerate(all_chars):
        with cols[i % 4]:
            if st.button(f"Chatter avec {name}"):
                st.session_state.char_select = name
                st.session_state.page = "chat"
                st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    with st.container(border=True, height=500):
        for msg in load_msgs(st.session_state.pseudo, st.session_state.char_select):
            if msg["role"] != "system":
                with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Répondre..."):
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        messages_db = load_msgs(st.session_state.pseudo, st.session_state.char_select)
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_db)
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", response.choices[0].message.content)
        st.rerun()
