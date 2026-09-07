import streamlit as st
import json
import os
import re
import urllib.parse
from datetime import date, timedelta
from agent import get_travel_concierge_response, get_destination_weather, build_google_flights_url
from dreambox import get_inbox_items, get_dream_notes, save_dream_note, delete_dream_note
from exporter import save_itinerary_to_file
from feedback import record_user_feedback
from mapping import render_interactive_map

st.set_page_config(
    page_title="ATLAS - Personal Travel Concierge",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING CSS PER MOSTRARE L'HEADER E L'ICONA MENU SU MOBILE ---
st.markdown("""
    <style>
        /* Assicura che l'header e l'icona menu siano visibili su mobile */
        header[data-testid="stHeader"] {
            display: flex !important;
            z-index: 99999 !important;
        }
        button[data-testid="baseButton-header"] {
            display: inline-flex !important;
            visibility: visible !important;
        }

        /* ELIMINA DEFINITIVAMENTE IL MENU NATIVO IN ALTO */
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        div[data-testid="stSidebarNavSeparator"] {
            display: none !important;
            height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
        }
    </style>
""", unsafe_allow_html=True)
# Inserimento esplicito nella Sidebar per sbloccarla su mobile
with st.sidebar:
    st.title("🧭 ATLAS")
    st.caption("Navigation & Options")

st.markdown("""
    <style>
        /* Mantiene visibile l'interfaccia principale e la sidebar */
        footer, header {
            display: none !important;
        }

        /* Stile personalizzato per la Sidebar visibile */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #CBD5E1 !important;
        }

        /* Modern Slate Background */
        .stApp {
            background: linear-gradient(180deg, #F1F5F9 0%, #E2E8F0 100%) !important;
            color: #0F172A !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Card Container - Glassmorphic Style */
        div[data-testid="stContainer"] {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 16px !important;
            padding: 24px !important;
            margin-bottom: 20px !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02) !important;
        }

        /* Headers Styling */
        h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #1E293B !important;
            font-weight: 700 !important;
            letter-spacing: -0.3px !important;
        }

        /* Primary Action Buttons (Gradiente Salvia / Ardesia) */
        button[kind="primary"] {
            background: linear-gradient(135deg, #3B4A3E 0%, #222C24 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            letter-spacing: 0.5px !important;
            box-shadow: 0 4px 14px rgba(34, 44, 36, 0.35) !important;
            min-height: 48px !important;
            transition: all 0.2s ease-in-out !important;
        }

        button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(34, 44, 36, 0.45) !important;
        }

        /* Secondary Action Buttons */
        button[kind="secondary"] {
            background-color: #FFFFFF !important;
            color: #334155 !important;
            border: 1px solid #94A3B8 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            min-height: 42px !important;
        }

        /* Input Fields Styling */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], div[data-baseweb="input"] {
            border-radius: 10px !important;
            border: 1px solid #94A3B8 !important;
            background-color: #FAFAFA !important;
            color: #0F172A !important;
            font-size: 15px !important;
            min-height: 44px !important;
        }

        /* Multiselect Tags */
        span[data-baseweb="tag"] {
            background-color: #3B4A3E !important;
            border-radius: 6px !important;
            padding: 4px 10px !important;
        }

        span[data-baseweb="tag"] span {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Tab Navigation Bar (iOS Style) */
        div[data-baseweb="tab-list"] {
            gap: 6px !important;
            background-color: #E2E8F0 !important;
            padding: 6px !important;
            border-radius: 12px !important;
        }

        button[data-baseweb="tab"] {
            border-radius: 8px !important;
            padding: 8px 16px !important;
            border: none !important;
            color: #475569 !important;
            font-weight: 600 !important;
        }

        button[aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
            font-weight: 700 !important;
        }

        /* Custom Badge Pill */
        .badge-pill {
            background: #E2E8F0;
            color: #1E293B;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
            margin-right: 6px;
            margin-bottom: 6px;
        }
    </style>
""", unsafe_allow_html=True)

if "current_itinerary" not in st.session_state:
    st.session_state.current_itinerary = None
if "trip_params" not in st.session_state:
    st.session_state.trip_params = {}

def load_taste_graph():
    path = os.path.join("data", "taste_graph.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "File profilo non trovato!"}

profile_data = load_taste_graph()

def fix_google_maps_links(text: str) -> str:
    def replace_match(match):
        label = match.group(1)
        url = match.group(2)
        if "google.com/travel/flights" in url:
            return f"[{label if label else '✈️ Apri ricerca su Google Flights'}]({url})"
            
        if "apri" in label.lower() or "maps" in label.lower() or label.strip() == "":
            query_match = re.search(r'query=([^&]+)', url)
            if query_match:
                place_name = query_match.group(1).replace('+', ' ').replace('%20', ' ')
                return f"[📍 {place_name} (Apri Mappa)]({url})"
        return f"[📍 {label}]({url})"

    pattern = r'\[([^\]]*)\]\((https?://[^\)]+)\)'
    return re.sub(pattern, replace_match, text)

def parse_itinerary_advanced(itinerary_text: str):
    if not itinerary_text:
        return {}, ""

    itinerary_text = fix_google_maps_links(itinerary_text)
    budget_summary = ""
    main_text = itinerary_text

    budget_keywords = [
        r'##\s*STIMA ECONOMICA', 
        r'##\s*BOX STIMA', 
        r'STIMA ECONOMICA', 
        r'BOX STIMA ECONOMICA'
    ]
    
    for kw in budget_keywords:
        parts = re.split(f'(?i)(?={kw})', main_text, maxsplit=1)
        if len(parts) > 1:
            main_text = parts[0].strip()
            budget_summary = parts[1].strip()
            break

    day_matches = re.split(r'\n(?=##\s*(?:Giorno|Day)|\*\*\s*(?:Giorno|Day)|Giorno\s+\d+|Day\s+\d+|##\s*PROPOSTA ALLOGGI|##\s*LOGISTICA TRASPORTI)', main_text, flags=re.IGNORECASE)
    days_dict = {}

    for day_block in day_matches:
        if not day_block:
            continue
        block_clean = str(day_block).strip()
        if not block_clean:
            continue

        lines = block_clean.split('\n')
        day_title = lines[0].replace('#', '').replace('*', '').strip()
        day_content = '\n'.join(lines[1:]).strip()

        if any(k in day_title.lower() for k in ["giorno", "day", "proposta alloggi", "logistica trasporti"]):
            step_matches = re.split(r'\n(?=###\s+|\n\*\*Giorno\s+\d+|\n\*\*(?:Mattina|Pranzo|Pomeriggio|Sera))', day_content, flags=re.IGNORECASE)
            steps = []

            for step_b in step_matches:
                if not step_b:
                    continue
                step_clean = str(step_b).strip()
                if step_clean:
                    s_lines = step_clean.split('\n')
                    s_title = s_lines[0].replace('#', '').replace('*', '').strip()
                    s_body = '\n'.join(s_lines[1:]).strip() if len(s_lines) > 1 else step_clean
                    steps.append({
                        "title": s_title,
                        "content": s_body
                    })

            if not steps:
                steps = [{"title": "Dettagli della sezione", "content": day_content}]

            tab_label = day_title.split('-')[0].strip() if '-' in day_title else day_title
            if len(tab_label) > 22:
                tab_label = tab_label[:20] + "..."

            days_dict[tab_label] = steps
        else:
            if "Info e Logistica" not in days_dict:
                days_dict["Info e Logistica"] = [{"title": day_title, "content": day_content}]

    return days_dict, budget_summary

# --- BARRA LATERALE ---
with st.sidebar:
    st.markdown("### 📌 Navigazione")
    st.page_link("app.py", label="Generatore Itinerari", icon="🏠")
    st.page_link("pages/1_Storico_Viaggi.py", label="Storico Viaggi", icon="📂")
    st.page_link("pages/2_Profilo.py", label="Il Mio Profilo", icon="👤")

    st.divider()

    st.header("⚙️ Configurazione")
    st.info("🔒 **Privacy & Sicurezza:** I tuoi dati vengono elaborati in memoria locale e non vengono ceduti a terzi.")
    
    if "user_profile" in profile_data:
        st.write(f"**Utente:** {profile_data['user_profile'].get('name', 'Elia')}")
        st.write(f"**Passo:** {profile_data['user_profile'].get('travel_style', {}).get('pace', 'rilassato')}")
        st.write(f"**Budget:** {profile_data['user_profile'].get('budget_tier', 'Medio-Alto')}")
        
    st.divider()
    
    st.header("📥 Dream Box")
    st.caption("Salva idee e spunti al volo da includere nei tuoi itinerari.")
    new_note = st.text_input("Nuova ispirazione:", placeholder="Es. Visita alla cantina X")
    if st.button("Aggiungi alla Dream Box", use_container_width=True):
        if new_note:
            save_dream_note(new_note)
            st.success("Nota salvata!")
            st.rerun()
            
    dreams = get_dream_notes()
    if dreams:
        st.markdown("**Note salvate:**")
        for idx, item in enumerate(dreams):
            col_note, col_del = st.columns([0.8, 0.2])
            with col_note:
                st.caption(f"- {item['note']}")
            with col_del:
                if st.button("🗑️", key=f"del_dream_{idx}", help="Elimina nota"):
                    delete_dream_note(idx)
                    st.rerun()
    else:
        st.caption("La Dream Box è vuota.")

    st.divider()
    st.caption("ATLAS v2.5 - Mobile Ready Suite")

# --- AREA HEADER / LOGO ---
logo_path = os.path.join("data", "logo.png")
col_l1, col_l2, col_l3 = st.columns([0.35, 0.3, 0.35])
with col_l2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.title("🧭 ATLAS")
        st.caption("PERSONAL TRAVEL CONCIERGE")

st.markdown("<hr style='margin-bottom: 20px; border-color: #CBD5E1;'>", unsafe_allow_html=True)

# --- VISUALIZZAZIONE ITINERARIO O MOSTRA FORM ---
if st.session_state.current_itinerary:
    col_hdr1, col_hdr2 = st.columns([0.65, 0.35])
    with col_hdr1:
        st.success("✨ Itinerario Pronto!")
    with col_hdr2:
        if st.button("✏️ Nuova Ricerca", use_container_width=True):
            st.session_state.current_itinerary = None
            st.rerun()

    if "trip_params" in st.session_state and st.session_state.trip_params.get("destination"):
        params = st.session_state.trip_params
        dest_name = params.get("destination")
        origin_name = params.get("origin_city", "Partenza")
        start_d = params.get("start_date", "")
        end_d = params.get("end_date", "")
        
        weather_data = get_destination_weather(dest_name)
        flights_direct_url = build_google_flights_url(origin_name, dest_name, start_d, end_d)
        
        with st.expander(f"🗺️ **Mappa, Voli & Meteo ({dest_name})**", expanded=False):
            st.markdown(f"""
                <div>
                    <span class="badge-pill">🛫 {origin_name} ➔ {dest_name}</span>
                    <span class="badge-pill">🚗 {params.get('transport_mode', 'Mezzi')}</span>
                    <span class="badge-pill">🍽️ {params.get('meal_style', 'Ibrido Famiglia').split('(')[0]}</span>
                </div>
            """, unsafe_allow_html=True)
            st.write(f"**Alloggio base:** `{params.get('lodging_address', 'Proposta da generare')}`")
            
            if params.get("origin_city") != dest_name:
                st.markdown("---")
                st.markdown(f"[✈️ **Cerca Voli {origin_name} ➔ {dest_name} su Google Flights**]({flights_direct_url})")

            st.markdown("---")
            st.markdown("**📍 Mappa Interattiva:**")
            from mapping import render_interactive_map
            render_interactive_map(dest_name, st.session_state.current_itinerary)
            
            if weather_data and "daily" in weather_data:
                daily = weather_data["daily"]
                dates = daily.get("time", [])
                t_max = daily.get("temperature_2m_max", [])
                t_min = daily.get("temperature_2m_min", [])
                precip = daily.get("precipitation_probability_max", [])
                
                num_days = 5
                if start_d and end_d:
                    try:
                        d1 = date.fromisoformat(start_d)
                        d2 = date.fromisoformat(end_d)
                        num_days = max(1, (d2 - d1).days + 1)
                    except ValueError:
                        pass

                st.markdown("---")
                st.markdown(f"**Meteo previsto ({num_days} gg):**")
                for i in range(min(len(dates), num_days)):
                    prob_p = precip[i] if i < len(precip) else 0
                    rain_icon = "🌧️" if prob_p >= 70 else "☀️"
                    st.write(f"- `{dates[i]}`: {rain_icon} Min {t_min[i]}°C / Max {t_max[i]}°C | Pioggia: **{prob_p}%**")

    # --- BARRA METRICA BUDGET LIVE ---
    if "trip_expenses" not in st.session_state:
        st.session_state.trip_expenses = []
    total_spent = sum(item["amount"] for item in st.session_state.trip_expenses)
    target_daily = st.session_state.trip_params.get("daily_budget", 120.0)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="📊 Speso Finora", value=f"{total_spent:.2f} €")
    with col_m2:
        st.metric(label="🎯 Target Giornaliero", value=f"{target_daily:.2f} €/p")

    days_dict, budget_summary = parse_itinerary_advanced(st.session_state.current_itinerary)
    
    if days_dict:
        tab_titles = list(days_dict.keys())
        tabs = st.tabs(tab_titles)
        
        for tab, day_title in zip(tabs, tab_titles):
            with tab:
                st.markdown(f"## 🗓️ {day_title}")
                steps = days_dict[day_title]
                
                for idx, step in enumerate(steps):
                    with st.container(border=True):
                        st.subheader(f"📍 {step['title']}")
                        st.markdown(step['content'])
                        
                        st.divider()
                        st.caption("🛠️ **Azioni rapide sulla tappa:**")
                        col_btn1, col_btn2 = st.columns(2)
                        
                        key_suffix = f"{day_title}_{idx}".replace(" ", "_").replace(":", "").replace("-", "")
                        
                        with col_btn1:
                            if st.button("👁️ Escludi Tappa", key=f"excl_{key_suffix}", use_container_width=True):
                                record_user_feedback("Già visto / Da escludere", step['title'], "Escluso direttamente dalla card")
                                with st.spinner("Sostituzione in corso..."):
                                    params = st.session_state.trip_params
                                    adapted_prompt = f"L'utente vuole escludere la tappa '{step['title']}'. Proponi un'alternativa coerente per questa specifica fascia oraria."
                                    updated_itinerary = get_travel_concierge_response(
                                        destination_prompt=params.get("destination", ""),
                                        start_date=params.get("start_date", ""),
                                        arrival_time=params.get("arrival_time", ""),
                                        end_date=params.get("end_date", ""),
                                        departure_time=params.get("departure_time", ""),
                                        origin_city=params.get("origin_city", ""),
                                        transit_mode=params.get("transit_mode", ""),
                                        arrival_hub=params.get("arrival_hub", ""),
                                        has_lodging=params.get("has_lodging", "Sì"),
                                        lodging_address=params.get("lodging_address", ""),
                                        meal_style=params.get("meal_style", "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)"),
                                        travel_context=params.get("travel_context", ""),
                                        num_adults=params.get("num_adults", 1),
                                        num_children=params.get("num_children", 0),
                                        children_ages=params.get("children_ages", ""),
                                        daily_budget=params.get("daily_budget", 120.0),
                                        interests=params.get("interests", []),
                                        trip_type=params.get("trip_type", "Città Singola / Stanziale"),
                                        transport_mode=params.get("transport_mode", "Mezzi Pubblici / A piedi"),
                                        live_adaptation_prompt=adapted_prompt
                                    )
                                    st.session_state.current_itinerary = updated_itinerary
                                    save_itinerary_to_file(params.get("destination", "Viaggio"), updated_itinerary)
                                    st.rerun()

                        with col_btn2:
                            if st.button("🌧️ Piove (Piano B)", key=f"rain_{key_suffix}", use_container_width=True):
                                record_user_feedback("Maltempo", step['title'], "Richiesta alternativa al chiuso")
                                with st.spinner("Ricerca alternativa al chiuso..."):
                                    params = st.session_state.trip_params
                                    adapted_prompt = f"Piove durante l'attività '{step['title']}'. Proponi subito un'alternativa al chiuso nelle vicinanze."
                                    updated_itinerary = get_travel_concierge_response(
                                        destination_prompt=params.get("destination", ""),
                                        start_date=params.get("start_date", ""),
                                        arrival_time=params.get("arrival_time", ""),
                                        end_date=params.get("end_date", ""),
                                        departure_time=params.get("departure_time", ""),
                                        origin_city=params.get("origin_city", ""),
                                        transit_mode=params.get("transit_mode", ""),
                                        arrival_hub=params.get("arrival_hub", ""),
                                        has_lodging=params.get("has_lodging", "Sì"),
                                        lodging_address=params.get("lodging_address", ""),
                                        meal_style=params.get("meal_style", "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)"),
                                        travel_context=params.get("travel_context", ""),
                                        num_adults=params.get("num_adults", 1),
                                        num_children=params.get("num_children", 0),
                                        children_ages=params.get("children_ages", ""),
                                        daily_budget=params.get("daily_budget", 120.0),
                                        interests=params.get("interests", []),
                                        trip_type=params.get("trip_type", "Città Singola / Stanziale"),
                                        transport_mode=params.get("transport_mode", "Mezzi Pubblici / A piedi"),
                                        live_adaptation_prompt=adapted_prompt
                                    )
                                    st.session_state.current_itinerary = updated_itinerary
                                    save_itinerary_to_file(params.get("destination", "Viaggio"), updated_itinerary)
                                    st.rerun()
    else:
        st.markdown(st.session_state.current_itinerary)

    # --- SEZIONE CONSIGLI ALLOGGI ---
    st.divider()
    with st.expander("🏨 **Alloggi & Pernottamenti Strategici**", expanded=False):
        params = st.session_state.trip_params
        dest_query = params.get("destination", "Destinazione").replace(" ", "+")
        checkin = params.get("start_date", "")
        checkout = params.get("end_date", "")

        booking_url = f"https://www.booking.com/searchresults.it.html?ss={dest_query}&checkin={checkin}&checkout={checkout}"
        google_hotels_url = f"https://www.google.com/travel/hotels/{dest_query}"
        
        st.markdown(f"- [🏨 **Cerca Alloggi su Booking.com**]({booking_url})")
        st.markdown(f"- [🔍 **Confronta Prezzi su Google Hotels**]({google_hotels_url})")

        if st.button("💡 Chiedi ad Atlas 3 Strutture Consigliate", key="btn_suggest_hotels", use_container_width=True):
            with st.spinner("Ricerca strutture consigliate..."):
                hotel_prompt = f"Consiglia 3 alloggi/hotel reali a {params.get('destination')}: 1 Economico/Guesthouse, 1 Boutique/Caratteristico, 1 Comfort/Hotel. Per ognuno indica nome, zona, motivo della scelta e prezzo stimato a notte."
                hotel_resp = get_travel_concierge_response(
                    destination_prompt=params.get("destination", ""),
                    start_date=params.get("start_date", ""),
                    arrival_time=params.get("arrival_time", ""),
                    end_date=params.get("end_date", ""),
                    departure_time=params.get("departure_time", ""),
                    origin_city=params.get("origin_city", ""),
                    transit_mode=params.get("transit_mode", ""),
                    arrival_hub=params.get("arrival_hub", ""),
                    has_lodging=params.get("has_lodging", "Sì"),
                    lodging_address=params.get("lodging_address", ""),
                    meal_style=params.get("meal_style", "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)"),
                    travel_context=params.get("travel_context", ""),
                    num_adults=params.get("num_adults", 1),
                    num_children=params.get("num_children", 0),
                    children_ages=params.get("children_ages", ""),
                    daily_budget=params.get("daily_budget", 120.0),
                    interests=params.get("interests", []),
                    trip_type=params.get("trip_type", "Città Singola / Stanziale"),
                    transport_mode=params.get("transport_mode", "Mezzi Pubblici / A piedi"),
                    live_adaptation_prompt=hotel_prompt
                )
                st.markdown(fix_google_maps_links(hotel_resp))

    # --- CONSIGLI GOURMET SU MISURA ---
    st.divider()
    with st.expander("🍷 **Consigli Gourmet & Ristoranti Tipici**", expanded=False):
        meal_type = st.selectbox("Cosa stai cercando?", ["Cena Tipica / Trattoria Locale", "Pranzo Rapido di Qualità", "Aperitivo / Enoteca con Prodotti Tipici", "Ristorante Gourmet / Esperienza"])
        
        if st.button("🔎 Cerca Locali Consigliati", key="btn_gourmet_search", use_container_width=True):
            with st.spinner("Selezione opzioni enogastronomiche..."):
                params = st.session_state.trip_params
                gourmet_prompt = f"Fornisci 3 consigli eccellenti per '{meal_type}' a {params.get('destination', 'destinazione')}, vicino a {params.get('lodging_address', 'centro')}. Per ciascuno indica: Nome, Specialità imperdibile, Fascia di prezzo reale e link Google Maps."
                gourmet_resp = get_travel_concierge_response(
                    destination_prompt=params.get("destination", ""),
                    start_date=params.get("start_date", ""),
                    arrival_time=params.get("arrival_time", ""),
                    end_date=params.get("end_date", ""),
                    departure_time=params.get("departure_time", ""),
                    origin_city=params.get("origin_city", ""),
                    transit_mode=params.get("transit_mode", ""),
                    arrival_hub=params.get("arrival_hub", ""),
                    has_lodging=params.get("has_lodging", "Sì"),
                    lodging_address=params.get("lodging_address", ""),
                    meal_style=params.get("meal_style", "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)"),
                    travel_context=params.get("travel_context", ""),
                    num_adults=params.get("num_adults", 1),
                    num_children=params.get("num_children", 0),
                    children_ages=params.get("children_ages", ""),
                    daily_budget=params.get("daily_budget", 120.0),
                    interests=params.get("interests", []),
                    trip_type=params.get("trip_type", "Città Singola / Stanziale"),
                    transport_mode=params.get("transport_mode", "Mezzi Pubblici / A piedi"),
                    live_adaptation_prompt=gourmet_prompt
                )
                st.markdown(fix_google_maps_links(gourmet_resp))

    if budget_summary:
        st.divider()
        with st.container(border=True):
            st.markdown(budget_summary)

        with st.expander("💳 **Tracker Spese Effettive**", expanded=False):
            exp_desc = st.text_input("Descrizione spesa:", placeholder="Es. Cena Osteria", key="exp_desc_input")
            exp_amount = st.number_input("Importo (€):", min_value=0.0, step=5.0, key="exp_amount_input")
            
            if st.button("Aggiungi Spesa", key="btn_add_expense", use_container_width=True):
                if exp_desc and exp_amount > 0:
                    st.session_state.trip_expenses.append({"desc": exp_desc, "amount": exp_amount})
                    st.success("Spesa registrata!")
                    st.rerun()

            if st.session_state.trip_expenses:
                st.markdown("---")
                for i, item in enumerate(st.session_state.trip_expenses):
                    st.caption(f"- {item['desc']}: **{item['amount']:.2f} €**")

    st.divider()
    st.subheader("🛡️ Segnalazione Imprevisto Generale")
    feedback_action = st.selectbox(
        "Tipo di imprevisto:",
        ["Luogo già visto / Da escludere", "Imprevisto / Maltempo (Piano B)", "Cambio preferenza ristorante / cibo"],
        key="fb_action_live"
    )
    target_item = st.text_input("Descrivi l'imprevisto:", placeholder="Es. Ritardo treno o strada chiusa", key="fb_item_live")

    if st.button("🚨 Registra e Riprogramma Itinerario", type="primary", key="btn_adapt_live", use_container_width=True):
        if target_item:
            record_user_feedback(feedback_action, target_item, "Adattamento live generale")
            with st.spinner("Riprogrammazione in corso..."):
                params = st.session_state.trip_params
                adapted_prompt = f"L'utente segnala '{target_item}' ({feedback_action}). Risolvi l'imprevisto e rimodula le tappe."
                updated_itinerary = get_travel_concierge_response(
                    destination_prompt=params.get("destination", ""),
                    start_date=params.get("start_date", ""),
                    arrival_time=params.get("arrival_time", ""),
                    end_date=params.get("end_date", ""),
                    departure_time=params.get("departure_time", ""),
                    origin_city=params.get("origin_city", ""),
                    transit_mode=params.get("transit_mode", ""),
                    arrival_hub=params.get("arrival_hub", ""),
                    has_lodging=params.get("has_lodging", "Sì"),
                    lodging_address=params.get("lodging_address", ""),
                    meal_style=params.get("meal_style", "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)"),
                    travel_context=params.get("travel_context", ""),
                    num_adults=params.get("num_adults", 1),
                    num_children=params.get("num_children", 0),
                    children_ages=params.get("children_ages", ""),
                    daily_budget=params.get("daily_budget", 120.0),
                    interests=params.get("interests", []),
                    trip_type=params.get("trip_type", "Città Singola / Stanziale"),
                    transport_mode=params.get("transport_mode", "Mezzi Pubblici / A piedi"),
                    live_adaptation_prompt=adapted_prompt
                )
                if updated_itinerary.startswith("⚠️"):
                    st.error(updated_itinerary)
                else:
                    st.session_state.current_itinerary = updated_itinerary
                    save_itinerary_to_file(params.get("destination", "Viaggio"), updated_itinerary)
                    st.success("Itinerario Riprogrammato!")
                    st.rerun()

    st.divider()
    st.subheader("📲 Esporta e Sincronizza")
    
    params = st.session_state.trip_params
    dest_name = params.get("destination", "Viaggio")
    start_d = params.get("start_date", "")
    
    from src.exporter import generate_ics_calendar, generate_pdf_itinerary
    
    ics_content = generate_ics_calendar(dest_name, st.session_state.current_itinerary, start_d)
    
    st.download_button(
        label="📅 Aggiungi a Calendar (.ics)",
        data=ics_content,
        file_name=f"Atlas_Itinerario_{dest_name}.ics",
        mime="text/calendar",
        use_container_width=True
    )
    
    try:
        pdf_bytes = generate_pdf_itinerary(dest_name, st.session_state.current_itinerary)
        st.download_button(
            label="📄 Scarica PDF Stampabile",
            data=pdf_bytes,
            file_name=f"Atlas_Itinerario_{dest_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Errore generazione PDF: {e}")

    st.markdown("""
        <div style="text-align: center; margin-top: 25px; margin-bottom: 15px;">
            <a href="#" style="background-color: #3B4A3E; color: white; padding: 12px 24px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block;">⬆️ Torna in cima</a>
        </div>
    """, unsafe_allow_html=True)

else:
    # --- FORM INIZIALE SUDDIVISO IN 3 SCHEDE CARDS ELEGANTI ---
    saved_params = st.session_state.trip_params
    
    # SCHEDA 1: ROTTA E DESTINAZIONE
    with st.container(border=True):
        st.markdown("### 1. Rotta e Destinazione")
        destination = st.text_input(
            "Meta o regione del Tour:", 
            placeholder="Es. Cormòns, Stoccolma, Parigi",
            value=saved_params.get("destination", ""),
            help="(i) Indica la città o la regione di interesse."
        )

        skip_transit = st.checkbox(
            "📍 Sono già sul posto (Salta la ricerca di voli e trasporti di arrivo)", 
            value=saved_params.get("skip_transit", False)
        )

        if skip_transit:
            origin_city = destination
            transit_mode = "Nessuno (Già a destinazione)"
        else:
            origin_city = st.text_input(
                "Città / Aeroporto di Partenza:",
                placeholder="Es. Belo Horizonte, Milano, Roma",
                value=saved_params.get("origin_city", "Belo Horizonte"),
                help="(i) Serve a calcolare le rotte aeree e le stime dei trasporti."
            )
            transit_options = [
                "Chiedi ad ATLAS rotta e tratte consigliate",
                "Volo / Treno già prenotato (Solo guida sul posto)"
            ]
            curr_transit = saved_params.get("transit_mode", "Chiedi ad ATLAS rotta e tratte consigliate")
            transit_idx = transit_options.index(curr_transit) if curr_transit in transit_options else 0
            transit_mode = st.selectbox("Come arrivi a destinazione?", transit_options, index=transit_idx)

        trip_type = st.selectbox(
            "Tipologia di Viaggio:",
            ["Città Singola / Stanziale", "Tour Itinerante / On-The-Road (Multi-Tappa)"],
            index=0 if saved_params.get("trip_type") != "Tour Itinerante / On-The-Road (Multi-Tappa)" else 1
        )
        
        transport_options = ["Mezzi Pubblici / A piedi", "Auto a Noleggio (stima carburante/pedaggi)", "Auto Propria", "Treni / Pass Ferroviario", "Voli Interni + Taxi"]
        current_trans = saved_params.get("transport_mode", "Mezzi Pubblici / A piedi")
        trans_idx = transport_options.index(current_trans) if current_trans in transport_options else 0
        transport_mode = st.selectbox("Mezzo sul posto:", transport_options, index=trans_idx)

    # SCHEDA 2: LOGISTICA, ALLOGGIO & PASTI
    with st.container(border=True):
        st.markdown("### 2. Logistica, Alloggio & Pasti")
        
        has_lodging_check = st.checkbox(
            "🏨 Ho già un alloggio (Salta la proposta hotel)", 
            value=saved_params.get("has_lodging") == "Sì" if "has_lodging" in saved_params else True
        )

        if has_lodging_check:
            has_lodging = "Sì"
            lodging_address = st.text_input(
                "Indirizzo o Nome Alloggio:",
                placeholder="Es. Via Roma 10, Cormòns oppure Parigi centro",
                value=saved_params.get("lodging_address", "") if saved_params.get("lodging_address") != "Proposta da generare" else ""
            )
        else:
            has_lodging = "No"
            lodging_address = "Proposta da generare"
            st.info("💡 Atlas analizzerà le zone migliori e includerà 2 proposte alloggio consigliate.")

        meal_style_options = [
            "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)",
            "Tutti i pasti al ristorante / locale",
            "Autonomo (Cucinare quasi sempre in appartamento)"
        ]
        curr_meal_style = saved_params.get("meal_style", "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)")
        meal_style_idx = meal_style_options.index(curr_meal_style) if curr_meal_style in meal_style_options else 0

        meal_style = st.selectbox("Gestione Pasti:", meal_style_options, index=meal_style_idx)

        today = date.today()
        default_end = today + timedelta(days=5)

        try:
            s_date_val = date.fromisoformat(saved_params.get("start_date")) if saved_params.get("start_date") else today
        except Exception:
            s_date_val = today

        try:
            e_date_val = date.fromisoformat(saved_params.get("end_date")) if saved_params.get("end_date") else default_end
        except Exception:
            e_date_val = default_end

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data arrivo", value=s_date_val, format="DD/MM/YYYY")
        with col2:
            end_date = st.date_input("Data partenza", value=e_date_val, format="DD/MM/YYYY")

        col3, col4 = st.columns(2)
        with col3:
            arrival_time = st.time_input("Orario arrivo", value=None)
        with col4:
            departure_time = st.time_input("Orario partenza", value=None)

        if not skip_transit:
            arrival_hub = st.text_input(
                "Hub di arrivo (Aeroporto / Stazione):",
                placeholder="Es. Aeroporto Charles de Gaulle o Stazione Centrale",
                value=saved_params.get("arrival_hub", "")
            )
        else:
            arrival_hub = ""

    # SCHEDA 3: GRUPPO & PREFERENZE
    with st.container(border=True):
        st.markdown("### 3. Gruppo & Preferenze")

        context_options = ["In famiglia (con bambini)", "In coppia", "Da solo / Esplorazione", "Con amici"]
        current_ctx = saved_params.get("travel_context", "In famiglia (con bambini)")
        ctx_idx = context_options.index(current_ctx) if current_ctx in context_options else 0

        travel_context = st.selectbox("Con chi viaggi?", context_options, index=ctx_idx, key="select_travel_context")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            num_adults = st.number_input("Adulti", min_value=1, max_value=10, value=int(saved_params.get("num_adults", 2)))
        with col_p2:
            num_children = st.number_input("Bambini", min_value=0, max_value=10, value=int(saved_params.get("num_children", 0)))
            
        children_ages = st.text_input("Età bambini:", placeholder="Es. 4, 8, 12", value=saved_params.get("children_ages", ""))

        if travel_context == "Da solo / Esplorazione" and (num_adults > 1 or num_children > 0):
            st.warning("⚠️ Hai selezionato 'Da solo', ma risulta indicato più di 1 passeggero.")
        elif travel_context == "In coppia" and (num_adults != 2 or num_children > 0):
            st.warning("⚠️ Per un viaggio 'In coppia' sono previsti solitamente 2 adulti e 0 bambini.")
        elif travel_context == "In famiglia (con bambini)" and num_children == 0:
            st.info("💡 Suggerimento: Hai indicato 'In famiglia (con bambini)', ma il numero di bambini è 0.")

        daily_budget = st.slider("Budget Giornaliero (€/persona):", min_value=30.0, max_value=500.0, value=float(saved_params.get("daily_budget", 120.0)), step=10.0)

        all_interests = ["Arte", "Architettura", "Musica", "Ballo", "Intrattenimento", "Gioco / Gaming", "Cultura & Storia", "Cucina & Enogastronomia", "Natura & Relax"]
        saved_interests = saved_params.get("interests", ["Arte", "Architettura", "Cultura & Storia", "Cucina & Enogastronomia"])
        valid_default_interests = [i for i in saved_interests if i in all_interests]

        interests = st.multiselect("Interessi chiave:", all_interests, default=valid_default_interests if valid_default_interests else ["Arte", "Architettura", "Cultura & Storia", "Cucina & Enogastronomia"])

        dreams = get_dream_notes()
        selected_dreams = []
        if dreams:
            st.markdown("📥 **Includi dalla Dream Box:**")
            for idx, item in enumerate(dreams):
                if st.checkbox(f"{item['note']}", key=f"dream_use_{idx}"):
                    selected_dreams.append(item['note'])

    btn_label = "🔄 Rigenera Itinerario" if saved_params.get("destination") else "🚀 Genera Itinerario Intelligente"
    
    if st.button(btn_label, type="primary", use_container_width=True):
        if destination:
            arr_str = str(arrival_time) if arrival_time else "Non specificato"
            dep_str = str(departure_time) if departure_time else "Non specificato"
            
            combined_interests = interests + selected_dreams
            
            st.session_state.trip_params = {
                "destination": destination,
                "origin_city": origin_city,
                "skip_transit": skip_transit,
                "trip_type": trip_type,
                "transport_mode": transport_mode,
                "transit_mode": transit_mode,
                "has_lodging": has_lodging,
                "lodging_address": lodging_address,
                "meal_style": meal_style,
                "start_date": str(start_date),
                "arrival_time": arr_str,
                "end_date": str(end_date),
                "departure_time": dep_str,
                "arrival_hub": arrival_hub,
                "travel_context": travel_context,
                "num_adults": num_adults,
                "num_children": num_children,
                "children_ages": children_ages,
                "daily_budget": daily_budget,
                "interests": combined_interests
            }

            with st.spinner("Atlas sta elaborando l'itinerario..."):
                itinerary = get_travel_concierge_response(
                    destination_prompt=destination,
                    start_date=str(start_date),
                    arrival_time=arr_str,
                    end_date=str(end_date),
                    departure_time=dep_str,
                    origin_city=origin_city,
                    transit_mode=transit_mode,
                    arrival_hub=arrival_hub,
                    has_lodging=has_lodging,
                    lodging_address=lodging_address,
                    meal_style=meal_style,
                    travel_context=travel_context,
                    num_adults=num_adults,
                    num_children=num_children,
                    children_ages=children_ages,
                    daily_budget=daily_budget,
                    interests=combined_interests,
                    trip_type=trip_type,
                    transport_mode=transport_mode
                )
                
            if itinerary.startswith("⚠️"):
                st.error(itinerary)
            else:
                st.session_state.current_itinerary = itinerary
                save_itinerary_to_file(destination, itinerary)
                st.rerun()
        else:
            st.warning("Inserisci una destinazione per iniziare.")
