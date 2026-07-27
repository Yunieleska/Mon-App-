import io
import os
import re
import requests
from PIL import Image
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


def generer_image_huggingface(prompt_image, current_char_name=None):
    if not hf_api_key:
        return None, "Clé API Hugging Face manquante."
    try:
        client_hf = InferenceClient(
            model="stabilityai/stable-diffusion-xl-base-1.0", token=hf_api_key
        )
        
        prompt_final = (
            f"A hyper-realistic cinematic photograph of {current_char_name or 'the character'}. "
            f"Scene details: {prompt_image}. "
            f"RAW photo, highly detailed skin pores, realistic human anatomy, shot on 35mm film, professional photography, cinematic lighting, masterpiece, 8k, photorealistic."
        )

        image = client_hf.text_to_image(prompt_final)

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
        clean_pseudo = str(pseudo).strip()
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
        clean_pseudo = str(pseudo).strip()
        res = (
            supabase.table("messages")
            .select("role, content")
            .eq("user_pseudo", clean_pseudo)
            .eq("char_name", str(char))
            .order("id", desc=True)
            .limit(1000)
            .execute()
        )
        if res.data:
            messages = [{"role": r["role"], "content": r["content"]} for r in res.data]
            return messages[::-1]
        return []
    except Exception:
        return []


def save_to_gallery(pseudo, char_name, img_bytes, prompt):
    if not supabase:
        return
    import base64
    try:
        encoded_img = base64.b64encode(img_bytes).decode('utf-8')
        supabase.table("user_gallery").insert({
            "user_pseudo": str(pseudo).strip(),
            "char_name": str(char_name),
            "image_base64": encoded_img,
            "image_prompt": str(prompt)
        }).execute()
    except Exception:
        pass


