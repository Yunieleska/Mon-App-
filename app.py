import streamlit as st
from supabase import create_client
from groq import Groq
import os

# --- CONFIGURATION ---
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key and "GROQ_API_KEY" in st.secrets:
    groq_key = st.secrets["GROQ_API_KEY"]

try:
    client = Groq(api_key=groq_key)
except Exception:
    client = None

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    supabase = None

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- STYLE GLOBAL & CORRECTIONS VISUELLES ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #ffffff;
    }
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stInfoBox"], 
    [data-testid="stSidebar"] div[data-baseweb="notification"],
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
        background-color: #161b22 !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stInfoBox"] *, 
    [data-testid="stSidebar"] div[data-baseweb="notification"] *,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    .stButton>button {
        background-color: #21262d !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #30363d !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
    }
    .stButton>button p {
        color: #ffffff !important;
    }
    /* Correctif responsive pour forcer un affichage en grille propre sur mobile */
    @media(max-width: 768px) {
        [data-testid="column"] {
            width: 48% !important;
            flex: 1 1 48% !important;
            min-width: 48% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- PERSISTANCE PAR URL (ANTI-RESET STREAMLIT) ---
query_params = st.query_params

if "user" in query_params and query_params["user"]:
    st.session_state.logged_in = True
    st.session_state.pseudo = query_params["user"]
else:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "pseudo" not in st.session_state:
        st.session_state.pseudo = "Invité"

if "page" not in st.session_state: 
    st.session_state.page = "home"
if "char_select" not in st.session_state: 
    st.session_state.char_select = "Caelum"

# --- SUPABASE FUNCTIONS SÉCURISÉES ---
def save_msg(pseudo, char, role, content):
    if not supabase:
        return
    try:
        supabase.table("messages").insert({
            "user_pseudo": str(pseudo), 
            "char_name": str(char), 
            "role": str(role), 
            "content": str(content)
        }).execute()
    except Exception:
        pass

def load_msgs(pseudo, char):
    if not supabase:
        return []
    try:
        res = supabase.table("messages").select("role, content").eq("user_pseudo", str(pseudo)).eq("char_name", str(char)).execute()
        if res.data:
            return [{"role": r["role"], "content": r["content"]} for r in res.data]
        return []
    except Exception:
        return []

def get_user_conversations(pseudo):
    if not supabase:
        return {}
    try:
        res = supabase.table("messages").select("char_name, content, role").eq("user_pseudo", str(pseudo)).execute()
        chars_met = {}
        if res.data:
            for r in res.data:
                chars_met[r["char_name"]] = r["content"]
        return chars_met
    except Exception:
        return {}

def get_all_characters():
    chars = {
        "Caelum": {
            "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", 
            "prompt": "Tu es Caelum, Prince des Ténèbres. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as rien à y faire."
        },
        "Alexei": {
            "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", 
            "prompt": "Tu es Alexei, mafieux. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "Regardez qui s'est perdue sur mon territoire. La petite princesse des Volkov..."
        },
        "Killian": {
            "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", 
            "prompt": "Tu es Killian, motard. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "Respire, c'est fini... T'as pas changé, toujours aussi maladroite."
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG", 
            "prompt": "Tu es Lucas, populaire. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série ?"
        },
        "Ethan": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/ethan.png", 
            "prompt": "Tu es Ethan, Loup Alpha. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines..."
        },
        "Léo": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/leo.png.PNG", 
            "prompt": "Tu es Léo, streameur. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "Prête à ce qu'on détruise l'équipe d'en face ?"
        },
        "Liam": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/liam.png.PNG", 
            "prompt": "Tu es Liam, le grand frère. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit."
        },
        "Noah": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/noah.png.PNG", 
            "prompt": "Tu es Noah, quarterback star. Reste strictement dans ton rôle, adopte un ton immersif de roleplay.",
            "quote": "Dis, tu crois qu'on est tous obligés de jouer un rôle pour plaire ?"
        }
    }
    
    if supabase:
        try:
            res = supabase.table("custom_characters").select("*").execute()
            if res.data:
                for item in res.data:
                    if item.get("is_public", True) or item.get("creator") == st.session_state.pseudo:
                        chars[item["name"]] = {
                            "img": item["img_url"] if item.get("img_url") and (item["img_url"].startswith("http") or os.path.exists(item["img_url"])) else "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
                            "prompt": f"Tu es {item['name']}, un personnage {item.get('sex', '')}. Description : {item.get('description', '')}. Personnages secondaires / Contexte additionnel : {item.get('secondary_chars', '')}. Reste strictement dans ton rôle.",
                            "quote": item.get("quote") if item.get("quote") else f"Bonjour, je suis {item['name']}."
                        }
        except Exception:
            pass
            
    return chars

