import streamlit as str_lit
from supabase import create_client
from groq import Groq
import os

# --- CONFIGURATION ---
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key and "GROQ_API_KEY" in str_lit.secrets:
    groq_key = str_lit.secrets["GROQ_API_KEY"]

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
                    # Affiché si le personnage est public OU s'il appartient à l'utilisateur connecté
                    if item.get("is_public", True) or item.get("creator") == str_lit.session_state.pseudo:
                        chars[item["name"]] = {
                            "img": item["img_url"] if item.get("img_url") and (item["img_url"].startswith("http") or os.path.exists(item["img_url"])) else "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
                            "prompt": f"Tu es {item['name']}, un personnage {item.get('sex', '')}. Description : {item.get('description', '')}. Personnages secondaires / Contexte additionnel : {item.get('secondary_chars', '')}. Reste strictement dans ton rôle.",
                            "quote": item.get("quote") if item.get("quote") else f"Bonjour, je suis {item['name']}."
                        }
        except Exception:
            pass
            
    return chars

CHARACTERS = get_all_characters()

def get_user_conversations(pseudo):
    """Retourne uniquement les noms des personnages valides avec lesquels cet utilisateur a un historique de messages."""
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
                else:
                    str_lit.error("Base de données non disponible.")

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
                else:
                    str_lit.error("Base de données non disponible.")
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

# --- NAVIGATION ENTRE PAGES ---
if str_lit.session_state.page == "home":
    str_lit.title("Explorer")
    str_lit.write("Découvre et discute avec les personnages du moment :")
    
    # On filtre pour ne montrer sur l'accueil que les personnages officiels ou ceux qui sont publics
    public_items = []
    if supabase:
        try:
            res_pub = supabase.table("custom_characters").select("*").eq("is_public", True).execute()
            public_custom_names = {item["name"] for item in res_pub.data} if res_pub.data else set()
            
            # Personnages par défaut + personnages custom publics
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

    if total_pages > 1:
        str_lit.markdown("---")
        p_col1, p_col2, p_col3 = str_lit.columns([1, 2, 1])
        with p_col1:
            if str_lit.session_state.home_page > 0:
                if str_lit.button("⬅️ Précédent", use_container_width=True):
                    str_lit.session_state.home_page -= 1
                    str_lit.rerun()
        with p_col2:
            str_lit.markdown(f"<p style='text-align: center; color: #8b949e;'>Page {str_lit.session_state.home_page + 1} sur {total_pages}</p>", unsafe_allow_html=True)
        with p_col3:
            if str_lit.session_state.home_page < total_pages - 1:
                if str_lit.button("Suivant ➡️", use_container_width=True):
                    str_lit.session_state.home_page += 1
                    str_lit.rerun()

elif str_lit.session_state.page == "create_character":
    str_lit.title("✨ Créer un nouveau personnage")
    str_lit.write("Conçois ton propre personnage sur mesure, définis son univers et choisis s'il est visible par tous ou uniquement par toi.")

    with str_lit.form("create_char_form"):
        char_name = str_lit.text_input("Nom du personnage")
        char_sex = str_lit.selectbox("Sexe / Genre", ["Homme", "Femme", "Non-binaire", "Autre"])
        char_quote = str_lit.text_input("Phrase d'accroche (Citation affichée sous l'image)")
        char_description = str_lit.text_area("Description et Personnalité (Comment se comporte-t-il, son histoire, son ton...)", help="Ex: Tu es ténébreux, protecteur, un peu distant au début...")
        char_secondary = str_lit.text_area("Personnages secondaires / Éléments contextuels (Optionnel)", help="Ex: Inclut des mentions de ses frères ou de rivaux si nécessaire dans l'histoire.")
        
        uploaded_char_img = str_lit.file_uploader("Image du personnage (PNG, JPG)", type=["png", "jpg", "jpeg"])
        
        visibility = str_lit.radio("Visibilité", ["Public (visible par toute la communauté)", "Privé (uniquement pour moi)"])
        
        submitted = str_lit.form_submit_button("🚀 Créer le personnage", use_container_width=True)
        
        if submitted:
            if not char_name or not char_description:
                str_lit.warning("Veuillez remplir au moins le nom et la description du personnage.")
            else:
                img_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                if uploaded_char_img is not None:
                    img_path_saved = f"char_{str_lit.session_state.pseudo}_{char_name}.png"
                    with open(img_path_saved, "wb") as f:
                        f.write(uploaded_char_img.getbuffer())
                    img_path = img_path_saved
                
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
                            "creator": str_lit.session_state.pseudo
                        }).execute()
                        
                        str_lit.success(f"Le personnage {char_name} a été créé avec succès ! Retrouvez-le dans votre Profil.")
                        str_lit.session_state.page = "profile"
                        str_lit.rerun()
                    except Exception as e:
                        str_lit.error(f"Erreur lors de la création : {e}")
                else:
                    str_lit.error("Base de données non disponible.")

