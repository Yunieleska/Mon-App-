import streamlit as st
import os
import sqlite3
import hashlib
from groq import Groq

# ==========================================
# 1. CONFIGURATION & DESIGN DE STORYIA
# ==========================================
st.set_page_config(page_title="Storyia - AI Roleplay", layout="centered")

IMAGE_FOND = "https://share.gemini.google/zeM5fxLPDnhb" 

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{IMAGE_FOND}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stChatMessage {{
        background-color: rgba(20, 20, 20, 0.75) !important;
        border: 1px solid rgba(255, 75, 75, 0.2);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        color: #ffffff !important;
    }}
    .stChatMessage p {{
        color: #ffffff !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. GESTION DE LA BASE DE DONNÉES (UTILISATEURS UNIQUE)
# ==========================================
DB_FILE = "storyia_users.db"

def init_db():
    """Crée la table des utilisateurs si elle n'existe pas."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hache le mot de passe pour ne pas le stocker en texte brut."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def user_exists(username):
    """Vérifie si un pseudo existe déjà (insensible à la casse)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # LOWER() empêche de créer "Batman" si "batman" existe déjà
    c.execute('SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)', (username.strip(),))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_user(username, password):
    """Ajoute un utilisateur unique dans la base de données."""
    username_clean = username.strip()
    if user_exists(username_clean):
        return False  # Le pseudo est déjà pris
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?,?)', (username_clean, hash_password(password)))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def login_user(username, password):
    """Vérifie si les identifiants sont corrects (insensible à la casse)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE LOWER(username) = LOWER(?) AND password = ?', (username.strip(), hash_password(password)))
    data = c.fetchone()
    conn.close()
    
    if data:
        st.session_state.username = data[0]  # Récupère l'orthographe exacte du pseudo (ex: "MonPseudo")
        return True
    return False

# Initialisation automatique de la base de données
init_db()

# ==========================================
# 3. INTERFACE D'INSCRIPTION / CONNEXION
# ==========================================
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False
if "username" not in st.session_state:
    st.session_state.username = ""

def systeme_authentification():
    if not st.session_state.authentifie:
        st.markdown("<h1 style='text-align: center; color: #ff4b4b; text-shadow: 2px 2px 4px #000;'>✨ Storyia ✨</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white;'>Inscris-toi ou connecte-toi pour rejoindre l'aventure.</p>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔒 Connexion", "📝 S'inscrire"])
        
        with tab_login:
            username = st.text_input("Pseudo", key="login_user")
            password = st.text_input("Mot de passe", type="password", key="login_pass")
            if st.button("Se connecter", use_container_width=True):
                if login_user(username, password):
                    st.session_state.authentifie = True
                    st.success(f"Ravi de te revoir, {st.session_state.username} !")
                    st.rerun()
                else:
                    st.error("Pseudo ou mot de passe incorrect.")
                    
        with tab_register:
            new_username = st.text_input("Choisis un Pseudo", key="reg_user")
            new_password = st.text_input("Choisis un Mot de passe", type="password", key="reg_pass")
            confirm_password = st.text_input("Confirme le mot de passe", type="password", key="reg_pass_conf")
            
            if st.button("Créer mon compte", use_container_width=True):
                if not new_username or not new_password:
                    st.error("Veuillez remplir tous les champs.")
                elif new_password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    if add_user(new_username, new_password):
                        st.success("Compte créé avec succès ! Tu peux maintenant te connecter.")
                    else:
                        st.error("❌ Ce pseudo est déjà pris par un autre joueur. Choisis-en un autre !")
        st.stop()

systeme_authentification()

# ==========================================
# 4. INITIALISATION DE L'API GROQ & DOSSIERS
# ==========================================
client = Groq(api_key="VOTRE_CLE_API_GROQ_ICI")

CATEGORIES = ["Mafieux", "Fantaisie", "Motard", "École"]
BASE_DIR = "personnages"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
for cat in CATEGORIES:
    cat_path = os.path.join(BASE_DIR, cat)
    if not os.path.exists(cat_path):
        os.makedirs(cat_path)
    if not os.listdir(cat_path):
        with open(os.path.join(cat_path, "Exemple.txt"), "w", encoding="utf-8") as f:
            f.write("Tu es un personnage mystérieux et séduisant.")

# ==========================================
# 5. MENU LATÉRAL (PROFIL, SÉLECTION & CRÉATION)
# ==========================================
st.sidebar.markdown(f"<h3 style='color: white;'>👤 Joueur : {st.session_state.username}</h3>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Déconnexion"):
    st.session_state.authentifie = False
    st.session_state.username = ""
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("<h2 style='color: #ff4b4b;'>🔮 Storyia Menu</h2>", unsafe_allow_html=True)

categorie_choisie = st.sidebar.selectbox("Choisir un univers :", CATEGORIES)
path_persos_filtres = os.path.join(BASE_DIR, categorie_choisie)
liste_persos = [f.replace(".txt", "") for f in os.listdir(path_persos_filtres) if f.endswith(".txt")]

if not liste_persos:
    liste_persos = ["Aucun personnage"]

choix_perso = st.sidebar.selectbox("Avec qui veux-tu RP ?", liste_persos)

if "personnage_actuel" not in st.session_state or st.session_state.personnage_actuel != choix_perso:
    if choix_perso != "Aucun personnage":
        st.session_state.personnage_actuel = choix_perso
        
        chemin_fichier = os.path.join(BASE_DIR, categorie_choisie, f"{choix_perso}.txt")
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            contexte_perso = f.read()
        
        prompt_systeme = (
            f"Tu es {choix_perso}. Voici ta personnalité, tes secrets et ton histoire : {contexte_perso}. "
            f"Tu te trouves actuellement dans un univers de type [{categorie_choisie}]. "
            "Ceci est un jeu de rôle textuel interactif, immersif et romantique. Reste TOUJOURS strictement dans ton personnage. "
            "Fais des réponses engageantes mais courtes pour laisser l'utilisateur répondre. "
            "Décris TOUJOURS tes actions, expressions corporelles et pensées entre astérisques *comme ceci* "
            "et utilise les guillemets ou le texte normal pour les dialogues."
        )
        st.session_state.messages = [{"role": "system", "content": prompt_systeme}]

if st.sidebar.button("🗑️ Recommencer l'histoire"):
    if len(st.session_state.messages) > 0:
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# --- FORMULAIRE DE CRÉATION DE PERSONNAGE ---
st.sidebar.markdown("---")
with st.sidebar.expander("➕ Créer un personnage"):
    nom_perso = st.text_input("Nom du personnage")
    univers_perso = st.selectbox("Assigner à l'univers", CATEGORIES, key="create_cat")
    bio_perso = st.text_area("Description / Background (Sa 'Bible')")
    
    if st.button("Sauvegarder le personnage"):
        if nom_perso and bio_perso:
            nom_propre = nom_perso.strip().replace("/", "_")
            chemin_sauvegarde = os.path.join(BASE_DIR, univers_perso, f"{nom_propre}.txt")
            
            with open(chemin_sauvegarde, "w", encoding="utf-8") as f:
                f.write(bio_perso)
                
            st.success(f"✨ {nom_propre} a rejoint l'univers {univers_perso} !")
            st.rerun()
        else:
            st.error("Veuillez remplir le nom et la description.")

# ==========================================
# 6. INTERFACE DE CHAT PRINCIPALE
# ==========================================
if choix_perso and choix_perso != "Aucun personnage":
    st.markdown(f"<h1 style='color: white; text-shadow: 2px 2px 8px #000000;'>🎭 {choix_perso} <span style='font-size:16px; color:#ff4b4b;'>({categorie_choisie})</span></h1>", unsafe_allow_html=True)

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input(f"Écris la suite de ton histoire avec {choix_perso}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            response = client.chat.completions.create(
                messages=st.session_state.messages,
                model="llama-3.1-8b-instant",
                temperature=0.8,
            )
            
            reponse_ia = response.choices[0].message.content
            placeholder.markdown(reponse_ia)
            
        st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
else:
    st.info("Sélectionnez ou créez un personnage dans le menu latéral pour commencer l'aventure.")