CHARACTERS = get_all_characters()

# --- LOGIN LOGIC ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("bg.png"):
            st.image("bg.png")
        
        if not supabase or not client:
            st.error("⚠️ Attention : Vérifie tes clés Supabase et Groq dans les secrets de Streamlit Cloud.")

        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            email_log = st.text_input("E-mail", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In"):
                if supabase:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email_log, "password": password})
                        if res and res.user:
                            user_data = supabase.table("users").select("pseudo").eq("id", res.user.id).single().execute()
                            pseudo_val = user_data.data["pseudo"] if user_data.data else email_log.split("@")[0]
                            
                            st.session_state.logged_in = True
                            st.session_state.pseudo = pseudo_val
                            if res.session:
                                st.session_state.access_token = res.session.access_token
                            st.query_params["user"] = pseudo_val
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur de connexion : {e}")
                else:
                    st.error("Base de données non disponible.")

        with tab2:
            new_pseudo = st.text_input("Pseudo", key="sign_pseudo")
            new_email = st.text_input("E-mail", key="sign_email")
            new_pass = st.text_input("Password", type="password", key="sign_pass")
            reponse_secrete = st.text_input("Question : Ta couleur préférée ?", key="sign_q")
            if st.button("Sign Up"):
                if supabase:
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
                else:
                    st.error("Base de données non disponible.")
    st.stop()

# --- SIDEBAR ---
if os.path.exists("couple.png"):
    st.sidebar.image("couple.png")
st.sidebar.info(f"Connecté : **{st.session_state.pseudo}**")

if st.sidebar.button("🏠 Home"): 
    st.session_state.page = "home"
    st.rerun()

if st.sidebar.button("✨ Créer un Personnage"):
    st.session_state.page = "create_character"
    st.rerun()

if st.sidebar.button("💬 Messages"):
    st.session_state.page = "messages"
    st.rerun()

if st.sidebar.button("👤 Profil"):
    st.session_state.page = "profile"
    st.rerun()

if st.sidebar.button("🚪 Logout"):
    if supabase:
        try:
            supabase.auth.sign_out()
        except:
            pass
    st.session_state.logged_in = False
    st.session_state.pseudo = "Invité"
    if "access_token" in st.session_state:
        del st.session_state.access_token
    if "user" in st.query_params:
        del st.query_params["user"]
    st.rerun()

