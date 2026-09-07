import streamlit as st
import json
import os

st.set_page_config(
    page_title="Il Mio Profilo - ATLAS",
    page_icon="👤",
    layout="centered"
)

# STYLING COERENTE CON IL BRAND
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

# BARRA LATERALE DI NAVIGAZIONE
with st.sidebar:
    st.markdown("### 📌 Navigazione")
    st.page_link("app.py", label="Generatore Itinerari", icon="🏠")
    st.page_link("pages/1_Storico_Viaggi.py", label="Storico Viaggi", icon="📂")
    st.page_link("pages/2_Profilo.py", label="Il Mio Profilo", icon="👤")
    st.divider()
    st.caption("ATLAS v2.0 - Profilo Avanzato")

# GESTIONE FILE PROFILO
profile_path = os.path.join("data", "taste_graph.json")

def load_profile():
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "user_profile": {
            "name": "Elia",
            "travel_style": {"pace": "Equilibrato"},
            "budget_tier": "Medio-Alto",
            "dietary_restrictions": "Nessuna",
            "preferred_mobility": "A piedi / Mezzi pubblici"
        }
    }

data = load_profile()
user_p = data.get("user_profile", {})

st.title("👤 Profilo Utente e Preferenze Atlas")
st.markdown("Modifica i parametri stabili che guidano l'intelligenza artificiale nella creazione dei tuoi itinerari personalizzati.")

with st.container(border=True):
    st.subheader("⚙️ Impostazioni Generali & Stile")
    
    new_name = st.text_input("Nome Utente:", value=user_p.get("name", "Elia"))
    
    current_pace = user_p.get("travel_style", {}).get("pace", "Equilibrato")
    paces_list = ["Rilassato (Poche tappe, pause frequenti)", "Equilibrato (Mix ideale tra visite e relax)", "Intenso (Esplorazione dinamica a pieno ritmo)"]
    pace_idx = 1 if "Equilibrato" in current_pace else (0 if "Rilassato" in current_pace else 2)
    new_pace = st.selectbox("Ritmo di viaggio preferito:", paces_list, index=pace_idx)
    
    current_budget = user_p.get("budget_tier", "Medio-Alto")
    budgets_list = ["Economico / Smart", "Medio", "Medio-Alto", "Lusso / Premium"]
    budget_idx = budgets_list.index(current_budget) if current_budget in budgets_list else 2
    new_budget = st.selectbox("Fascia di Budget abituale:", budgets_list, index=budget_idx)

    st.markdown("---")
    st.subheader("🥗 Preferenze di Mobilità & Alimentari (Fisse)")
    
    current_diet = user_p.get("dietary_restrictions", "Nessuna")
    diet_options = ["Nessuna", "Vegetariano", "Vegano", "Celiaco / Senza Glutine", "Senza Lattosio", "Halal"]
    diet_idx = diet_options.index(current_diet) if current_diet in diet_options else 0
    new_diet = st.selectbox("Restrizioni alimentari fisse:", diet_options, index=diet_idx)

    current_mobility = user_p.get("preferred_mobility", "A piedi / Mezzi pubblici")
    mobility_options = ["A piedi / Mezzi pubblici", "Taxi / Uber / NCC prioritario", "Auto a noleggio / Guida autonoma", "Bicicletta / Mobilità dolce"]
    mob_idx = mobility_options.index(current_mobility) if current_mobility in mobility_options else 0
    new_mobility = st.selectbox("Modalità di spostamento preferita:", mobility_options, index=mob_idx)

    st.markdown("---")
    
    if st.button("💾 Salva Modifiche Profilo", type="primary"):
        data["user_profile"]["name"] = new_name
        if "travel_style" not in data["user_profile"]:
            data["user_profile"]["travel_style"] = {}
        data["user_profile"]["travel_style"]["pace"] = new_pace
        data["user_profile"]["budget_tier"] = new_budget
        data["user_profile"]["dietary_restrictions"] = new_diet
        data["user_profile"]["preferred_mobility"] = new_mobility
        
        os.makedirs("data", exist_ok=True)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        st.success("Profilo aggiornato e salvato con successo nel sistema locale!")

st.divider()

# SEZIONE STORICO FEEDBACK / ESCLUSIONI APPORTATE
st.subheader("🛡️ Esclusioni e Storico Adattamenti Live")
history = user_p.get("dynamic_feedback_history", [])

if history:
    st.caption("Questi elementi sono stati esclusi o modificati direttamente dalle schede di viaggio:")
    for idx, item in enumerate(history):
        st.markdown(f"- **{item.get('action', 'Azione')}**: `{item.get('item', 'N/D')}` — *{item.get('reason', '')}*")
        
    if st.button("🗑️ Pulisci Storico Esclusioni"):
        data["user_profile"]["dynamic_feedback_history"] = []
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.success("Cronologia esclusioni pulita!")
        st.rerun()
else:
    st.info("Nessuna esclusione attiva registrata. Il sistema è pronto per apprendere dai tuoi feedback di viaggio.")