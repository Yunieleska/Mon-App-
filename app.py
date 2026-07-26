import streamlit as st
from supabase import create_client
from groq import Groq

# --- CONFIGURATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- STYLE GLOBAL (FOND NOIR, TEXTE BLANC & BOUTONS CUSTOM) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
    }
    /* Style des boutons en mode sombre */
    .stButton>button {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }
    .stButton>button:hover {
        background-color: #333333 !important;
        border-color: #555555 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "pseudo" not in st.session_state: st.session_state.pseudo = "Invité"
if "page" not in st.session_state: st.session_state.page = "home"
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

def get_user_conversations(pseudo):
    try:
        res = supabase.table("messages").select("char_name, content, role").eq("user_pseudo", pseudo).execute()
        chars_met = {}
        for r in res.data:
            chars_met[r["char_name"]] = r["content"]
        return chars_met
    except:
        return {}

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

# --- LOGIN LOGIC ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("bg.png", use_container_width=True)
        
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

# --- SIDEBAR ---
st.sidebar.image("couple.png", use_container_width=True)
st.sidebar.info(f"Connecté : **{st.session_state.pseudo}**")

if st.sidebar.button("🏠 Home"): 
    st.session_state.page = "home"
    st.rerun()

if st.sidebar.button("💬 Messages"):
    st.session_state.page = "messages"
    st.rerun()

if st.sidebar.button("👤 Profil"):
    st.session_state.page = "profile"
    st.rerun()

if st.sidebar.button("🚪 Logout"):
    supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.rerun()

# --- NAVIGATION ENTRE PAGES ---
if st.session_state.page == "home":
    st.title("Choose your character")
    cols = st.columns(4)
    for i, (name, data) in enumerate(CHARACTERS.items()):
        with cols[i % 4]:
            st.image(data["img"], use_container_width=True)
            st.caption(f"*{data['quote']}*")
            if st.button(f"Discuter avec {name}", key=f"chat_btn_{name}__"):
                st.session_state.char_select = name
                st.session_state.page = "chat"
                st.rerun()

elif st.session_state.page == "messages":
    st.title("Mes Discussions")
    st.write("Retrouvez ici l'ensemble de vos conversations avec les personnages.")
    
    convs = get_user_conversations(st.session_state.pseudo)
    
    if not convs:
        st.info("Vous n'avez pas encore de discussions en cours. Allez sur l'accueil pour choisir un personnage !")
    else:
        for char_name in convs.keys():
            if char_name in CHARACTERS:
                col1, col2, col3 = st.columns([1, 4, 1])
                with col1:
                    st.image(CHARACTERS[char_name]["img"], width=80)
                with col2:
                    st.subheader(char_name)
                    st.caption(CHARACTERS[char_name]["quote"])
                with col3:
                    if st.button(f"Ouvrir", key=f"open_msg_{char_name}"):
                        st.session_state.char_select = char_name
                        st.session_state.page = "chat"
                        st.rerun()
                st.markdown("---")

elif st.session_state.page == "profile":
    st.title("Mon Profil")
    
    try:
        session = supabase.auth.get_session()
        user_email = session.user.email if session else "Inconnu"
        user_id = session.user.id if session else None
        
        # Récupération de l'avatar utilisateur depuis Supabase
        user_db = supabase.table("users").select("*").eq("id", user_id).single().execute()
        user_info = user_db.data if user_db.data else {}
        avatar_path = user_info.get("avatar_url", "couple.png")

        # Calcul du nombre de personnages collectionnés (discussions actives)
        convs = get_user_conversations(st.session_state.pseudo)
        nb_collected = len(convs)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            try:
                st.image(avatar_path, use_container_width=True)
            except:
                st.image("couple.png", use_container_width=True)
            
        with col2:
            st.subheader(st.session_state.pseudo)
            st.write(f"📧 {user_email}")
            
            # Statistiques (Personnages dynamiques, Abonnés et Abonnements à 0)
            stat1, stat2, stat3 = st.columns(3)
            with stat1:
                st.metric(label="Personnages", value=nb_collected)
            with stat2:
                st.metric(label="Abonnés", value=0)
            with stat3:
                st.metric(label="Abonnements", value=0)

        st.markdown("---")
        
        # Pseudo non modifiable (affiché en texte simple)
        st.text_input("Pseudo (non modifiable)", value=st.session_state.pseudo, disabled=True)
        
        # Upload d'une nouvelle photo de profil
        uploaded_file = st.file_uploader("Changer votre photo de profil", type=["png", "jpg", "jpeg"])
        
        if st.button("Mettre à jour la photo de profil"):
            update_data = {}
            if uploaded_file is not None:
                file_path = uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                update_data["avatar_url"] = file_path
                
                supabase.table("users").update(update_data).eq("id", user_id).execute()
                st.success("Photo de profil mise à jour avec succès !")
                st.rerun()
            else:
                st.warning("Veuillez sélectionner une image à uploader.")
            
    except Exception as e:
        st.error(f"Impossible de charger les données du profil : {e}")

elif st.session_state.page == "chat":
    current_char = st.session_state.char_select
    bg_image = CHARACTERS[current_char]["img"]
    char_quote = CHARACTERS[current_char]["quote"]

    # Fond d'écran du chat assombri pour garder la lisibilité
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url("{bg_image}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.title(f"Chat avec {current_char}")
    st.markdown(f"*{char_quote}*")

    # Chargement et affichage de l'historique
    messages = load_msgs(st.session_state.pseudo, current_char)
    char_prompt = CHARACTERS[current_char]["prompt"]
    full_messages = [{"role": "system", "content": char_prompt}] + messages

    for msg in messages:
        with st.chat_message(msg["role"]): 
            st.write(msg["content"])

    if prompt := st.chat_input("Écris ton message ici..."):
        save_msg(st.session_state.pseudo, current_char, "user", prompt)
        full_messages.append({"role": "user", "content": prompt})
        
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
        assistant_reply = res.choices[0].message.content
        
        save_msg(st.session_state.pseudo, current_char, "assistant", assistant_reply)
        st.rerun()
