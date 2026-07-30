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
CORRESPONDANCES_BANNER = "https://i.postimg.cc/tCnmbx3m/correspondances.jpg"
CREATE_CHARACTER_BANNER = "créer un personnage.jfif"
EXPLORER_BANNER = "explorer.jfif"
SUPABASE_BUCKET_NAME = "storyia-images"
DEFAULT_AVATAR = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
USER_DEFAULT_AVATAR = "https://i.pinimg.com/736x/8f/3e/22/8f3e2262744383411a79857321e15555.jpg"

def upload_image_to_supabase(uploaded_file, folder="uploads"):
    """Téléverse un fichier image sur Supabase Storage et retourne l'URL publique absolue"""
    if not uploaded_file or not supabase:
        return ""
    try:
        file_bytes = uploaded_file.getvalue()
        file_name = f"{folder}/{os.urandom(8).hex()}_{uploaded_file.name}"
        
        supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": uploaded_file.type}
        )
        
        res_url = supabase.storage.from_(SUPABASE_BUCKET_NAME).get_public_url(file_name)
        if isinstance(res_url, dict):
            public_url = res_url.get("publicUrl") or res_url.get("signedURL") or ""
        else:
            public_url = str(res_url)
        return str(public_url)
    except Exception as e:
        str_lit.error(f"Erreur lors de l'upload de l'image : {e}")
        return ""