elif str_lit.session_state.page == "messages":
    str_lit.title("Mes Discussions")
    str_lit.write("Retrouvez ici l'ensemble de vos conversations avec les personnages.")
    
    char_names_with_conv = get_user_conversations(str_lit.session_state.pseudo)
    
    if not char_names_with_conv:
        str_lit.info("Vous n'avez pas encore de discussions en cours. Allez sur l'accueil pour choisir un personnage !")
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
            user_db = supabase.table("users").select("*").eq("pseudo", str_lit.session_state.pseudo).single().execute()
            user_info = user_db.data if user_db.data else {}
            
            user_email = user_info.get("email", "Non disponible")
            user_id = user_info.get("id")
            
            avatar_path = user_info.get("avatar_url", "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg")
            if not avatar_path or (not str(avatar_path).startswith("http") and not os.path.exists(avatar_path)):
                avatar_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

            char_names_with_conv = get_user_conversations(str_lit.session_state.pseudo)
            nb_collected = len(char_names_with_conv)
            
            col1, col2 = str_lit.columns([1, 3])
            
            with col1:
                str_lit.image(avatar_path, use_container_width=True)
                
            with col2:
                str_lit.subheader(str_lit.session_state.pseudo)
                str_lit.write(f"📧 {user_email}")
                
                stat1, stat2, stat3 = str_lit.columns(3)
                with stat1:
                    str_lit.metric(label="Discussions", value=nb_collected)
                with stat2:
                    str_lit.metric(label="Abonnés", value=0)
                with stat3:
                    str_lit.metric(label="Abonnements", value=0)

            str_lit.markdown("---")
            
            str_lit.text_input("Pseudo (non modifiable)", value=str_lit.session_state.pseudo, disabled=True)
            
            uploaded_file = str_lit.file_uploader("Changer votre photo de profil", type=["png", "jpg", "jpeg"], key="avatar_uploader")
            
            if uploaded_file is not None and user_id:
                file_extension = uploaded_file.name.split(".")[-1]
                file_name = f"avatar_{user_id}.{file_extension}"
                
                with open(file_name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    supabase.table("users").update({"avatar_url": file_name}).eq("id", user_id).execute()
                    str_lit.success("Photo de profil mise à jour avec succès !")
                    str_lit.rerun()
                except Exception:
                    str_lit.success("Photo enregistrée localement !")
                    str_lit.rerun()

            # --- SECTION PERSONNALISÉE : PERSONNAGES CRÉÉS / PRIVÉS (Style TYPSY) ---
            str_lit.markdown("---")
            str_lit.subheader("🎭 Mes personnages créés & privés")
            str_lit.write("Retrouvez ici tous les personnages sur mesure que vous avez imaginés (publics ou privés).")

            try:
                my_chars_res = supabase.table("custom_characters").select("*").eq("creator", str_lit.session_state.pseudo).execute()
                my_chars = my_chars_res.data if my_chars_res.data else []

                if not my_chars:
                    str_lit.info("Vous n'avez pas encore créé de personnage. Rendez-vous dans l'onglet 'Créer un Personnage' !")
                else:
                    for mc in my_chars:
                        mc_name = mc["name"]
                        mc_quote = mc.get("quote", "Pas de citation")
                        mc_img = mc.get("img_url", "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg")
                        if not str(mc_img).startswith("http") and not os.path.exists(mc_img):
                            mc_img = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                        
                        is_pub_status = "🌍 Public" if mc.get("is_public", True) else "🔒 Privé"

                        c_img, c_info, c_act1, c_act2 = str_lit.columns([1, 4, 1, 1])
                        with c_img:
                            str_lit.image(mc_img, width=65)
                        with c_info:
                            str_lit.markdown(f"**{mc_name}** ({is_pub_status})")
                            str_lit.caption(f'"{mc_quote}"')
                        with c_act1:
                            if str_lit.button("Discuter", key=f"chat_my_char_{mc_name}"):
                                str_lit.session_state.char_select = mc_name
                                str_lit.session_state.page = "chat"
                                str_lit.rerun()
                        with c_act2:
                            if str_lit.button("Supprimer", key=f"del_my_char_{mc_name}"):
                                try:
                                    supabase.table("custom_characters").delete().eq("name", mc_name).eq("creator", str_lit.session_state.pseudo).execute()
                                    str_lit.success(f"Personnage {mc_name} supprimé.")
                                    str_lit.rerun()
                                except Exception as e:
                                    str_lit.error(f"Erreur : {e}")
                        str_lit.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)

            except Exception as e:
                str_lit.error(f"Erreur lors du chargement de vos personnages : {e}")
                
        except Exception as e:
            str_lit.error(f"Impossible de charger les données du profil : {e}")

