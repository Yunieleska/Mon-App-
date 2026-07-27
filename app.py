import io
import os
import re
import requests
import streamlit as str_lit
from supabase import create_client
from groq import Groq
from huggingface_hub import InferenceClient

# --- CONFIGURATION ---
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key and "GROQ_API_KEY" in str_lit.secrets:
    groq_key = str_lit.secrets["GROQ_API_KEY"]

hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
if not hf_api_key and "HUGGINGFACE_API_KEY" in str_lit.secrets:
    hf_api_key = str_lit.secrets["HUGGINGFACE_API_KEY"]

# --- CONSTANTES IMAGES ---
BACKGROUND_IMG_NAME = "bg.png"
SIDEBAR_HEADER_IMG = "couple.png"


def generer_image_huggingface(prompt_image):
    if not hf_api_key:
        return None, "Clé API Hugging Face manquante."
    try:
        client_hf = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell", token=hf_api_key
        )
        image = client_hf.text_to_image(prompt_image)

        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        return buf.getvalue(), None
    except Exception as e:
        return None, f"Erreur Hugging Face : {str(e)}"


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
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- PERSISTANCE PAR URL ---
query_params = str_lit.query_params

if "user" in query_params and query_params["user"]:
    str_lit.session_state.logged_in = True
    str_lit.session_state.pseudo = query_params["user"]
else:
    if "logged_in" not in str_lit.session_state:
        str_lit.session_state.logged_in = False
    if "pseudo" not in str_lit.session_state:
        str_lit.session_state.pseudo = "Invité"

if "page" not in str_lit.session_state:
    str_lit.session_state.page = "home"
if "char_select" not in str_lit.session_state:
    str_lit.session_state.char_select = "Caelum"

# --- SUPABASE FUNCTIONS ---


def save_msg(pseudo, char, role, content):
    if not supabase:
        return
    try:
        clean_pseudo = str(pseudo).strip().lower()
        supabase.table("messages").insert({
            "user_pseudo": clean_pseudo,
            "char_name": str(char),
            "role": str(role),
            "content": str(content),
        }).execute()
    except Exception:
        pass


def load_msgs(pseudo, char):
    if not supabase:
        return []
    try:
        clean_pseudo = str(pseudo).strip().lower()
        res = (
            supabase.table("messages")
            .select("role, content")
            .eq("user_pseudo", clean_pseudo)
            .eq("char_name", str(char))
            .execute()
        )
        if res.data:
            return [{"role": r["role"], "content": r["content"]} for r in res.data]
        return []
    except Exception:
        return []


