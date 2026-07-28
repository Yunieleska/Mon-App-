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

try:
    client = Groq(api_key=groq_key)
except Exception:
    client = None

try:
    supabase = create_client(
        str_lit.secrets["SUPABASE_URL"], str_lit.secrets["SUPABASE_KEY"]
    )
except Exception:
    supabase = None

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

# --- SUPABASE FUNCTIONS ---

def save_msg(pseudo, char, role, content):
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
            return messages[::-1]
        return []
    except Exception:
        return []


def get_affinity(pseudo, char):
    cache_key = f"{pseudo}_{char}"
    if cache_key in str_lit.session_state.affinities_cache:
        return str_lit.session_state.affinities_cache[cache_key]

    if not supabase:
        return 50
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
            score = 50
            supabase.table("affinities").insert({
                "user_pseudo": str(pseudo).strip(),
                "char_name": str(char),
                "score": 50
            }).execute()
        
        str_lit.session_state.affinities_cache[cache_key] = score
        return score
    except Exception:
        return 50


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
        "N'invente JAMAIS et ne décris JAMAIS l'apparence physique, les vêtements, les cheveux ou le corps de Yuna. "
        "Laisse toujours Yuna libre de décrire son propre physique."
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
        "Killian": {
            "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg",
            "prompt": "Tu es Killian, un homme, le motard. C'est toi qui as sauvé Yuna lors de son grave accident de voiture par le passé." + base_instruction,
            "quote": "Respire, c'est fini... Je t'ai sorti de cette voiture à temps, t'inquiète pas.",
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG",
            "prompt": "Tu es Lucas, un garçon populaire, décontracté et complice. RÈGLE ABSOLUE : Tu n'as jamais sauvé Yuna d'un accident de voiture (c'est le rôle d'un autre personnage). Ton univers est celui d'un lycéen/étudiant populaire, tu proposes simplement de squatter le canapé pour regarder une série ensemble." + base_instruction,
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
            "prompt": "Tu es Noah, quarterback star." + base_instruction,
            "quote": "Dis, tu crois qu'on est tous obligés de jouer un rôle pour plaire ?",
        },
    }

    try:
        supabase_temp = create_client(
            str_lit.secrets["SUPABASE_URL"], str_lit.secrets["SUPABASE_KEY"]
        )
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


def get_user_conversations(pseudo):
    if not supabase or not pseudo or pseudo == "Invité":
        return []
    try:
        clean_pseudo = str(pseudo).strip()
        res = (
            supabase.table("messages")
            .select("char_name")
            .eq("user_pseudo", clean_pseudo)
            .execute()
        )
        chars_met = set()
        if res.data:
            for r in res.data:
                c_name = r.get("char_name")
                if c_name and c_name in CHARACTERS:
                    chars_met.add(c_name)
        return list(chars_met)
    except Exception as e:
        str_lit.error(f"Erreur chargement discussions : {e}")
        return []


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
                    "Caelum", "Alexei", "Killian", "Lucas",
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
                f"Alors que {user_pseudo} marche en ayant les bras chargés de livres, un manque d'attention la fait trébucher et se cogner directement contre lui. "
                f"Le choc est brutal : les livres s'éparpillent lourdement sur le sol carrelé. "
                f"{user_pseudo} relève vivement les yeux pour s'excuser et croise aussitôt un regard d'un bleu glacier perçant, glacial et indifférent.\n\n"
                f"Caelum la regarde de haut, sans un geste pour l'aider à ramasser ses affaires, esquissant un sourire narquois :\n\n"
                f"— Tu devrais regarder où tu mets les pieds, humaine. Ma vie est déjà tracée, et tu n'as rien à y faire."
            )
        else:
            if client:
                try:
                    user_pseudo = str_lit.session_state.pseudo
                    init_prompt = [
                        {"role": "system", "content": char_data["prompt"]},
                        {"role": "user", "content": f"L'utilisateur qui te parle s'appelle {user_pseudo}. Écris un long premier message d'introduction immersif, descriptif et détaillé pour débuter notre roleplay avec {user_pseudo}. Ta phrase d'accroche de référence est : \"{char_data['quote']}\". Mets {user_pseudo} tout de suite dans l'ambiance, décris la scène, tes actions en restant strictement fidèle à ton profil, sans JAMAIS décrire son physique ou ses vêtements."}
                    ]
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
                str_lit.write(msg["content"])
                
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
                # Bouton Régénérer pour le dernier message de l'assistant
                if idx == len(messages) - 1 and client:
                    if str_lit.button("🔄", key=f"regen_{idx}", help="Régénérer la réponse"):
                        messages.pop()
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
                        if supabase:
                            try:
                                supabase.table("messages").delete().eq("user_pseudo", str_lit.session_state.pseudo).eq("char_name", current_char).execute()
                                for m in messages:
                                    save_msg(str_lit.session_state.pseudo, current_char, m["role"], m["content"])
                            except Exception:
                                pass
                        str_lit.rerun()

    str_lit.markdown("""
        <script>
            window.scrollTo(0, document.body.scrollHeight);
        </script>
    """, unsafe_allow_html=True)

    user_input = str_lit.chat_input("Votre message...")
    if user_input:
        with str_lit.chat_message("user"):
            str_lit.write(user_input)
        save_msg(str_lit.session_state.pseudo, current_char, "user", user_input)
        messages.append({"role": "user", "content": user_input})

        typing_placeholder = str_lit.empty()
        typing_placeholder.markdown(f'<div class="typing-indicator">💬 {current_char} est en train d\'écrire...</div>', unsafe_allow_html=True)

        if client:
            try:
                user_pseudo = str_lit.session_state.pseudo
                current_aff = get_affinity(user_pseudo, current_char)
                
                aff_context = f" Niveau d'affinité actuel avec Yuna : {current_aff}%."
                if current_aff < 30:
                    aff_context += " Tu es distant, froid ou méfiant envers elle."
                elif current_aff > 70:
                    aff_context += " Tu es très attaché, chaleureux et complice avec elle."

                context_reminder = {"role": "system", "content": f"Rappel important : Ton interlocuteur actuel s'appelle {user_pseudo}. Adresse-toi directement à elle au féminin en respectant strictement ton profil d'origine.{aff_context}"}
                system_prompt = char_data["prompt"]
                
                api_messages = [{"role": "system", "content": system_prompt}, context_reminder] + messages[-20:]

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=api_messages,
                    temperature=0.8,
                )
                bot_reply = response.choices[0].message.content
                
                update_affinity(user_pseudo, current_char, 1)

            except Exception as e:
                bot_reply = f"Erreur de communication avec l'IA : {str(e)}"
        else:
            bot_reply = "Client Groq non initialisé."

        typing_placeholder.empty()

        col_avatar, col_content = str_lit.columns([1, 6])
        with col_avatar:
            str_lit.image(char_data["img"], width=65)
        with col_content:
            str_lit.write(bot_reply)

        save_msg(str_lit.session_state.pseudo, current_char, "assistant", bot_reply)
        str_lit.rerun()

