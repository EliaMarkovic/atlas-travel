import streamlit as st
import json
import os

PROFILE_PATH = os.path.join("data", "taste_graph.json")

def load_profile():
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Errore nella lettura del profilo: {e}")
    return {}

def save_profile(data):
    try:
        os.makedirs("data", exist_ok=True)
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Errore nel salvataggio: {e}")
        return False

st.set_page_config(
    page_title="Profilo Utente - Atlas",
    page_icon="👤",
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
    st.caption("Atlas v1.5 - Profilo Utente")

st.title("👤 Profilo & Preferenze di Viaggio")
st.markdown("Gestisci la tua scheda personale. Atlas userà questi parametri come base per calcolare ogni nuovo itinerario.")

profile_data = load_profile()
user_prof = profile_data.get("user_profile", {})

with st.form("profile_form"):
    st.subheader("📌 Anagrafica & Stile di Viaggio")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Nome", value=user_prof.get("name", "Elia"))
        age = st.number_input("Età", value=user_prof.get("age", 40), min_value=18, max_value=100)
    with col2:
        pace = st.selectbox("Passo di viaggio", ["rilassato ma curioso", "intenso e dinamico", "molto lento e contemplativo"], index=0)
        max_km = st.slider("Chilometri max a piedi / giorno", min_value=3, max_value=25, value=user_prof.get("travel_style", {}).get("max_walking_km_per_day", 10))

    st.divider()
    st.subheader("💰 Budget Tier & Abitudini")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        budget_tier = st.selectbox("Fascia di Budget predefinita", ["Economico / Stretto", "Medio-Alto (Qualità ed Esperienze)", "Lusso / Senza Limiti"], index=1)
    with col_b2:
        coffee_breaks = st.text_input("Frequenza pause", value=user_prof.get("constraints_and_habits", {}).get("coffee_breaks", "pausa caffè/ristoro ogni 2 ore"))

    dietary = st.text_input("Preferenze/Restrizioni Alimentari", value=user_prof.get("constraints_and_habits", {}).get("dietary_preferences", "cucina tipica locale, no fast food"))

    st.divider()
    st.subheader("⚖️ Pesi degli Interessi (0-10)")
    weights = user_prof.get("interests_weights", {})
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        w_arte = st.slider("Arte e Architettura", 0, 10, weights.get("arte_e_architettura", 9))
        w_cucina = st.slider("Cucina locale e Mercati", 0, 10, weights.get("cucina_locale_e_mercati", 9))
        w_musei = st.slider("Musei e Storia", 0, 10, weights.get("musei_e_storia", 7))
    with col_w2:
        w_natura = st.slider("Natura e Parchi", 0, 10, weights.get("natura_e_parchi", 6))
        w_nightlife = st.slider("Vita notturna e Club", 0, 10, weights.get("vita_notturna_e_club", 2))
        w_shopping = st.slider("Shopping commerciale", 0, 10, weights.get("shopping_commerciale", 1))

    st.divider()
    submitted = st.form_submit_button("💾 Salva Preferenze Profilo", type="primary")

if submitted:
    new_profile = {
        "user_profile": {
            "name": name,
            "age": age,
            "budget_tier": budget_tier,
            "travel_style": {
                "pace": pace,
                "max_walking_km_per_day": max_km,
                "preferred_transport": ["a piedi", "mezzi pubblici", "bicicletta"],
                "avoid": ["tour di gruppo affollati", "trappole per turisti", "orari troppo rigidi"]
            },
            "interests_weights": {
                "arte_e_architettura": w_arte,
                "cucina_locale_e_mercati": w_cucina,
                "musei_e_storia": w_musei,
                "natura_e_parchi": w_natura,
                "vita_notturna_e_club": w_nightlife,
                "shopping_commerciale": w_shopping
            },
            "constraints_and_habits": {
                "coffee_breaks": coffee_breaks,
                "museum_limit_per_day": 2,
                "dietary_preferences": dietary
            },
            "dynamic_feedback_history": user_prof.get("dynamic_feedback_history", [])
        }
    }
    if save_profile(new_profile):
        st.success("Profilo aggiornato con successo!")
        st.rerun()