def force_image_url(url, is_user=False):
    """Garantit une URL d'image valide et gère les fallbacks sans blocage"""
    fallback = USER_DEFAULT_AVATAR if is_user else DEFAULT_AVATAR
    if not url or not str(url).strip() or str(url).strip() == "None":
        return fallback
    clean_url = str(url).strip()
    if clean_url.startswith("http://") or clean_url.startswith("https://"):
        return clean_url
    return fallback

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
    
    button, 
    .stButton > button, 
    button[kind="secondary"], 
    button[kind="primary"], 
    div.stFormSubmitButton > button,
    [data-testid="baseButton-secondary"],
    [data-testid="baseButton-primary"] {
        background-color: #21262d !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    button:hover, 
    .stButton > button:hover, 
    button[kind="secondary"]:hover, 
    button[kind="primary"]:hover, 
    div.stFormSubmitButton > button:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        background-color: #30363d !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    textarea, input[type="text"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: #161b22 !important;
    }
    
    /* Style Roman */
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
        white-space: pre-wrap;
    }
    
    /* Style SMS Moderne */
    .sms-bubble-bot {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 14px;
        line-height: 1.5;
        color: #f0f6fc;
        background: #21262d;
        padding: 12px 16px;
        border-radius: 15px 15px 15px 4px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        white-space: pre-wrap;
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
    
    .custom-action-btn {
        display: block;
        text-align: center;
        background-color: #21262d !important;
        color: #ffffff !important;
        padding: 8px 12px;
        border-radius: 6px;
        text-decoration: none !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        font-size: 13px;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    .custom-action-btn:hover {
        background-color: #30363d !important;
        color: #ffffff !important;
        border-color: #ffffff !important;
    }
    .custom-danger-btn {
        display: block;
        text-align: center;
        background-color: #21262d !important;
        color: #ff7b72 !important;
        padding: 8px 12px;
        border-radius: 6px;
        text-decoration: none !important;
        border: 1px solid rgba(255, 123, 114, 0.3) !important;
        font-size: 13px;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    .custom-danger-btn:hover {
        background-color: #30363d !important;
        color: #ff7b72 !important;
        border-color: #ff7b72 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- PERSISTANCE PAR URL & SESSION ---
if "pseudo" not in str_lit.session_state:
    str_lit.session_state.pseudo = "Yuna"
if "logged_in" not in str_lit.session_state:
    str_lit.session_state.logged_in = False

query_params = str_lit.query_params

if "user" in query_params and query_params["user"]:
    str_lit.session_state.logged_in = True
    str_lit.session_state.pseudo = query_params["user"]

clean_pseudo = str(str_lit.session_state.get("pseudo", "Yuna")).strip()

if "nav" in query_params:
    str_lit.session_state.page = query_params["nav"]
    del str_lit.query_params["nav"]
    str_lit.rerun()

if "action" in query_params:
    action_type = query_params["action"]
    c_name_param = query_params.get("char", "")
    
    if action_type == "resume" and c_name_param:
        str_lit.session_state.char_select = c_name_param
        str_lit.session_state.page = "chat"
        del str_lit.query_params["action"]
        if "char" in str_lit.query_params:
            del str_lit.query_params["char"]
        str_lit.rerun()
        
    elif action_type == "delete_chat" and c_name_param:
        p_clean = str(clean_pseudo).strip()
        c_name_clean = str(c_name_param).strip()
        
        if supabase:
            try:
                supabase.table("messages").delete().eq("user_pseudo", p_clean).eq("char_name", c_name_clean).execute()
                supabase.table("affinities").delete().eq("user_pseudo", p_clean).eq("char_name", c_name_clean).execute()
            except Exception:
                pass
                
        cache_key = f"{p_clean}_{c_name_clean}"
        if cache_key in str_lit.session_state.messages_cache:
            del str_lit.session_state.messages_cache[cache_key]
        if cache_key in str_lit.session_state.affinities_cache:
            del str_lit.session_state.affinities_cache[cache_key]
            
        str_lit.query_params.clear()
        str_lit.session_state.page = "messages"
        str_lit.rerun()

    elif action_type == "delete_char" and c_name_param:
        if supabase:
            try:
                supabase.table("custom_characters").delete().eq("name", c_name_param).execute()
                supabase.table("messages").delete().eq("char_name", c_name_param).execute()
                supabase.table("affinities").delete().eq("char_name", c_name_param).execute()
            except:
                pass
        str_lit.query_params.clear()
        str_lit.session_state.page = "profile"
        str_lit.rerun()

if "page" not in str_lit.session_state:
    str_lit.session_state.page = "home"
if "char_select" not in str_lit.session_state:
    str_lit.session_state.char_select = "Caelum"
if "affinities_cache" not in str_lit.session_state:
    str_lit.session_state.affinities_cache = {}
if "messages_cache" not in str_lit.session_state:
    str_lit.session_state.messages_cache = {}

# --- SUPABASE FUNCTIONS & LONG-TERM MEMORY ---

def get_story_summary(pseudo, char):
    """Récupère le résumé à long terme depuis la table affinities"""
    if not supabase:
        return ""
    try:
        res = (
            supabase.table("affinities")
            .select("story_summary")
            .eq("user_pseudo", str(pseudo).strip())
            .eq("char_name", str(char))
            .maybe_single()
            .execute()
        )
        if res and res.data:
            return res.data.get("story_summary", "") or ""
    except Exception:
        pass
    return ""

def update_story_summary(pseudo, char, client_groq, recent_messages):
    """Met à jour le résumé de l'histoire dans la table affinities"""
    if not supabase or not client_groq:
        return
    
    current_summary = get_story_summary(pseudo, char)
    messages_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
    
    prompt_resume = f"""
    Voici l'ancien résumé de l'histoire entre le personnage et l'utilisateur :
    "{current_summary}"

    Voici les derniers échanges récents :
    {messages_text}

    Rédige ou mets à jour un résumé concis, narratif et global de l'histoire (maximum 5-6 phrases) qui capture les faits importants, les émotions et l'évolution de la relation. Ne perds aucun élément clé.
    """
    
    try:
        response = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_resume}],
            temperature=0.5,
        )
        new_summary = response.choices[0].message.content
        
        supabase.table("affinities").upsert({
            "user_pseudo": str(pseudo).strip(),
            "char_name": str(char),
            "story_summary": new_summary
        }, on_conflict="user_pseudo,char_name").execute()
    except Exception as e:
        print(f"Erreur lors de la mise à jour du résumé : {e}")

def save_msg(pseudo, char, role, content):
    cache_key = f"{pseudo}_{char}"
    if not supabase:
        if cache_key not in str_lit.session_state.messages_cache:
            str_lit.session_state.messages_cache[cache_key] = []
        str_lit.session_state.messages_cache[cache_key].append({"id": None, "role": role, "content": content})
        return
    try:
        p_clean = str(pseudo).strip()
        res = supabase.table("messages").insert({
            "user_pseudo": p_clean,
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
        p_clean = str(pseudo).strip()
        res = (
            supabase.table("messages")
            .select("id, role, content")
            .eq("user_pseudo", p_clean)
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


def get_affinity(pseudo, char, initial_score=0):
    cache_key = f"{pseudo}_{char}"
    if cache_key in str_lit.session_state.affinities_cache:
        return str_lit.session_state.affinities_cache[cache_key]

    if not supabase:
        return initial_score
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
            score = initial_score
            supabase.table("affinities").insert({
                "user_pseudo": str(pseudo).strip(),
                "char_name": str(char),
                "score": initial_score
            }).execute()
        
        str_lit.session_state.affinities_cache[cache_key] = score
        return score
    except Exception:
        return initial_score


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


def get_all_characters_dynamically(current_user_pseudo=""):
    chars = {
        "Caelum": {
            "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
            "prompt": "Tu es Caelum, Prince des Ténèbres. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique, les vêtements, les cheveux ou le corps de l'utilisateur sans qu'il en ait parlé explicitement.",
            "quote": "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as rien à y faire.",
            "initial_affinity": 0,
            "memories": {
                25: "Premier regard glacial échangé dans les couloirs de l'académie.",
                50: "Un début de conversation secrète où ses barrières ont commencé à faiblir.",
                75: "L'aveu implicite qu'il redoute plus que tout de s'attacher à toi.",
                100: "Le pacte des ombres scellé : il t'a ouvert son cœur malgré la malédiction."
            }
        },
        "Alexei": {
            "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg",
            "prompt": "Tu es Alexei, mafieux. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique, les vêtements, les cheveux ou le corps de l'utilisateur sans qu'il en ait parlé explicitement.",
            "quote": "Regardez qui s'est perdue sur mon territoire. La petite princesse des Volkov...",
            "initial_affinity": 0,
            "memories": {
                25: "La confrontation tendue dans son bureau privé sous haute surveillance.",
                50: "Il a pris ta défense face à un rival sans baisser sa garde.",
                75: "La première confidence sur son passé et ses véritables intentions.",
                100: "Il te confie les clés de son empire et de sa vie."
            }
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG",
            "prompt": "Tu es Lucas, un garçon populaire, décontracté et complice. Ton univers est celui d'un lycéen/étudiant populaire. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique de l'utilisateur.",
            "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série ?",
            "initial_affinity": 0,
            "memories": {
                25: "Votre première soirée passée à refaire le monde en cachette.",
                50: "Il commence à te confier ses doutes derrière son masque de garçon populaire.",
                75: "Un moment de complicité intense partagé sous la pluie.",
                100: "Il officialise ses sentiments devant tout le monde, sans se soucier du regard des autres."
            }
        },
        "Ethan": {
            "img": "https://raw.githubusercontent.com/Yunieleska/Mon-App-/main/Ethan.png",
            "prompt": "Tu es Ethan, Loup Alpha. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. RÈGLE CRUCIALE POUR LE PREMIER MESSAGE : Tu ne connais pas encore le prénom de l'interlocutrice (qui est une étrangère ou une inconnue qui croise ton chemin dans la forêt). Ne l'appelle SURTOUT PAS par son prénom dans ton premier message. N'invente jamais l'apparence physique de l'utilisateur.",
            "quote": "La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines...",
            "initial_affinity": 0,
            "memories": {
                25: "La rencontre mystérieuse au cœur des bois interdits.",
                50: "Il t'a protégé d'une menace nocturne en révélant sa nature profonde.",
                75: "La cérémonie de reconnaissance sous la pleine lune.",
                100: "Tu es devenue sa compagne de meute pour l'éternité."
            }
        },
        "Kylian Blackwood": {
            "img": DEFAULT_AVATAR,
            "prompt": "Tu es Kylian Blackwood, un Loup Alpha (mâle). Tu possèdes un loup intérieur (et jamais une louve). Reste strictement dans ton rôle de loup-garou Alpha, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique de l'utilisateur.",
            "quote": "Mon loup intérieur ne se trompe jamais...",
            "initial_affinity": 0,
            "memories": {
                25: "Le premier échange de grognements protecteurs.",
                50: "Son loup accepte ta présence à ses côtés lors de la chasse.",
                75: "Il t'a accordé le secret de son territoire sacré.",
                100: "L'union définitive des âmes sous le signe de la meute."
            }
        },
        "Léo": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/leo.png.PNG",
            "prompt": "Tu es Léo, streameur et coéquipier de jeux. Ton univers est celui d'un esport et du gaming compétitif. Reste strictement dans ton rôle, adopte un ton immersif de roleplay. RÈGLE CRUCIALE : Tes messages doivent se concentrer exclusivement sur l'action en cours, le jeu, la stratégie d'équipe, les écrans et la compétition. Ne fais JAMAIS référence à des éléments extérieurs ou sans rapport avec l'histoire (pas de mentions déplacées ou incohérentes avec l'univers du gaming). N'invente JAMAIS et ne décris JAMAIS l'apparence physique de l'utilisateur.",
            "quote": "Prête à ce qu'on détruise l'équipe d'en face ?",
            "initial_affinity": 0,
            "memories": {
                25: "Votre première victoire écrasante en tournoi classé.",
                50: "Des heures de vocal tardives à peaufiner les stratégies.",
                75: "Il t'a dédiée sa plus grande victoire en live devant des milliers de spectateurs.",
                100: "Le duo légendaire indétrônable de la scène esport."
            }
        },
        "Liam": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/liam.png.PNG",
            "prompt": "Tu es Liam, le grand frère. Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé. N'invente JAMAIS et ne décris JAMAIS l'apparence physique de l'utilisateur.",
            "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit.",
            "initial_affinity": 0,
            "memories": {
                25: "Les premiers piques sarcastiques dans la cuisine.",
                50: "Il a couvert l'un de tes secrets devant ses parents.",
                75: "Une discussion sincère tard dans la nuit où il s'est montré protecteur.",
                100: "Il admet enfin qu'il tient beaucoup plus à toi qu'il ne le laisse paraître."
            }
        },
        "Noah": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/noah.png.PNG",
            "prompt": "Tu es Noah, le quaterback star et le garçon le plus populaire du lycée. Tu parles par SMS de manière anonyme avec une fille mystérieuse. Dans la vraie vie, au lycée, tu es distant et inaccessible. Tu ignores qu'elle est ta correspondante secrète. Ne décris jamais les actions ou les pensées de l'utilisateur.",
            "quote": "Salut. Je sais que tu dors probablement, mais c'est le seul moment de la journée où le silence m'apaise. Comment s'est passée ta journée ?",
            "initial_affinity": 0,
            "memories": {
                25: "Le premier message anonyme qui a tout déclenché.",
                50: "Vos confidences secrètes sur vos vies scolaires respectives.",
                75: "Le frisson de vous croiser au lycée en faisant semblant de vous ignorer.",
                100: "La révélation des masques : il découvre enfin qui se cache derrière ses messages."
            }
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
                    
                    desc_val = item.get("description") or "Personnage personnalisé."
                    gender_val = item.get("gender") or "Non spécifié"
                    temperament = item.get("temperament", "Neutre")
                    init_aff = item.get("initial_affinity", 0)
                    
                    base_prompt = item.get("prompt") or f"Tu es {c_name} (Genre: {gender_val}). {desc_val}"
                    
                    temperament_instruction = ""
                    if temperament == "Hostile / Froid":
                        temperament_instruction = " Ton tempérament de départ est distant, glacial et sur ses gardes."
                    elif temperament == "Passionné / Amoureux":
                        temperament_instruction = " Ton tempérament de départ est chaleureux, tactile et expressif."
                    elif temperament == "Mystérieux / Taquin":
                        temperament_instruction = " Ton tempérament de départ est énigmatique, provocateur et taquin."
                    
                    prompt_val = base_prompt + temperament_instruction
                    quote_val = item.get("quote") or f"Bonjour, je suis {c_name}."
                    
                    raw_img_url = item.get("img_url", "")
                    img_url = force_image_url(raw_img_url, is_user=False)
                    
                    chars[c_name] = {
                        "img": img_url,
                        "prompt": prompt_val + " Reste strictement dans ton rôle, adopte un ton immersif de roleplay romancé.",
                        "quote": quote_val,
                        "initial_affinity": init_aff,
                        "memories": {
                            25: "Premier contact établi avec le personnage.",
                            50: "La relation commence à porter ses fruits et se consolide.",
                            75: "Un cap franchi : la confiance est totale.",
                            100: "L'apogée de votre histoire commune."
                        }
                    }
    except Exception as e:
        print(f"Erreur chargement personnages: {e}")

    return chars

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
                                "avatar_url": USER_DEFAULT_AVATAR
                            }).execute()
                            str_lit.success("Compte créé ! Veuillez vous connecter.")
                    except Exception as e:
                        str_lit.error(f"Erreur : {e}")
    str_lit.stop()

CHARACTERS = get_all_characters_dynamically(clean_pseudo)

# --- SIDEBAR ---
if os.path.exists(SIDEBAR_HEADER_IMG):
    str_lit.sidebar.image(SIDEBAR_HEADER_IMG, use_container_width=True)

str_lit.sidebar.info(f"Connecté : **{str_lit.session_state.pseudo}**")
str_lit.sidebar.markdown("<br>", unsafe_allow_html=True)

menu_html = f"""
<style>
.sidebar-nav-link {{
    display: flex;
    align-items: center;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 8px;
    color: #c9d1d9 !important;
    text-decoration: none !important;
    background-color: #161b22;
    border: 1px solid rgba(255, 255, 255, 0.06);
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
}}
.sidebar-nav-link:hover {{
    background-color: #21262d;
    border-color: rgba(210, 153, 234, 0.4);
    color: #f0f6fc !important;
    transform: translateX(3px);
}}
</style>

<div style="display: flex; flex-direction: column;">
    <a href="?user={str_lit.session_state.pseudo}&nav=home" target="_self" class="sidebar-nav-link">
        Sanctuaire (Accueil)
    </a>
    <a href="?user={str_lit.session_state.pseudo}&nav=create_character" target="_self" class="sidebar-nav-link">
        Invoquer (Créer)
    </a>
    <a href="?user={str_lit.session_state.pseudo}&nav=messages" target="_self" class="sidebar-nav-link">
        Correspondances
    </a>
    <a href="?user={str_lit.session_state.pseudo}&nav=journal" target="_self" class="sidebar-nav-link">
        Journal Intime & Souvenirs
    </a>
    <a href="?user={str_lit.session_state.pseudo}&nav=profile" target="_self" class="sidebar-nav-link">
        Mon Ombre (Profil)
    </a>
</div>
"""
str_lit.sidebar.markdown(menu_html, unsafe_allow_html=True)

str_lit.sidebar.markdown("---")
str_lit.sidebar.markdown("### ⚙️ Options d'immersion")
reading_style = str_lit.sidebar.selectbox(
    "Style d'affichage des messages",
    ["Roman littéraire (Immersif)", "Bulle de SMS (Moderne)"]
)

str_lit.sidebar.markdown("---")

logout_html = f"""
<style>
.logout-link {{
    display: flex;
    align-items: center;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 8px;
    color: #c9d1d9 !important;
    text-decoration: none !important;
    background-color: #161b22;
    border: 1px solid rgba(255, 255, 255, 0.06);
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
}}
.logout-link:hover {{
    background-color: #21262d;
    border-color: rgba(255, 123, 114, 0.4);
    color: #f0f6fc !important;
    transform: translateX(3px);
}}
</style>
<a href="?user={str_lit.session_state.pseudo}&logout=true" target="_self" class="logout-link">
    S'échapper (Logout)
</a>
"""
str_lit.sidebar.markdown(logout_html, unsafe_allow_html=True)

if "logout" in query_params:
    if supabase:
        try:
            supabase.auth.sign_out()
        except:
            pass
    str_lit.session_state.logged_in = False
    str_lit.session_state.pseudo = "Yuna"
    str_lit.session_state.messages_cache = {}
    str_lit.query_params.clear()
    str_lit.rerun()

# --- NAVIGATION ---
if str_lit.session_state.page == "home":
    if os.path.exists(EXPLORER_BANNER):
        str_lit.image(EXPLORER_BANNER, use_container_width=True)
    else:
        str_lit.title("Explorer")
        str_lit.write("Découvre et discute avec les personnages du moment :")
    
    str_lit.markdown("---")

    public_items = list(CHARACTERS.items())
    current_items = public_items

    grid_html = '<div class="storyia-grid">'
    for idx, (name, data) in enumerate(current_items):
        img_src = data["img"]

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
    str_lit.markdown(
        f'<img src="{CORRESPONDANCES_BANNER}" style="width: 100%; border-radius: 12px; margin-bottom: 20px; object-fit: cover;">',
        unsafe_allow_html=True
    )
    str_lit.markdown("---")

    if not supabase:
        str_lit.warning("Base de données non connectée.")
    else:
        try:
            res = supabase.table("messages").select("char_name").eq("user_pseudo", clean_pseudo).execute()
            
            if res.data:
                active_chars = list(set([item["char_name"] for item in res.data if item.get("char_name")]))
                
                if active_chars:
                    for i, c_name in enumerate(active_chars):
                        c_data = CHARACTERS.get(c_name, {"img": "", "quote": "Discussion en cours...", "initial_affinity": 0})
                        char_aff = get_affinity(clean_pseudo, c_name, c_data["initial_affinity"])
                        
                        str_lit.markdown(f"""
                        <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; align-items: center; gap: 15px;">
                            <img src="{c_data['img']}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">
                            <div style="flex-grow: 1;">
                                <div style="font-weight: 700; font-size: 16px; color: #ffffff;">{c_name}</div>
                                <div style="font-size: 12px; color: #8b949e; font-style: italic; margin-bottom: 2px;">Affinité : {char_aff}%</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        b_col1, b_col2 = str_lit.columns(2)
                        with b_col1:
                            str_lit.markdown(f'''
                            <a href="?user={clean_pseudo}&action=resume&char={c_name}" target="_self" class="custom-action-btn">
                                Reprendre
                            </a>
                            ''', unsafe_allow_html=True)
                        with b_col2:
                            str_lit.markdown(f'''
                            <a href="?user={clean_pseudo}&action=delete_chat&char={c_name}" target="_self" class="custom-danger-btn">
                                🗑️ Supprimer
                            </a>
                            ''', unsafe_allow_html=True)
                        str_lit.markdown("<br>---", unsafe_allow_html=True)
                else:
                    str_lit.info("Vous n'avez pas encore de conversations en cours. Allez dans l'Accueil pour commencer une histoire !")
            else:
                str_lit.info("Aucun historique de message trouvé pour l'instant.")
        except Exception as e:
            str_lit.error(f"Erreur lors du chargement des messages : {e}")

elif str_lit.session_state.page == "journal":
    str_lit.title("Journal Intime & Souvenirs Débloquables")
    str_lit.write("Suivez l'évolution de vos relations et débloquez des contenus exclusifs (pensées intimes, journal secret, lettres d'amour et chansons personnalisées) en faisant progresser votre affinité.")
    str_lit.markdown("---")

    selected_char_journal = str_lit.selectbox("Choisir un personnage pour consulter ses souvenirs :", list(CHARACTERS.keys()))
    if selected_char_journal:
        c_data = CHARACTERS[selected_char_journal]
        current_aff = get_affinity(clean_pseudo, selected_char_journal, c_data["initial_affinity"])
        
        str_lit.markdown(f"""
        <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px; margin-bottom: 20px; display: flex; align-items: center; gap: 20px;">
            <img src="{c_data['img']}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #58a6ff;">
            <div>
                <h3 style="margin: 0 0 5px 0;">{selected_char_journal}</h3>
                <p style="margin: 0; color: #8b949e; font-size: 14px;">Niveau d'affinité actuel : <strong>{current_aff}%</strong></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        str_lit.subheader("🔒 Paliers de Souvenirs & Trésors Émotionnels")
        
        rewards = {
            25: {"title": "Palier 25% : Pensées Intimes", "desc": "Découvre ce que le personnage pense secrètement de toi lorsqu'il est seul."},
            50: {"title": "Palier 50% : Le Journal Secret", "desc": "Une page intime écrite de sa main sur l'évolution de ses sentiments."},
            75: {"title": "Palier 75% : La Lettre d'Amour", "desc": "Une déclaration poignante et exclusive rédigée par le personnage."},
            100: {"title": "Palier 100% : La Chanson de votre Histoire", "desc": "Un morceau poétique unique créé à partir de vos souvenirs de discussion."}
        }
        
        chat_history_for_gen = load_msgs(clean_pseudo, selected_char_journal, limit=30)
        history_text_snippet = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_gen])

        for threshold, info in rewards.items():
            unlocked = current_aff >= threshold
            if unlocked:
                str_lit.markdown(f"""
                <div style="background-color: #161b22; border: 1px solid #3fb950; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <div style="color: #3fb950; font-weight: 700; font-size: 13px; margin-bottom: 4px;">✅ {info['title']} (Débloqué)</div>
                    <div style="color: #8b949e; font-size: 13px; margin-bottom: 10px;">{info['desc']}</div>
                """, unsafe_allow_html=True)
                
                gen_key = f"gen_content_{selected_char_journal}_{threshold}"
                if gen_key not in str_lit.session_state:
                    str_lit.session_state[gen_key] = ""

                if str_lit.button(f"📖 Lire le contenu ({threshold}%)", key=f"btn_read_{selected_char_journal}_{threshold}"):
                    if client:
                        with str_lit.spinner("Inspiration des souvenirs en cours..."):
                            prompt_type_map = {
                                25: f"Rédige un court paragraphe intime à la première personne simulant les pensées secrètes de {selected_char_journal} envers {clean_pseudo}.",
                                50: f"Rédige une page de journal intime écrite par {selected_char_journal} qui évoque ses doutes et son attachement grandissant pour {clean_pseudo}.",
                                75: f"Rédige une magnifique lettre d'amour romantique et immersive signée par {selected_char_journal} adressée à {clean_pseudo}.",
                                100: f"Rédige les paroles d'une chanson romantique inspirée par l'histoire d'amour entre {selected_char_journal} et {clean_pseudo} en te basant sur ces échanges : {history_text_snippet}"
                            }
                            try:
                                resp = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=[
                                        {"role": "system", "content": c_data["prompt"]},
                                        {"role": "user", "content": prompt_type_map[threshold]}
                                    ],
                                    temperature=0.85
                                )
                                str_lit.session_state[gen_key] = resp.choices[0].message.content
                            except Exception as e:
                                str_lit.session_state[gen_key] = f"Erreur de génération : {e}"
                    else:
                        str_lit.session_state[gen_key] = c_data.get("memories", {}).get(threshold, "Un souvenir précieux gravé dans les ombres.")

                if str_lit.session_state[gen_key]:
                    str_lit.markdown(f"""
                    <div style="font-family: 'Georgia', serif; font-size: 14px; line-height: 1.6; color: #e6edf3; background: #0b0e14; padding: 12px; border-radius: 8px; border-left: 3px solid #3fb950; margin-top: 8px; white-space: pre-wrap;">
                        {str_lit.session_state[gen_key]}
                    </div>
                    """, unsafe_allow_html=True)

                str_lit.markdown("</div>", unsafe_allow_html=True)
            else:
                str_lit.markdown(f"""
                <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; margin-bottom: 10px; opacity: 0.6;">
                    <div style="color: #8b949e; font-weight: 700; font-size: 13px; margin-bottom: 4px;">🔒 {info['title']} (Requiert {threshold}% d'affinité)</div>
                    <div style="color: #8b949e; font-style: italic; font-size: 14px;">??? Continuez à discuter pour percer ce secret...</div>
                </div>
                """, unsafe_allow_html=True)

