import streamlit as st
import os

st.set_page_config(page_title="Storyia", layout="wide")

# DEBUG : On va afficher ce que le programme voit dans le dossier racine
st.sidebar.write("Fichiers trouvés à la racine :", os.listdir("."))
if os.path.exists("Personnages"):
    st.sidebar.write("Fichiers dans /Personnages :", os.listdir("Personnages"))

def lire_accroche(nom):
    # On teste les deux chemins possibles : racine ou dossier Personnages
    for chemin in [f"Personnages/{nom}.txt", f"{nom}.txt"]:
        if os.path.exists(chemin):
            with open(chemin, "r", encoding="utf-8") as f:
                return f.read().strip()
    return f"Accroche introuvable pour {nom}..."

# --- PERSONNAGES ---
# Ici, on ne met plus "Personnages/" devant, on laisse le code chercher
personnages = [
    {"nom": "Lucas", "img": "Lucas.png"},
    {"nom": "Ethan", "img": "Ethan.png"},
    {"nom": "Léo", "img": "Léo.png"}
]

st.title("Choisis ton personnage")
for p in personnages:
    # DEBUG : Affiche le chemin qu'il tente d'utiliser
    st.write(f"Tentative de chargement : {p['img']}")
    
    if os.path.exists(p["img"]):
        st.image(p["img"])
    else:
        st.error(f"Fichier {p['img']} introuvable sur le serveur.")
    
    st.subheader(p["nom"])
    st.write(lire_accroche(p["nom"]))