# --- NAVIGATION ENTRE PAGES ---
if st.session_state.page == "home":
    st.title("Explorer")
    st.write("Découvre et discute avec les personnages du moment :")
    
    items = list(CHARACTERS.items())
    
    ITEMS_PER_PAGE = 8
    if "home_page" not in st.session_state:
        st.session_state.home_page = 0
        
    total_pages = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    st.session_state.home_page = min(st.session_state.home_page, total_pages - 1)
    
    start_idx = st.session_state.home_page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_items = items[start_idx:end_idx]

    cols_per_row = 4
    for i in range(0, len(current_items), cols_per_row):
        row_items = current_items[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        
        for idx, (name, data) in enumerate(row_items):
            with cols[idx]:
                img_src = data['img']
                if not img_src.startswith("http") and not os.path.exists(img_src):
                    img_src = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                
                with st.container():
                    st.image(img_src, use_container_width=True)
                    st.markdown(f"**{name}**")
                    st.markdown(f"<span style='color: #8b949e; font-style: italic; font-size: 12px;'>\"{data['quote']}\"</span>", unsafe_allow_html=True)
                    
                    if st.button("💬 Discuter", key=f"btn_chat_{name}", use_container_width=True):
                        st.session_state.char_select = name
                        st.session_state.page = "chat"
                        st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)

    if "chat_target" in query_params:
        target_char = query_params["chat_target"]
        if target_char in CHARACTERS:
            st.session_state.char_select = target_char
            st.session_state.page = "chat"
            if "chat_target" in st.query_params:
                del st.query_params["chat_target"]
            st.rerun()

    if total_pages > 1:
        st.markdown("---")
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if st.session_state.home_page > 0:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.home_page -= 1
                    st.rerun()
        with p_col2:
            st.markdown(f"<p style='text-align: center; color: #8b949e;'>Page {st.session_state.home_page + 1} sur {total_pages}</p>", unsafe_allow_html=True)
        with p_col3:
            if st.session_state.home_page < total_pages - 1:
                if st.button("Suivant ➡️", use_container_width=True):
                    st.session_state.home_page += 1
                    st.rerun()

elif st.session_state.page == "create_character":
    st.title("✨ Créer un nouveau personnage")
    st.write("Conçois ton propre personnage sur mesure, définis son univers et choisis s'il est visible par tous ou uniquement par toi.")

    with st.form("create_char_form"):
        char_name = st.text_input("Nom du personnage")
        char_sex = st.selectbox("Sexe / Genre", ["Homme", "Femme", "Non-binaire", "Autre"])
        char_quote = st.text_input("Phrase d'accroche (Citation affichée sous l'image)")
        char_description = st.text_area("Description et Personnalité (Comment se comporte-t-il, son histoire, son ton...)", help="Ex: Tu es ténébreux, protecteur, un peu distant au début...")
        char_secondary = st.text_area("Personnages secondaires / Éléments contextuels (Optionnel)", help="Ex: Inclut des mentions de ses frères ou de rivaux si nécessaire dans l'histoire.")
        
        uploaded_char_img = st.file_uploader("Image du personnage (PNG, JPG)", type=["png", "jpg", "jpeg"])
        visibility = st.radio("Visibilité", ["Public (visible par toute la communauté)", "Privé (uniquement pour moi)"])
        
        submitted = st.form_submit_button("Créer le personnage")
        
        if submitted:
            if not char_name or not char_description:
                st.warning("Veuillez remplir au moins le nom et la description du personnage.")
            else:
                img_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                if uploaded_char_img is not None:
                    file_name = f"char_{st.session_state.pseudo}_{char_name}.png"
                    if supabase:
                        try:
                            admin_key = st.secrets.get("SUPABASE_SERVICE_KEY", st.secrets["SUPABASE_KEY"])
                            admin_supabase = create_client(st.secrets["SUPABASE_URL"], admin_key)
                            
                            admin_supabase.storage.from_("storyia-images").upload(file_name, uploaded_char_img.read(), file_options={"upsert": "true"})
                            img_path = admin_supabase.storage.from_("storyia-images").get_public_url(file_name)
                        except Exception:
                            pass
                
                is_public = True if "Public" in visibility else False
                
                if supabase:
                    try:
                        supabase.table("custom_characters").insert({
                            "name": char_name,
                            "sex": char_sex,
                            "quote": char_quote,
                            "description": char_description,
                            "secondary_chars": char_secondary,
                            "img_url": img_path,
                            "is_public": is_public,
                            "creator": st.session_state.pseudo
                        }).execute()
                        
                        st.success(f"Le personnage {char_name} a été créé avec succès !")
                        st.session_state.page = "home"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la création : {e}")
                else:
                    st.error("Base de données non disponible.")

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
                    st.image(CHARACTERS[char_name]["img"], width=85)
                with col2:
                    st.subheader(char_name)
                    st.caption(CHARACTERS[char_name]["quote"])
                with col3:
                    if st.button("Ouvrir", key=f"open_msg_{char_name}", use_container_width=True):
                        st.session_state.char_select = char_name
                        st.session_state.page = "chat"
                        st.rerun()
                st.markdown("---")

