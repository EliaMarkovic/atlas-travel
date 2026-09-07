import streamlit as st
import os
import json

st.set_page_config(
    page_title="Storico Viaggi - ATLAS",
    page_icon="📂",
    layout="centered"
)

# STYLING COERENTE
st.markdown("""
    <style>
        div[data-testid="stSidebarNav"] { display: none !important; }
        .stApp, section[data-testid="stSidebar"] {
            background-color: #F4F6F8 !important;
            color: #1E293B !important;
        }
        h1, h2, h3, h4 {
            color: #2D3A30 !important;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 600 !important;
        }
        div[data-testid="stContainer"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            padding: 20px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.04) !important;
        }
        button[kind="primary"] {
            background-color: #6B7C67 !important;
            color: #FFFFFF !important;
            border: none !important;
            font-weight: bold !important;
        }
        hr { border-color: #C5A059 !important; opacity: 0.6; }
    </style>
""", unsafe_allow_html=True)

# NAVIGAZIONE LATERALE
with st.sidebar:
    st.markdown("### 📌 Navigazione")
    st.page_link("app.py", label="Generatore Itinerari", icon="🏠")
    st.page_link("pages/1_Storico_Viaggi.py", label="Storico Viaggi", icon="📂")
    st.page_link("pages/2_Profilo.py", label="Il Mio Profilo", icon="👤")
    st.divider()
    st.caption("ATLAS v2.0 - Storico Avanzato")

st.title("📂 Archivio Storico Viaggi")
st.markdown("Consulta, ricarica o gestisci gli itinerari generati in precedenza.")

data_dir = "data"
os.makedirs(data_dir, exist_ok=True)

# Cerchiamo tutti i file txt salvati (esclusi file di sistema se presenti)
itinerary_files = [f for f in os.listdir(data_dir) if f.endswith(".txt") and f != "current_itinerary.txt"]

if not itinerary_files:
    st.info("Nessun itinerario storico salvato nell'archivio. Genera un nuovo viaggio dalla schermata principale per vederlo comparire qui.")
else:
    # Ordiniamo per data di modifica recente
    itinerary_files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)), reverse=True)

    selected_file = st.selectbox("Seleziona un viaggio dall'archivio:", itinerary_files)
    
    if selected_file:
        file_path = os.path.join(data_dir, selected_file)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("📥 Carica questo viaggio nella Home", type="primary"):
                st.session_state.current_itinerary = content
                # Estraiamo un nome pulito per la destinazione dal nome file
                dest_extracted = selected_file.replace("Atlas_Itinerario_", "").replace(".txt", "").replace("_", " ")
                st.session_state.trip_params = {"destination": dest_extracted}
                st.success(f"Viaggio '{dest_extracted}' caricato con successo! Torna alla Home per visualizzarlo.")
        with col_act2:
            if st.button("🗑️ Elimina dall'archivio"):
                os.remove(file_path)
                st.success("Itinerario eliminato dall'archivio.")
                st.rerun()

        st.divider()
        st.subheader(f"📄 Anteprima: {selected_file}")
        with st.container(border=True):
            st.markdown(content)