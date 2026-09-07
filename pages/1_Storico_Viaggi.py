import streamlit as st
import os
from src.history import get_saved_trips, load_trip_content, delete_trip_file

st.set_page_config(
    page_title="Storico Viaggi - Atlas",
    page_icon="📂",
    layout="centered"
)

st.markdown("""
    <style>
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    logo_path = os.path.join("data", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.title("🌍 Atlas")

    st.markdown("### 📌 Navigazione")
    st.page_link("../app.py", label="Generatore Itinerari", icon="🏠")
    st.page_link("1_Storico_Viaggi.py", label="Storico Viaggi", icon="📂")
    st.page_link("2_Profilo.py", label="Il Mio Profilo", icon="👤")

    st.divider()
    st.caption("Atlas v1.5 - Storico Viaggi")

st.title("📂 Storico e Gestione Viaggi Salvati")
st.markdown("Consulta i tuoi vecchi itinerari o fai pulizia rimuovendo i file di prova non più necessari.")

saved_trips = get_saved_trips()

if not saved_trips:
    st.info("Nessun itinerario salvato al momento.")
else:
    st.divider()
    
    with st.expander("🗑️ Pulizia File (Eliminazione Multipla)", expanded=False):
        st.write("Seleziona i file da eliminare definitivamente:")
        selected_to_delete = []
        for trip in saved_trips:
            if st.checkbox(f"📄 `{trip['filename']}`", key=f"del_chk_{trip['filename']}"):
                selected_to_delete.append(trip)
                
        if selected_to_delete:
            if st.button(f"🔥 Elimina {len(selected_to_delete)} file selezionati", type="primary"):
                deleted_count = sum(1 for trip in selected_to_delete if delete_trip_file(trip["path"]))
                st.success(f"Eliminati con successo {deleted_count} file!")
                st.rerun()

    st.divider()
    st.subheader("📖 Consulta un Itinerario")
    trip_options = {trip["filename"]: trip["path"] for trip in saved_trips}
    chosen_trip_name = st.selectbox("Scegli un itinerario:", ["-- Seleziona --"] + list(trip_options.keys()))

    if chosen_trip_name and chosen_trip_name != "-- Seleziona --":
        selected_path = trip_options[chosen_trip_name]
        col_title, col_del = st.columns([0.8, 0.2])
        with col_title:
            st.info(f"Visualizzando: `{chosen_trip_name}`")
        with col_del:
            if st.button("🗑️ Elimina", help="Elimina questo singolo file"):
                if delete_trip_file(selected_path):
                    st.success("File eliminato!")
                    st.rerun()

        trip_text = load_trip_content(selected_path)
        st.markdown("---")
        st.markdown(trip_text)