elif st.session_state.page == "profile":
    st.title("Mon Profil")
    
    if supabase:
        try:
            user_db = supabase.table("users").select("*").eq("pseudo", st.session_state.pseudo).single().execute()
            user_info = user_db.data if user_db.data else {}
            
            user_email = user_info.get("email", "Non disponible")
            user_id = user_info.get("id")
            
            avatar_path = user_info.get("avatar_url", "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg")
            if not avatar_path or not str(avatar_path).startswith("http"):
                avatar_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

            convs = get_user_conversations(st.session_state.pseudo)
            nb_collected = len(convs)
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.image(avatar_path, use_container_width=True)
                
            with col2:
                st.subheader(st.session_state.pseudo)
                st.write(f"📧 {user_email}")
                
                stat1, stat2, stat3 = st.columns(3)
                with stat1:
                    st.metric(label="Personnages", value=nb_collected)
                with stat2:
                    st.metric(label="Abonnés", value=0)
                with stat3:
                    st.metric(label="Abonnements", value=0)

            st.markdown("---")
            st.text_input("Pseudo (non modifiable)", value=st.session_state.pseudo, disabled=True)
            
            uploaded_file = st.file_uploader("Changer votre photo de profil", type=["png", "jpg", "jpeg"], key="avatar_uploader")
            
            if uploaded_file is not None and user_id:
                file_extension = uploaded_file.name.split(".")[-1]
                file_name = f"avatar_{user_id}.{file_extension}"
                
                try:
                    admin_key = st.secrets.get("SUPABASE_SERVICE_KEY", st.secrets["SUPABASE_KEY"])
                    admin_supabase = create_client(st.secrets["SUPABASE_URL"], admin_key)
                    
                    admin_supabase.storage.from_("storyia-images").upload(file_name, uploaded_file.read(), file_options={"upsert": "true"})
                    public_url = admin_supabase.storage.from_("storyia-images").get_public_url(file_name)
                    
                    supabase.table("users").update({"avatar_url": public_url}).eq("id", user_id).execute()
                    st.success("Photo de profil mise à jour avec succès !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'upload de la photo : {e}")
                
        except Exception as e:
            st.error(f"Impossible de charger les données du profil : {e}")

