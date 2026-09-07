import os
import requests
import urllib.parse

def render_interactive_map(destination: str, itinerary_text: str = ""):
    """
    Genera e renderizza una mappa interattiva Folium mobile-responsive.
    In caso di mancanza del modulo folium, effettua un fallback elegante
    senza mandare l'applicazione in crash.
    """
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        import streamlit as st
        st.warning("⚠️ Mappa interattiva temporaneamente disabilitata (modulo 'folium' non trovato nell'ambiente attivo).")
        st.markdown(f"[📍 Apri la posizione di **{destination}** direttamente su Google Maps](https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(destination)})")
        return

    try:
        # Otteniamo coordinate reali della destinazione via Open-Meteo
        encoded_dest = urllib.parse.quote(destination)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_dest}&count=1&language=it&format=json"
        geo_resp = requests.get(geo_url, timeout=3).json()
        
        if not geo_resp.get("results"):
            return
            
        lat = geo_resp["results"][0]["latitude"]
        lon = geo_resp["results"][0]["longitude"]
        city_name = geo_resp["results"][0].get("name", destination)
        country = geo_resp["results"][0].get("country", "")

        # Creazione della mappa con OpenStreetMap
        m = folium.Map(
            location=[lat, lon],
            zoom_start=13,
            tiles="OpenStreetMap"
        )

        folium.Marker(
            [lat, lon],
            popup=f"<b>{city_name}</b> ({country})<br>Destinazione principale",
            tooltip=city_name,
            icon=folium.Icon(color="green", icon="compass", prefix="fa")
        ).add_to(m)

        # Mappa responsive adatta a schermi mobile e desktop
        st_folium(m, use_container_width=True, height=300, returned_objects=[])

    except Exception as e:
        import streamlit as st
        st.caption(f"Impossibile caricare la mappa interattiva: {e}")