elif str_lit.session_state.page == "chat":
    current_char = str_lit.session_state.char_select
    char_data = CHARACTERS.get(current_char, {"img": "", "quote": "", "prompt": f"Tu es {current_char}.", "initial_affinity": 0, "memories": {}})

    user_avatar_url = USER_DEFAULT_AVATAR
    if supabase:
        try:
            res_u = supabase.table("users").select("avatar_url").eq("pseudo", clean_pseudo).maybe_single().execute()
            if res_u and res_u.data and res_u.data.get("avatar_url"):
                user_avatar_url = force_image_url(res_u.data.get("avatar_url"), is_user=True)
        except Exception:
            pass

    col_h1, col_h2, col_h3, col_h4 = str_lit.columns([1, 3, 2, 1.5])
    with col_h1:
        str_lit.image(char_data["img"], width=70)
    with col_h2:
        str_lit.title(current_char)
        str_lit.caption(char_data["quote"])
    with col_h3:
        affinity_score = get_affinity(clean_pseudo, current_char, char_data["initial_affinity"])
        
        aff_status_text = "Relation neutre"
        if affinity_score >= 80:
            aff_status_text = "❤️ Passion / Fusionnel (80%+)"
        elif affinity_score >= 50:
            aff_status_text = "🤝 Confiance mutuelle (50%+)"
        elif affinity_score <= 25:
            aff_status_text = "❄️ Méfiance / Distant (<25%)"
            
        str_lit.markdown(f"### 💖 Affinité : {affinity_score}%")
        str_lit.caption(aff_status_text)
        str_lit.progress(affinity_score / 100.0)
    with col_h4:
        str_lit.write("")
        if str_lit.button("🗑️ Tout effacer", key="btn_clear_entire_chat"):
            p_clean = str(clean_pseudo).strip()
            c_name_clean = str(current_char).strip()
            if supabase:
                try:
                    supabase.table("messages").delete().eq("user_pseudo", p_clean).eq("char_name", c_name_clean).execute()
                    supabase.table("affinities").delete().eq("user_pseudo", p_clean).eq("char_name", c_name_clean).execute()
                except:
                    pass
            cache_key = f"{p_clean}_{c_name_clean}"
            if cache_key in str_lit.session_state.messages_cache:
                del str_lit.session_state.messages_cache[cache_key]
            if cache_key in str_lit.session_state.affinities_cache:
                del str_lit.session_state.affinities_cache[cache_key]
            str_lit.success("Conversation effacée !")
            str_lit.rerun()

    str_lit.markdown("---")

    messages = load_msgs(clean_pseudo, current_char, limit=100)

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
                    init_prompt = [
                        {"role": "system", "content": char_data["prompt"] + f" RÈGLE ABSOLUE POUR CE PREMIER MESSAGE : Tu ne connais PAS encore le prénom de l'interlocutrice. Il est strictement interdit d'utiliser le prénom '{clean_pseudo}' ou n'importe quel autre prénom. Utilise des termes neutres."},
                        {"role": "user", "content": f"Écris un premier message d'introduction immersif et détaillé pour débuter le roleplay. CONSIGNE D'ACCROCHE : Intègre naturellement la phrase \"{char_data['quote']}\"."}
                    ]
                    with str_lit.spinner(f"Génération de l'introduction avec {current_char}..."):
                        resp_init = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=init_prompt,
                            temperature=0.7,
                        )
                    intro_msg = resp_init.choices[0].message.content
                    intro_msg = intro_msg.replace(clean_pseudo, "tu").replace(clean_pseudo.lower(), "tu")
                except Exception:
                    intro_msg = char_data["quote"]
            else:
                intro_msg = char_data["quote"]

        save_msg(clean_pseudo, current_char, "assistant", intro_msg)
        messages = load_msgs(clean_pseudo, current_char, limit=100)

    for idx, msg in enumerate(messages):
        msg_id = msg.get("id")
        edit_key = f"edit_mode_{idx}"
        
        if edit_key not in str_lit.session_state:
            str_lit.session_state[edit_key] = False
        
        if msg["role"] == "assistant":
            col_avatar, col_content, col_actions = str_lit.columns([1, 5, 1.3])
            with col_avatar:
                str_lit.image(char_data["img"], width=65)
            with col_content:
                if str_lit.session_state[edit_key]:
                    new_text = str_lit.text_area("Modifier la réponse :", value=msg["content"], key=f"txt_area_{idx}")
                    col_save, col_cancel = str_lit.columns(2)
                    with col_save:
                        if str_lit.button("💾 Enregistrer", key=f"save_edit_{idx}"):
                            msg["content"] = new_text
                            str_lit.session_state[edit_key] = False
                            cache_key = f"{clean_pseudo}_{current_char}"
                            str_lit.session_state.messages_cache[cache_key] = messages
                            if supabase and msg_id:
                                try:
                                    supabase.table("messages").update({"content": new_text}).eq("id", msg_id).execute()
                                except Exception:
                                    pass
                            str_lit.success("Modifié !")
                            str_lit.rerun()
                    with col_cancel:
                        if str_lit.button("❌ Annuler", key=f"cancel_edit_{idx}"):
                            str_lit.session_state[edit_key] = False
                            str_lit.rerun()
                else:
                    if "Roman" in reading_style:
                        str_lit.markdown(f'<div class="novel-dialogue">{msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        str_lit.markdown(f'<div class="sms-bubble-bot">{msg["content"]}</div>', unsafe_allow_html=True)
                    
            with col_actions:
                col_b1, col_b2 = str_lit.columns(2)
                with col_b1:
                    if str_lit.button("✏️", key=f"btn_edit_{idx}", help="Modifier"):
                        str_lit.session_state[edit_key] = not str_lit.session_state[edit_key]
                        str_lit.rerun()
                with col_b2:
                    if str_lit.button("❌", key=f"btn_del_{idx}", help="Supprimer"):
                        messages.pop(idx)
                        cache_key = f"{clean_pseudo}_{current_char}"
                        str_lit.session_state.messages_cache[cache_key] = messages
                        if supabase and msg_id:
                            try:
                                supabase.table("messages").delete().eq("id", msg_id).execute()
                            except:
                                pass
                        str_lit.rerun()
                
                if idx == len(messages) - 1:
                    if str_lit.button("🔄", key=f"btn_regen_{idx}", help="Régénérer"):
                        messages.pop()
                        if supabase and msg_id:
                            try:
                                supabase.table("messages").delete().eq("id", msg_id).execute()
                            except:
                                pass
                        
                        current_aff = get_affinity(clean_pseudo, current_char, char_data["initial_affinity"])
                        behavior_boost = ""
                        if current_aff >= 80:
                            behavior_boost = "\n- ÉTAT D'ESPRIT ACTUEL : Affinité très élevée (80%+). Le personnage est profondément attaché, vulnérable, et montre des sentiments intenses ou passionnés envers l'interlocutrice."
                        elif current_aff <= 25:
                            behavior_boost = "\n- ÉTAT D'ESPRIT ACTUEL : Affinité basse. Le personnage reste distant, méfiant, sur ses gardes ou provocateur."
                        else:
                            behavior_boost = "\n- ÉTAT D'ESPRIT ACTUEL : Affinité neutre/évolutive. La relation se construit pas à pas."

                        aff_context = f" Niveau d'affinité actuel : {current_aff}%."
                        narration_rule = "\n- RÈGLE DE MISE EN SCÈNE : Intègre toujours des descriptions d'ambiance physique, de gestes ou de décors en italique pour renforcer l'immersion comme dans un roman."
                        memory_context = "\n- MÉMOIRE DE L'HISTOIRE : Ne perds jamais le fil des actions précédentes, des lieux visités et des émotions exprimées dans les messages précédents."
                        
                        long_term_summary = get_story_summary(clean_pseudo, current_char)
                        summary_section = ""
                        if long_term_summary:
                            summary_section = f"\n- SOUVENIRS ET HISTORIQUE GLOBAL DE VOTRE RELATION (Mémoire à long terme) : {long_term_summary}\n"

                        prompt_systeme_complet = (
                            f"{char_data.get('prompt', '')}\n"
                            f"RAPPELS IMPORTANTS POUR LA MÉMOIRE :\n"
                            f"- L'interlocutrice s'appelle {clean_pseudo}.\n"
                            f"-{aff_context}"
                            f"{behavior_boost}"
                            f"{summary_section}"
                            f"{narration_rule}"
                            f"{memory_context}"
                        )
                        api_messages = [{"role": "system", "content": prompt_systeme_complet}]
                        for m in messages[-40:]:
                            role = m.get("role")
                            content = m.get("content")
                            if role in ["user", "assistant"] and content:
                                api_messages.append({"role": role, "content": content})

                        if client:
                            try:
                                response = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=api_messages,
                                    temperature=0.9,
                                )
                                bot_reply = response.choices[0].message.content
                                save_msg(clean_pseudo, current_char, "assistant", bot_reply)
                                cache_key = f"{clean_pseudo}_{current_char}"
                                if cache_key in str_lit.session_state.messages_cache:
                                    del str_lit.session_state.messages_cache[cache_key]
                            except:
                                pass
                        str_lit.rerun()
        else:
            col_content_u, col_avatar_u = str_lit.columns([5, 1])
            with col_content_u:
                if str_lit.session_state[edit_key]:
                    new_u_text = str_lit.text_area("Modifier ton message :", value=msg["content"], key=f"txt_usr_{idx}")
                    col_save_u, col_cancel_u = str_lit.columns(2)
                    with col_save_u:
                        if str_lit.button("💾 Valider", key=f"save_usr_{idx}"):
                            msg["content"] = new_u_text
                            str_lit.session_state[edit_key] = False
                            cache_key = f"{clean_pseudo}_{current_char}"
                            str_lit.session_state.messages_cache[cache_key] = messages
                            if supabase and msg_id:
                                try:
                                    supabase.table("messages").update({"content": new_u_text}).eq("id", msg_id).execute()
                                except:
                                    pass
                            str_lit.success("Message modifié !")
                            str_lit.rerun()
                    with col_cancel_u:
                        if str_lit.button("❌ Annuler", key=f"cancel_usr_{idx}"):
                            str_lit.session_state[edit_key] = False
                            str_lit.rerun()
                else:
                    str_lit.markdown(f"""
                    <div style="background-color: #21262d; font-family: 'Georgia', serif; font-size: 15px; line-height: 1.6; color: #e6edf3; padding: 15px; border-radius: 10px; border-right: 4px solid #d299ea; margin-bottom: 10px; text-align: right; white-space: pre-wrap;">
                        {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                
                col_ub1, col_ub2 = str_lit.columns([1, 10])
                with col_ub1:
                    if str_lit.button("✏️", key=f"btn_edit_u_{idx}", help="Modifier"):
                        str_lit.session_state[edit_key] = not str_lit.session_state[edit_key]
                        str_lit.rerun()
                with col_ub2:
                    if str_lit.button("❌", key=f"btn_del_u_{idx}", help="Supprimer"):
                        messages.pop(idx)
                        cache_key = f"{clean_pseudo}_{current_char}"
                        str_lit.session_state.messages_cache[cache_key] = messages
                        if supabase and msg_id:
                            try:
                                supabase.table("messages").delete().eq("id", msg_id).execute()
                            except:
                                pass
                        str_lit.rerun()

            with col_avatar_u:
                valid_avatar = user_avatar_url if (user_avatar_url and str(user_avatar_url).startswith("http") and "undefined" not in user_avatar_url and "null" not in user_avatar_url) else USER_DEFAULT_AVATAR
                str_lit.markdown(f"""
                <div style="display: flex; justify-content: flex-end;">
                    <img src="{valid_avatar}" style="width: 55px; height: 55px; border-radius: 50%; object-fit: cover; border: 2px solid #d299ea;" onerror="this.onerror=null;this.src='{USER_DEFAULT_AVATAR}';">
                </div>
                """, unsafe_allow_html=True)

    str_lit.markdown("<br>", unsafe_allow_html=True)
    
    user_input = str_lit.text_area("Écris ta réponse...", key="user_message_input", label_visibility="collapsed", height=90)
    send_clicked = str_lit.button("Envoyer 🚀", key="send_message_btn", use_container_width=True)

    if send_clicked and user_input and user_input.strip():
        if not client:
            str_lit.error("❌ Erreur : Le client Groq n'est pas initialisé.")
        else:
            save_msg(clean_pseudo, current_char, "user", user_input.strip())
            
            # Rechargement de tous les messages pour compter le total exact
            messages_actuels = load_msgs(clean_pseudo, current_char, limit=1000)
            total_messages = len(messages_actuels)
            
            old_aff = get_affinity(clean_pseudo, current_char, char_data["initial_affinity"])
            
            # L'affinité augmente de +1 uniquement si le total de messages est un multiple de 20
            if total_messages > 0 and total_messages % 20 == 0:
                new_aff = update_affinity(clean_pseudo, current_char, 1)
            else:
                new_aff = old_aff
            
            milestones = [25, 50, 75, 100]
            for m in milestones:
                if old_aff < m and new_aff >= m:
                    str_lit.balloons()
                    str_lit.success(f"✨ Félicitations ! Vous avez atteint le palier d'affinité de {m}% avec {current_char}. Un nouveau **Souvenir** a été débloqué dans votre Journal Intime !")

            cache_key = f"{clean_pseudo}_{current_char}"
            if cache_key in str_lit.session_state.messages_cache:
                del str_lit.session_state.messages_cache[cache_key]

            behavior_boost = ""
            if new_aff >= 80:
                behavior_boost = "\n- ÉTAT D'ESPRIT ACTUEL : Affinité très élevée (80%+). Le personnage est profondément attaché, vulnérable, et montre des sentiments intenses ou passionnés envers l'interlocutrice."
            elif new_aff <= 25:
                behavior_boost = "\n- ÉTAT D'ESPRIT ACTUEL : Affinité basse. Le personnage reste distant, méfiant, sur ses gardes ou provocateur."
            else:
                behavior_boost = "\n- ÉTAT D'ESPRIT ACTUEL : Affinité neutre/évolutive. La relation se construit pas à pas."

            aff_context = f" Niveau d'affinité actuel : {new_aff}%."
            narration_rule = "\n- RÈGLE DE MISE EN SCÈNE : Intègre toujours des descriptions d'ambiance physique, de gestes ou de décors en italique pour renforcer l'immersion comme dans un roman."
            memory_context = "\n- MÉMOIRE DE L'HISTOIRE : Ne perds jamais le fil des actions précédentes, des lieux visités et des émotions exprimées dans les messages précédents."
            
            long_term_summary = get_story_summary(clean_pseudo, current_char)
            summary_section = ""
            if long_term_summary:
                summary_section = f"\n- SOUVENIRS ET HISTORIQUE GLOBAL DE VOTRE RELATION (Mémoire à long terme) : {long_term_summary}\n"

            prompt_systeme_complet = (
                f"{char_data['prompt']}\n"
                f"RAPPELS IMPORTANTS POUR LA MÉMOIRE :\n"
                f"- L'interlocutrice s'appelle {clean_pseudo}.\n"
                f"-{aff_context}"
                f"{behavior_boost}"
                f"{summary_section}"
                f"{narration_rule}"
                f"{memory_context}"
            )
            
            api_messages = [{"role": "system", "content": prompt_systeme_complet}]
            
            for m in messages_actuels[-40:]:
                role = m.get("role")
                content = m.get("content")
                if role in ["user", "assistant"] and content:
                    api_messages.append({"role": role, "content": content})
            
            try:
                with str_lit.spinner(f"{current_char} est en train d'écrire..."):
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=api_messages,
                        temperature=0.85,
                    )
                bot_reply = response.choices[0].message.content
                if bot_reply:
                    save_msg(clean_pseudo, current_char, "assistant", bot_reply)
                    
                    if len(messages_actuels) > 0 and len(messages_actuels) % 10 == 0:
                        update_story_summary(clean_pseudo, current_char, client, messages_actuels[-15:])

                    if cache_key in str_lit.session_state.messages_cache:
                        del str_lit.session_state.messages_cache[cache_key]
                    str_lit.rerun()
            except Exception as e:
                str_lit.error(f"❌ Erreur technique : {e}")

elif str_lit.session_state.page == "create_character":
    if os.path.exists(CREATE_CHARACTER_BANNER):
        str_lit.image(CREATE_CHARACTER_BANNER, use_container_width=True)
    else:
        str_lit.title("✨ Créer un Personnage")
    str_lit.markdown("---")

    with str_lit.form("create_char_form"):
        new_name = str_lit.text_input("Nom du personnage")
        new_gender = str_lit.selectbox("Sexe / Genre", ["Homme", "Femme", "Non-binaire / Autre"])
        new_temperament = str_lit.selectbox("Tempérament de départ", ["Neutre", "Hostile / Froid", "Passionné / Amoureux", "Mystérieux / Taquin"])
            
        new_quote = str_lit.text_input("Phrase d'accroche (Citation)")
        new_desc = str_lit.text_area("Description / Personnalité / Contexte")
        uploaded_file = str_lit.file_uploader("Importer l'image du personnage", type=["png", "jpg", "jpeg", "jfif"])
        new_vis = str_lit.selectbox("Visibilité", ["Public", "Privé"])

        submitted = str_lit.form_submit_button("Créer le Personnage")
        if submitted:
            if new_name.strip():
                if supabase:
                    try:
                        final_img = ""
                        if uploaded_file:
                            final_img = upload_image_to_supabase(uploaded_file, folder="characters")

                        supabase.table("custom_characters").insert({
                            "name": new_name.strip(),
                            "gender": new_gender,
                            "temperament": new_temperament,
                            "initial_affinity": 0,
                            "quote": new_quote,
                            "description": new_desc,
                            "img_url": final_img,
                            "visibility": new_vis,
                            "creator_pseudo": clean_pseudo
                        }).execute()
                        str_lit.success(f"Personnage créé avec succès !")
                        str_lit.session_state.page = "home"
                        str_lit.rerun()
                    except Exception as e:
                        str_lit.error(f"Erreur : {e}")
            else:
                str_lit.error("Veuillez donner un nom.")

elif str_lit.session_state.page == "profile":
    banner_path = "profil utilisateur.jfif"
    if os.path.exists(banner_path):
        str_lit.image(banner_path, use_container_width=True)
    else:
        str_lit.title("Profil Utilisateur")
        
    str_lit.write(f"Ton sanctuaire personnel, **{clean_pseudo}**.")
    str_lit.markdown("---")

    user_email = "Non disponible"
    avatar_url = USER_DEFAULT_AVATAR

    if supabase:
        try:
            res = supabase.table("users").select("*").eq("pseudo", clean_pseudo).maybe_single().execute()
            if res and res.data:
                user_email = res.data.get("email", "Non renseigné")
                if res.data.get("avatar_url"):
                    avatar_url = force_image_url(res.data.get("avatar_url"), is_user=True)
        except:
            pass

    col_av1, col_av2 = str_lit.columns([1.5, 8.5])
    
    with col_av1:
        str_lit.markdown(f"""
        <div style="position: relative; display: inline-block;">
            <img src="{avatar_url}" style="width: 95px; height: 95px; border-radius: 50%; object-fit: cover; border: 2px solid #d299ea; box-shadow: 0 0 15px rgba(210,153,234,0.3);" onerror="this.onerror=null;this.src='{USER_DEFAULT_AVATAR}';">
        </div>
        """, unsafe_allow_html=True)

    with col_av2:
        str_lit.markdown(f"""
        <div style="padding-top: 10px;">
            <h2 style="margin: 0 0 5px 0; color: #f0f6fc; font-family: 'Georgia', serif;">{clean_pseudo}</h2>
            <p style="margin: 0; color: #8b949e; font-size: 14px;">Membre des ombres • E-mail : {user_email}</p>
        </div>
        """, unsafe_allow_html=True)

    str_lit.markdown("<br>", unsafe_allow_html=True)
    
    with str_lit.expander("✏️ Modifier mon avatar", expanded=False):
        uploaded_avatar = str_lit.file_uploader("Choisir une nouvelle image", type=["png", "jpg", "jpeg", "jfif"], key="mobile_safe_avatar_uploader")
        if uploaded_avatar:
            if str_lit.button("💾 Enregistrer le nouvel avatar", key="save_mobile_avatar"):
                if supabase:
                    try:
                        with str_lit.spinner("Téléversement en cours..."):
                            new_avatar_url = upload_image_to_supabase(uploaded_file=uploaded_avatar, folder="avatars")
                            if new_avatar_url:
                                supabase.table("users").update({"avatar_url": new_avatar_url}).eq("pseudo", clean_pseudo).execute()
                                str_lit.success("Avatar mis à jour avec succès !")
                                str_lit.rerun()
                    except Exception as e:
                        str_lit.error(f"Erreur : {e}")

    str_lit.markdown("<br>", unsafe_allow_html=True)
    str_lit.subheader("🖤 Mes Créations ténébreuses")
    if supabase:
        try:
            my_chars_res = supabase.table("custom_characters").select("*").or_(f"creator_pseudo.eq.{clean_pseudo},creator_pseudo.is.null").execute()
            if my_chars_res and my_chars_res.data:
                cols = str_lit.columns(4)
                for i, char in enumerate(my_chars_res.data):
                    with cols[i % 4]:
                        c_name_val = char.get("name")
                        raw_c_img = char.get("img_url", "").strip()
                        c_img = force_image_url(raw_c_img, is_user=False)

                        vis_status = char.get('visibility', 'Public')
                        badge_color = "#ff7b72" if vis_status == "Privé" else "#3fb950"
                            
                        str_lit.markdown(f"""
                        <div style="background-color: #161b22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 10px;">
                            <img src="{c_img}" style="width: 100%; height: 130px; object-fit: cover; border-radius: 8px; margin-bottom: 8px;">
                            <strong style="color: #ffffff; font-size: 14px; display: block; margin-bottom: 4px;">{c_name_val}</strong>
                            <span style="font-size: 10px; color: {badge_color}; background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">● {vis_status}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        str_lit.markdown(f'''
                        <a href="?user={clean_pseudo}&chat_target={c_name_val}" target="_self" class="custom-action-btn" style="margin-bottom: 6px;">💬 Discuter</a>
                        <a href="?user={clean_pseudo}&action=delete_char&char={c_name_val}" target="_self" class="custom-danger-btn">🗑️ Supprimer</a>
                        ''', unsafe_allow_html=True)
            else:
                str_lit.info("Vous n'avez créé aucun personnage pour l'instant.")
        except Exception as e:
            str_lit.error(f"Erreur : {e}")
