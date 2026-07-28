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
    .stButton>button:focus, .stButton>button:active, button[kind="secondary"]:focus, button[kind="secondary"]:active {
        background-color: #21262d !important;
        color: #ffffff !important;
        box-shadow: none !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    textarea, input[type="text"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: #161b22 !important;
    }
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
if "messages_cache" not in str_lit.session_state:
    str_lit.session_state.messages_cache = {}

# --- SUPABASE FUNCTIONS & CACHE ---

def save_msg(pseudo, char, role, content):
    cache_key = f"{pseudo}_{char}"
    if not supabase:
        if cache_key not in str_lit.session_state.messages_cache:
            str_lit.session_state.messages_cache[cache_key] = []
        str_lit.session_state.messages_cache[cache_key].append({"id": None, "role": role, "content": content})
        return
    try:
        clean_pseudo = str(pseudo).strip()
        res = supabase.table("messages").insert({
            "user_pseudo": clean_pseudo,
            "char_name": str(char),
            "role": str(role),
            "content": str(content),
        }).execute()
        
        msg_id = res.data[0]["id"] if res.data and "id" in res.data[0] else None
        
        if cache_key not in str_lit.session_state.messages_cache:
            str_lit.session_state.messages_cache[cache_key] = []
        str_lit.session_state.messages_cache[cache_key].append({"id": msg_id, "role": role, "content": content})
    except Exception:
        pass


def load_msgs(pseudo, char, limit=100):
    cache_key = f"{pseudo}_{char}"
    if cache_key in str_lit.session_state.messages_cache and str_lit.session_state.messages_cache[cache_key]:
        return str_lit.session_state.messages_cache[cache_key]

    if not supabase:
        return str_lit.session_state.messages_cache.get(cache_key, [])
    try:
        clean_pseudo = str(pseudo).strip()
        res = (
            supabase.table("messages")
            .select("id, role, content")
            .eq("user_pseudo", clean_pseudo)
            .eq("char_name", str(char))
            .order("id", desc=False)
            .limit(limit)
            .execute()
        )
        if res.data:
            messages = []
            seen_contents = set()
            for r in res.data:
                content = r["content"]
                if content not in seen_contents or r["role"] != "assistant":
                    messages.append({"id": r["id"], "role": r["role"], "content": content})
                    if r["role"] == "assistant":
                        seen_contents.add(content)
                else:
                    try:
                        supabase.table("messages").delete().eq("id", r["id"]).execute()
                    except:
                        pass

            str_lit.session_state.messages_cache[cache_key] = messages
            return messages
        
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
    chars = {
        "Caelum": {
            "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
            "prompt": "Tu es Caelum, Prince des Ténèbres. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique, les vêtements, les cheveux ou le corps de l'utilisateur sans qu'il en ait parlé explicitement.",
            "quote": "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as rien à y faire.",
        },
        "Alexei": {
            "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg",
            "prompt": "Tu es Alexei, mafieux. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique, les vêtements, les cheveux ou le corps de l'utilisateur sans qu'il en ait parlé explicitement.",
            "quote": "Regardez qui s'est perdue sur mon territoire. La petite princesse des Volkov...",
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG",
            "prompt": "Tu es Lucas, un garçon populaire, décontracté et complice. Ton univers est celui d'un lycéen/étudiant populaire. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique de l'utilisateur.",
            "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série ?",
        },
        "Ethan": {
            "img": "https://raw.githubusercontent.com/Yunieleska/Mon-App-/main/Ethan.png",
            "prompt": "Tu es Ethan, Loup Alpha. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. RÈGLE CRUCIALE POUR LE PREMIER MESSAGE : Tu ne connais pas encore le prénom de l'interlocutrice (qui est une étrangère ou une inconnue qui croise ton chemin dans la forêt). Ne l'appelle SURTOUT PAS par son prénom dans ton premier message. N'invente jamais l'apparence physique de l'utilisateur.",
            "quote": "La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines...",
        },
        "Léo": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/leo.png.PNG",
            "prompt": "Tu es Léo, streameur et coéquipier de jeux. Ton univers est celui de l'esport et du gaming compétitif. Reste strictement dans ton rôle, adopte un ton immersif de roleplay. RÈGLE CRUCIALE : Tes messages doivent se concentrer exclusivement sur l'action en cours, le jeu, la stratégie d'équipe, les écrans et la compétition. Ne fais JAMAIS référence à des éléments extérieurs ou sans rapport avec l'histoire (pas de mentions déplacées ou incohérentes avec l'univers du gaming). N'invente JAMAIS et ne décris JAMAIS l'apparence physique de l'utilisateur.",
            "quote": "Prête à ce qu'on détruise l'équipe d'en face ?",
        },
        "Liam": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/liam.png.PNG",
            "prompt": "Tu es Liam, le grand frère. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique de l'utilisateur.",
            "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit.",
        },
        "Noah": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/noah.png.PNG",
            "prompt": "Tu es Noah, le quaterback star et le garçon le plus populaire du lycée. Tu parles par SMS de manière anonyme avec une fille mystérieuse. Dans la vraie vie, au lycée, tu es distant et inaccessible. Tu ignores qu'elle est ta correspondante secrète. Ne décris jamais les actions ou les pensées de l'utilisateur.",
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
                    
                    if c_name == "Lord Valerian Vance":
                        img_url = "https://i.ibb.co/Cstfcz6S/image.png"
                    else:
                        img_url = item.get("img_url", DEFAULT_FALLBACK_IMG)
                    
                    chars[c_name] = {
                        "img": img_url if img_url and (img_url.startswith("http") or os.path.exists(img_url)) else DEFAULT_FALLBACK_IMG,
                        "prompt": prompt_val + " Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé.",
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
str_lit.sidebar.markdown("<br>", unsafe_allow_html=True)

if str_lit.sidebar.button("🕯️ Sanctuaire (Home)"):
    str_lit.session_state.page = "home"
    str_lit.rerun()

if str_lit.sidebar.button("🖋️ Invoquer (Créer)"):
    str_lit.session_state.page = "create_character"
    str_lit.rerun()

if str_lit.sidebar.button("📜 Correspondances"):
    str_lit.session_state.page = "messages"
    str_lit.rerun()

if str_lit.sidebar.button("🪞 Mon Ombre (Profil)"):
    str_lit.session_state.page = "profile"
    str_lit.rerun()

str_lit.sidebar.markdown("---")
if str_lit.sidebar.button("🚪 S'échapper (Logout)"):
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
            res_pub = supabase.table("custom_characters").select("*").execute()
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

    total_pages = max(1, (len(public_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    str_lit.session_state.home_page = min(str_lit.session_state.home_page, total_pages - 1)

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
                <img src="{img_src}" onerror="this.onerror=null; this.src='{DEFAULT_FALLBACK_IMG}';" style="width: 100%; height: 140px; object-fit: cover; display: block;">
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
                    for i, c_name in enumerate(active_chars):
                        c_data = CHARACTERS.get(c_name, {"img": DEFAULT_FALLBACK_IMG, "quote": "Discussion en cours..."})
                        
                        str_lit.markdown(f"""
                        <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; align-items: center; gap: 15px;">
                            <img src="{c_data['img']}" onerror="this.onerror=null; this.src='{DEFAULT_FALLBACK_IMG}';" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">
                            <div style="flex-grow: 1;">
                                <div style="font-weight: 700; font-size: 16px; color: #ffffff;">{c_name}</div>
                                <div style="font-size: 12px; color: #8b949e; font-style: italic; margin-bottom: 2px;">Affinité : {get_affinity(clean_pseudo, c_name)}%</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        b_col1, b_col2 = str_lit.columns(2)
                        with b_col1:
                            if str_lit.button(f"Reprendre", key=f"resume_{c_name}_{i}"):
                                str_lit.session_state.char_select = c_name
                                str_lit.session_state.page = "chat"
                                str_lit.rerun()
                        with b_col2:
                            if str_lit.button(f"🗑️ Supprimer", key=f"del_{c_name}_{i}"):
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
                        str_lit.markdown("---")
                else:
                    str_lit.info("Vous n'avez pas encore de conversations en cours. Allez dans l'Accueil pour commencer une histoire !")
            else:
                str_lit.info("Aucun historique de message trouvé pour l'instant.")
        except Exception as e:
            str_lit.error(f"Erreur lors du chargement des messages : {e}")

elif str_lit.session_state.page == "chat":
    current_char = str_lit.session_state.char_select
    char_data = CHARACTERS.get(current_char, {"img": DEFAULT_FALLBACK_IMG, "quote": "", "prompt": f"Tu es {current_char}."})

    col_h1, col_h2, col_h3, col_h4 = str_lit.columns([1, 3, 2, 1.5])
    with col_h1:
        str_lit.image(char_data["img"], width=70)
    with col_h2:
        str_lit.title(current_char)
        str_lit.caption(char_data["quote"])
    with col_h3:
        affinity_score = get_affinity(str_lit.session_state.pseudo, current_char)
        str_lit.markdown("### 💖 Affinité")
        str_lit.progress(affinity_score / 100.0, text=f"{affinity_score}%")
    with col_h4:
        str_lit.write("")
        if str_lit.button("🗑️ Tout effacer", key="btn_delete_chat_page", help="Effacer toute la discussion"):
            clean_pseudo = str(str_lit.session_state.pseudo).strip()
            if supabase:
                try:
                    supabase.table("messages").delete().eq("user_pseudo", clean_pseudo).eq("char_name", current_char).execute()
                    supabase.table("affinities").delete().eq("user_pseudo", clean_pseudo).eq("char_name", current_char).execute()
                except Exception:
                    pass
            
            cache_key = f"{clean_pseudo}_{current_char}"
            if cache_key in str_lit.session_state.messages_cache:
                del str_lit.session_state.messages_cache[cache_key]
            if cache_key in str_lit.session_state.affinities_cache:
                del str_lit.session_state.affinities_cache[cache_key]
                
            str_lit.success("Conversation réinitialisée !")
            str_lit.rerun()

    str_lit.markdown("---")

    # Chargement de l'historique
    messages = load_msgs(str_lit.session_state.pseudo, current_char, limit=50)

    # Génération du premier message unique si la conversation est vide
    if not messages:
        if current_char == "Caelum":
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
                    user_current_pseudo = str_lit.session_state.pseudo
                    init_prompt = [
                        {"role": "system", "content": char_data["prompt"] + f" RÈGLE ABSOLUE POUR CE PREMIER MESSAGE : Tu ne connais PAS encore le prénom de l'interlocutrice. Il est strictement interdit d'utiliser le prénom '{user_current_pseudo}' ou n'importe quel autre prénom. Utilise des termes neutres ('tu', 'l'étrangère', 'cette personne')."},
                        {"role": "user", "content": f"Écris un premier message d'introduction immersif et détaillé pour débuter le roleplay. CONSIGNE D'ACCROCHE : Intègre naturellement la phrase \"{char_data['quote']}\". Décris le décor et la situation. INTERDICTION FORMELLE d'inclure le prénom {user_current_pseudo}."}
                    ]
                    with str_lit.spinner(f"Génération de l'introduction avec {current_char}..."):
                        resp_init = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=init_prompt,
                            temperature=0.7,
                        )
                    intro_msg = resp_init.choices[0].message.content
                    intro_msg = intro_msg.replace(user_current_pseudo, "tu").replace(user_current_pseudo.lower(), "tu")
                except Exception:
                    intro_msg = char_data["quote"]
            else:
                intro_msg = char_data["quote"]

        save_msg(str_lit.session_state.pseudo, current_char, "assistant", intro_msg)
        messages = load_msgs(str_lit.session_state.pseudo, current_char, limit=50)

    # Affichage des messages
    for idx, msg in enumerate(messages):
        msg_id = msg.get("id")
        
        if msg["role"] == "assistant":
            col_avatar, col_content, col_actions = str_lit.columns([1, 5, 1.2])
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
                        if supabase and msg_id:
                            try:
                                supabase.table("messages").update({"content": new_text}).eq("id", msg_id).execute()
                            except Exception:
                                pass
                        str_lit.success("Modifié !")
                        str_lit.rerun()
            with col_actions:
                if str_lit.button("❌", key=f"del_msg_{idx}", help="Supprimer ce message"):
                    messages.pop(idx)
                    cache_key = f"{str_lit.session_state.pseudo}_{current_char}"
                    str_lit.session_state.messages_cache[cache_key] = messages
                    if supabase and msg_id:
                        try:
                            supabase.table("messages").delete().eq("id", msg_id).execute()
                        except Exception:
                            pass
                    str_lit.rerun()

                if str_lit.button("✏️", key=f"btn_edit_ast_{idx}", help="Modifier"):
                    str_lit.session_state[edit_key] = not str_lit.session_state[edit_key]
                    str_lit.rerun()
                    
                if idx == len(messages) - 1 and client:
                    if str_lit.button("🔄", key=f"regen_{idx}", help="Régénérer la réponse"):
                        messages.pop()
                        cache_key = f"{str_lit.session_state.pseudo}_{current_char}"
                        str_lit.session_state.messages_cache[cache_key] = messages
                        
                        if supabase and msg_id:
                            try:
                                supabase.table("messages").delete().eq("id", msg_id).execute()
                            except Exception:
                                pass
                        
                        user_pseudo = str_lit.session_state.pseudo
                        current_aff = get_affinity(user_pseudo, current_char)
                        aff_context = f" Niveau d'affinité actuel : {current_aff}%."
                        context_reminder = {"role": "system", "content": f"Rappel important : Le prénom de l'utilisatrice est {user_pseudo} (à n'utiliser que s'ils se connaissent déjà).{aff_context}"}
                        
                        api_messages = [{"role": "system", "content": char_data["prompt"]}, context_reminder] + messages[-20:]
                        
                        try:
                            with str_lit.spinner("Régénération en cours..."):
                                response = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=api_messages,
                                    temperature=0.9,
                                )
                            bot_reply = response.choices[0].message.content
                            save_msg(user_pseudo, current_char, "assistant", bot_reply)
                            if cache_key in str_lit.session_state.messages_cache:
                                del str_lit.session_state.messages_cache[cache_key]
                        except Exception:
                            pass
                        str_lit.rerun()
        else:
            with str_lit.chat_message("user"):
                str_lit.write(msg["content"])
                
                edit_u_key = f"edit_mode_usr_{idx}"
                if edit_u_key not in str_lit.session_state:
                    str_lit.session_state[edit_u_key] = False

                col_u1, col_u2, col_u3 = str_lit.columns([1, 1, 4])
                with col_u1:
                    if str_lit.button("❌", key=f"del_usr_msg_{idx}", help="Supprimer ce message"):
                        messages.pop(idx)
                        cache_key = f"{str_lit.session_state.pseudo}_{current_char}"
                        str_lit.session_state.messages_cache[cache_key] = messages
                        if supabase and msg_id:
                            try:
                                supabase.table("messages").delete().eq("id", msg_id).execute()
                            except Exception:
                                pass
                        str_lit.rerun()
                with col_u2:
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
                        if supabase and msg_id:
                            try:
                                supabase.table("messages").update({"content": new_u_text}).eq("id", msg_id).execute()
                            except Exception:
                                pass
                        str_lit.success("Message modifié !")
                        str_lit.rerun()

    # --- ZONE DE SAISIE MULTILIGNE ---
    with str_lit.form(key="chat_input_form", clear_on_submit=True):
        user_input = str_lit.text_area("Écris ta réponse (appuie sur Entrée pour aller à la ligne)...", key="user_message_input", height=90)
        submitted_user = str_lit.form_submit_button("Envoyer 🚀")

        if submitted_user and user_input.strip():
            save_msg(str_lit.session_state.pseudo, current_char, "user", user_input.strip())
            update_affinity(str_lit.session_state.pseudo, current_char, 2)
            
            cache_key = f"{str_lit.session_state.pseudo}_{current_char}"
            if cache_key in str_lit.session_state.messages_cache:
                del str_lit.session_state.messages_cache[cache_key]

            if client:
                user_pseudo = str_lit.session_state.pseudo
                current_aff = get_affinity(user_pseudo, current_char)
                aff_context = f" Niveau d'affinité actuel : {current_aff}%."
                context_reminder = {"role": "system", "content": f"Rappel important : L'interlocutrice s'appelle {user_pseudo}. Tu peux maintenant l'appeler par son prénom si le contexte s'y prête.{aff_context}"}
                
                messages_actuels = load_msgs(user_pseudo, current_char, limit=50)
                api_messages = [{"role": "system", "content": char_data["prompt"]}, context_reminder] + messages_actuels[-20:]
                
                try:
                    with str_lit.spinner(f"{current_char} est en train d'écrire..."):
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=api_messages,
                            temperature=0.85,
                        )
                    bot_reply = response.choices[0].message.content
                    save_msg(user_pseudo, current_char, "assistant", bot_reply)
                    if cache_key in str_lit.session_state.messages_cache:
                        del str_lit.session_state.messages_cache[cache_key]
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
                    str_lit.warning("Supabase n'est pas configuré.")
            else:
                str_lit.error("Veuillez donner un nom à votre personnage.")

elif str_lit.session_state.page == "profile":
    str_lit.title("👤 Profil Utilisateur")
    str_lit.write(f"Ton sanctuaire personnel, **{str_lit.session_state.pseudo}**.")
    str_lit.markdown("---")

    user_email = "Non disponible"
    avatar_url = "https://cdn-icons-png.flaticon.com/512/847/847969.png"

    if supabase:
        try:
            res = supabase.table("users").select("*").eq("pseudo", str_lit.session_state.pseudo).maybe_single().execute()
            if res and res.data:
                user_email = res.data.get("email", "Non renseigné")
                avatar_url = res.data.get("avatar_url", avatar_url)
        except Exception:
            pass

    # --- BANNIÈRE & PROFIL DARK ROMANCE ---
    str_lit.markdown(f"""
    <div style="background: linear-gradient(135deg, #1f1a24 0%, #0d1117 100%); border: 1px solid rgba(210, 153, 234, 0.2); border-radius: 16px; padding: 25px; margin-bottom: 25px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 25px;">
        <img src="{avatar_url}" style="width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 2px solid #d299ea; box-shadow: 0 0 15px rgba(210,153,234,0.3);">
        <div>
            <h2 style="margin: 0 0 5px 0; color: #f0f6fc; font-family: 'Georgia', serif;">{str_lit.session_state.pseudo}</h2>
            <p style="margin: 0; color: #8b949e; font-size: 14px;">Membre des ombres • E-mail : {user_email}</p>
            <span style="display: inline-block; margin-top: 8px; background-color: rgba(210, 153, 234, 0.1); color: #d299ea; padding: 2px 10px; border-radius: 12px; font-size: 11px; border: 1px solid rgba(210, 153, 234, 0.3);">Lecteur / Rôle-playeur</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- SECTION 2 : PERSONNAGES CRÉÉS & ACTIONS ---
    str_lit.subheader("🖤 Mes Créations ténébreuses")
    if supabase:
        try:
            my_chars_res = supabase.table("custom_characters").select("*").execute()

            if my_chars_res and my_chars_res.data and len(my_chars_res.data) > 0:
                cols = str_lit.columns(4)
                for i, char in enumerate(my_chars_res.data):
                    with cols[i % 4]:
                        c_name_val = char.get("name")
                        if c_name_val == "Lord Valerian Vance":
                            c_img = "https://i.ibb.co/Cstfcz6S/image.png"
                        else:
                            c_img = char.get("img_url", "")
                            if not c_img or not c_img.startswith("http"):
                                c_img = DEFAULT_FALLBACK_IMG
                            
                        vis_status = char.get('visibility', 'Public')
                        badge_color = "#ff7b72" if vis_status == "Privé" else "#3fb950"
                            
                        str_lit.markdown(f"""
                        <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 10px; transition: transform 0.2s;">
                            <img src="{c_img}" onerror="this.onerror=null; this.src='{DEFAULT_FALLBACK_IMG}';" style="width: 100%; height: 130px; object-fit: cover; border-radius: 8px; margin-bottom: 8px;">
                            <strong style="color: #ffffff; font-size: 14px; display: block; margin-bottom: 4px;">{c_name_val}</strong>
                            <span style="font-size: 10px; color: {badge_color}; background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1);">● {vis_status}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if str_lit.button(f"💬 Discuter", key=f"chat_my_char_{i}"):
                            str_lit.session_state.char_select = c_name_val
                            str_lit.session_state.page = "chat"
                            str_lit.rerun()

                        if str_lit.button(f"🗑️ Supprimer", key=f"del_char_db_{i}"):
                            try:
                                supabase.table("custom_characters").delete().eq("name", c_name_val).execute()
                                supabase.table("messages").delete().eq("char_name", c_name_val).execute()
                                supabase.table("affinities").delete().eq("char_name", c_name_val).execute()
                                str_lit.cache_data.clear()
                                str_lit.success(f"Personnage {c_name_val} supprimé !")
                                str_lit.rerun()
                            except Exception as e:
                                str_lit.error(f"Erreur : {e}")
            else:
                str_lit.info("Aucun personnage ténébreux créé pour l'instant.")
        except Exception as e:
            str_lit.error(f"Erreur lors du chargement de tes personnages : {e}")
    else:
        str_lit.warning("Connexion à la base de données requise.")

    str_lit.markdown("<br>", unsafe_allow_html=True)

    # --- SECTION 3 : STATISTIQUES ---
    str_lit.subheader("📊 Grimoire de statistiques")
    if supabase:
        try:
            clean_pseudo = str(str_lit.session_state.pseudo).strip()
            res_msg = supabase.table("messages").select("char_name").eq("user_pseudo", clean_pseudo).execute()
            if res_msg.data:
                nb_convs = len(set([item["char_name"] for item in res_msg.data if item.get("char_name")]))
                str_lit.markdown(f"""
                <div style="background-color: #161b22; border: 1px solid rgba(210, 153, 234, 0.15); border-radius: 12px; padding: 15px; color: #c9d1d9;">
                    ✨ Histoires passionnelles en cours : <b style="color: #d299ea;">{nb_convs}</b>
                </div>
                """, unsafe_allow_html=True)
            else:
                str_lit.info("Ton grimoire est encore vierge. Lance une conversation pour commencer.")
        except Exception:
            str_lit.info("Impossible de charger les statistiques pour le moment.")
    else:
        str_lit.info("Mode hors-ligne : statistiques non disponibles.")
