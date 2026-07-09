import streamlit as st
import os
# ... (garde tes imports et init session_state habituels)

# CSS pour le look "Portrait Social Media"
st.markdown(
    """
    <style>
    .card-img { 
        width: 100%; height: 350px; object-fit: cover; 
        border-radius: 20px; margin-bottom: 10px;
    }
    .card-name { font-size: 18px; font-weight: 800; color: white; margin: 0; }
    .card-desc { font-size: 13px; color: #a0a0a0; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True
)

# ... (garde ta logique de récupération des personnages)

if st.session_state.personnage_actuel is None:
    st.markdown("### ✨ Pour vous")
    
    tous = [] # ... (ton code pour lister les persos)
    
    # On utilise une grille de 2 colonnes comme sur ta capture d'écran
    cols = st.columns(2)
    for i, (cat, f) in enumerate(tous):
        with open(os.path.join(BASE_DIR, cat, f), "r", encoding="utf-8", errors="ignore") as file: 
            desc = file.read()
        
        with cols[i % 2]:
            # Image placeholder (tu pourras remplacer par une vraie URL d'image)
            st.markdown(f'<img src="https://picsum.photos/400/600" class="card-img">', unsafe_allow_html=True)
            st.markdown(f'<p class="card-name">{f.replace(".txt", "")}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="card-desc">{desc[:40]}...</p>', unsafe_allow_html=True)
            
            if st.button(f"Chatter", key=f"btn_{i}", use_container_width=True):
                st.session_state.personnage_actuel = f.replace(".txt", "")
                st.rerun()