def get_all_characters():
    base_instruction = (
        " Reste strictement dans ton rôle, adopte un ton immersif de roleplay"
        " romancé. IMPORTANT : À la fin de CHAQUE message, tu dois obligatoirement"
        " intégrer une balise visuelle au format exact suivant pour illustrer"
        " l'action en cours sous forme de photographie réelle : [IMAGE: description détaillée en anglais de"
        " l'ambiance, du personnage ou du décor, photorealistic shot]."
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
            "prompt": "Tu es Killian, motard." + base_instruction,
            "quote": "Respire, c'est fini... T'as pas changé, toujours aussi maladroite.",
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG",
            "prompt": "Tu es Lucas, populaire." + base_instruction,
            "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série ?",
        },
        "Ethan": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/ethan.png",
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

    if supabase:
        try:
            res = supabase.table("custom_characters").select("*").execute()
            if res.data:
                for item in res.data:
                    c_name = item.get("name")
                    if not c_name:
                        continue
                    
                    desc_val = item.get("description", "")
                    prompt_val = item.get("prompt", f"Tu es {c_name}. {desc_val}")
                    quote_val = item.get("quote", f"Bonjour, je suis {c_name}.")
                    img_url = item.get("img_url", "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg")
                    
                    chars[c_name] = {
                        "img": (
                            img_url
                            if img_url and (img_url.startswith("http") or os.path.exists(img_url))
                            else "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                        ),
                        "prompt": prompt_val + base_instruction,
                        "quote": quote_val,
                    }
        except Exception:
            pass

    return chars


CHARACTERS = get_all_characters()


def get_user_conversations(pseudo):
    if not supabase or not pseudo or pseudo == "Invité":
        return []
    try:
        clean_pseudo = str(pseudo).strip()
        res = (
            supabase.table("messages")
            .select("user_pseudo, char_name")
            .execute()
        )
        chars_met = set()
        if res.data:
            for r in res.data:
                db_pseudo = str(r.get("user_pseudo", "")).strip()
                c_name = r.get("char_name")
                if db_pseudo.lower() == clean_pseudo.lower() and c_name and c_name in CHARACTERS:
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
                .execute()
            )
            public_custom_names = (
                {item["name"] for item in res_pub.data} if res_pub.data else set()
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
            img_src = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

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

    col_h1, col_h2 = str_lit.columns([1, 5])
    with col_h1:
        str_lit.image(char_data["img"], width=80)
    with col_h2:
        str_lit.title(current_char)
        str_lit.caption(char_data["quote"])

    str_lit.markdown("---")

    messages = load_msgs(str_lit.session_state.pseudo, current_char)
    if not messages:
        intro_msg = f"*{char_data['quote']}*"
        messages.append({"role": "assistant", "content": intro_msg})
        save_msg(str_lit.session_state.pseudo, current_char, "assistant", intro_msg)

    for msg in messages:
        with str_lit.chat_message(msg["role"]):
            content = msg["content"]
            match = re.search(r"\[IMAGE:\s*(.*?)\]", content)
            if match:
                img_prompt = match.group(1)
                text_clean = content.replace(match.group(0), "").strip()
                str_lit.write(text_clean)
                with str_lit.spinner("Génération de l'image..."):
                    img_bytes, err = generer_image_huggingface(img_prompt, current_char)
                    if img_bytes:
                        str_lit.image(img_bytes, caption=img_prompt, use_container_width=True)
                        save_to_gallery(str_lit.session_state.pseudo, current_char, img_bytes, img_prompt)
                    else:
                        str_lit.warning(f"Impossible de générer l'image : {err}")
            else:
                str_lit.write(content)

    user_input = str_lit.chat_input("Votre message...")
    if user_input:
        with str_lit.chat_message("user"):
            str_lit.write(user_input)
        save_msg(str_lit.session_state.pseudo, current_char, "user", user_input)
        messages.append({"role": "user", "content": user_input})

        if client:
            try:
                system_prompt = char_data["prompt"]
                api_messages = [{"role": "system", "content": system_prompt}] + messages[-1000:]

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=api_messages,
                    temperature=0.8,
                )
                bot_reply = response.choices[0].message.content
            except Exception as e:
                bot_reply = f"Erreur de communication avec l'IA : {str(e)}"
        else:
            bot_reply = "Client Groq non initialisé."

        with str_lit.chat_message("assistant"):
            match = re.search(r"\[IMAGE:\s*(.*?)\]", bot_reply)
            if match:
                img_prompt = match.group(1)
                text_clean = bot_reply.replace(match.group(0), "").strip()
                str_lit.write(text_clean)
                with str_lit.spinner("Génération de l'image..."):
                    img_bytes, err = generer_image_huggingface(img_prompt, current_char)
                    if img_bytes:
                        str_lit.image(img_bytes, caption=img_prompt, use_container_width=True)
                        save_to_gallery(str_lit.session_state.pseudo, current_char, img_bytes, img_prompt)
                    else:
                        str_lit.warning(f"Impossible de générer l'image : {err}")
            else:
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
            img_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
            if uploaded_char_img is not None:
                img_path = f"char_{str_lit.session_state.pseudo}_{char_name}.png"
                with open(img_path, "wb") as f:
                    f.write(uploaded_char_img.getbuffer())

            if supabase:
                try:
                    built_prompt = f"Tu es {char_name}, un personnage {char_sex}. Description et contexte : {char_description}."

                    insert_data = {
                        "name": char_name,
                        "creator": str_lit.session_state.pseudo,
                        "prompt": built_prompt,
                        "description": char_description,
                        "sex": char_sex,
                        "quote": char_quote if char_quote else f"Bonjour, je suis {char_name}.",
                        "secondary_chars": char_secondary,
                        "img_url": img_path
                    }
                    
                    supabase.table("custom_characters").insert(insert_data).execute()

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
            "Aucune discussion en cours. Choisissez un personnage sur l'accueil !"
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

            following_count = 0
            followers_count = 0
            try:
                following_res = supabase.table("follows").select("id", count="exact").eq("follower_pseudo", str_lit.session_state.pseudo).execute()
                following_count = following_res.count if following_res.count is not None else 0
            except Exception:
                pass

            try:
                followers_res = supabase.table("follows").select("id", count="exact").eq("following_pseudo", str_lit.session_state.pseudo).execute()
                followers_count = followers_res.count if followers_res.count is not None else 0
            except Exception:
                pass

            str_lit.markdown(
                f"""
                <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 25px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <img src="{avatar_path}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(255,255,255,0.2);">
                        <div>
                            <h2 style="margin: 0; color: #ffffff;">{str_lit.session_state.pseudo}</h2>
                            <p style="margin: 4px 0 0 0; color: #8b949e; font-size: 14px;">📧 {user_info.get('email', 'N/A')}</p>
                        </div>
                    </div>
                    <div style="display: flex; gap: 25px; background-color: #0b0e14; padding: 12px 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                        <div style="text-align: center;">
                            <div style="font-size: 18px; font-weight: 700; color: #ffffff;">{followers_count}</div>
                            <div style="font-size: 12px; color: #8b949e;">Abonnés</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 18px; font-weight: 700; color: #ffffff;">{following_count}</div>
                            <div style="font-size: 12px; color: #8b949e;">Abonnements</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            tab_prof1, tab_prof2, tab_prof3, tab_prof4, tab_prof5 = str_lit.tabs([
                "✨ Mes Personnages", 
                "👥 Découvrir & Suivre", 
                "📊 Activité & Stats", 
                "🖼️ Galerie Souvenirs", 
                "⚙️ Paramètres"
            ])

            with tab_prof1:
                str_lit.subheader("Personnages créés")
                chars_res = (
                    supabase.table("custom_characters")
                    .select("*")
                    .eq("creator", str_lit.session_state.pseudo)
                    .execute()
                )
                user_created_chars = chars_res.data if chars_res.data else []

                if not user_created_chars:
                    str_lit.info("Vous n'avez pas encore créé de personnage. Rendez-vous dans l'onglet 'Créer un Personnage' dans le menu latéral !")
                else:
                    for c_item in user_created_chars:
                        c_name = c_item.get("name")
                        c_img = c_item.get("img_url", "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg")
                        c_quote = c_item.get("quote", "")

                        if not c_img.startswith("http") and not os.path.exists(c_img):
                            c_img = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

                        col_c1, col_c2, col_c3 = str_lit.columns([1, 4, 2])
                        with col_c1:
                            str_lit.image(c_img, width=70)
                        with col_c2:
                            str_lit.markdown(f"**{c_name}**", unsafe_allow_html=True)
                            str_lit.caption(f'"{c_quote}"')
                        with col_c3:
                            if str_lit.button("Discuter", key=f"chat_my_char_{c_name}"):
                                str_lit.session_state.char_select = c_name
                                str_lit.session_state.page = "chat"
                                str_lit.rerun()
                            if str_lit.button("Supprimer", key=f"del_my_char_{c_name}"):
                                try:
                                    supabase.table("custom_characters").delete().eq("name", c_name).eq("creator", str_lit.session_state.pseudo).execute()
                                    str_lit.success(f"Personnage '{c_name}' supprimé.")
                                    str_lit.rerun()
                                except Exception as e:
                                    str_lit.error(f"Erreur suppression : {e}")
                        str_lit.markdown("<br>", unsafe_allow_html=True)

            with tab_prof2:
                str_lit.subheader("Communauté - Suivre des utilisateurs")
                try:
                    all_users_res = supabase.table("users").select("pseudo, email").neq("pseudo", str_lit.session_state.pseudo).execute()
                    other_users = all_users_res.data if all_users_res.data else []

                    my_follows_res = supabase.table("follows").select("following_pseudo").eq("follower_pseudo", str_lit.session_state.pseudo).execute()
                    already_following = {item["following_pseudo"] for item in my_follows_res.data} if my_follows_res.data else set()

                    if not other_users:
                        str_lit.info("Aucun autre utilisateur inscrit pour le moment.")
                    else:
                        for u in other_users:
                            u_pseudo = u.get("pseudo")
                            is_following = u_pseudo in already_following

                            col_u1, col_u2 = str_lit.columns([4, 1])
                            with col_u1:
                                str_lit.markdown(f"**{u_pseudo}**")
                            with col_u2:
                                if is_following:
                                    if str_lit.button("Ne plus suivre", key=f"unfollow_{u_pseudo}"):
                                        supabase.table("follows").delete().eq("follower_pseudo", str_lit.session_state.pseudo).eq("following_pseudo", u_pseudo).execute()
                                        str_lit.rerun()
                                else:
                                    if str_lit.button("Suivre", key=f"follow_{u_pseudo}"):
                                        supabase.table("follows").insert({
                                            "follower_pseudo": str_lit.session_state.pseudo,
                                            "following_pseudo": u_pseudo
                                        }).execute()
                                        str_lit.rerun()
                except Exception as e:
                    str_lit.error(f"Erreur : {e}")

            with tab_prof3:
                str_lit.subheader("Statistiques d'activité")
                try:
                    msg_count_res = supabase.table("messages").select("id", count="exact").eq("user_pseudo", str_lit.session_state.pseudo).execute()
                    total_messages = msg_count_res.count if msg_count_res.count is not None else 0

                    gallery_count_res = supabase.table("user_gallery").select("id", count="exact").eq("user_pseudo", str_lit.session_state.pseudo).execute()
                    total_memories = gallery_count_res.count if gallery_count_res.count is not None else 0

                    col_s1, col_s2 = str_lit.columns(2)
                    with col_s1:
                        str_lit.metric("Messages échangés", total_messages)
                    with col_s2:
                        str_lit.metric("Souvenirs en galerie", total_memories)
                except Exception as e:
                    str_lit.error(f"Erreur : {e}")
        except Exception as e:
            str_lit.error(f"Erreur chargement profil : {e}")
