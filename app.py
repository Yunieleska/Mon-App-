import streamlit as st
import sqlite3
from groq import Groq
import os

# --- CONFIGURATION ---
client = Groq(api_key="TON_API_KEY") 
st.set_page_config(page_title="Storyia", layout="wide")

# --- BASE DE DONNÉES ---
def init_db():
    # On utilise un nom de fichier unique pour forcer la recréation si besoin
    conn = sqlite3.connect('storyia_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (user_pseudo TEXT, char_name TEXT, role TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS custom_characters 
                 (name TEXT PRIMARY KEY, prompt TEXT, start TEXT, visibility TEXT, image_path TEXT, creator TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- LOGIQUE ---
def get_user_chars(pseudo):
    conn = sqlite3.connect('storyia_v4.db')
    c = conn.cursor()
    c.execute("SELECT name, visibility FROM custom_characters WHERE creator=?", (pseudo,))
    data = c.fetchall()
    conn.close()
    return data

# --- NAVIGATION ---
st.sidebar.title("Storyia")
if "pseudo" not in st.session_state: st.session_state.pseudo = "User"
st.session_state.pseudo = st.sidebar.text_input("Ton pseudo :", st.session_state.pseudo)

if st.sidebar.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()
if st.sidebar.button("👤 Mon Profil"): st.session_state.page = "profile"; st.rerun()
if st.sidebar.button("✨ Créer un personnage"): st.session_state.page = "create"; st.rerun()

# --- PAGES ---
if "page" not in st.session_state: st.session_state.page = "home"

if st.session_state.page == "profile":
    st.title("Ton Profil")
    st.image(f"https://api.dicebear.com/7.x/adventurer/png?seed={st.session_state.pseudo}", width=150)
    st.subheader(st.session_state.pseudo)
    st.subheader("Tes créations")
    for char in get_user_chars(st.session_state.pseudo):
        st.write(f"- **{char[0]}** (Visibilité: {char[1]})")

elif st.session_state.page == "home":
    st.title("Choisis ton personnage")
    st.info("La base est vide, utilise la page 'Créer un personnage' pour ajouter des contenus.")
    # Logique d'affichage des personnages ici...

elif st.session_state.page == "create":
    st.title("Créer ton personnage")
    with st.form("new_char"):
        name = st.text_input("Nom")
        if st.form_submit_button("Sauvegarder"):
            conn = sqlite3.connect('storyia_v4.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO custom_characters VALUES (?,?,?,?,?,?)", 
                      (name, "Prompt...", "Accroche...", "Public", "", st.session_state.pseudo))
            conn.commit()
            conn.close()
            st.success("Personnage ajouté !")

elif st.session_state.page == "chat":
    st.title("Chat")
    # Logique de chat...
