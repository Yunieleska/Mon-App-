import streamlit as st
from supabase import create_client
from groq import Groq

# --- CONFIGURATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- SESSION INITIALIZATION ---
session = supabase.auth.get_session()
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "pseudo" not in st.session_state: st.session_state.pseudo = "Invité"

if session:
    st.session_state.logged_in = True
    user_data = supabase.table("users").select("pseudo").eq("id", session.user.id).execute()
    if user_data.data:
        st.session_state.pseudo = user_data.data[0]["pseudo"]

# --- SUPABASE FUNCTIONS ---
def save_msg(pseudo, char, role, content):
    supabase.table("messages").insert({"user_pseudo": pseudo, "char_name": char, "role": role, "content": content}).execute()

def load_msgs(pseudo, char):
    res = supabase.table("messages").select("role, content").eq("user_pseudo", pseudo).eq("char_name", char).execute()
    return [{"role": r["role"], "content": r["content"]} for r in res.data]

# --- LOGIN LOGIC ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image("bg.png", use_container_width=True)
        except: st.info("Image 'bg.png' manquante.")
        
        st.title("Welcome to Storyia")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            pseudo_log = st.text_input("Pseudo", key="login_pseudo")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In"):
                email_virtuel = f"{pseudo_log.lower()}@storyia.com"
                try:
                    supabase.auth.sign_in_with_password({"email": email_virtuel, "password": password})
                    st.rerun()
                except: st.error("Pseudo ou mot de passe incorrect.")
                
        with tab2:
            new_pseudo = st.text_input("Pseudo", key="sign_pseudo")
            new_pass = st.text_input("Password", type="password", key="sign_pass")
            if st.button("Sign Up"):
                email_virtuel = f"{new_pseudo.lower()}@storyia.com"
                try:
                    auth_res = supabase.auth.sign_up({"email": email_virtuel, "password": new_pass})
                    supabase.table("users").insert({"id": auth_res.user.id, "pseudo": new_pseudo}).execute()
                    st.success("Compte créé ! Veuillez vous connecter.")
                except Exception as e: st.error(f"Erreur : {e}")
    st.stop()

# --- INTERFACE ---
CHARACTERS = {"Caelum": {"img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "prompt": "Tu es Caelum, Prince des Ténèbres.", "start": "Tu es sur mon chemin."}, "Noah": {"img": "Noah.png", "prompt": "Tu es Noah, quaterback star.", "start": "Une façade."}, "Ethan": {"img": "Ethan.png", "prompt": "Tu es Ethan, Loup Alpha.", "start": "La forêt est dangereuse."}, "Léo": {"img": "Léo.png", "prompt": "Tu es Léo, streameur.", "start": "Tu es enfin là."}, "Liam": {"img": "Liam.png", "prompt": "Tu es Liam, le grand frère.", "start": "Calme de ma maison."}, "Alexei": {"img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "prompt": "Tu es Alexei, mafieux.", "start": "La mafia n'attend personne."}, "Lucas": {"img": "Lucas.png", "prompt": "Tu es Lucas, populaire.", "start": "On squatte ton canapé ?"}, "Killian": {"img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "prompt": "Tu es Killian, motard.", "start": "Je t'ai sortie de là."}}

st.sidebar.info(f"Connecté : **{st.session_state.pseudo}**")
if st.sidebar.button("🚪 Logout"):
    supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.rerun()

if "page" not in st.session_state: st.session_state.page = "home"
if st.sidebar.button("🏠 Home"): st.session_state.page = "home"; st.rerun()

if st.session_state.page == "home":
    st.title("Choose your character")
    cols = st.columns(4)
    for i, (name, data) in enumerate(CHARACTERS.items()):
        with cols[i % 4]:
            st.image(data["img"], use_container_width=True)
            if st.button(name): 
                st.session_state.char_select = name
                st.session_state.page = "chat"
                st.rerun()

elif st.session_state.page == "chat":
    st.title(f"Chat with {st.session_state.char_select}")
    for msg in load_msgs(st.session_state.pseudo, st.session_state.char_select):
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input():
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        messages = load_msgs(st.session_state.pseudo, st.session_state.char_select)
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", res.choices[0].message.content)
        st.rerun()
