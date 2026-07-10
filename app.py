import streamlit as st
import sqlite3
from groq import Groq
import os

# --- CONFIGURATION ---
client = Groq(api_key="TON_API_KEY") 
st.set_page_config(page_title="Storyia", layout="wide", initial_sidebar_state="expanded")

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (user_pseudo TEXT, char_name TEXT, role TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS custom_characters (name TEXT PRIMARY KEY, prompt TEXT, start TEXT, visibility TEXT, image_path TEXT, creator TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_msg(pseudo, char, role, content):
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (pseudo, char, role, content))
    conn.commit()
    conn.close()

def load_msgs(pseudo, char):
    conn = sqlite3.connect('storyia_v3.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE user_pseudo=? AND char_name=?", (pseudo, char))
    data = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in data]

# --- DONNÉES ET ACCROCHES ---
CHARACTERS = {
    "Caelum": {"img": "https://i.pinimg.com/736x/2d/0f/41/2d0f41737963229e1368041e8cb45183.jpg", "prompt": "Tu es Caelum, Prince des Ténèbres.", "start": "*Tu viens d'arriver à l'académie. En marchant rapidement dans le couloir, tu bouscules accidentellement quelqu'un et tes affaires s'éparpillent au sol. Tu lèves les yeux et croises un regard bleu glacier. Caelum te regarde de haut, avec une indifférence totale.*\n\nTu es sur mon chemin, humaine. Ramasse tes affaires et disparais."},
    "Noah": {"img": "Noah.png", "prompt": "Tu es Noah, quaterback star.", "start": "*Ton téléphone vibre sur ton bureau au milieu de la nuit. Noah t'écrit sous son pseudonyme secret.*\n\nHey... Désolé de t'écrire si tard. Le match de ce soir était d'un ennui mortel et tout le monde fait la fête en bas, mais je préfère de loin te parler ici. Dis, tu crois qu'on est tous obligés de jouer un rôle pour plaire aux autres, ou il y a un endroit où on peut juste être soi-même ?"},
    "Ethan": {"img": "Ethan.png", "prompt": "Tu es Ethan, Loup Alpha.", "start": "*La nuit est tombée sur la petite ville de Blackwood. Tu t'es perdue en lisière de forêt et la silhouette athlétique d'Ethan émerge de la pénombre. Ses yeux sombres se fixent sur toi avec une intensité animale.*\n\nTu ne devrais pas te promener seule ici à cette heure, humaine. La forêt cache des prédateurs bien plus dangereux que tu ne l'imagines... Reste près de moi si tu veux rentrer entière."},
    "Léo": {"img": "Léo.png", "prompt": "Tu es Léo, streameur.", "start": "*Le signal sonore de Discord retentit. La voix grave de Léo (Neo) résonne dans ton casque.*\n\nAh, te voilà enfin ! Je t'attendais pour lancer la partie. Ma session de stream était d'un ennui mortel sans toi... Prête à ce qu'on détruise l'équipe d'en face ? D'ailleurs, t'as pas l'air en forme, t'as une petite voix. Dis-moi pas que tu stresses encore pour le nouveau de ta classe demain ?"},
    "Liam": {"img": "Liam.png", "prompt": "Tu es Liam, le grand frère.", "start": "*Tu es installée sur le tapis du salon. Liam entre dans la pièce, retire sa veste en cuir révélant ses tatouages, et plante ses yeux dans les tiens avec une froideur totale.*\n\nSalut, l'amie de ma sœur. Essaie de ne pas faire trop de bruit, l'orage arrive et j'ai besoin de dormir."},
    "Alexei": {"img": "
