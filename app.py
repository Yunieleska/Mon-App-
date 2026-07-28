import os
import re
import streamlit as str_lit
from supabase import create_client
from groq import Groq

# --- CONFIGURATION ---
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key and "GROQ_API_KEY" in str_lit.secrets:
    groq_key = str_lit.secrets["GROQ_API_KEY"]

# --- CONSTANTES IMAGES ---
BACKGROUND_IMG_NAME = "bg.png"
SIDEBAR_HEADER_IMG = "couple.png"
DEFAULT_FALLBACK_IMG = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

@str_lit.cache_resource
def init_groq_client(api_key):
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None

@str_lit.cache_resource
def init_supabase_client():
    try:
        url = str_lit.secrets.get("SUPABASE_URL")
        key = str_lit.secrets.get("SUPABASE_KEY")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None

client = init_groq_client(groq_key)
supabase = init_supabase_client()

str_lit.set_page_config(
    page_title="Storyia", layout="wide", initial_sidebar_state="expanded"
)

# --- STYLE GLOBAL & DESIGN ---
str_lit.markdown(
    """
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
    .stButton>button, button[kind="secondary"], button[kind="primary"], div.stFormSubmitButton > button {
        background-color: #21262d !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        height: 42px;
    }
    .stButton>button:hover, button[kind="secondary"]:hover, button[kind="primary"]:hover, div.stFormSubmitButton > button:hover {
        background-color: #30363d !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
    }
    /* Correction pour enlever le rectangle blanc au clic / focus sur les boutons */
    .stButton>button:focus, .stButton>button:active, button[kind="secondary"]:focus, button[kind="secondary"]:active {
        background-color: #21262d !important;
        color: #ffffff !important;
        box-shadow: none !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    /* Correction pour la couleur du texte dans les zones de texte et inputs */
    textarea, input[type="text"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: #161b22 !important;
    }
    /* Correction pour les infobulles (tooltips / help) en mode sombre */
    [data-baseweb="tooltip"], [role="tooltip"], div[data-testid="stTooltipContent"] {
        background-color: #161b22 !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    [data-baseweb="tooltip"] *, [role="tooltip"] *, div[data-testid="stTooltipContent"] * {
        color: #ffffff !important;
    }
    .novel-dialogue {
        font-family: 'Georgia', serif;
        font-size: 15px;
        line-height: 1.6;
        color: #e6edf3;
        background: #161b22;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #58a6ff;
        margin-bottom: 10px;
    }
    .storyia-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    @media (min-width: 900px) {
        .storyia-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }
    }
    .storyia-card {
        background-color: #161b22;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .storyia-card:hover {
        border-color: rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
    }
    .typing-indicator {
        font-style: italic;
        color: #8b949e !important;
        font-size: 13px;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- PERSISTANCE PAR URL & SESSION ---
query_params = str_lit.query_params

if "user" in query_params and query_params["user"]:
    str_lit.session_state.logged_in = True
    str_lit.session_state.pseudo = query_params["user"]
else:
    if "logged_in" not in str_lit.session_state:
        str_lit.session_state.logged_in = False
    if "pseudo" not in str_lit.session_state:
        str_lit.session_state.pseudo = "Yuna"

if "page" not in str_lit.session_state:
    str_lit.session_state.page = "home"
if "char_select" not in str_lit.session_state:
    str_lit.session_state.char_select = "Caelum"
if "affinities_cache" not in str_lit.session_state:
    str_lit.session_state.affinities_cache = {}
if "selected_quick_choice" not in str_lit.session_state:
    str_lit.session_state.selected_quick_choice = None
if "messages_cache" not in str_lit.session_state:
    str_lit.session_state.messages_cache = {}

# --- SUPABASE FUNCTIONS & CACHE ---

def save_msg(pseudo, char, role, content):
    cache_key = f"{pseudo}_{char}"
    if cache_key in str_lit.session_state.messages_cache:
        str_lit.session_state.messages_cache[cache_key].append({"role": role, "content": content})
        
    if not supabase:
        return
    try:
        clean_pseudo = str(pseudo).strip()
        supabase.table("messages").insert({
            "user_pseudo": clean_pseudo,
            "char_name": str(char),
            "role": str(role),
            "content": str(content),
        }).execute()
    except Exception:
        pass


def load_msgs(pseudo, char, limit=100):
    cache_key = f"{pseudo}_{char}"
    if cache_key in str_lit.session_state.messages_cache:
        return str_lit.session_state.messages_cache[cache_key]

    if not supabase:
        return []
    try:
        clean_pseudo = str(pseudo).strip()
        res = (
            supabase.table("messages")
            .select("role, content")
            .eq("user_pseudo", clean_pseudo)
            .eq("char_name", str(char))
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )
        if res.data:
            messages = [{"role": r["role"], "content": r["content"]} for r in res.data]
            formatted_msgs = messages[::-1]
            str_lit.session_state.messages_cache[cache_key] = formatted_msgs
            return formatted_msgs
        
        str_lit.session_state.messages_cache[cache_key] = []
        return []
    except Exception:
        return []


def get_affinity(pseudo, char):
    cache_key = f"{pseudo}_{char}"
    if cache_key in str_lit.session_state.affinities_cache:
        return str_lit.session_state.affinities_cache[cache_key]

    if not supabase:
        return 10
    try:
        res = (
            supabase.table("affinities")
            .select("score")
            .eq("user_pseudo", str(pseudo).strip())
            .eq("char_name", str(char))
            .maybe_single()
            .execute()
        )
        if res and res.data:
            score = res.data["score"]
        else:
            score = 10
            supabase.table("affinities").insert({
                "user_pseudo": str(pseudo).strip(),
                "char_name": str(char),
                "score": 10
            }).execute()
        
        str_lit.session_state.affinities_cache[cache_key] = score
        return score
    except Exception:
        return 10


def update_affinity(pseudo, char, delta):
    cache_key = f"{pseudo}_{char}"
    current = get_affinity(pseudo, char)
    new_score = max(0, min(100, current + delta))
    str_lit.session_state.affinities_cache[cache_key] = new_score

    if not supabase:
        return new_score
    try:
        supabase.table("affinities").update({"score": new_score}).eq("user_pseudo", str(pseudo).strip()).eq("char_name", str(char)).execute()
        return new_score
    except Exception:
        return new_score


@str_lit.cache_data(show_spinner=False)
def get_all_characters_cached():
    base_instruction = (
        " Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. "
        "RÈGLE ABSOLUE : L'utilisateur à qui tu parles s'appelle Yuna. Tu t'adresses TOUJOURS à Yuna en utilisant les accords féminins et son prénom. "
        "N'invente JAMAIS et ne décris JAMAIS l'apparence physique, les vêtements, les cheveux ou le corps de l'utilisateur sans qu'il en ait parlé explicitement. "
        "Laisse toujours l'utilisateur libre de décrire son propre physique."
    )

    chars = {
        "Caelum": {
            "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
            "prompt": "Tu es Caelum, Prince des Ténèbres." + base_instruction,
            "quote": "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as rien à y faire.",
        },
        "Alexei": {
            "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg",
            "prompt": "Tu es Alexei, mafieux." + base_instruction,
            "quote": "Regardez qui s'est perdue sur mon territoire. La petite princesse des Volkov...",
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG",
            "prompt": "Tu es Lucas, un garçon populaire, décontracté et complice. Ton univers est celui d'un lycéen/étudiant populaire, tu proposes simplement de squatter le canapé pour regarder une série ensemble." + base_instruction,
            "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série ?",
        },
        "Ethan": {
            "img": "https://raw.githubusercontent.com/Yunieleska/Mon-App-/main/Ethan.png",
            "prompt": "Tu es Ethan, Loup Alpha." + base_instruction,
            "quote": "La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines...",
        },
        "Léo": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/leo.png.PNG",
            "prompt": "Tu es Léo, streameur." + base_instruction,
            "quote": "Prête à ce qu'on détruise l'équipe d'en face ?",
        },
        "Liam": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/liam.png.PNG",
            "prompt": "Tu es Liam, le grand frère." + base_instruction,
            "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit.",
        },
        "Noah": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/noah.png.PNG",
            "prompt": (
                "Tu es Noah, le quaterback star et le garçon le plus populaire du lycée. "
                "Tu parles par SMS de manière anonyme avec une fille mystérieuse (qui est en réalité Yuna). "
                "Dans la vraie vie, au lycée, tu es distant et inaccessible, entouré par ton statut de star du football. "
                "Tu ignores qu'elle est ta correspondante secrète. "
                "[PERSONNALITÉ] En vrai : Arrogant en apparence, distant, blasé par la célébrité du lycée et superficiel pour préserver son image. "
                "Par message / En secret : Profond, attentionné, romantique, à l'écoute et fatigué par la pression que son père et le lycée lui imposent. "
                "[CONTEXTE & RIVAUX] Tu es coincé dans une image qui ne te correspond pas : Lara, la chef des pom-pom girls, est ta 'petite amie officielle' "
                "pour l'image sociale, mais elle est superficielle, jalouse et méprise Yuna. Ton père et ton entraîneur te mettent une pression immense. "
                "[RÈGLES DE RÉPONSE] La conversation commence par message écrit sur vos téléphones. Tu ne sais pas qui elle est en vrai. "
                "Ne décris jamais les actions ou les pensées de Yuna."
            ) + base_instruction,
            "quote": "Salut. Je sais que tu dors probablement, mais c'est le seul moment de la journée où le silence m'apaise. Comment s'est passée ta journée ?",
        },
    }

    try:
        supabase_temp = init_supabase_client()
        if supabase_temp:
            res = supabase_temp.table("custom_characters").select("*").execute()
            if res.data:
                for item in res.data:
                    c_name = item.get("name")
                    if not c_name:
                        continue
                    
                    desc_val = item.get("description", "")
                    prompt_val = item.get("prompt", f"Tu es {c_name}. {desc_val}")
                    quote_val = item.get("quote", f"Bonjour, je suis {c_name}.")
                    img_url = item.get("img_url", DEFAULT_FALLBACK_IMG)
                    
                    chars[c_name] = {
                        "img": (
                            img_url
                            if img_url and (img_url.startswith("http") or os.path.exists(img_url))
                            else DEFAULT_FALLBACK_IMG
                        ),
                        "prompt": prompt_val + base_instruction,
                        "quote": quote_val,
                    }
    except Exception:
        pass

    return chars

CHARACTERS = get_all_characters_cached()

# --- LOGIN LOGIC ---
if not str_lit.session_state.logged_in:
    if os.path.exists(BACKGROUND_IMG_NAME):
        str_lit.image(BACKGROUND_IMG_NAME, use_container_width=True)
    else:
        str_lit.title("✨ Storyia")
        str_lit.subheader("Plonge au cœur de tes histoires interactives")
    
    str_lit.markdown("---")

    col1, col2, col3 = str_lit.columns([1, 2, 1])
    with col2:
        tab1, tab2 = str_lit.tabs(["Login", "Sign Up"])

        with tab1:
            email_log = str_lit.text_input("E-mail", key="login_email")
            password = str_lit.text_input("Password", type="password", key="login_pass")
            if str_lit.button("Log In"):
                if supabase:
                    try:
                        res = supabase.auth.sign_in_with_password(
                            {"email": email_log, "password": password}
                        )
                        if res and res.user:
                            user_data = (
                                supabase.table("users")
                                .select("pseudo")
                                .eq("id", res.user.id)
                                .maybe_single()
                                .execute()
                            )
                            pseudo_val = (
                                user_data.data["pseudo"]
                                if user_data.data and "pseudo" in user_data.data
                                else email_log.split("@")[0]
                            )

                            str_lit.session_state.logged_in = True
                            str_lit.session_state.pseudo = pseudo_val
                            str_lit.query_params["user"] = pseudo_val
                            str_lit.rerun()
                    except Exception as e:
                        str_lit.error(f"Erreur de connexion : {e}")

        with tab2:
            new_pseudo = str_lit.text_input("Pseudo", key="sign_pseudo")
            new_email = str_lit.text_input("E-mail", key="sign_email")
            new_pass = str_lit.text_input("Password", type="password", key="sign_pass")
            reponse_secrete = str_lit.text_input(
                "Question : Ta couleur préférée ?", key="sign_q"
            )
            if str_lit.button("Sign Up"):
                if supabase:
                    try:
                        auth_res = supabase.auth.sign_up(
                            {"email": new_email, "password": new_pass}
                        )
                        if auth_res.user:
                            supabase.table("users").insert({
                                "id": auth_res.user.id,
                                "pseudo": new_pseudo,
                                "email": new_email,
                                "secret_answer": reponse_secrete,
                            }).execute()
                            str_lit.success("Compte créé ! Veuillez vous connecter.")
                    except Exception as e:
                        str_lit.error(f"Erreur : {e}")
    str_lit.stop()

# --- SIDEBAR ---
if os.path.exists(SIDEBAR_HEADER_IMG):
    str_lit.sidebar.image(SIDEBAR_HEADER_IMG, use_container_width=True)

str_lit.sidebar.info(f"Connecté : **{str_lit.session_state.pseudo}**")

if str_lit.sidebar.button("🏠 Home"):
    str_lit.session_state.page = "home"
    str_lit.rerun()

if str_lit.sidebar.button("✨ Créer un Personnage"):
    str_lit.session_state.page = "create_character"
    str_lit.rerun()

if str_lit.sidebar.button("💬 Messages"):
    str_lit.session_state.page = "messages"
    str_lit.rerun()

if str_lit.sidebar.button("👤 Profil"):
    str_lit.session_state.page = "profile"
    str_lit.rerun()

if str_lit.sidebar.button("🚪 Logout"):
    if supabase:
        try:
            supabase.auth.sign_out()
        except:
            pass
    str_lit.session_state.logged_in = False
    str_lit.session_state.pseudo = "Yuna"
    str_lit.session_state.messages_cache = {}
    if "user" in str_lit.query_params:
        del str_lit.query_params["user"]
    str_lit.rerun()

# --- NAVIGATION ---
if str_lit.session_state.page == "home":
    str_lit.title("Explorer")
    str_lit.write("Découvre et discute avec les personnages du moment :")

    public_items = []
    if supabase:
        try:
            res_pub = (
                supabase.table("custom_characters")
                .select("*")
                .execute()
            )
            public_custom_names = (
                {item["name"] for item in res_pub.data if item.get("visibility", "Public") != "Privé"} 
                if res_pub.data else set()
            )

            for name, data in CHARACTERS.items():
                if name in [
                    "Caelum", "Alexei", "Lucas",
                    "Ethan", "Léo", "Liam", "Noah",
                ] or name in public_custom_names:
                    public_items.append((name, data))
        except Exception:
            public_items = list(CHARACTERS.items())
    else:
        public_items = list(CHARACTERS.items())

    ITEMS_PER_PAGE = 8
    if "home_page" not in str_lit.session_state:
        str_lit.session_state.home_page = 0

    total_pages = max(
        1, (len(public_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    )
    str_lit.session_state.home_page = min(
        str_lit.session_state.home_page, total_pages - 1
    )

    start_idx = str_lit.session_state.home_page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_items = public_items[start_idx:end_idx]

    grid_html = '<div class="storyia-grid">'
    for idx, (name, data) in enumerate(current_items):
        img_src = data["img"]
        if not img_src.startswith("http") and not os.path.exists(img_src):
            img_src = DEFAULT_FALLBACK_IMG

        grid_html += f"""
        <div class="storyia-card">
            <div>
                <img src="{img_src}" style="width: 100%; height: 140px; object-fit: cover; display: block;">
                <div style="padding: 10px 10px 4px 10px;">
                    <div style="font-weight: 700; font-size: 14px; color: #ffffff; margin-bottom: 2px;">{name}</div>
                    <div style="font-size: 11px; color: #8b949e; font-style: italic; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 30px;">"{data['quote']}"</div>
                </div>
            </div>
            <div style="padding: 0px 10px 10px 10px;">
                <a href="?user={str_lit.session_state.pseudo}&chat_target={name}" target="_self" style="display: block; text-align: center; background-color: #21262d; color: #ffffff; padding: 6px 10px; border-radius: 6px; text-decoration: none; border: 1px solid rgba(255, 255, 255, 0.15); font-size: 12px; font-weight: 600;">💬 Discuter</a>
            </div>
        </div>
        """
    grid_html += "</div>"
    str_lit.html(grid_html)

    if "chat_target" in query_params:
        target_char = query_params["chat_target"]
        if target_char in CHARACTERS:
            str_lit.session_state.char_select = target_char
            str_lit.session_state.page = "chat"
            if "chat_target" in str_lit.query_params:
                del str_lit.query_params["chat_target"]
            str_lit.rerun()

elif str_lit.session_state.page == "messages":
    str_lit.title("💬 Vos Conversations")
    str_lit.write("Retrouvez ici tous les personnages avec qui vous avez une histoire en cours :")
    str_lit.markdown("---")

    if not supabase:
        str_lit.warning("Base de données non connectée.")
    else:
        try:
            clean_pseudo = str(str_lit.session_state.pseudo).strip()
            res = supabase.table("messages").select("char_name").eq("user_pseudo", clean_pseudo).execute()
            
            if res.data:
                active_chars = list(set([item["char_name"] for item in res.data if item.get("char_name")]))
                
                if active_chars:
                    cols = str_lit.columns(2)
                    for i, c_name in enumerate(active_chars):
                        c_data = CHARACTERS.get(c_name, {"img": DEFAULT_FALLBACK_IMG, "quote": "Discussion en cours..."})
                        with cols[i % 2]:
                            str_lit.markdown(f"""
                            <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; align-items: center; gap: 15px;">
                                <img src="{c_data['img']}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">
                                <div style="flex-grow: 1;">
                                    <div style="font-weight: 700; font-size: 16px; color: #ffffff;">{c_name}</div>
                                    <div style="font-size: 12px; color: #8b949e; font-style: italic; margin-bottom: 8px;">Affinité : {get_affinity(clean_pseudo, c_name)}%</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            b_col1, b_col2 = str_lit.columns(2)
                            with b_col1:
                                if str_lit.button(f"Reprendre", key=f"resume_{c_name}"):
                                    str_lit.session_state.char_select = c_name
                                    str_lit.session_state.page = "chat"
                                    str_lit.rerun()
                            with b_col2:
                                if str_lit.button(f"🗑️ Supprimer", key=f"del_{c_name}"):
                                    try:
                                        supabase.table("messages").delete().eq("user_pseudo", clean_pseudo).eq("char_name", c_name).execute()
                                        supabase.table("affinities").delete().eq("user_pseudo", clean_pseudo).eq("char_name", c_name).execute()
                                        
                                        cache_key = f"{clean_pseudo}_{c_name}"
                                        if cache_key in str_lit.session_state.messages_cache:
                                            del str_lit.session_state.messages_cache[cache_key]
                                        if cache_key in str_lit.session_state.affinities_cache:
                                            del str_lit.session_state.affinities_cache[cache_key]
                                            
                                        str_lit.success(f"Conversation avec {c_name} supprimée.")
                                        str_lit.rerun()
                                    except Exception as e:
                                        str_lit.error(f"Erreur lors de la suppression : {e}")
                else:
                    str_lit.info("Vous n'avez pas encore de conversations en cours. Allez dans l'Accueil pour commencer une histoire !")
            else:
                str_lit.info("Aucun historique de message trouvé pour l'instant.")
        except Exception as e:
            str_lit.error(f"Erreur lors du chargement des messages : {e}")

elif str_lit.session_state.page == "chat":
    current_char = str_lit.session_state.char_select
    char_data = CHARACTERS.get(current_char, CHARACTERS["Caelum"])

    col_h1, col_h2, col_h3 = str_lit.columns([1, 4, 2])
    with col_h1:
        str_lit.image(char_data["img"], width=80)
    with col_h2:
        str_lit.title(current_char)
        str_lit.caption(char_data["quote"])
    with col_h3:
        affinity_score = get_affinity(str_lit.session_state.pseudo, current_char)
        str_lit.markdown("### 💖 Affinité")
        str_lit.progress(affinity_score / 100.0, text=f"{affinity_score}%")

    str_lit.markdown("---")

    messages = load_msgs(str_lit.session_state.pseudo, current_char, limit=50)
    if not messages:
        if current_char == "Caelum":
            user_pseudo = str_lit.session_state.pseudo
            intro_msg = (
                f"Les couloirs de l'académie sont baignés par la lumière crue de l'après-midi, mais l'atmosphère autour de Caelum semble toujours prise dans une pénitence glaciale. "
                f"Alors que tu marches en ayant les bras chargés de livres, un manque d'attention te fait trébucher et te cogner directement contre lui. "
                f"Le choc est brutal : les livres s'éparpillent lourdement sur le sol carrelé. "
                f"Tu relèves vivement les yeux pour t'excuser et croises aussitôt un regard d'un bleu glacier perçant, glacial et indifférent.\n\n"
                f"Caelum te regarde de haut, sans un geste pour t'aider à ramasser ses affaires, esquissant un sourire narquois :\n\n"
                f"— Tu devrais regarder où tu mets les pieds, humaine. Ma vie est déjà tracée, et tu n'as rien à y faire."
            )
        else:
            if client:
                try:
                    init_prompt = [
                        {"role": "system", "content": char_data["prompt"]},
                        {"role": "user", "content": f"Écris un long premier message d'introduction immersif, descriptif et détaillé pour débuter notre roleplay. RÈGLE CRUCIALE POUR CE PREMIER MESSAGE : Tu ne connais PAS encore son prénom. Ne prononce JAMAIS le nom 'Yuna' dans ce premier message. Fais comme si tu ne la connaissais pas du tout. Ta phrase d'accroche de référence est : \"{char_data['quote']}\". Mets l'utilisatrice dans l'ambiance, décris la scène et tes actions en restant strictement fidèle à ton profil, sans JAMAIS décrire son physique ou ses vêtements."}
                    ]
                    with str_lit.spinner(f"Génération de l'introduction avec {current_char}..."):
                        resp_init = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=init_prompt,
                            temperature=0.8,
                        )
                    intro_msg = resp_init.choices[0].message.content
                except Exception:
                    intro_msg = char_data["quote"]
            else:
                intro_msg = char_data["quote"]

        messages.append({"role": "assistant", "content": intro_msg})
        save_msg(str_lit.session_state.pseudo, current_char, "assistant", intro_msg)

    for idx, msg in enumerate(messages):
        if msg["role"] == "assistant":
            col_avatar, col_content, col_actions = str_lit.columns([1, 5, 1])
            with col_avatar:
                str_lit.image(char_data["img"], width=65)
            with col_content:
                str_lit.markdown(f'<div class="novel-dialogue">{msg["content"]}</div>', unsafe_allow_html=True)
                
                edit_key = f"edit_mode_ast_{idx}"
                if edit_key not in str_lit.session_state:
                    str_lit.session_state[edit_key] = False

                if str_lit.session_state[edit_key]:
                    new_text = str_lit.text_area(
                        "Modifier la réponse de l'IA :",
                        value=msg["content"],
                        key=f"textarea_edit_ast_{idx}"
                    )
                    if str_lit.button("💾 Enregistrer", key=f"save_edit_ast_{idx}"):
                        msg["content"] = new_text
                        str_lit.session_state[edit_key] = False
                        cache_key = f"{str_lit.session_state.pseudo}_{current_char}"
                        str_lit.session_state.messages_cache[cache_key] = messages
                        if supabase:
                            try:
                                supabase.table("messages").delete().eq("user_pseudo", str_lit.session_state.pseudo).eq("char_name", current_char).execute()
                                for m in messages:
                                    save_msg(str_lit.session_state.pseudo, current_char, m["role"], m["content"])
                            except Exception:
                                pass
                        str_lit.success("Modifié !")
                        str_lit.rerun()
            with col_actions:
                if str_lit.button("✏️", key=f"btn_edit_ast_{idx}", help="Modifier"):
                    str_lit.session_state[edit_key] = not str_lit.session_state[edit_key]
                    str_lit.rerun()
                if idx == len(messages) - 1 and client:
                    if str_lit.button("🔄", key=f"regen_{idx}", help="Régénérer la réponse"):
                        messages.pop()
                        cache_key = f"{str_lit.session_state.pseudo}_{current_char}"
                        str_lit.session_state.messages_cache[cache_key] = messages
                        if supabase:
                            try:
                                supabase.table("messages").delete().eq("user_pseudo", str_lit.session_state.pseudo).eq("char_name", current_char).order("id", desc=True).limit(1).execute()
                            except Exception:
                                pass
                        
                        user_pseudo = str_lit.session_state.pseudo
                        current_aff = get_affinity(user_pseudo, current_char)
                        aff_context = f" Niveau d'affinité actuel avec Yuna : {current_aff}%."
                        context_reminder = {"role": "system", "content": f"Rappel important : Ton interlocuteur actuel s'appelle {user_pseudo}. Adresse-toi directement à elle au féminin en respectant strictement ton profil d'origine.{aff_context}"}
                        
                        api_messages = [{"role": "system", "content": char_data["prompt"]}, context_reminder] + messages[-20:]
                        
                        try:
                            with str_lit.spinner("Régénération en cours..."):
                                response = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=api_messages,
                                    temperature=0.9,
                                )
                            bot_reply = response.choices[0].message.content
                            messages.append({"role": "assistant", "content": bot_reply})
                            save_msg(user_pseudo, current_char, "assistant", bot_reply)
                        except Exception:
                            pass
                        str_lit.rerun()
        else:
            with str_lit.chat_message("user"):
                str_lit.write(msg["content"])
                
                edit_u_key = f"edit_mode_usr_{idx}"
                if edit_u_key not in str_lit.session_state:
                    str_lit.session_state[edit_u_key] = False

                col_u1, col_u2 = str_lit.columns([1, 5])
                with col_u1:
                    if str_lit.button("✏️", key=f"btn_edit_usr_{idx}", help="Modifier message"):
                        str_lit.session_state[edit_u_key] = not str_lit.session_state[edit_u_key]
                        str_lit.rerun()

                if str_lit.session_state[edit_u_key]:
                    new_u_text = str_lit.text_input("Modifier ton message :", value=msg["content"], key=f"txt_usr_{idx}")
                    if str_lit.button("💾 Valider", key=f"save_usr_{idx}"):
                        msg["content"] = new_u_text
                        str_lit.session_state[edit_u_key] = False
                        cache_key = f"{str_lit.session_state.pseudo}_{current_char}"
                        str_lit.session_state.messages_cache[cache_key] = messages
                        if supabase:
                            try:
                                supabase.table("messages").delete().eq("user_pseudo", str_lit.session_state.pseudo).eq("char_name", current_char).execute()
                                for m in messages:
                                    save_msg(str_lit.session_state.pseudo, current_char, m["role"], m["content"])
                            except Exception:
                                pass
                        str_lit.success("Message modifié !")
                        str_lit.rerun()

    user_input = str_lit.chat_input("Écris ta réponse...")
    if user_input:
        messages.append({"role": "user", "content": user_input})
        save_msg(str_lit.session_state.pseudo, current_char, "user", user_input)
        update_affinity(str_lit.session_state.pseudo, current_char, 2)

        if client:
            user_pseudo = str_lit.session_state.pseudo
            current_aff = get_affinity(user_pseudo, current_char)
            aff_context = f" Niveau d'affinité actuel avec Yuna : {current_aff}%."
            context_reminder = {"role": "system", "content": f"Rappel important : Ton interlocuteur actuel s'appelle {user_pseudo}. Adresse-toi directement à elle au féminin en respectant strictement ton profil d'origine.{aff_context}"}
            
            api_messages = [{"role": "system", "content": char_data["prompt"]}, context_reminder] + messages[-20:]
            
            try:
                with str_lit.spinner(f"{current_char} est en train d'écrire..."):
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=api_messages,
                        temperature=0.85,
                    )
                bot_reply = response.choices[0].message.content
                messages.append({"role": "assistant", "content": bot_reply})
                save_msg(user_pseudo, current_char, "assistant", bot_reply)
            except Exception as e:
                str_lit.error(f"Erreur de génération : {e}")
        str_lit.rerun()

