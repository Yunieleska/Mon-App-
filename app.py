import streamlit as st
import os
from groq import Groq

# ==========================================
# 1. CONFIGURATION & DESIGN DE STORYIA
# ==========================================
st.set_page_config(page_title="Storyia - AI Roleplay", layout="centered")

# Nettoyage de l'URL de fond
IMAGE_FOND = "https://share.gemini.google/zeM5fxLPDnhb" 

# Injection CSS pour l'univers immersif (Dark Mode text-friendly)
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{IMAGE_FOND}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Style pour les messages de chat (Bulles sombres semi-transparentes) */
    .stChatMessage {{
        background-color: rgba(20, 20, 20, 0.75) !important;
        border: 1px solid rgba(255, 75, 75, 0.2);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        color: #ffffff !important;
    }}
    /* Forcer la couleur du texte dans le chat */
    .stChatMessage p {{
        color: #ffffff !important;
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
        st.markdown("<h1 style='text-align: center; color: #ff4b4b; text-shadow: 2px 2px 4px #000;'>✨ Storyia ✨</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white;'>Bienvenue sur votre plateforme de RP privée.</p>", unsafe_allow_html=True)
        
        password = st.text_input("Entre le mot de passe secret :", type="password")
        if st.button("Entrer dans Storyia"):
            if password == "SECRET":  # Pense à changer "SECRET" par ton vrai MDP
                st.session_state.authentifie = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
        st.stop()

check_password()

# ==========================================
# 3. INITIALISATION DE L'API GROQ & DOSSIERS
# ==========================================
# Client Groq (Idéalement, utilise st.secrets pour masquer ta clé)
client = Groq(api_key="VOTRE_CLE_API_GROQ_ICI")

# Initialisation des catégories par défaut
CATEGORIES = ["Mafieux", "Fantaisie", "Motard", "École"]
BASE_DIR = "personnages"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
for cat in CATEGORIES:
    cat_path = os.path.join(BASE_DIR, cat)
    if not os.path.exists(cat_path):
        os.makedirs(cat_path)
    # Création d'un exemple si la catégorie est complètement vide
    if not os.listdir(cat_path):
        with open(os.path.join(cat_path, "Exemple.txt"), "w", encoding="utf-8") as f:
            f.write("Tu es un personnage mystérieux et séduisant.")

# ==========================================
# 4. MENU LATÉRAL (SÉLECTION & CRÉATION)
# ==========================================
st.sidebar.markdown("<h2 style='color: #ff4b4b;'>🔮 Storyia Menu</h2>", unsafe_allow_html=True)

# Étape A : Choisir la catégorie
categorie_choisie = st.sidebar.selectbox("Choisir un univers :", CATEGORIES)

# Étape B : Filtrer les personnages selon la catégorie choisie
path_persos_filtres = os.path.join(BASE_DIR, categorie_choisie)
liste_persos = [f.replace(".txt", "") for f in os.listdir(path_persos_filtres) if f.endswith(".txt")]

if not liste_persos:
    liste_persos = ["Aucun personnage"]

choix_perso = st.sidebar.selectbox("Avec qui veux-tu RP ?", liste_persos)

# Gestion du changement de personnage et initialisation de la mémoire du chat
if "personnage_actuel" not in st.session_state or st.session_state.personnage_actuel != choix_perso:
    if choix_perso != "Aucun personnage":
        st.session_state.personnage_actuel = choix_perso
        
        chemin_fichier = os.path.join(BASE_DIR, categorie_choisie, f"{choix_perso}.txt")
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            contexte_perso = f.read()
        
        # Prompt système calibré style Character.ai / Polybuzz
        prompt_systeme = (
            f"Tu es {choix_perso}. Voici ta personnalité, tes secrets et ton histoire : {contexte_perso}. "
            f"Tu te trouves actuellement dans un univers de type [{categorie_choisie}]. "
            "Ceci est un jeu de rôle textuel interactif, immersif et romantique. Reste TOUJOURS strictement dans ton personnage. "
            "Fais des réponses engageantes mais courtes pour laisser l'utilisateur répondre. "
            "Décris TOUJOURS tes actions, expressions corporelles et pensées entre astérisques *comme ceci* "
            "et utilise les guillemets ou le texte normal pour les dialogues."
        )
        st.session_state.messages = [{"role": "system", "content": prompt_systeme}]

# Bouton de réinitialisation de l'histoire
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
# 5. INTERFACE DE CHAT PRINCIPALE
# ==========================================
if choix_perso and choix_perso != "Aucun personnage":
    st.markdown(f"<h1 style='color: white; text-shadow: 2px 2px 8px #000000;'>🎭 {choix_perso} <span style='font-size:16px; color:#ff4b4b;'>({categorie_choisie})</span></h1>", unsafe_allow_html=True)

    # Affichage de l'historique (en masquant le prompt système de l'IA)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Entrée utilisateur et streaming/réponse de l'IA
    if prompt := st.chat_input(f"Écris la suite de ton histoire avec {choix_perso}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            # Utilisation du modèle Llama 3.1 8B optimisé et mis à jour
            response = client.chat.completions.create(
                messages=st.session_state.messages,
                model="llama-3.1-8b-instant",
                temperature=0.8, # Un poil de créativité pour le RP
            )
            
            reponse_ia = response.choices[0].message.content
            placeholder.markdown(reponse_ia)
            
        st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
else:
    st.info("Sélectionnez ou créez un personnage dans le menu latéral pour commencer l'aventure.")
