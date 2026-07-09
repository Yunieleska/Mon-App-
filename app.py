import streamlit as st
import os

st.set_page_config(page_title="Debug Page", layout="wide")

st.title("Diagnostic des fichiers")

# 1. Liste tout ce qui existe à la racine
st.subheader("Fichiers trouvés à la racine du projet :")
fichiers = os.listdir(".")
st.write(fichiers)

# 2. Vérification visuelle
st.subheader("Test d'affichage des images trouvées :")
for f in fichiers:
    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
        st.write(f"Tentative d'afficher : {f}")
        st.image(f, caption=f)

# 3. Vérification des textes
st.subheader("Test des fichiers texte :")
for f in fichiers:
    if f.lower().endswith('.txt'):
        st.write(f"Contenu de {f} :")
        with open(f, "r", encoding="utf-8") as file:
            st.code(file.read())