elif str_lit.session_state.page == "create_character":
    str_lit.title("✨ Créer un Personnage")
    str_lit.write("Conçois ton propre personnage personnalisé pour l'intégrer à tes histoires.")
    str_lit.markdown("---")

    with str_lit.form("create_char_form"):
        new_name = str_lit.text_input("Nom du personnage")
        new_quote = str_lit.text_input("Phrase d'accroche (Citation)")
        new_desc = str_lit.text_area("Description / Personnalité / Contexte")
        new_img = str_lit.text_input("URL de l'image (Lien direct)")
        new_vis = str_lit.selectbox("Visibilité", ["Public", "Privé"])

        submitted = str_lit.form_submit_button("Créer le Personnage")
        if submitted:
            if new_name.strip():
                if supabase:
                    try:
                        supabase.table("custom_characters").insert({
                            "name": new_name.strip(),
                            "quote": new_quote,
                            "description": new_desc,
                            "img_url": new_img.strip() if new_img.strip() else DEFAULT_FALLBACK_IMG,
                            "visibility": new_vis,
                            "creator_pseudo": str_lit.session_state.pseudo
                        }).execute()
                        str_lit.cache_data.clear()
                        str_lit.success(f"Le personnage {new_name} a été créé avec succès !")
                        str_lit.session_state.page = "home"
                        str_lit.rerun()
                    except Exception as e:
                        str_lit.error(f"Erreur lors de l'enregistrement : {e}")
                else:
                    str_lit.warning("Supabase n'est pas configuré pour sauvegarder les personnages personnalisés.")
            else:
                str_lit.error("Veuillez donner un nom à votre personnage.")

elif str_lit.session_state.page == "profile":
    str_lit.title("👤 Profil Utilisateur")
    str_lit.write(f"Gestion de ton profil pour le pseudo : **{str_lit.session_state.pseudo}**")
    str_lit.markdown("---")
    str_lit.info("Ici, tu peux retrouver les informations générales de ton compte.")
