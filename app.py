
import streamlit as st
import os
from groq import Groq

# ==========================================
# 1. CONFIGURATION & DESIGN DE STORYIA
# ==========================================
st.set_page_config(page_title="Storyia - AI Roleplay", layout="centered")

# URL de ton image de fond (mets le lien direct de ton image ici)

import streamlit as st
import os
from groq import Groq

# ==========================================
# 1. CONFIGURATION & DESIGN DE STORYIA
# ==========================================
st.set_page_config(page_title="Storyia - AI Roleplay", layout="centered")

# URL de ton image de fond (mets le lien direct de ton image ici

# Injection CSS pour le fond visuel et le style
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{IMAGE_FOND}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Style optionnel pour rendre le texte du chat plus lisible sur l'image de fond */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. ACCÈS PRIVÉ
# ==========================================
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

def check_password():
    if not st.session_state.authentifie:
        st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>✨ Storyia ✨</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Bienvenue sur ta plateforme de RP privée.</p>", unsafe_allow_html=True)
        
        password = st.text_input("Entre le mot de passe secret :", type="password")
        if st.button("Entrer dans Storyia"):
            if password == "SECRET":  # Change "SECRET" par ton vrai mot de passe
                st.session_state.authentifie = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
        st.stop()

check_password()

# ==========================================
# 3. CONNEXION À L'API GROQ
# ==========================================
client = Groq(api_key="VOTRE_CLE_API_GROQ_ICI")

# ==========================================
# 4. SÉLECTION DES CHARACTERS
# ==========================================
st.sidebar.markdown("<h2 style='color: #ff4b4b;'>🔮 Storyia Menu</h2>", unsafe_allow_html=True)

if not os.path.exists("personnages"):
    os.makedirs("personnages")
    # On crée un premier personnage fictif si le dossier est vide
    with open("personnages/Exemple.txt", "w", encoding="utf-8") as f:
        f.write("Tu es un personnage mystérieux et séduisant.")
    
liste_persos = [f.replace(".txt", "") for f in os.listdir("personnages") if f.endswith(".txt")]
choix = st.sidebar.selectbox("Avec qui veux-tu RP ?", liste_persos)

# Gestion du changement de personnage et reset du chat
if "personnage_actuel" not in st.session_state or st.session_state.personnage_actuel != choix:
    st.session_state.personnage_actuel = choix
    with open(f"personnages/{choix}.txt", "r", encoding="utf-8") as f:
        contexte_perso = f.read()
    
    # Prompt système pour forcer l'IA à agir comme sur Character.ai
    prompt_systeme = (
        f"Tu es {choix}. Voici ta personnalité et ton histoire : {contexte_perso}. "
        "Tu es dans un jeu de rôle textuel de romance/action. Reste TOUJOURS dans ton personnage. "
        "Fais des réponses immersives, décris tes actions entre astérisques *comme ceci* et parle normalement pour les dialogues."
    )
    st.session_state.messages = [{"role": "system", "content": prompt_systeme}]

if st.sidebar.button("🗑️ Recommencer l'histoire"):
    st.session_state.messages = [st.session_state.messages[0]]
    st.rerun()

# ==========================================
# 5. L'INTERFACE DE CHAT
# ==========================================
st.markdown(f"<h1 style='color: white; text-shadow: 2px 2px 4px #000000;'>🎭 {choix}</h1>", unsafe_allow_html=True)

# Affichage des messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Entrée utilisateur et réponse IA
if prompt := st.chat_input(f"Écris la suite de l'histoire avec {choix}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        response = client.chat.completions.create(
            messages=st.session_state.messages,
            model="llama3-8b-8192",
        )
        reponse_ia = response.choices[0].message.content
        placeholder.markdown(reponse_ia)
        
    st.session_state.messages.append({"role": "assistant", "content": reponse_ia}) 
# Section de création de personnage
with st.sidebar.expander("➕ Créer un personnage"):
    nom_perso = st.text_input("Nom du personnage")
    univers_perso = st.selectbox("Choisir l'univers", os.listdir("personnages"))
    bio_perso = st.text_area("Description du personnage (la Bible)")
    
    if st.button("Sauvegarder le personnage"):
        if nom_perso and bio_perso:
            chemin = f"personnages/{univers_perso}/{nom_perso}.txt"
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(bio_perso)
            st.success(f"{nom_perso} a été créé !")
            st.rerun() # Rafraîchit l'app pour voir le nouveau perso

