import streamlit as str_lit
from supabase import create_client
from groq import Groq
import os
import requests
import re

# --- CONFIGURATION ---
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key and "GROQ_API_KEY" in str_lit.secrets:
    groq_key = str_lit.secrets["GROQ_API_KEY"]

hf_key = os.getenv("HUGGINGFACE_API_KEY")
if not hf_key and "HUGGINGFACE_API_KEY" in str_lit.secrets:
    hf_key = str_lit.secrets["HUGGINGFACE_API_KEY"]

try:
    client = Groq(api_key=groq_key)
except Exception:
    client = None

try:
    supabase = create_client(str_lit.secrets["SUPABASE_URL"], str_lit.secrets["SUPABASE_KEY"])
except Exception:
    supabase = None

str_lit.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- STYLE GLOBAL & CORRECTIONS VISUELLES ---
str_lit.markdown("""
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
    .stButton>button, button[kind="secondary"], button[kind="primary"], div.stFormSubmitButton > button {
        background-color: #21262d !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        width: 100%;
    }
    .stButton>button:hover, button[kind="secondary"]:hover, button[kind="primary"]:hover, div.stFormSubmitButton > button:hover {
        background-color: #30363d !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
    }
    .stButton>button p, div.stFormSubmitButton > button p {
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
""", unsafe_allow_html=True)

# --- FONCTION DE GÉNÉRATION D'IMAGE GRATUITE (Hugging Face) ---
def generate_chat_image(prompt_text):
    if not hf_key:
        return None
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {hf_key}"}
    payload = {"inputs": prompt_text}
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            img_path = "temp_generated_img.png"
            with open(img_path, "wb") as f:
                f.write(response.content)
            return img_path
    except Exception:
        pass
    return None

# --- PERSISTANCE PAR URL (ANTI-RESET STREAMLIT) ---
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

# --- SUPABASE FUNCTIONS SÉCURISÉES ---
def save_msg(pseudo, char, role, content, image_url=None):
    if not supabase:
        return
    try:
        supabase.table("messages").insert({
            "user_pseudo": str(pseudo), 
            "char_name": str(char), 
            "role": str(role), 
            "content": str(content),
            "image_url": str(image_url) if image_url else None
        }).execute()
    except Exception:
        pass

def load_msgs(pseudo, char):
    if not supabase:
        return []
    try:
        res = supabase.table("messages").select("role, content, image_url").eq("user_pseudo", str(pseudo)).eq("char_name", str(char)).execute()
        if res.data:
            return [{"role": r["role"], "content": r["content"], "image_url": r.get("image_url")} for r in res.data]
        return []
    except Exception:
        return []

def get_all_characters():
    base_instructions = " Tu es dans une discussion immersive de roleplay. Si la situation s'y prête (action marquante, paysage, selfie ou expression forte), tu peux ajouter à la toute fin de ton message une balise au format exact suivant pour envoyer une photo : [IMAGE: description en anglais de ce qu'on doit voir]. N'utilise cette balise qu'occasionnellement."
    
    chars = {
        "Caelum": {
            "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", 
            "prompt": "Tu es Caelum, Prince des Ténèbres. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as rien à y faire."
        },
        "Alexei": {
            "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", 
            "prompt": "Tu es Alexei, mafieux. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "Regardez qui s'est perdue sur mon territoire. La petite princesse des Volkov..."
        },
        "Killian": {
            "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", 
            "prompt": "Tu es Killian, motard. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "Respire, c'est fini... T'as pas changé, toujours aussi maladroite."
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG", 
            "prompt": "Tu es Lucas, populaire. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série ?"
        },
        "Ethan": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/ethan.png", 
            "prompt": "Tu es Ethan, Loup Alpha. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines..."
        },
        "Léo": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/leo.png.PNG", 
            "prompt": "Tu es Léo, streameur. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "Prête à ce qu'on détruise l'équipe d'en face ?"
        },
        "Liam": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/liam.png.PNG", 
            "prompt": "Tu es Liam, le grand frère. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit."
        },
        "Noah": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/noah.png.PNG", 
            "prompt": "Tu es Noah, quarterback star. Reste strictement dans ton rôle, adopte un ton immersif de roleplay." + base_instructions,
            "quote": "Dis, tu crois qu'on est tous obligés de jouer un rôle pour plaire ?"
        }
    }
    
    if supabase:
        try:
            res = supabase.table("custom_characters").select("*").execute()
            if res.data:
                for item in res.data:
                    if item.get("is_public", True) or item.get("creator") == str_lit.session_state.pseudo:
                        chars[item["name"]] = {
                            "img": item["img_url"] if item.get("img_url") and (item["img_url"].startswith("http") or os.path.exists(item["img_url"])) else "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
                            "prompt": f"Tu es {item['name']}, un personnage {item.get('sex', '')}. Description : {item.get('description', '')}. Personnages secondaires / Contexte additionnel : {item.get('secondary_chars', '')}. Reste strictement dans ton rôle." + base_instructions,
                            "quote": item.get("quote") if item.get("quote") else f"Bonjour, je suis {item['name']}."
                        }
        except Exception:
            pass
            
    return CHARACTERS if 'CHARACTERS' in locals() and not supabase else chars # Sécurité fallback