elif str_lit.session_state.page == "create_character":
    str_lit.title("✨ Créer un nouveau personnage")
    
    str_lit.markdown("""
        <style>
        textarea, input[type="text"] {
            background-color: #21262d !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    char_name = str_lit.text_input("Nom du personnage", key="input_char_name")
    char_sex = str_lit.selectbox(
        "Sexe / Genre", ["Homme", "Femme", "Non-binaire", "Autre"], key="select_char_sex"
    )
    char_quote = str_lit.text_input("Phrase d'accroche", key="input_char_quote")
    
    char_description = str_lit.text_area(
        "Description et Personnalité (Histoire, ton, etc.)", height=150, key="textarea_char_desc"
    )
    char_secondary = str_lit.text_area(
        "Personnages secondaires (Optionnel)", height=100, key="textarea_char_sec"
    )
    
    uploaded_char_img = str_lit.file_uploader(
        "Image du personnage", type=["png", "jpg", "jpeg"], key="uploader_char_img"
    )
    visibility = str_lit.radio(
        "Visibilité", ["Public (toute la communauté)", "Privé"], key="radio_char_vis"
    )
    
    if str_lit.button("🚀 Créer", use_container_width=True, key="btn_submit_char"):
        if char_name and char_description:
            img_path = DEFAULT_FALLBACK_IMG
            if uploaded_char_img is not None:
                img_path = f"char_{str_lit.session_state.pseudo}_{char_name}.png"
                with open(img_path, "wb") as f:
                    f.write(uploaded_char_img.getbuffer())

            if supabase:
                try:
                    built_prompt = f"Tu es {char_name}, un personnage {char_sex}. Description et contexte : {char_description}."

                    vis_val = "Privé" if "Privé" in visibility else "Public"

                    insert_data = {
                        "name": char_name,
                        "creator": str_lit.session_state.pseudo,
                        "prompt": built_prompt,
                        "description": char_description,
                        "sex": char_sex,
                        "quote": char_quote if char_quote else f"Bonjour, je suis {char_name}.",
                        "secondary_chars": char_secondary,
                        "img_url": img_path,
                        "visibility": vis_val
                    }
                    
                    supabase.table("custom_characters").insert(insert_data).execute()
                    
                    get_all_characters_cached.clear()

                    str_lit.success("Personnage créé avec succès !")
                    str_lit.session_state.page = "profile"
                    str_lit.rerun()
                except Exception as e:
                    str_lit.error(f"Erreur Supabase : {e}")
        else:
            str_lit.warning("Veuillez remplir au moins le nom et la description du personnage.")

elif str_lit.session_state.page == "messages":
    str_lit.title("Mes Discussions")
    char_names_with_conv = get_user_conversations(str_lit.session_state.pseudo)
    if not char_names_with_conv:
        str_lit.info(
            "Aucune discussion en cours. Choisissez un personnage sur l'accueil ou depuis votre profil !"
        )
    else:
        for char_name in char_names_with_conv:
            if char_name in CHARACTERS:
                col1, col2, col3, col4 = str_lit.columns([1, 3, 1, 1])
                with col1:
                    str_lit.image(CHARACTERS[char_name]["img"], width=75)
                with col2:
                    str_lit.subheader(char_name)
                    str_lit.caption(CHARACTERS[char_name]["quote"])
                with col3:
                    if str_lit.button(f"Ouvrir", key=f"open_msg_{char_name}"):
                        str_lit.session_state.char_select = char_name
                        str_lit.session_state.page = "chat"
                        str_lit.rerun()
                with col4:
                    if str_lit.button(f"🗑️ Supprimer", key=f"del_conv_{char_name}"):
                        if supabase:
                            try:
                                supabase.table("messages").delete().eq("user_pseudo", str_lit.session_state.pseudo).eq("char_name", char_name).execute()
                                str_lit.success(f"Discussion avec {char_name} supprimée.")
                                str_lit.rerun()
                            except Exception as e:
                                str_lit.error(f"Erreur : {e}")
                str_lit.markdown("---")

elif str_lit.session_state.page == "profile":
    str_lit.title("Mon Profil")
    str_lit.write(f"Pseudo actuel : **{str_lit.session_state.pseudo}**")
    str_lit.info("Gère tes informations et retrouve tes personnages créés ici.")
