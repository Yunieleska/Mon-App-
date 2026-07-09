import streamlit as st
import os

st.set_page_config(page_title="Storyia", layout="wide")

# Fonction améliorée qui cherche le fichier .txt PARTOUT dans le dossier Personnages
def trouver_accroche(nom):
    nom_fichier = f"{nom}.txt"
    # On parcourt le dossier Personnages et tous ses sous-dossiers
    for root, dirs, files in os.walk("Personnages"):
        if nom_fichier in files:
            chemin = os.path.join(root, nom_fichier)
            with open(chemin, "r", encoding="utf-8") as f:
                return f.read().strip()
    return "Clique pour commencer une romance..."

# --- PERSONNAGES ---
# Tes images sont à la racine, donc on laisse le nom du fichier tel quel
personnages = [
    {"nom": "Lucas", "img": "Lucas.png"},
    {"nom": "Ethan", "img": "Ethan.png"},
    {"nom": "Léo", "img": "Léo.png"},
    {"nom": "Liam", "img": "Liam.png"},
    {"nom": "Noah", "img": "Noah.png"}
]

st.title("Choisis ton personnage")

cols = st.columns(len(personnages))
for i, p in enumerate(personnages):
    with cols[i]:
        # Chargement image
        if os.path.exists(p["img"]):
            st.image(p["img"], use_container_width=True)
        else:
            st.error(f"Image {p['img']} introuvable.")
        
        st.subheader(p["nom"])
        # Recherche auto du texte dans n'importe quel sous-dossier
        st.write(trouver_accroche(p["nom"]))