CHARACTERS = get_all_characters()

def get_user_conversations(pseudo):
    if not supabase or not pseudo or pseudo == "Invité":
        return []
    try:
        res = supabase.table("messages").select("char_name").eq("user_pseudo", str(pseudo)).execute()
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
    col1, col2, col3 = str_lit.columns([1, 2, 1])
    with col2:
        if os.path.exists("bg.png"):
            str_lit.image("bg.png")
        
        if not supabase or not client:
            str_lit.error("⚠️ Attention : Vérifie tes clés Supabase et Groq dans les secrets de Streamlit Cloud.")

        tab1, tab2 = str_lit.tabs(["Login", "Sign Up"])
        
        with tab1:
            email_log = str_lit.text_input("E-mail", key="login_email")
            password = str_lit.text_input("Password", type="password", key="login_pass")
            if str_lit.button("Log In"):
                if supabase:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email_log, "password": password})
                        if res and res.user:
                            user_data = supabase.table("users").select("pseudo").eq("id", res.user.id).single().execute()
                            pseudo_val = user_data.data["pseudo"] if user_data.data else email_log.split("@")[0]
                            
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
            reponse_secrete = str_lit.text_input("Question : Ta couleur préférée ?", key="sign_q")
            if str_lit.button("Sign Up"):
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
                            str_lit.success("Compte créé ! Veuillez vous connecter.")
                    except Exception as e:
                        str_lit.error(f"Erreur : {e}")
    str_lit.stop()

# --- SIDEBAR ---
if os.path.exists("couple.png"):
    str_lit.sidebar.image("couple.png")
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
            res_pub = supabase.table("custom_characters").select("*").eq("is_public", True).execute()
            public_custom_names = {item["name"] for item in res_pub.data} if res_pub.data else set()
            
            for name, data in CHARACTERS.items():
                if name in ["Caelum", "Alexei", "Killian", "Lucas", "Ethan", "Léo", "Liam", "Noah"] or name in public_custom_names:
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
        img_src = data['img']
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
    grid_html += '</div>'
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
        char_sex = str_lit.selectbox("Sexe / Genre", ["Homme", "Femme", "Non-binaire", "Autre"])
        char_quote = str_lit.text_input("Phrase d'accroche")
        char_description = str_lit.text_area("Description et Personnalité")
        char_secondary = str_lit.text_area("Personnages secondaires / Éléments contextuels (Optionnel)")
        uploaded_char_img = str_lit.file_uploader("Image du personnage", type=["png", "jpg", "jpeg"])
        visibility = str_lit.radio("Visibilité", ["Public", "Privé"])
        
        if str_lit.form_submit_button("🚀 Créer le personnage", use_container_width=True):
            if char_name and char_description:
                img_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                if uploaded_char_img is not None:
                    img_path_saved = f"char_{str_lit.session_state.pseudo}_{char_name}.png"
                    with open(img_path_saved, "wb") as f:
                        f.write(uploaded_char_img.getbuffer())
                    img_path = img_path_saved
                
                is_public = True if "Public" in visibility else False
                if supabase:
                    supabase.table("custom_characters").insert({
                        "name": char_name, "sex": char_sex, "quote": char_quote,
                        "description": char_description, "secondary_chars": char_secondary, "img_url": img_path,
                        "is_public": is_public, "creator": str_lit.session_state.pseudo
                    }).execute()
                    str_lit.success("Personnage créé !")
                    str_lit.session_state.page = "profile"
                    str_lit.rerun()

elif str_lit.session_state.page == "messages":
    str_lit.title("Mes Discussions")
    char_names_with_conv = get_user_conversations(str_lit.session_state.pseudo)
    if not char_names_with_conv:
        str_lit.info("Aucune discussion en cours.")
    else:
        for char_name in char_names_with_conv:
            if char_name in CHARACTERS:
                col1, col2, col3 = str_lit.columns([1, 4, 1])
                with col1: str_lit.image(CHARACTERS[char_name]["img"], width=85)
                with col2: 
                    str_lit.subheader(char_name)
                    str_lit.caption(CHARACTERS[char_name]["quote"])
                with col3:
                    if str_lit.button("Ouvrir", key=f"open_{char_name}"):
                        str_lit.session_state.char_select = char_name
                        str_lit.session_state.page = "chat"
                        str_lit.rerun()

