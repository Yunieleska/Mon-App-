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
        supabase.table("messages").insert({
            "user_pseudo": str(pseudo),
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
        res = (
            supabase.table("messages")
            .select("role, content")
            .eq("user_pseudo", str(pseudo))
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
        res = (
            supabase.table("messages")
            .select("char_name")
            .eq("user_pseudo", str(pseudo))
            .execute()
        )
        chars_met = set()
        if res.data:
            for r in res.data:
                c_name = r.get("char_name")
                if c_name and c_name in CHARACTERS:
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
    str_lit.session_state.page = "create"
    str_lit.rerun()

if str_lit.sidebar.button("💬 Messages"):
    str_lit.session_state.page = "messages"
    str_lit.rerun()

if str_lit.sidebar.button("👤 Profil"):
    str_lit.session_state.page = "profile"
    str_lit.rerun()

if str_lit.sidebar.button("🚪 Logout"):
    str_lit.session_state.logged_in = False
    str_lit.session_state.pseudo = "Invité"
    str_lit.query_params.clear()
    str_lit.rerun()

# --- ROUTAGE DES PAGES ---
page = str_lit.session_state.get("page", "home")

if page == "home":
    str_lit.title("Explorer")
    str_lit.write("Découvre et discute avec les personnages du moment :")

    cols = str_lit.columns(4)
    idx = 0
    for name, data in CHARACTERS.items():
        with cols[idx % 4]:
            str_lit.markdown(
                f"""
                <div class="storyia-card">
                    <img src="{data['img']}" style="width:100%; height:220px; object-fit:cover;">
                    <div style="padding: 12px;">
                        <b style="font-size: 1.1em;">{name}</b>
                        <p style="font-size: 0.85em; color: #8b949e; margin-top: 5px; margin-bottom: 15px;">"{data['quote']}"</p>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )
            if str_lit.button(f"Discuter", key=f"btn_chat_{name}"):
                str_lit.session_state.char_select = name
                str_lit.session_state.page = "chat"
                str_lit.rerun()
        idx += 1

elif page == "chat":
    char_name = str_lit.session_state.get("char_select", "Caelum")
    char_data = CHARACTERS.get(char_name, list(CHARACTERS.values())[0])

    col_h1, col_h2 = str_lit.columns([1, 6])
    with col_h1:
        if str_lit.button("← Retour"):
            str_lit.session_state.page = "home"
            str_lit.rerun()
    with col_h2:
        str_lit.title(f"Discussion avec {char_name}")

    if "messages_cache" not in str_lit.session_state:
        str_lit.session_state.messages_cache = load_msgs(
            str_lit.session_state.pseudo, char_name
        )

    msgs = str_lit.session_state.messages_cache
    if not msgs:
        init_msg = f"*{char_data['quote']}*"
        msgs.append({"role": "assistant", "content": init_msg})
        save_msg(str_lit.session_state.pseudo, char_name, "assistant", init_msg)

    for m in msgs:
        with str_lit.chat_message(m["role"]):
            content = m["content"]
            match = re.search(r"\[IMAGE:\s*(.*?)\]", content)
            if match:
                img_prompt = match.group(1)
                clean_text = re.sub(r"\[IMAGE:\s*.*?\]", "", content).strip()
                str_lit.write(clean_text)
                with str_lit.spinner("Génération de l'illustration..."):
                    img_bytes, err = generer_image_huggingface(img_prompt)
                    if img_bytes:
                        str_lit.image(img_bytes, use_container_width=True)
                    else:
                        str_lit.caption(f"(Impossible de générer l'image)")
            else:
                str_lit.write(content)

    if user_prompt := str_lit.chat_input("Écris ton message..."):
        msgs.append({"role": "user", "content": user_prompt})
        save_msg(str_lit.session_state.pseudo, char_name, "user", user_prompt)
        with str_lit.chat_message("user"):
            str_lit.write(user_prompt)

        if client:
            history = [{"role": m["role"], "content": m["content"]} for m in msgs]
            system_prompt = char_data["prompt"]
            messages_payload = [{"role": "system", "content": system_prompt}] + history

            with str_lit.chat_message("assistant"):
                with str_lit.spinner(f"{char_name} est en train d'écrire..."):
                    try:
                        completion = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages_payload,
                            temperature=0.8,
                        )
                        reply = completion.choices[0].message.content
                        msgs.append({"role": "assistant", "content": reply})
                        save_msg(
                            str_lit.session_state.pseudo, char_name, "assistant", reply
                        )

                        match = re.search(r"\[IMAGE:\s*(.*?)\]", reply)
                        if match:
                            img_prompt = match.group(1)
                            clean_text = re.sub(
                                r"\[IMAGE:\s*.*?\]", "", reply
                            ).strip()
                            str_lit.write(clean_text)
                            img_bytes, err = generer_image_huggingface(
                                img_prompt
                            )
                            if img_bytes:
                                str_lit.image(
                                    img_bytes, use_container_width=True
                                )
                        else:
                            str_lit.write(reply)
                    except Exception as e:
                        str_lit.error(fErreur API : {e}")

elif page == "create":
    str_lit.title("✨ Créer un Personnage")
    with str_lit.form("create_char_form"):
        c_name = str_lit.text_input("Nom du personnage")
        c_sex = str_lit.selectbox("Genre", ["Masculin", "Féminin", "Autre"])
        c_desc = str_lit.text_area("Description / Personnalité")
        c_quote = str_lit.text_input("Phrase d'accroche (Quote)")
        c_img = str_lit.text_input("URL de l'image du personnage")
        c_public = str_lit.checkbox("Rendre public pour tous les utilisateurs", value=True)

        submitted = str_lit.form_submit_button("Créer le personnage")
        if submitted:
            if supabase and c_name:
                try:
                    supabase.table("custom_characters").insert({
                        "name": c_name,
                        "sex": c_sex,
                        "description": c_desc,
                        "quote": c_quote,
                        "img_url": c_img,
                        "is_public": c_public,
                        "creator": str_lit.session_state.pseudo,
                    }).execute()
                    str_lit.success("Personnage créé avec succès !")
                except Exception as e:
                    str_lit.error(f"Erreur : {e}")

elif page == "messages":
    str_lit.title("💬 Mes Conversations")
    convs = get_user_conversations(str_lit.session_state.pseudo)
    if not convs:
        str_lit.write("Tu n'as pas encore de conversations en cours.")
    else:
        for c in convs:
            if str_lit.button(f"Reprendre avec {c}"):
                str_lit.session_state.char_select = c
                str_lit.session_state.page = "chat"
                str_lit.rerun()

elif page == "profile":
    str_lit.title("👤 Mon Profil")
    str_lit.write(f"Pseudo : **{str_lit.session_state.pseudo}**")
