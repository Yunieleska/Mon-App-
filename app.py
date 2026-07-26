import streamlit as st
from supabase import create_client
from groq import Groq
import os

# --- CONFIGURATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- STYLE GLOBAL & GRILLE RESPONSIVE MOBILE/PC ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #ffffff;
    }
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
    }
    /* Grille magique : 2 colonnes sur téléphone, 4 colonnes sur PC */
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

# --- SESSION INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "pseudo" not in st.session_state: st.session_state.pseudo = "Invité"
if "page" not in st.session_state: st.session_state.page = "home"
if "char_select" not in st.session_state: st.session_state.char_select = "Caelum"

try:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.logged_in = True
        user_data = supabase.table("users").select("pseudo").eq("id", session.user.id).single().execute()
        if user_data.data:
            st.session_state.pseudo = user_data.data["pseudo"]
except Exception:
    pass

# --- SUPABASE FUNCTIONS ---
def save_msg(pseudo, char, role, content):
    try:
        supabase.table("messages").insert({"user_pseudo": pseudo, "char_name": char, "role": role, "content": content}).execute()
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

def load_msgs(pseudo, char):
    try:
        res = supabase.table("messages").select("role, content").eq("user_pseudo", pseudo).eq("char_name", char).execute()
        return [{"role": r["role"], "content": r["content"]} for r in res.data]
    except:
        return []

def get_user_conversations(pseudo):
    try:
        res = supabase.table("messages").select("char_name, content, role").eq("user_pseudo", pseudo).execute()
        chars_met = {}
        for r in res.data:
            chars_met[r["char_name"]] = r["content"]
        return chars_met
    except:
        return {}

def get_all_characters():
    chars = {
        "Caelum": {
            "img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", 
            "prompt": "Tu es Caelum, Prince des Ténèbres.",
            "quote": "Ne t'approche pas de moi. Ma vie est déjà tracée, et tu n'as rien à y faire."
        },
        "Alexei": {
            "img": "https://i.pinimg.com/1200x/b4/36/28/b436280907640408f8e5bd9644c07a63.jpg", 
            "prompt": "Tu es Alexei, mafieux.",
            "quote": "Regardez qui s'est perdue sur mon territoire. La petite princesse des Volkov..."
        },
        "Killian": {
            "img": "https://i.pinimg.com/1200x/cf/a9/be/cfa9beb0f05ad076286f3982827c061b.jpg", 
            "prompt": "Tu es Killian, motard.",
            "quote": "Respire, c'est fini... T'as pas changé, toujours aussi maladroite."
        },
        "Lucas": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/public/storyia-images/lucas.png.PNG", 
            "prompt": "Tu es Lucas, populaire.",
            "quote": "On s'esquive tous les deux et on va squatter ton canapé devant une série ?"
        },
        "Ethan": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/sign/storyia-images/ethan.png?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV85OTJlMjk3Yy0zMjkyLTQ3OWMtYTFhYi1kNTkwOGMzYzdmNzQiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJzdG9yeWlhLWltYWdlcy9ldGhhbi5wbmciLCJzY29wZSI6ImRvd25sb2FkIiwiaWF0IjoxNzg1MTAyMzk3LCJleHAiOjE4MTY2MzgzOTd9.qwJMbypu9ehzFbY7l89vvVSk9wHIGFWF5tiYiEQqdmY", 
            "prompt": "Tu es Ethan, Loup Alpha.",
            "quote": "La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines..."
        },
        "Léo": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/sign/storyia-images/leo.png.PNG?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV85OTJlMjk3Yy0zMjkyLTQ3OWMtYTFhYi1kNTkwOGMzYzdmNzQiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJzdG9yeWlhLWltYWdlcy9sZW8ucG5nLlBORyIsInNjb3BlIjoiZG93bmxvYWQiLCJpYXQiOjE3ODUxMDI1MTAsImV4cCI6MTgxNjYzODUxMH0.dVAfMNONuMdKiE00cA4n7dutO4D8TfGz8v1OFuFItGE", 
            "prompt": "Tu es Léo, streameur.",
            "quote": "Prête à ce qu'on détruise l'équipe d'en face ?"
        },
        "Liam": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/sign/storyia-images/liam.png.PNG?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV85OTJlMjk3Yy0zMjkyLTQ3OWMtYTFhYi1kNTkwOGMzYzdmNzQiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJzdG9yeWlhLWltYWdlcy9saWFtLnBuZy5QTkciLCJzY29wZSI6ImRvd25sb2FkIiwiaWF0IjoxNzg1MTAyNTM2LCJleHAiOjE4MTY2Mzg1MzZ9.u6k31EmGbpgzmcmKZcmidKDid0iqGqF_p78ALJdtP08", 
            "prompt": "Tu es Liam, le grand frère.",
            "quote": "Salut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit."
        },
        "Noah": {
            "img": "https://ipbczphrawlrlglwwwpq.supabase.co/storage/v1/object/sign/storyia-images/noah.png.PNG?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV85OTJlMjk3Yy0zMjkyLTQ3OWMtYTFhYi1kNTkwOGMzYzdmNzQiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJzdG9yeWlhLWltYWdlcy9ub2FoLnBuZy5QTkciLCJzY29wZSI6ImRvd25sb2FkIiwiaWF0IjoxNzg1MTAyNTgwLCJleHAiOjE4MTY2Mzg1ODB9.dSDMmVTEts9VHKhmbEHqleTJNbiqxhQQ96Q3P5AurFs", 
            "prompt": "Tu es Noah, quarterback star.",
            "quote": "Dis, tu crois qu'on est tous obligés de jouer un rôle pour plaire ?"
        }
    }
    
    try:
        res = supabase.table("custom_characters").select("*").execute()
        if res.data:
            for item in res.data:
                if item["is_public"] or item["creator"] == st.session_state.pseudo:
                    chars[item["name"]] = {
                        "img": item["img_url"] if item["img_url"] and (item["img_url"].startswith("http") or os.path.exists(item["img_url"])) else "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg",
                        "prompt": f"Tu es {item['name']}, un personnage {item['sex']}. Description : {item['description']}. Personnages secondaires / Contexte additionnel : {item['secondary_chars']}",
                        "quote": item["quote"] if "quote" in item and item["quote"] else f"Bonjour, je suis {item['name']}."
                    }
    except Exception:
        pass
        
    return chars