def get_all_characters():
    base_instruction = (
        " Reste strictement dans ton rôle, adopte un ton immersif de roleplay"
        " romancé. IMPORTANT : À la fin de CHAQUE message, tu dois obligatoirement"
        " intégrer une balise visuelle au format exact suivant pour illustrer"
        " l'action en cours : [IMAGE: description détaillée en anglais de"
        " l'ambiance, du personnage ou du décor]."
    )

    chars = {
        "Caelum": {
            "img": (
                "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
            ),
            "prompt": "Tu es Caelum, Prince des Ténèbres." + base_instruction,
            "quote": (
                "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as"
                " rien à y faire."
            ),
        },
        "Alexei": {
            "img": (
                "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg"
            ),
            "prompt": "Tu es Alexei, mafieux." + base_instruction,
            "quote": (
                "Regardez qui s'est perdue sur mon territoire. La petite princesse"
                " des Volkov..."
            ),
        },
        "Killian": {
            "img": (
                "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg"
            ),
            "prompt": "Tu es Killian, motard." + base_instruction,
            "quote": "Respire, c'est fini... T'as pas changé, toujours aussi maladroite.",
        },
        "Lucas": {
            "img": (
                "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG"
            ),
            "prompt": "Tu es Lucas, populaire." + base_instruction,
            "quote": (
                "On s'esquive tous les deux et on va squatter ton canapé devant"
                " une série ?"
            ),
        },
        "Ethan": {
            "img": (
                "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/ethan.png"
            ),
            "prompt": "Tu es Ethan, Loup Alpha." + base_instruction,
            "quote": (
                "La forêt cache des prédateurs bien plus dangereux que tu ne"
                " l'imagines..."
            ),
        },
        "Léo": {
            "img": (
                "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/leo.png.PNG"
            ),
            "prompt": "Tu es Léo, streameur." + base_instruction,
            "quote": "Prête à ce qu'on détruise l'équipe d'en face ?",
        },
        "Liam": {
            "img": (
                "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/liam.png.PNG"
            ),
            "prompt": "Tu es Liam, le grand frère." + base_instruction,
            "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit.",
        },
        "Noah": {
            "img": (
                "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/noah.png.PNG"
            ),
            "prompt": "Tu es Noah, quarterback star." + base_instruction,
            "quote": "Dis, tu crois qu'on est tous obligés de jouer un rôle pour plaire ?",
        },
    }

    if supabase:
        try:
            res = supabase.table("custom_characters").select("*").execute()
            if res.data:
                for item in res.data:
                    if item.get("is_public", True) or item.get("creator") == str_lit.session_state.pseudo:
                        chars[item["name"]] = {
                            "img": (
                                item["img_url"]
                                if item.get("img_url")
                                and (
                                    item["img_url"].startswith("http")
                                    or os.path.exists(item["img_url"])
                                )
                                else (
                                    "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                                )
                            ),
                            "prompt": (
                                f"Tu es {item['name']}, un personnage"
                                f" {item.get('sex', '')}. Description :"
                                f" {item.get('description', '')}. Personnages secondaires :"
                                f" {item.get('secondary_chars', '')}." + base_instruction
                            ),
                            "quote": (
                                item.get("quote")
                                if item.get("quote")
                                else f"Bonjour, je suis {item['name']}."
                            ),
                        }
        except Exception:
            pass

    return chars


CHARACTERS = get_all_characters()


def get_user_conversations(pseudo):
    if not supabase or not pseudo or pseudo == "Invité":
        return []
    try:
        clean_pseudo = str(pseudo).strip().lower()
        res = (
            supabase.table("messages")
            .select("user_pseudo, char_name")
            .execute()
        )
        chars_met = set()
        if res.data:
            for r in res.data:
                db_pseudo = str(r.get("user_pseudo", "")).strip().lower()
                c_name = r.get("char_name")
                if db_pseudo == clean_pseudo and c_name and c_name in CHARACTERS:
                    chars_met.add(c_name)
        return list(chars_met)
    except Exception:
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
                                .single()
                                .execute()
                            )
                            pseudo_val = (
                                user_data.data["pseudo"]
                                if user_data.data
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
    str_lit.session_state.pseudo = "Invité"
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
                .eq("is_public", True)
                .execute()
            )
            public_custom_names = (
                {item["name"] for item in res_pub.data} if res_pub.data else set()
            )

            for name, data in CHARACTERS.items():
                if name in [
                    "Caelum",
                    "Alexei",
                    "Killian",
                    "Lucas",
                    "Ethan",
                    "Léo",
                    "Liam",
                    "Noah",
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
            img_src = (
                "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
            )

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

elif str_lit.session_state.page == "create_character":
    str_lit.title("✨ Créer un nouveau personnage")
    with str_lit.form("create_char_form"):
        char_name = str_lit.text_input("Nom du personnage")
        char_sex = str_lit.selectbox(
            "Sexe / Genre", ["Homme", "Femme", "Non-binaire", "Autre"]
        )
        char_quote = str_lit.text_input("Phrase d'accroche")
        char_description = str_lit.text_area(
            "Description et Personnalité (Histoire, ton, etc.)"
        )
        char_secondary = str_lit.text_area("Personnages secondaires (Optionnel)")
        uploaded_char_img = str_lit.file_uploader(
            "Image du personnage", type=["png", "jpg", "jpeg"]
        )
        visibility = str_lit.radio(
            "Visibilité", ["Public (toute la communauté)", "Privé"]
        )
        submitted = str_lit.form_submit_button(
            "🚀 Créer", use_container_width=True
        )

        if submitted and char_name and char_description:
            img_path = (
                "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
            )
            if uploaded_char_img is not None:
                img_path = f"char_{str_lit.session_state.pseudo}_{char_name}.png"
                with open(img_path, "wb") as f:
                    f.write(uploaded_char_img.getbuffer())

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
                        "creator": str_lit.session_state.pseudo,
                    }).execute()
                    str_lit.success("Personnage créé avec succès !")
                    str_lit.session_state.page = "profile"
                    str_lit.rerun()
                except Exception as e:
                    str_lit.error(f"Erreur : {e}")