elif str_lit.session_state.page == "chat":
    current_char = str_lit.session_state.char_select
    bg_image = CHARACTERS[current_char]["img"]
    char_quote = CHARACTERS[current_char]["quote"]
    char_prompt = CHARACTERS[current_char]["prompt"]

    if not str(bg_image).startswith("http") and not os.path.exists(str(bg_image)):
        bg_image = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

    str_lit.markdown(f"""
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

    str_lit.markdown(f"""
        <div class="chat-header-container">
            <h2 style="margin: 0; color: #ffffff;">Chat avec {current_char}</h2>
            <p style='color: #a0a0a0; font-style: italic; margin: 6px 0 0 0;'>"{char_quote}"</p>
        </div>
    """, unsafe_allow_html=True)

    messages = load_msgs(str_lit.session_state.pseudo, current_char)

    if not messages and client:
        intro_system_prompt = [
            {"role": "system", "content": f"{char_prompt} Commence l'histoire en envoyant un premier message d'accroche immersif en incarnant ton personnage, en te basant sur cette citation : '{char_quote}'."}
        ]
        try:
            res_intro = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=intro_system_prompt)
            first_message = res_intro.choices[0].message.content
            save_msg(str_lit.session_state.pseudo, current_char, "assistant", first_message)
            messages = load_msgs(str_lit.session_state.pseudo, current_char)
        except Exception as e:
            str_lit.error(f"Erreur d'authentification Groq : {e}")

    user_avatar_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
    if supabase:
        try:
            u_db = supabase.table("users").select("avatar_url").eq("pseudo", str(str_lit.session_state.pseudo)).single().execute()
            if u_db.data and u_db.data.get("avatar_url"):
                p_url = u_db.data["avatar_url"]
                if str(p_url).startswith("http") or os.path.exists(str(p_url)):
                    user_avatar_path = p_url
        except Exception:
            pass

    char_avatar_path = bg_image

    for idx, msg in enumerate(messages):
        is_user = (msg["role"] == "user")
        avatar_to_use = user_avatar_path if is_user else char_avatar_path
        name_to_use = str_lit.session_state.pseudo if is_user else current_char

        with str_lit.container():
            col_av, col_txt = str_lit.columns([1, 11])
            with col_av:
                str_lit.markdown(
                    f"<img src='{avatar_to_use}' style='width: 38px; height: 38px; border-radius: 50%; object-fit: cover; margin-top: 4px;'>", 
                    unsafe_allow_html=True
                )
            with col_txt:
                str_lit.markdown(f"<b style='color: #ffffff; font-size: 14px;'>{name_to_use}</b>", unsafe_allow_html=True)
                
                if is_user:
                    edit_key = f"edit_mode_{idx}"
                    if edit_key not in str_lit.session_state:
                        str_lit.session_state[edit_key] = False

                    if not str_lit.session_state[edit_key]:
                        str_lit.write(msg["content"])
                        if str_lit.button("✏️ Modifier ce message", key=f"btn_edit_{idx}"):
                            str_lit.session_state[edit_key] = True
                            str_lit.rerun()
                    else:
                        new_content = str_lit.text_area("Modifier le message :", value=msg["content"], key=f"input_edit_{idx}")
                        col_save, col_cancel = str_lit.columns([1, 1])
                        with col_save:
                            if str_lit.button("💾 Enregistrer", key=f"save_edit_{idx}"):
                                if supabase and new_content.strip():
                                    try:
                                        supabase.table("messages").delete().eq("user_pseudo", str(str_lit.session_state.pseudo)).eq("char_name", str(current_char)).execute()
                                        
                                        messages[idx]["content"] = new_content
                                        trimmed_messages = messages[:idx+1]
                                        
                                        for m in trimmed_messages:
                                            supabase.table("messages").insert({
                                                "user_pseudo": str(str_lit.session_state.pseudo),
                                                "char_name": str(current_char),
                                                "role": m["role"],
                                                "content": m["content"]
                                            }).execute()
                                        
                                        str_lit.session_state[edit_key] = False
                                        
                                        if idx == len(messages) - 1 and client:
                                            full_messages = [{"role": "system", "content": char_prompt}] + trimmed_messages
                                            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
                                            assistant_reply = res.choices[0].message.content
                                            save_msg(str_lit.session_state.pseudo, current_char, "assistant", assistant_reply)
                                        
                                        str_lit.rerun()
                                    except Exception as e:
                                        str_lit.error(f"Erreur lors de la modification : {e}")
                        with col_cancel:
                            if str_lit.button("❌ Annuler", key=f"cancel_edit_{idx}"):
                                str_lit.session_state[edit_key] = False
                                str_lit.rerun()
                else:
                    str_lit.write(msg["content"])
            
            str_lit.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    str_lit.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    with str_lit.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = str_lit.columns([5, 1])
        with col_input:
            user_input = str_lit.text_input("Écris ton message ici...", label_visibility="collapsed", placeholder="Écris ton message ici...")
        with col_btn:
            submit_chat = str_lit.form_submit_button("Envoyer ➔", use_container_width=True)

        if submit_chat and user_input.strip():
            save_msg(str_lit.session_state.pseudo, current_char, "user", user_input)
            messages.append({"role": "user", "content": user_input})
            
            if client:
                try:
                    full_messages = [{"role": "system", "content": char_prompt}] + messages
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
                    assistant_reply = res.choices[0].message.content
                    save_msg(str_lit.session_state.pseudo, current_char, "assistant", assistant_reply)
                    str_lit.rerun()
                except Exception as e:
                    str_lit.error(f"Erreur lors de l'envoi du message : {e}")
            else:
                str_lit.error("Client Groq non initialisé.")