# Injection CSS pour le fond visuel et le style
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{IMAGE_FOND}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Style optionnel pour rendre le texte du chat plus lisible sur l'image de fond */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. ACCÈS PRIVÉ
# ==========================================
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

def check_password():
    if not st.session_state.authentifie:
        st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>✨ Storyia ✨</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Bienvenue sur ta plateforme de RP privée.</p>", unsafe_allow_html=True)
        
        password = st.text_input("Entre le mot de passe secret :", type="password")
        if st.button("Entrer dans Storyia"):
            if password == "SECRET":  # Change "SECRET" par ton vrai mot de passe
                st.session_state.authentifie = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
        st.stop()

check_password()

# ==========================================
# 3. CONNEXION À L'API GROQ
# ==========================================
client = Groq(api_key="VOTRE_CLE_API_GROQ_ICI")

# ==========================================
# 4. SÉLECTION DES CHARACTERS
# ==========================================
st.sidebar.markdown("<h2 style='color: #ff4b4b;'>🔮 Storyia Menu</h2>", unsafe_allow_html=True)

if not os.path.exists("personnages"):
    os.makedirs("personnages")
    # On crée un premier personnage fictif si le dossier est vide
    with open("personnages/Exemple.txt", "w", encoding="utf-8") as f:
        f.write("Tu es un personnage mystérieux et séduisant.")
    
liste_persos = [f.replace(".txt", "") for f in os.listdir("personnages") if f.endswith(".txt")]
choix = st.sidebar.selectbox("Avec qui veux-tu RP ?", liste_persos)

# Gestion du changement de personnage et reset du chat
if "personnage_actuel" not in st.session_state or st.session_state.personnage_actuel != choix:
    st.session_state.personnage_actuel = choix
    with open(f"personnages/{choix}.txt", "r", encoding="utf-8") as f:
        contexte_perso = f.read()
    
    # Prompt système pour forcer l'IA à agir comme sur Character.ai
    prompt_systeme = (
        f"Tu es {choix}. Voici ta personnalité et ton histoire : {contexte_perso}. "
        "Tu es dans un jeu de rôle textuel de romance/action. Reste TOUJOURS dans ton personnage. "
        "Fais des réponses immersives, décris tes actions entre astérisques *comme ceci* et parle normalement pour les dialogues."
    )
    st.session_state.messages = [{"role": "system", "content": prompt_systeme}]

if st.sidebar.button("🗑️ Recommencer l'histoire"):
    st.session_state.messages = [st.session_state.messages[0]]
    st.rerun()

# ==========================================
# 5. L'INTERFACE DE CHAT
# ==========================================
st.markdown(f"<h1 style='color: white; text-shadow: 2px 2px 4px #000000;'>🎭 {choix}</h1>", unsafe_allow_html=True)

# Affichage des messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Entrée utilisateur et réponse IA
if prompt := st.chat_input(f"Écris la suite de l'histoire avec {choix}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        response = client.chat.completions.create(
            messages=st.session_state.messages,
            model="llama3-8b-8192",
        )
        reponse_ia = response.choices[0].message.content
        placeholder.markdown(reponse_ia)
        
    st.session_state.messages.append({"role": "assistant", "content": reponse_ia}) 
# Section de création de personnage
with st.sidebar.expander("➕ Créer un personnage"):
    nom_perso = st.text_input("Nom du personnage")
    univers_perso = st.selectbox("Choisir l'univers", os.listdir("personnages"))
    bio_perso = st.text_area("Description du personnage (la Bible)")
    
    if st.button("Sauvegarder le personnage"):
        if nom_perso and bio_perso:
            chemin = f"personnages/{univers_perso}/{nom_perso}.txt"
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(bio_perso)
            st.success(f"{nom_perso} a été créé !")
            st.rerun() # Rafraîchit l'app pour voir le nouveau perso