elif str_lit.session_state.page == "messages":
    str_lit.title("Mes Discussions")
    char_names_with_conv = get_user_conversations(str_lit.session_state.pseudo)
    if not char_names_with_conv:
        str_lit.info(
            "Aucune discussion en cours. Choisissez un personnage sur l'accueil !"
        )
    else:
        for char_name in char_names_with_conv:
            if char_name in CHARACTERS:
                col1, col2, col3 = str_lit.columns([1, 4, 1])
                with col1:
                    str_lit.image(CHARACTERS[char_name]["img"], width=85)
                with col2:
                    str_lit.subheader(char_name)
                    str_lit.caption(CHARACTERS[char_name]["quote"])
                with col3:
                    if str_lit.button(f"Ouvrir", key=f"open_msg_{char_name}"):
                        str_lit.session_state.char_select = char_name
                        str_lit.session_state.page = "chat"
                        str_lit.rerun()
                str_lit.markdown("---")

elif str_lit.session_state.page == "profile":
    str_lit.title("Mon Profil")
    if supabase:
        try:
            user_db = (
                supabase.table("users")
                .select("*")
                .eq("pseudo", str_lit.session_state.pseudo)
                .single()
                .execute()
            )
            user_info = user_db.data if user_db.data else {}
            user_id = user_info.get("id")
            avatar_path = user_info.get(
                "avatar_url",
                "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
            )

            col1, col2 = str_lit.columns([1, 3])
            with col1:
                str_lit.image(avatar_path, use_container_width=True)
            with col2:
                str_lit.subheader(str_lit.session_state.pseudo)
                str_lit.write(f"📧 {user_info.get('email', 'N/A')}")

            str_lit.markdown("---")
            uploaded_file = str_lit.file_uploader(
                "Changer votre photo de profil", type=["png", "jpg", "jpeg"]
            )
            if uploaded_file is not None and user_id:
                file_name = f"avatar_{user_id}.png"
                with open(file_name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                supabase.table("users").update({"avatar_url": file_name}).eq(
                    "id", user_id
                ).execute()
                str_lit.success("Photo mise à jour !")
                str_lit.rerun()
        except Exception as e:
            str_lit.error(f"Erreur profil : {e}")

elif str_lit.session_state.page == "chat":
    current_char = str_lit.session_state.char_select
    bg_image = CHARACTERS[current_char]["img"]
    char_quote = CHARACTERS[current_char]["quote"]
    char_prompt = CHARACTERS[current_char]["prompt"]

    user_avatar_url = (
        "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
    )
    if supabase:
        try:
            u_res = (
                supabase.table("users")
                .select("avatar_url")
                .eq("pseudo", str_lit.session_state.pseudo)
                .single()
                .execute()
            )
            if u_res.data and u_res.data.get("avatar_url"):
                user_avatar_url = u_res.data.get("avatar_url")
        except Exception:
            pass

    str_lit.markdown(
        f"""
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
        </style>
    """,
        unsafe_allow_html=True,
    )

    str_lit.markdown(
        f"""
        <div class="chat-header-container">
            <h2 style="margin: 0; color: #ffffff;">Chat avec {current_char}</h2>
            <p style='color: #a0a0a0; font-style: italic; margin: 6px 0 0 0;'>"{char_quote}"</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    messages = load_msgs(str_lit.session_state.pseudo, current_char)

    if not messages and client:
        intro_system_prompt = [{
            "role": "system",
            "content": (
                f"{char_prompt} Commence l'histoire en envoyant un premier message"
                f" d'accroche immersif incluant une [IMAGE: ...]."
            ),
        }]
        try:
            res_intro = client.chat.completions.create(
                model="llama-3.3-70b-versatile", messages=intro_system_prompt
            )
            first_message = res_intro.choices[0].message.content
            save_msg(
                str_lit.session_state.pseudo, current_char, "assistant", first_message
            )
            messages = load_msgs(str_lit.session_state.pseudo, current_char)
        except Exception as e:
            str_lit.error(f"Erreur Groq : {e}")

    char_avatar_url = CHARACTERS[current_char]["img"]

    for idx, msg in enumerate(messages):
        is_user = msg["role"] == "user"
        name_to_use = str_lit.session_state.pseudo if is_user else current_char
        avatar_to_use = user_avatar_url if is_user else char_avatar_url

        with str_lit.container():
            col_av, col_txt = str_lit.columns([1, 11])
            with col_av:
                str_lit.markdown(
                    f"<img src='{avatar_to_use}' style='width: 38px; height: 38px;"
                    " border-radius: 50%; object-fit: cover; margin-top:"
                    " 4px;'>",
                    unsafe_allow_html=True,
                )
            with col_txt:
                str_lit.markdown(
                    f"<b style='color: #ffffff; font-size: 14px;'>{name_to_use}</b>",
                    unsafe_allow_html=True,
                )

                if is_user:
                    str_lit.write(msg["content"])
                else:
                    contenu_message = msg.get("content", "")
                    match_image = re.search(
                        r"\[IMAGE:\s*(.*?)\]", contenu_message, re.IGNORECASE
                    )

                    if match_image:
                        prompt_image = match_image.group(1).strip()
                        texte_propre = contenu_message.replace(
                            match_image.group(0), ""
                        ).strip()
                    else:
                        texte_propre = contenu_message
                        prompt_image = None

                    str_lit.write(texte_propre)

                    if match_image and prompt_image:
                        with str_lit.expander("🖼️ Voir l'illustration de la scène"):
                            with str_lit.spinner(
                                f"🎨 {current_char} génère l'illustration..."
                            ):
                                image_bytes, err_msg = generer_image_huggingface(prompt_image)
                                if image_bytes:
                                    str_lit.image(
                                        image_bytes,
                                        caption=f"Scène - {current_char}",
                                        use_container_width=True,
                                    )
                                else:
                                    str_lit.warning(
                                        f"Impossible de charger l'illustration ({err_msg})."
                                    )

    st_container = str_lit.container()
    with st_container:
        user_input = str_lit.chat_input("Écris ton message...")
        
        if str_lit.button("🎨 Générer l'image de la dernière scène", key="btn_gen_img_direct"):
            if client:
                dernier_prompt_image = (
                    f"Cinematic illustration of {current_char} in a fantasy magic school"
                    f" setting, dramatic lighting, high quality"
                )
                for m in reversed(messages):
                    if m["role"] == "assistant":
                        m_img = re.search(r"\[IMAGE:\s*(.*?)\]", m["content"], re.IGNORECASE)
                        if m_img:
                            dernier_prompt_image = m_img.group(1).strip()
                        break

                with str_lit.spinner(
                    f"🎨 {current_char} génère l'illustration à la volée..."
                ):
                    image_bytes, err_msg = generer_image_huggingface(dernier_prompt_image)
                    if image_bytes:
                        str_lit.image(
                            image_bytes,
                            caption=f"Scène - {current_char}",
                            use_container_width=True,
                        )
                    else:
                        str_lit.error(f"Erreur de génération : {err_msg}")

    if user_input and client:
        save_msg(str_lit.session_state.pseudo, current_char, "user", user_input)

        formatted_history = [{"role": "system", "content": char_prompt}]
        for m in load_msgs(str_lit.session_state.pseudo, current_char):
            formatted_history.append({"role": m["role"], "content": m["content"]})

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", messages=formatted_history
            )
            bot_reply = response.choices[0].message.content
            save_msg(str_lit.session_state.pseudo, current_char, "assistant", bot_reply)
            str_lit.rerun()
        except Exception as e:
            str_lit.error(f"Erreur de communication avec Groq : {e}")
