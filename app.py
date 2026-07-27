import io
import re
import requests
import streamlit as str_lit  # Utilisation de votre alias existant

# --- 1. CONFIGURATION HUGGING FACE (Intégrée proprement) ---
HF_API_KEY = str_lit.secrets.get("HUGGINGFACE_API_KEY", "")
# Utilisation d'un modèle rapide et performant pour la génération d'images
IMAGE_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

def generer_image_huggingface(prompt_image):
    if not HF_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt_image}
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.content
    except Exception:
        pass
    return None

# --- 2. VOTRE CODE EXISTANT CORRIGÉ ET COMPLÉTÉ ---
# (On reprend votre structure exacte avec l'ajout de la gestion des balises [IMAGE: ...])

# Supposons que vous parcouriez vos messages stockés (par exemple dans st.session_state.messages) :
# for idx, msg in enumerate(messages):
#     ...

# --- EXEMPLE INTÉGRÉ DANS VOTRE LOGIQUE D'AFFICHAGE ---
# Remplacez simplement la ligne où vous affichez le contenu du message par ce bloc :

# if edit_key in str_lit.session_state and str_lit.session_state[edit_key]:
#     # ... (votre code d'édition existant)
#     pass
# else:
    # Récupération sécurisée du contenu du message
    contenu_message = msg.get("content", "")

    # Analyse du texte pour détecter la balise image optionnelle (Étape 3 & 4)
    # On cherche le format [IMAGE: description]
    match_image = re.search(r'\[IMAGE:\s*(.*?)\]', contenu_message)

    if match_image:
        # Extraction de la description en anglais pour l'IA
        prompt_image = match_image.group(1).strip()
        # Nettoyage du texte pour ne garder que la partie narrative
        texte_propre = contenu_message.replace(match_image.group(0), "").strip()
    else:
        texte_propre = contenu_message
        prompt_image = None

    # Affichage du texte propre
    str_lit.write(texte_propre)

    # Si une balise image a été trouvée, on génère et affiche l'image sous le texte
    if prompt_image:
        with str_lit.spinner("📸 Génération de la photo en cours..."):
            image_bytes = generer_image_huggingface(prompt_image)
            if image_bytes:
                str_lit.image(image_bytes, caption="Photo envoyée par le personnage")
            else:
                str_lit.warning("Impossible de charger la photo pour le moment.")

# Suite de votre code existant pour les boutons d'édition / annulation
# with col_cancel:
#     if str_lit.button("❌ Annuler", key=f"cancel_edit_{idx}"):
#         str_lit.session_state[edit_key] = False
#         str_lit.rerun()
