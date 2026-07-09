import streamlit as st
import os
import sqlite3
import hashlib
import base64
from groq import Groq

# ==========================================
# 0. INITIALISATION STRICTE DU SESSION_STATE
# ==========================================
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page_recup" not in st.session_state:
    st.session_state.page_recup = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "personnage_actuel" not in st.session_state:
    st.session_state.personnage_actuel = None

# ==========================================
# 1. CONFIGURATION & DESIGN DE STORYIA
# ==========================================
st.set_page_config(page_title="Storyia - AI Roleplay", layout="wide")

def get_base64_image():
    """Trouve l'image bg.png localement sur le serveur GitHub/Streamlit et la convertit."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "bg.png")
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

image_base64 = get_base64_image()

# Injection CSS pour nettoyer l'interface et créer les cartes cliquables
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B0E14 !important;
    }
    .stChatMessage {
        background-color: rgba(25, 30, 40, 0.6) !important;
        border: 1px solid rgba(255, 75, 75, 0.2);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        color: #ffffff !important;
    }
    .auth-container {
        background-color: #151922;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 20px;
    }
    .char-card-box {
        background: #181E2A;
        border: 1px solid #242F41;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .char-avatar-circle {
        width: 70px;
        height: 70px;
        background: #242F41;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        margin: 0 auto 12px auto;
        border: 2px solid #ff4b4b;
    }
    .char-title {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .char-subtitle {
        color: #9CA3AF;
        font-size: 13px;
        line-height: 1.4;
        height: 40px;
        overflow: hidden;
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. GESTION DE LA BASE DE DONNÉES
# ==========================================
if os.path.exists("/mount/src"):
    DB_FILE = "/tmp/storyia_users.db"
else:
    DB_FILE = "storyia_users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            security_question TEXT,
            security_answer TEXT
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def user_exists(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)', (username.strip(),))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_user(username, password, question, answer):
    username_clean = username.strip()
    if user_exists(username_clean):
        return False
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        hashed_answer = hashlib.sha256(str.encode(answer.strip().lower())).hexdigest()
        c.execute('''
            INSERT INTO users (username, password, security_question, security_answer) 
            VALUES (?, ?, ?, ?)
        ''', (username_clean, hash_password(password), question, hashed_answer))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE LOWER(username) = LOWER(?) AND password = ?', (username.strip(), hash_password(password)))
    data = c.fetchone()
    conn.close()
    if data:
        st.session_state.username = data[0]
        return True
    return False

def get_security_question(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT security_question FROM users WHERE LOWER(username) = LOWER(?)', (username.strip(),))
    data = c.fetchone()
    conn.close()
    return data[0] if data else None

def update_password(username, answer, new_password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hashed_answer = hashlib.sha256(str.encode(answer.strip().lower())).hexdigest()
    c.execute('SELECT 1 FROM users WHERE LOWER(username) = LOWER(?) AND security_answer = ?', (username.strip(), hashed_answer))
    if c.fetchone():
        c.execute('UPDATE users SET password = ? WHERE LOWER(username) = LOWER(?)', (hash_password(new_password), username.strip()))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

init_db()

# ==========================================
# 3. INTERFACE D'INSCRIPTION / CONNEXION
# ==========================================
def systeme_authentification():
    if not st.session_state.authentifie:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        if st.session_state.page_recup:
            st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>🔑 Récupération</h3>", unsafe_allow_html=True)
            user_recup = st.text_input("Entre ton Pseudo :", key="user_recup")
            if user_recup:
                question = get_security_question(user_recup)
                if question:
                    st.info(f"❓ **Question de sécurité :** {question}")
                    reponse = st.text_input("Ta réponse :", type="password", key="ans_recup")
                    nouveau_mdp = st.text_input("Nouveau mot de passe :", type="password", key="new_pass_recup")
                    if st.button("Modifier mon mot de passe", use_container_width=True):
                        if reponse and nouveau_mdp:
                            if update_password(user_recup, reponse, nouveau_mdp):
                                st.success("🎉 Mot de passe modifié !")
                                st.session_state.page_recup = False
                                st.rerun()
                            else:
                                st.error("Réponse incorrecte.")
                        else:
                            st.error("Veuillez remplir tous les champs.")
                else:
                    st.error("Ce pseudo n'existe pas.")
            if st.button("⬅️ Retour à la connexion", use_container_width=True):
                st.session_state.page_recup = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.stop()

        tab_login, tab_register = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
        with tab_login:
            username = st.text_input("Pseudo", key="login_user")
            password = st.text_input("Mot de passe", type="password", key="login_pass")
            if st.button("Se connecter", use_container_width=True):
                if login_user(username, password):
                    st.session_state.authentifie = True
                    st.rerun()
                else:
                    st.error("Pseudo ou mot de passe incorrect.")
            if st.button("Mot de passe oublié ?", use_container_width=True):
                st.session_state.page_recup = True
                st.rerun()
                    
        with tab_register:
            new_username = st.text_input("Choisis un Pseudo", key="reg_user")
            new_password = st.text_input("Choisis un Mot de passe", type="password", key="reg_pass")
            confirm_password = st.text_input("Confirme le mot de passe", type="password", key="reg_pass_conf")
            st.markdown("---")
            liste_questions = ["Quel est le nom de ton premier animal de compagnie ?", "Dans quelle ville es-tu né(e) ?", "Quel était le nom de ton école primaire ?"]
            q_choisie = st.selectbox("Choisis une question secrète :", liste_questions)
            rep_choisie = st.text_input("Ta réponse secrète :")
            if st.button("Créer mon compte", use_container_width=True):
                if not new_username or not new_password or not rep_choisie:
                    st.error("Veuillez remplir tous les champs.")
                elif new_password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    if add_user(new_username, new_password, q_choisie, rep_choisie):
                        st.success("Compte créé avec succès !")
                    else:
                        st.error("❌ Ce pseudo est déjà pris.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

systeme_authentification()

# ==========================================
# 4. INITIALISATION DE L'API GROQ & DOSSIERS
# ==========================================
client = Groq(api_key="VOTRE_CLE_API_GROQ_ICI")

CATEGORIES = ["Mafieux", "Fantaisie", "Motard", "École"]
BASE_DIR = "Personnages"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
for cat in CATEGORIES:
    cat_path = os.path.join(BASE_DIR, cat)
    if not os.path.exists(cat_path):
        os.makedirs(cat_path)

# ==========================================
# 5. MENU LATÉRAL
# ==========================================
st.sidebar.markdown(f"### 👤 Joueur : {st.session_state.username}")
if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    st.session_state.authentifie = False
    st.session_state.username = ""
    st.session_state.messages = []
    st.session_state.personnage_actuel = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔮 Navigation")

if st.session_state.personnage_actuel:
    if st.sidebar.button("🏠 Menu Principal Hub", use_container_width=True):
        st.session_state.personnage_actuel = None
        st.session_state.messages = []
        st.rerun()

categorie_choisie = st.sidebar.selectbox("Choisir un univers :", CATEGORIES)

if st.sidebar.button("🗑️ Recommencer l'histoire", use_container_width=True) and st.session_state.personnage_actuel:
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("➕ Créer un personnage"):
    nom_perso = st.text_input("Nom")
    univers_perso = st.selectbox("Univers", CATEGORIES, key="create_cat")
    bio_perso = st.text_area("Description")
    if st.button("Sauvegarder"):
        if nom_perso and bio_perso:
            nom_propre = nom_perso.strip().replace("/", "_")
            with open(os.path.join(BASE_DIR, univers_perso, f"{nom_propre}.txt"), "w", encoding="utf-8") as f:
                f.write(bio_perso)
            st.success("Personnage ajouté !")
            st.rerun()

# ==========================================
# 6. INTERFACE PRINCIPALE (HUB OU CHAT)
# ==========================================
path_persos_filtres = os.path.join(BASE_DIR, categorie_choisie)
liste_fichiers = [f for f in os.listdir(path_persos_filtres) if f.endswith(".txt")] if os.path.exists(path_persos_filtres) else []

if st.session_state.personnage_actuel is None:
    if image_base64:
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="data:image/png;base64,{image_base64}" style="width: 100%; max-width: 650px; border-radius: 14px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);">
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown(f"### ✨ Personnages actifs ({categorie_choisie})")
    
    if not liste_fichiers:
        st.info(f"Aucun personnage dans la catégorie {categorie_choisie} pour l'instant.")
    else:
        cols = st.columns(4)
        for index, fichier in enumerate(liste_fichiers):
            nom_perso = fichier.replace(".txt", "")
            
            try:
                with open(os.path.join(path_persos_filtres, fichier), "r", encoding="utf-8", errors="ignore") as f:
                    description = f.read()
            except Exception:
                description = "Pas de description disponible."
            
            with cols[index % 4]:
                st.markdown(
                    f"""
                    <div class="char-card-box">
                        <div class="char-avatar-circle">🎭</div>
                        <div class="char-title">{nom_perso}</div>
                        <div class="char-subtitle">{description[:50]}...</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                if st.button(f"Chatter avec {nom_perso}", key=f"btn_{nom_perso}", use_container_width=True):
                    st.session_state.personnage_actuel = nom_perso
                    prompt_systeme = (
                        f"Tu es {nom_perso}. Contexte : {description}. Univers : [{categorie_choisie}]. "
                        "Jeu de rôle immersif. Réponses courtes. Décris les actions entre astérisques *comme ceci*."
                    )
                    st.session_state.messages = [{"role": "system", "content": prompt_systeme}]
                    st.rerun()

else:
    choix_perso = st.session_state.personnage_actuel
    st.markdown(f"## 🎭 En plein RP avec {choix_perso}")

    if "messages" in st.session_state and st.session_state.messages:
        for message in st.session_state.messages:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    if prompt := st.chat_input("Écris ton action ou dialogue..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = client.chat.completions.create(
                messages=st.session_state.messages,
                model="llama-3.1-8b-instant",
                temperature=0.8
            )
            reponse_ia = response.choices[0].message.content
            placeholder.markdown(reponse_ia)
            
        st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
