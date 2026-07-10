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

# --- DONNÉES PAR DÉFAUT ---
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

# --- SIDEBAR ---
st.sidebar.title("Storyia")
if "pseudo" not in st.session_state: st.session_state.pseudo = "User"
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.pseudo)

if st.sidebar.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()
if st.sidebar.button("✨ Créer un personnage"): st.session_state.page = "create"; st.rerun()

st.sidebar.markdown("---")
for char in get_user_chats(st.session_state.pseudo):
    if st.sidebar.button(f"💬 {char}"):
        st.session_state.char_select = char
        st.session_state.page = "chat"
        st.rerun()

# --- PAGES ---
if "page" not in st.session_state: st.session_state.page = "home"

elif st.session_state.page == "create":
    st.title("Créer ton personnage")
    if not os.path.exists("images"): os.makedirs("images")
    with st.form("create_char"):
        name = st.text_input("Nom")
        prompt = st.text_area("Prompt système")
        start = st.text_area("Phrase d'accroche")
        uploaded_file = st.file_uploader("Image", type=['png', 'jpg', 'jpeg'])
        vis = st.selectbox("Visibilité", ["Privé", "Public"])
        if st.form_submit_button("Sauvegarder"):
            path = f"images/{name}.png" if uploaded_file else ""
            if uploaded_file:
                with open(path, "wb") as f: f.write(uploaded_file.getbuffer())
            conn = sqlite3.connect('storyia_v3.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO custom_characters VALUES (?, ?, ?, ?, ?, ?)", 
                      (name, prompt, start, vis, path, st.session_state.pseudo))
            conn.commit()
            conn.close()
            st.success("Personnage créé !")

elif st.session_state.page == "home":
    st.title("Choisis ton personnage")
    display_chars = CHARACTERS.copy()
    
    # Chargement des persos depuis DB
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute("SELECT name, prompt, start, image_path FROM custom_characters WHERE visibility='Public'")
    for row in c.fetchall():
        display_chars[row[0]] = {"img": row[3], "prompt": row[1], "start": row[2], "accroche": row[2]}
    conn.close()
    
    cols = st.columns(4)
    i = 0
    for name, data in display_chars.items():
        with cols[i % 4]:
            # Logique de chargement d'image
            img = data["img"]
            # Si le lien est local et existe, on l'affiche, sinon placeholder
            if img and (img.startswith("http") or os.path.exists(img)):
                st.image(img, use_container_width=True)
            else:
                st.image("https://via.placeholder.com/150", use_container_width=True)
            
            st.subheader(name)
            st.caption(data["accroche"])
            if st.button(f"Chatter avec {name}", key=name):
                st.session_state.char_select = name
                if not load_msgs(st.session_state.pseudo, name):
                    save_msg(st.session_state.pseudo, name, "system", data["prompt"])
                    save_msg(st.session_state.pseudo, name, "assistant", data["start"])
                st.session_state.page = "chat"
                st.rerun()
        i += 1

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