CHARACTERS = get_all_characters()

# --- LOGIN LOGIC ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("bg.png"):
            st.image("bg.png")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            email_log = st.text_input("E-mail", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email_log, "password": password})
                    if res.user:
                        st.session_state.logged_in = True
                        user_data = supabase.table("users").select("pseudo").eq("id", res.user.id).single().execute()
                        if user_data.data:
                            st.session_state.pseudo = user_data.data["pseudo"]
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur de connexion : {e}")

        with tab2:
            new_pseudo = st.text_input("Pseudo", key="sign_pseudo")
            new_email = st.text_input("E-mail", key="sign_email")
            new_pass = st.text_input("Password", type="password", key="sign_pass")
            reponse_secrete = st.text_input("Question : Ta couleur préférée ?", key="sign_q")
            if st.button("Sign Up"):
                try:
                    auth_res = supabase.auth.sign_up({"email": new_email, "password": new_pass})
                    if auth_res.user:
                        supabase.table("users").insert({
                            "id": auth_res.user.id, 
                            "pseudo": new_pseudo, 
                            "email": new_email, 
                            "secret_answer": reponse_secrete
                        }).execute()
                        st.success("Compte créé ! Veuillez vous connecter.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
    st.stop()

# --- SIDEBAR ---
if os.path.exists("couple.png"):
    st.sidebar.image("couple.png")
st.sidebar.info(f"Connecté : **{st.session_state.pseudo}**")

if st.sidebar.button("🏠 Home"): 
    st.session_state.page = "home"
    st.rerun()

if st.sidebar.button("✨ Créer un Personnage"):
    st.session_state.page = "create_character"
    st.rerun()

if st.sidebar.button("💬 Messages"):
    st.session_state.page = "messages"
    st.rerun()

if st.sidebar.button("👤 Profil"):
    st.session_state.page = "profile"
    st.rerun()

if st.sidebar.button("🚪 Logout"):
    supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.session_state.pseudo = "Invité"
    st.rerun()

# --- NAVIGATION ENTRE PAGES ---
if st.session_state.page == "home":
    st.title("Explorer")
    st.write("Découvre et discute avec les personnages du moment :")
    
    items = list(CHARACTERS.items())
    
    # --- PAGINATION ---
    ITEMS_PER_PAGE = 8
    if "home_page" not in st.session_state:
        st.session_state.home_page = 0
        
    total_pages = max(1, (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    st.session_state.home_page = min(st.session_state.home_page, total_pages - 1)
    
    start_idx = st.session_state.home_page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_items = items[start_idx:end_idx]

    # Utilisation d'une grille CSS complète avec st.html()
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
                <a href="?chat_target={name}" target="_self" style="display: block; text-align: center; background-color: #21262d; color: #ffffff; padding: 6px 10px; border-radius: 6px; text-decoration: none; border: 1px solid rgba(255, 255, 255, 0.15); font-size: 12px; font-weight: 600;">💬 Discuter</a>
            </div>
        </div>
        """
    grid_html += '</div>'
    
    st.html(grid_html)

    # Gestion du clic sur les boutons de discussion en HTML/Query Param
    query_params = st.query_params
    if "chat_target" in query_params:
        target_char = query_params["chat_target"]
        if target_char in CHARACTERS:
            st.session_state.char_select = target_char
            st.session_state.page = "chat"
            st.query_params.clear()
            st.rerun()

    # Pagination en bas de page
    if total_pages > 1:
        st.markdown("---")
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if st.session_state.home_page > 0:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.home_page -= 1
                    st.rerun()
        with p_col2:
            st.markdown(f"<p style='text-align: center; color: #8b949e;'>Page {st.session_state.home_page + 1} sur {total_pages}</p>", unsafe_allow_html=True)
        with p_col3:
            if st.session_state.home_page < total_pages - 1:
                if st.button("Suivant ➡️", use_container_width=True):
                    st.session_state.home_page += 1
                    st.rerun()

elif st.session_state.page == "create_character":
    st.title("✨ Créer un nouveau personnage")
    st.write("Conçois ton propre personnage sur mesure, définis son univers et choisis s'il est visible par tous ou uniquement par toi.")

    with st.form("create_char_form"):
        char_name = st.text_input("Nom du personnage")
        char_sex = st.selectbox("Sexe / Genre", ["Homme", "Femme", "Non-binaire", "Autre"])
        char_quote = st.text_input("Phrase d'accroche (Citation affichée sous l'image)")
        char_description = st.text_area("Description et Personnalité (Comment se comporte-t-il, son histoire, son ton...)", help="Ex: Tu es ténébreux, protecteur, un peu distant au début...")
        char_secondary = st.text_area("Personnages secondaires / Éléments contextuels (Optionnel)", help="Ex: Inclut des mentions de ses frères ou de rivaux si nécessaire dans l'histoire.")
        
        uploaded_char_img = st.file_uploader("Image du personnage (PNG, JPG)", type=["png", "jpg", "jpeg"])
        
        visibility = st.radio("Visibilité", ["Public (visible par toute la communauté)", "Privé (uniquement pour moi)"])
        
        submitted = st.form_submit_button("Créer le personnage")
        
        if submitted:
            if not char_name or not char_description:
                st.warning("Veuillez remplir au moins le nom et la description du personnage.")
            else:
                img_path = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"
                if uploaded_char_img is not None:
                    img_path_saved = f"char_{st.session_state.pseudo}_{char_name}.png"
                    with open(img_path_saved, "wb") as f:
                        f.write(uploaded_char_img.getbuffer())
                    img_path = img_path_saved
                
                is_public = True if "Public" in visibility else False
                
                try:
                    supabase.table("custom_characters").insert({
                        "name": char_name,
                        "sex": char_sex,
                        "quote": char_quote,
                        "description": char_description,
                        "secondary_chars": char_secondary,
                        "img_url": img_path,
                        "is_public": is_public,
                        "creator": st.session_state.pseudo
                    }).execute()
                    
                    st.success(f"Le personnage {char_name} a été créé avec succès !")
                    st.session_state.page = "home"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la création : {e}")

elif st.session_state.page == "messages":
    st.title("Mes Discussions")
    st.write("Retrouvez ici l'ensemble de vos conversations avec les personnages.")
    
    convs = get_user_conversations(st.session_state.pseudo)
    
    if not convs:
        st.info("Vous n'avez pas encore de discussions en cours. Allez sur l'accueil pour choisir un personnage !")
    else:
        for char_name in convs.keys():
            if char_name in CHARACTERS:
                col1, col2, col3 = st.columns([1, 4, 1])
                with col1:
                    st.image(CHARACTERS[char_name]["img"], width=85)
                with col2:
                    st.subheader(char_name)
                    st.caption(CHARACTERS[char_name]["quote"])
                with col3:
                    if st.button(f"Ouvrir", key=f"open_msg_{char_name}"):
                        st.session_state.char_select = char_name
                        st.session_state.page = "chat"
                        st.rerun()
                st.markdown("---")

elif st.session_state.page == "profile":
    st.title("Mon Profil")
    
    try:
        user_db = supabase.table("users").select("*").eq("pseudo", st.session_state.pseudo).single().execute()
        user_info = user_db.data if user_db.data else {}
        
        user_email = user_info.get("email", "Non disponible")
        user_id = user_info.get("id")
        avatar_path = user_info.get("avatar_url", "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg")

        convs = get_user_conversations(st.session_state.pseudo)
        nb_collected = len(convs)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(avatar_path, use_container_width=True)
            
        with col2:
            st.subheader(st.session_state.pseudo)
            st.write(f"📧 {user_email}")
            
            stat1, stat2, stat3 = st.columns(3)
            with stat1:
                st.metric(label="Personnages", value=nb_collected)
            with stat2:
                st.metric(label="Abonnés", value=0)
            with stat3:
                st.metric(label="Abonnements", value=0)

        st.markdown("---")
        
        st.text_input("Pseudo (non modifiable)", value=st.session_state.pseudo, disabled=True)
        
        uploaded_file = st.file_uploader("Changer votre photo de profil", type=["png", "jpg", "jpeg"], key="avatar_uploader")
        
        if uploaded_file is not None and user_id:
            file_extension = uploaded_file.name.split(".")[-1]
            file_name = f"avatar_{user_id}.{file_extension}"
            
            with open(file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            supabase.table("users").update({"avatar_url": file_name}).eq("id", user_id).execute()
            st.success("Photo de profil mise à jour avec succès !")
            st.rerun()
            
    except Exception as e:
        st.error(f"Impossible de charger les données du profil : {e}")

elif st.session_state.page == "chat":
    current_char = st.session_state.char_select
    bg_image = CHARACTERS[current_char]["img"]
    char_quote = CHARACTERS[current_char]["quote"]

    if not str(bg_image).startswith("http"):
        bg_image = "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg"

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url("{bg_image}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.title(f"Chat avec {current_char}")
    st.markdown(f"*{char_quote}*")

    messages = load_msgs(st.session_state.pseudo, current_char)
    char_prompt = CHARACTERS[current_char]["prompt"]
    full_messages = [{"role": "system", "content": char_prompt}] + messages

    for msg in messages:
        with st.chat_message(msg["role"]): 
            st.write(msg["content"])

    if prompt := st.chat_input("Écris ton message ici..."):
        save_msg(st.session_state.pseudo, current_char, "user", prompt)
        full_messages.append({"role": "user", "content": prompt})
        
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages)
        assistant_reply = res.choices[0].message.content
        
        save_msg(st.session_state.pseudo, current_char, "assistant", assistant_reply)
        st.rerun()
