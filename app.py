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
# Récupération des clés API depuis les secrets Streamlit ou les variables d'environnement
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key and "GROQ_API_KEY" in str_lit.secrets:
    groq_key = str_lit.secrets["GROQ_API_KEY"]

hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
if not hf_api_key and "HUGGINGFACE_API_KEY" in str_lit.secrets:
    hf_api_key = str_lit.secrets["HUGGINGFACE_API_KEY"]

# --- CONSTANTES IMAGES ---
# Assurez-vous que ces fichiers existent dans le dossier de votre app
BACKGROUND_IMG_NAME = "bg.png"
SIDEBAR_HEADER_IMG = "couple.png"


def generer_image_huggingface(prompt_image, current_char_name=None):
    """
    Génère une image en mode Text-to-Image pur avec un style STRICTEMENT PHOTORÉALISTE 
    et cinématographique pour chaque personnage.
    """
    if not hf_api_key:
        return None, "Clé API Hugging Face manquante."
    try:
        client_hf = InferenceClient(
            model="stabilityai/stable-diffusion-xl-base-1.0", token=hf_api_key
        )
        
        # Identités visuelles rigoureusement axées sur le PHOTORÉALISME et la photographie réelle.
        # Ces descriptions guident le modèle SDXL pour obtenir un rendu type "photo de studio".
        character_identities = {
            "Caelum": "A hyper-realistic cinematic close-up photograph of Caelum, a handsome young man with defined jawline, dark hair, and piercing eyes, wearing a dark luxury coat with a high collar. Shot on 35mm lens, photorealistic skin texture, detailed facial pores, dramatic studio lighting, cinematic grading, high quality, raw photo.",
            "Alexei": "A hyper-realistic cinematic photograph of Alexei, a dangerous mafia leader with intense eyes and slick dark hair, wearing an elegant dark tailored suit, professional color grading, photorealistic, cinematic lighting, detailed skin pores.",
            "Killian": "A hyper-realistic cinematic photograph of Killian, a cool biker with messy hair and a leather jacket, intense gaze, outdoor natural daylight, photorealistic portrait, sharp focus, high-end photography.",
            "Lucas": "A hyper-realistic cinematic photograph of Lucas, a popular high school boy with a charming smile and trendy casual clothes, soft natural lighting, photorealistic, portrait photography style.",
            "Ethan": "A hyper-realistic cinematic photograph of Ethan, a fierce alpha wolf man with wild hair and intense piercing eyes, mysterious aura, dark cinematic moonlight, photorealistic, highly detailed.",
            "Léo": "A hyper-realistic cinematic photograph of Leo, a stylish streamer boy with headphones around his neck, energetic look, colorful RGB studio lighting, photorealistic portrait, sharp details.",
            "Liam": "A hyper-realistic cinematic photograph of Liam, an older brother figure with a calm and protective expression, warm natural indoor lighting, photorealistic, professional portrait.",
            "Noah": "A hyper-realistic cinematic photograph of Noah, a handsome quarterback athlete wearing a sports jacket, athletic photoshoot style, natural sunlight, photorealistic."
        }

        # Récupération de l'identité réaliste du personnage.
        # Pour les personnages utilisateurs, on génère un portrait photo générique mais réaliste.
        base_custom_identity = "A hyper-realistic professional studio portrait photograph of {char_name}, detailed skin texture, cinematic lighting, shot on 35mm lens, raw photo style."
        
        char_identity = character_identities.get(
            current_char_name, 
            base_custom_identity.format(char_name=current_char_name)
        )

        # Construction du prompt final ultra-orienté photo réelle (exclusion totale de style dessin/anime).
        # On combine l'identité du personnage avec le contexte de la scène (prompt_image).
        prompt_final = (
            f"{char_identity}, {prompt_image}, "
            f"RAW photo, highly detailed skin pores, realistic human anatomy, shot on 35mm film, professional photography, cinematic lighting, masterpiece, 8k, photorealistic."
        )

        # Appel à l'API Hugging Face
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

# --- STYLE GLOBAL & DESIGN (Thème sombre) ---
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

# --- PERSISTANCE PAR URL (Pour le login via lien direct) ---
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

# --- SUPABASE FUNCTIONS (Gestion de la base de données) ---

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
            .execute()
        )
        if res.data:
            return [{"role": r["role"], "content": r["content"]} for r in res.data]
        return []
    except Exception:
        return []


def get_all_characters():
    """
    Charge les personnages par défaut et les personnages personnalisés depuis Supabase.
    Définit le prompt système pour le LLM Groq.
    """
    # IMPORTANT : Cette instruction demande à l'IA d'inclure une description d'image DÉTAILLÉE
    # pour garantir la cohérence visuelle.
    base_instruction = (
        " Reste strictement dans ton rôle, adopte un ton immersif de roleplay"
        " romancé. IMPORTANT : À la fin de CHAQUE message, tu dois obligatoirement"
        " intégrer une balise visuelle au format exact suivant pour illustrer"
        " l'action en cours sous forme de photographie réelle : [IMAGE: description détaillée en anglais de"
        " l'ambiance, du personnage ou du décor, photorealistic shot]."
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

    # Ajout des personnages personnalisés depuis Supabase
    if supabase:
        try:
            res = supabase.table("custom_characters").select("*").execute()
            if res.data:
                for item in res.data:
                    # Affiche le perso s'il est public ou si c'est le créateur
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
    """Récupère la liste des personnages avec qui l'utilisateur a