elif st.session_state.page == "chat":
    current_char = st.session_state.char_select
    bg_image = CHARACTERS[current_char]["img"]
    char_quote = CHARACTERS[current_char]["quote"]
    char_prompt = CHARACTERS[current_char]["prompt"]

    if not str(bg_image).startswith("http"):
        bg_image = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(11, 14, 20, 0.90), rgba(11, 14, 20, 0.90)), url("{bg_image}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .chat-header-container {{
            background-color: rgba(22, 27, 34, 0.85);
            padding: 18px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            margin-bottom: 25px;
            backdrop-filter: blur(5px);
        }}
        .main .block-container {{
            padding-bottom: 100px;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="chat-header-container">
            <h2 style="margin: 0; color: #ffffff;">Chat avec {current_char}</h2>
            <p style='color: #a0a0a0; font-style: italic; margin: 6px 0 0 0;'>"{char_quote}"</p>
        </div>
    """, unsafe_allow_html=True)

    messages = load_msgs(st.session_state.pseudo, current_char)

    if not messages and client:
        intro_system_prompt = [
            {"role": "system", "content": f"{char_prompt} Commence l'histoire en envoyant un premier message d'accroche immersif en incarnant ton personnage, en te basant sur cette citation : '{char_quote}'."}
        ]
        try:
            res_intro = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=intro_system_prompt)
            first_message = res_intro.choices[0].message.content
            save_msg(st.session_state.pseudo, current_char, "assistant", first_message)
            messages = load_msgs(st.session_state.pseudo, current_char)
        except Exception as e:
            st.error(f"Erreur d'authentification Groq : {e}")

    default_avatar = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
    user_avatar_path = default_avatar
    if supabase:
        try:
            u_db = supabase.table("users").select("avatar_url").eq("pseudo", str(st.session_state.pseudo)).single().execute()
            if u_db.data and u_db.data.get("avatar_url"):
                p_url = u_db.data["avatar_url"]
                if str(p_url).startswith("http"):
                    user_avatar_path = p_url
        except Exception:
            pass

    char_avatar_path = bg_image

    for idx, msg in enumerate(messages):
        is_user = (msg["role"] == "user")
        avatar_to_use = user_avatar_path if is_user else char_avatar_path
        name_to_use = st.session_state.pseudo if is_user else current_char

        with st.container():
            col_av, col_txt = st.columns([1, 11])
            with col_av:
                st.markdown(
                    f"<img src='{avatar_to_use}' style='width: 38px; height: 38px; border-radius: 50%; object-fit: cover; margin-top: 4px;'>", 
                    unsafe_allow_html=True
                )
            with col_txt:
                st.markdown(f"<b style='color: #ffffff; font-size: 14px;'>{name_to_use}</b>", unsafe_allow_html=True)
                
                if is_user:
                    edit_key = f"edit_mode_{idx}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    if not st.session_state[edit_key]:
                        st.write(msg["content"])
                        if st.button("✏️ Modifier ce message", key=f"btn_edit_{idx}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    else:
                        new_content = st.text_area("Modifier le message :", value=msg["content"], key=f"input_edit_{idx}")
                        col_save, col_cancel = st.columns([1, 1])
                        with col_save:
                            if st.button("💾 Enregistrer", key=f"save_edit_{idx}"):
                                if supabase and new_content.strip():
                                    try:
                                        supabase.table("messages").delete().eq("user_pseudo", str(st.session_state.pseudo)).eq("char_name", str(current_char)).execute()
                                        
                                        messages[idx]["content"] = new_content
                                        trimmed_messages = messages[:idx+1]
                                        
                                        for m in trimmed_messages:
                                            supabase.table("messages").insert({
                                                "user_pseudo": str(st.session_state.pseudo),
                                                "char_name": str(current_char),
                                                "role": m["role"],
                                                "content": m["content"]
                                            }).execute()
                                            
                                        st.session_state[edit_key] = False
                                        
                                        if idx == len(messages) - 1 and client:
                                            full_messages = [{"role": "system", "content": char_prompt}] + trimmed_messages
                                            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
                                            assistant_reply = res.choices[0].message.content
                                            save_msg(st.session_state.pseudo, current_char, "assistant", assistant_reply)
                                        
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur lors de la modification : {e}")
                        with col_cancel:
                            if st.button("❌ Annuler", key=f"cancel_edit_{idx}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                else:
                    st.write(msg["content"])
            
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input("Écris ton message ici...", label_visibility="collapsed", placeholder="Écris ton message ici...")
        with col_btn:
            submit_chat = st.form_submit_button("Envoyer ➔", use_container_width=True)

        if submit_chat and user_input.strip():
            save_msg(st.session_state.pseudo, current_char, "user", user_input)
            messages.append({"role": "user", "content": user_input})
            
            if client:
                try:
                    full_messages = [{"role": "system", "content": char_prompt}] + messages
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
                    assistant_reply = res.choices[0].message.content
                    save_msg(st.session_state.pseudo, current_char, "assistant", assistant_reply)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'envoi du message : {e}")
            else:
                st.error("Client Groq non initialisé.")
