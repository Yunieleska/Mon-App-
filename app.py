import streamlit as st
from supabase import create_client
from groq import Groq
import hashlib

# --- CONFIGURATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()

# --- FONCTIONS SUPABASE ---
def save_msg(pseudo, char, role, content):
    supabase.table("messages").insert({"user_pseudo": pseudo, "char_name": char, "role": role, "content": content}).execute()

def load_msgs(pseudo, char):
    res = supabase.table("messages").select("role, content").eq("user_pseudo", pseudo).eq("char_name", char).execute()
    return [{"role": r["role"], "content": r["content"]} for r in res.data]

def get_user_chats(pseudo):
    res = supabase.table("messages").select("char_name").eq("user_pseudo", pseudo).execute()
    return list(set([row["char_name"] for row in res.data]))

# --- INITIALISATION SESSION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "pseudo" not in st.session_state: st.session_state.pseudo = ""

def logout():
    st.session_state.logged_in = False
    st.session_state.pseudo = ""
    st.rerun()

# --- LOGIQUE DE CONNEXION ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Bienvenue sur Storyia")
        tab1, tab2 = st.tabs(["Connexion", "Inscription"])
        
        with tab1:
            user_login = st.text_input("Ton pseudo", key="login_in")
            pass_login = st.text_input("Mot de passe", type="password", key="pass_in")
            if st.button("Se connecter"):
                # Requête simplifiée pour éviter l'APIError
                res = supabase.table("users").select("pseudo, password, question, answer").eq("pseudo", user_login).execute()
                if res.data and res.data[0].get("password") == hash_pass(pass_login):
                    st.session_state.pseudo = user_login
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("Pseudo ou mot de passe incorrect.")
            
            with st.expander("Mot de passe oublié ?"):
                rec_user = st.text_input("Entre ton pseudo pour récupérer")
                if rec_user:
                    res = supabase.table("users").select("question, answer").eq("pseudo", rec_user).execute()
                    if res.data:
                        st.write(f"Question : **{res.data[0]['question']}**")
                        ans_input = st.text_input("Réponse à la question")
                        new_pass = st.text_input("Nouveau mot de passe", type="password")
                        if st.button("Réinitialiser"):
                            if hash_pass(ans_input) == res.data[0]["answer"]:
                                supabase.table("users").update({"password": hash_pass(new_pass)}).eq("pseudo", rec_user).execute()
                                st.success("Mot de passe mis à jour !")
        
        with tab2:
            new_user = st.text_input("Choisis un pseudo", key="sign_in")
            new_pass = st.text_input("Mot de passe", type="password")
            quest = st.selectbox("Question secrète", ["Animal favori ?", "Ville de naissance ?"])
            ans = st.text_input("Réponse")
            if st.button("S'inscrire"):
                res = supabase.table("users").select("pseudo").eq("pseudo", new_user).execute()
                if res.data: st.error("Pseudo déjà utilisé.")
                else:
                    supabase.table("users").insert({"pseudo": new_user, "password": hash_pass(new_pass), "question": quest, "answer": hash_pass(ans)}).execute()
                    st.success("Compte créé !")
    st.stop()

# --- INTERFACE (Reste du code identique...) ---
CHARACTERS = {"Caelum": {"img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "prompt": "Tu es Caelum, Prince des Ténèbres.", "start": "Tu es sur mon chemin."}, "Noah": {"img": "Noah.png", "prompt": "Tu es Noah, quaterback star.", "start": "Une façade."}, "Ethan": {"img": "Ethan.png", "prompt": "Tu es Ethan, Loup Alpha.", "start": "La forêt est dangereuse."}, "Léo": {"img": "Léo.png", "prompt": "Tu es Léo, streameur.", "start": "Tu es enfin là."}, "Liam": {"img": "Liam.png", "prompt": "Tu es Liam, le grand frère.", "start": "Calme de ma maison."}, "Alexei": {"img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", "prompt": "Tu es Alexei, mafieux.", "start": "La mafia n'attend personne."}, "Lucas": {"img": "Lucas.png", "prompt": "Tu es Lucas, populaire.", "start": "On squatte ton canapé ?"}, "Killian": {"img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", "prompt": "Tu es Killian, motard.", "start": "Je t'ai sortie de là."}}

st.sidebar.image("couple.png", use_container_width=True)
st.sidebar.info(f"Connecté : **{st.session_state.pseudo}**")
if st.sidebar.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()
if st.sidebar.button("👤 Mon Profil"): st.session_state.page = "profile"; st.rerun()
if st.sidebar.button("✨ Créer un personnage"): st.session_state.page = "create"; st.rerun()
st.sidebar.markdown("---")
for chat in get_user_chats(st.session_state.pseudo):
    if st.sidebar.button(f"💬 {chat}"): st.session_state.char_select = chat; st.session_state.page = "chat"; st.rerun()
if st.sidebar.button("🚪 Déconnexion"): logout()

if "page" not in st.session_state: st.session_state.page = "home"

if st.session_state.page == "profile":
    st.title("Ton Profil")
    res = supabase.table("custom_characters").select("name").eq("creator", st.session_state.pseudo).execute()
    for char in res.data: st.write(f"- **{char['name']}**")
elif st.session_state.page == "create":
    st.title("Créer ton personnage")
    with st.form("create"):
        n, p, s = st.text_input("Nom"), st.text_area("Prompt"), st.text_area("Accroche")
        if st.form_submit_button("Sauvegarder"):
            supabase.table("custom_characters").insert({"name": n, "prompt": p, "start": s, "creator": st.session_state.pseudo, "visibility": "Public"}).execute()
            st.success("Personnage créé !")
elif st.session_state.page == "home":
    st.title("Choisis ton personnage")
    cols = st.columns(4)
    for i, (name, data) in enumerate(CHARACTERS.items()):
        with cols[i % 4]:
            st.image(data["img"], use_container_width=True)
            if st.button(name): st.session_state.char_select = name; st.session_state.page = "chat"; st.rerun()
elif st.session_state.page == "chat":
    st.title(f"Chat avec {st.session_state.char_select}")
    for msg in load_msgs(st.session_state.pseudo, st.session_state.char_select):
        if msg["role"] != "system":
            with st.chat_message(msg["role"]): st.write(msg["content"])
    if prompt := st.chat_input():
        save_msg(st.session_state.pseudo, st.session_state.char_select, "user", prompt)
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=load_msgs(st.session_state.pseudo, st.session_state.char_select))
        save_msg(st.session_state.pseudo, st.session_state.char_select, "assistant", res.choices[0].message.content)
        st.rerun()