elif str_lit.session_state.page == "profile":
    str_lit.title("Mon Profil")
    if supabase:
        try:
            user_db = supabase.table("users").select("*").eq("pseudo", str_lit.session_state.pseudo).single().execute()
            user_info = user_db.data if user_db.data else {}
            avatar_path = user_info.get("avatar_url", "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg")
            
            col1, col2 = str_lit.columns([1, 3])
            with col1: str_lit.image(avatar_path, use_container_width=True)
            with col2:
                str_lit.subheader(str_lit.session_state.pseudo)
                str_lit.write(f"📧 {user_info.get('email', '')}")

            str_lit.markdown("---")
            str_lit.subheader("🎭 Mes personnages créés & privés")
            my_chars_res = supabase.table("custom_characters").select("*").eq("creator", str_lit.session_state.pseudo).execute()
            for mc in (my_chars_res.data or []):
                mc_name = mc["name"]
                c_img, c_info, c_act1, c_act2 = str_lit.columns([1, 4, 1, 1])
                with c_img: str_lit.image(mc.get("img_url", ""), width=65)
                with c_info: str_lit.markdown(f"**{mc_name}** ({'🌍 Public' if mc.get('is_public') else '🔒 Privé'})")
                with c_act1:
                    if str_lit.button("Discuter", key=f"chat_mc_{mc_name}"):
                        str_lit.session_state.char_select = mc_name
                        str_lit.session_state.page = "chat"
                        str_lit.rerun()
                with c_act2:
                    if str_lit.button("Supprimer", key=f"del_mc_{mc_name}"):
                        supabase.table("custom_characters").delete().eq("name", mc_name).eq("creator", str_lit.session_state.pseudo).execute()
                        str_lit.rerun()
        except Exception:
            pass

elif str_lit.session_state.page == "chat":
    current_char = str_lit.session_state.char_select
    bg_image = CHARACTERS[current_char]["img"]
    char_quote = CHARACTERS[current_char]["quote"]
    char_prompt = CHARACTERS[current_char]["prompt"]

    str_lit.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(11, 14, 20, 0.90), rgba(11, 14, 20, 0.90)), url("{bg_image}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        .chat-header {{ background-color: rgba(22, 27, 34, 0.85); padding: 18px; border-radius: 12px; margin-bottom: 25px; }}
        </style>
        <div class="chat-header">
            <h2 style="margin: 0; color: #ffffff;">Chat avec {current_char}</h2>
            <p style='color: #a0a0a0; font-style: italic; margin: 6px 0 0 0;'>"{char_quote}"</p>
        </div>
    """, unsafe_allow_html=True)

    messages = load_msgs(str_lit.session_state.pseudo, current_char)

    if not messages and client:
        intro_prompt = [{"role": "system", "content": f"{char_prompt} Commence l'histoire avec un message d'accroche basé sur : '{char_quote}'."}]
        try:
            res_intro = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=intro_prompt)
            raw_text = res_intro.choices[0].message.content
            
            final_text = raw_text
            img_url = None
            match = re.search(r'\[IMAGE:\s*(.*?)\]', raw_text)
            if match:
                img_desc = match.group(1).strip()
                final_text = raw_text.replace(match.group(0), "").strip()
                img_url = generate_chat_image(img_desc)

            save_msg(str_lit.session_state.pseudo, current_char, "assistant", final_text, img_url)
            messages = load_msgs(str_lit.session_state.pseudo, current_char)
        except Exception:
            pass

    for msg in messages:
        is_user = (msg["role"] == "user")
        name_to_use = str_lit.session_state.pseudo if is_user else current_char
        
        with str_lit.container():
            str_lit.markdown(f"<b style='color: #ffffff;'>{name_to_use}</b>", unsafe_allow_html=True)
            str_lit.write(msg["content"])
            if msg.get("image_url") and os.path.exists(msg["image_url"]):
                str_lit.image(msg["image_url"], width=300)
            str_lit.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    with str_lit.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = str_lit.columns([5, 1])
        with col_input:
            user_input = str_lit.text_input("Écris ton message ici...", label_visibility="collapsed")
        with col_btn:
            submit_chat = str_lit.form_submit_button("Envoyer ➔", use_container_width=True)

        if submit_chat and user_input.strip():
            save_msg(str_lit.session_state.pseudo, current_char, "user", user_input)
            messages.append({"role": "user", "content": user_input})
            
            if client:
                try:
                    full_messages = [{"role": "system", "content": char_prompt}] + messages
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
                    raw_reply = res.choices[0].message.content
                    
                    reply_text = raw_reply
                    reply_img = None
                    match = re.search(r'\[IMAGE:\s*(.*?)\]', raw_reply)
                    if match:
                        img_desc = match.group(1).strip()
                        reply_text = raw_reply.replace(match.group(0), "").strip()
                        reply_img = generate_chat_image(img_desc)

                    save_msg(str_lit.session_state.pseudo, current_char, "assistant", reply_text, reply_img)
                    str_lit.rerun()
                except Exception:
                    pass
