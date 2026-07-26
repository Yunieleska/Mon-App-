import streamlit as st
from supabase import create_client
from groq import Groq

# --- CONFIGURATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- SESSION INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "pseudo" not in st.session_state: st.session_state.pseudo = "Invité"
if "char_select" not in st.session_state: st.session_state.char_select = "Caelum"

# Vérification de session existante
try:
    session = supabase.auth.get_session()
    if session:
        st.session_state.logged_in = True
        user_data = supabase.table("users").select("pseudo").eq("id", session.user.id).single().execute()
        st.session_state.pseudo = user_data.data["pseudo"] if user_data.data else "Utilisateur"
except Exception:
    st.session_state.logged_in = False

# --- SUPABASE FUNCTIONS ---
def save_msg(pseudo, char, role, content):
    try:
        supabase.table("messages").insert({"user_pseudo": pseudo, "char_name": char, "role": role, "content": content}).execute()
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

def load_msgs(pseudo, char):
    try:
        res = supabase.table("messages").select("role, content").eq("user_pseudo", pseudo).eq("char_name", char).execute()
        return [{"role": r["role"], "content": r["content"]} for r in res.data]
    except:
        return []

# --- LOGIN LOGIC ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Welcome to Storyia")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            email_log = st.text_input("E-mail", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email_log, "password": password})
                    if res.user:
                        st.session_state.logged_in = True
                        user_data = supabase.table("users").select("pseudo").eq("id", res.user.id).single().execute()
                        st.session_state.pseudo = user_data.data["pseudo"]
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur de connexion : {e}")

        with tab2:
            new_pseudo = st.text_input("Pseudo", key="sign_pseudo")
            new_email = st.text_input("E-mail", key="sign_email")
            new_pass = st.text_input("Password", type="password", key="sign_pass")
            reponse_secrete = st.text_input("Question : Ta couleur préférée ?", key="sign_q")
            if st.button("Sign Up"):
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
                except Exception as e:
                    st.error(f"Erreur : {e}")
    st.stop()

# --- INTERFACE ---
CHARACTERS = {
    "Caelum": {
        "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", 
        "prompt": "Tu es Caelum, Prince des Ténèbres.",
        "quote": "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as rien à y faire."
    },
    "Alexei": {
        "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", 
        "prompt": "Tu es Alexei, mafieux.",
        "quote": "Regardez qui s'est perdue sur mon territoire. La petite princesse des Volkov... Ton père est devenu tellement faible qu'il envoie sa fille faire son sale boulot, ou tu as juste envie de jouer avec le feu ?"
    },
    "Killian": {
        "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", 
        "prompt": "Tu es Killian, motard.",
        "quote": "Respire, c'est fini... T'as pas changé, toujours aussi maladroite. Dis-moi que t'as rien de cassé, par pitié."
    },
    "Lucas": {
        "img": "Lucas.png", 
        "prompt": "Tu es Lucas, populaire.",
        "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série comme d'habitude ?"
    },
    "Ethan": {
        "img": "https://i.pinimg.com/736x/d9/67/d2/d967d237f7127d2b7a60180639d7c447.jpg", 
        "prompt": "Tu es Ethan, Loup Alpha.",
        "quote": "La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines..."
    },
    "Léo": {
        "img": "https://i.pinimg.com/736x/c1/b7/68/c1b768a0366e73394825679aa81810c4.jpg", 
        "prompt": "Tu es Léo, streameur.",
        "quote": "Prête à ce qu'on détruise l'équipe d'en face ?"
    },
    "Liam": {
        "img": "https://i.pinimg.com/736x/f7/86/59/f786594b9a4a21a010bd06a119378235.jpg", 
        "prompt": "Tu es Liam, le grand frère.",
        "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit, l'orage arrive et j'ai besoin de dormir."
    },
    "Noah": {
        "img": "https://i.pinimg.com/736x/b4/ee/02/b4ee020d6481d35d02b0ac2c8c5830a7.jpg", 
        "prompt": "Tu es Noah, quarterback star.",
        "quote": "Dis, tu crois qu'on est tous obligés de jouer un rôle pour plaire aux autres, ou il y a un endroit où on peut juste être soi-même ?"
    }
}

# --- SIDEBAR ---
st.sidebar.info(f"Connecté : **{st.session_state.pseudo}**")
selected_char = st.sidebar.selectbox("Choisir un personnage", list(CHARACTERS.keys()), key="sidebar_char")

# --- NOUVELLE LOGIQUE DE MISE À JOUR ---
# Si le personnage change, on met à jour la session, mais sans forcer un rerun complet
if selected_char != st.session_state.char_select:
    st.session_state.char_select = selected_char

if st.sidebar.button("🚪 Logout"):
    supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.rerun()

# --- CHAT PAGE ---
current_char = st.session_state.char_select
bg_image = CHARACTERS[current_char]["img"]
char_quote = CHARACTERS[current_char]["quote"]

# Injection dynamique du CSS pour le fond d'écran
# (L'utilisation de .stEditor et .stMarkdown permet de cibler le fond du chat)
st.markdown(f"""
    <style>
    /* Cible le conteneur principal de la page de chat pour changer le fond */
    div[data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Change la couleur du texte pour qu'il soit visible sur le nouveau fond */
    div.stMarkdown, p, li, h1, h2, h3, span {{
        color: white !important;
    }}
    </style>
""", unsafe_allow_html=True)

st.title(f"Chat avec {current_char}")
st.markdown(f"*{char_quote}*")

# Chargement de l'historique et affichage
messages = load_msgs(st.session_state.pseudo, current_char)
char_prompt = CHARACTERS[current_char]["prompt"]
full_messages = [{"role": "system", "content": char_prompt}] + messages

# Affichage des messages avec le nouveau style de police
for msg in messages:
    with st.chat_message(msg["role"]): 
        st.write(msg["content"])

# Saisie du message
if prompt := st.chat_input("Écris ton message ici..."):
    save_msg(st.session_state.pseudo, current_char, "user", prompt)
    full_messages.append({"role": "user", "content": prompt})
    
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
    assistant_reply = res.choices[0].message.content
    
    save_msg(st.session_state.pseudo, current_char, "assistant", assistant_reply)
    st.rerun()
