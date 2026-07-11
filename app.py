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
    # On récupère le pseudo depuis la table 'users' en utilisant l'ID unique
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
            email_log = st.text_input("E-mail", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In"):
                try:
                    supabase.auth.sign_in_with_password({"email": email_log, "password": password})
                    st.rerun()
                except: st.error("E-mail ou mot de passe incorrect.")
            
            with st.expander("Mot de passe oublié ?"):
                recup_email = st.text_input("Ton e-mail", key="recup_email")
                reponse_user = st.text_input("Ta réponse secrète", key="recup_reponse")
                nouveau_pass = st.text_input("Nouveau mot de passe", type="password", key="new_pass")
                if st.button("Réinitialiser"):
                    user_db = supabase.table("users").select("id, secret_answer").eq("email", recup_email).execute()
                    if user_db.data and user_db.data[0]["secret_answer"] == reponse_user:
                        try:
                            supabase.functions.invoke("reset-password", body={"user_id": user_db.data[0]["id"], "new_password": nouveau_pass})
                            st.success("Mot de passe mis à jour !")
                        except Exception as e: st.error(f"Erreur : {e}")
                    else: st.error("E-mail ou réponse incorrecte.")

        with tab2:
            new_pseudo = st.text_input("Pseudo", key="sign_pseudo")
            new_email = st.text_input("E-mail", key="sign_email")
            new_pass = st.text_input("Password", type="password", key="sign_pass")
            reponse_secrete = st.text_input("Question : Ta couleur préférée ?", key="sign_q")
            
            if st.button("Sign Up"):
                # Vérification pour éviter les envois vides
                if not new_email or not new_pass or not new_pseudo:
                    st.error("Veuillez remplir tous les champs.")
                else:
                    try:
                        auth_res = supabase.auth.sign_up({"email": new_email, "password": new_pass})
                        if auth_res.user:
                            supabase.table("users").insert({
                                "id": auth_res.user.id, 
                                "pseudo": new_pseudo,
                                "email": new_email,
                                "secret_answer": reponse_secrete 
                            }).execute()
                            st.success("Compte créé ! Veuillez vous connecter.")
                        else:
                            st.error("Erreur à la création du compte.")
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
