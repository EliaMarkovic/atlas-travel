import os
import json
import time
import requests
import urllib.parse
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def get_destination_weather(destination: str):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(destination)}&count=1&language=it&format=json"
        geo_resp = requests.get(geo_url, timeout=3).json()
        if not geo_resp.get("results"):
            return None
        
        lat = geo_resp["results"][0]["latitude"]
        lon = geo_resp["results"][0]["longitude"]
        
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto"
        w_resp = requests.get(weather_url, timeout=3).json()
        
        return {
            "latitude": lat,
            "longitude": lon,
            "daily": w_resp.get("daily", {})
        }
    except Exception as e:
        print(f"Info Meteo non disponibile (timeout/rete): {e}")
        return None

def build_google_flights_url(origin: str, destination: str, start_date: str, end_date: str) -> str:
    query = f"flights from {origin} to {destination} from {start_date} to {end_date}"
    encoded_q = urllib.parse.quote(query)
    return f"https://www.google.com/travel/flights?q={encoded_q}&curr=EUR"

def get_travel_concierge_response(
    destination_prompt: str, 
    start_date: str = "", 
    arrival_time: str = "", 
    end_date: str = "", 
    departure_time: str = "", 
    origin_city: str = "",
    transit_mode: str = "Chiedi ad ATLAS rotta e tratte consigliate",
    arrival_hub: str = "", 
    has_lodging: str = "Sì",
    lodging_address: str = "",
    meal_style: str = "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)",
    travel_context: str = "", 
    num_adults: int = 1,
    num_children: int = 0,
    children_ages: str = "",
    daily_budget: float = 120.0,
    interests: list = None,
    trip_type: str = "Città Singola / Stanziale",
    transport_mode: str = "Mezzi Pubblici / A piedi",
    live_adaptation_prompt: str = ""
) -> str:
    if not api_key:
        return "Errore: Chiave API di Google non trovata nelle variabili d'ambiente!"
    
    if interests is None:
        interests = []
    
    client = genai.Client(api_key=api_key)
    
    profile_path = os.path.join("data", "taste_graph.json")
    profile_content = ""
    excluded_items = []
    budget_tier = "Medio"
    dietary_restrictions = "Nessuna"
    
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                prof_data = json.load(f)
                profile_content = json.dumps(prof_data, ensure_ascii=False)
                user_p = prof_data.get("user_profile", {})
                budget_tier = user_p.get("budget_tier", "Medio")
                dietary_restrictions = user_p.get("dietary_restrictions", "Nessuna")
                history = user_p.get("dynamic_feedback_history", [])
                excluded_items = [entry["item"] for entry in history if "item" in entry and entry.get("item")]
        except Exception as e:
            print(f"Errore lettura profilo: {e}")

    excluded_str = ", ".join(excluded_items) if excluded_items else "Nessuna esclusione"
    children_info = f"{num_children} bambini (età: {children_ages})" if num_children > 0 else "Nessun bambino"

    weather_info = get_destination_weather(destination_prompt)
    weather_prompt_snippet = "Meteo non rilevato (pianifica condizioni normali)."
    if weather_info and "daily" in weather_info:
        precip = weather_info["daily"].get("precipitation_probability_max", [])
        max_precip = max(precip) if precip else 0
        if max_precip >= 70:
            weather_prompt_snippet = f"⚠️ ATTENZIONE METEO: Forte rischio pioggia ({max_precip}%). Privilegia attività al chiuso."
        else:
            weather_prompt_snippet = f"Meteo prevalentemente favorevole/stabile (probabilità pioggia max {max_precip}%)."

    lodging_instruction = ""
    if has_lodging == "No":
        lodging_instruction = """
        L'UTENTE NON HA ANCORA PRENOTATO GLI ALLOGGI.
        All'inizio dell'itinerario, PRIMA DEL GIORNO 1, inserisci una sezione intitolata:
        ## PROPOSTA ALLOGGI E PERNOTTAMENTI STRATEGICI
        Per ogni tappa/città del viaggio, proponi 2 opzioni reali e altamente recensite con indirizzo preciso.
        """
    elif lodging_address and lodging_address.strip() and lodging_address.lower() != "centro città":
        lodging_instruction = f"""
        ALLOGGIO SPECIFICATO DALL'UTENTE: `{lodging_address}`.
        - ANCHOR LOGISTICO FISSO: Usa questo indirizzo esatto come PUNTO DI PARTENZA del mattino e PUNTO DI RIENTRO della sera.
        """
    else:
        lodging_instruction = f"Alloggio non specificato: usa come anchor logistico il centro della città di `{destination_prompt}`."

    flights_url = build_google_flights_url(origin_city, destination_prompt, start_date, end_date)
    origin_str = origin_city if origin_city else "Città di origine dell'utente"
    rentalcars_url = f"https://www.rentalcars.com/search-results?locationName={urllib.parse.quote(arrival_hub if arrival_hub else destination_prompt)}"

    transit_instruction = f"""
    ANALISI LOGISTICA TRASPORTI & ARRIVO:
    Partenza da: `{origin_str}` ➔ Destinazione: `{destination_prompt}` (Hub di arrivo: `{arrival_hub if arrival_hub else 'Aeroporto/Stazione'}`).

    PRIMA DEL GIORNO 1, inserisci una sezione intitolata:
    ## LOGISTICA TRASPORTI & ARRIVO
    1. TRATTA PRINCIPALE CON PROPOSTA VOLI/TRENI:
       - ✈️ [Confronta e prenota i Voli su Google Flights]({flights_url})
    2. CONNESSIONE 'LAST MILE' & NOLEGGIO AUTO:
       - Se il noleggio auto è consigliato, calcola un costo REALISTICO (es. min 30-50€ al giorno! Per 20-30 giorni il totale deve riflettere la reale durata del viaggio, indicativamente tra 700€ e 1200€).
       - Inserisci questo link esatto per il noleggio: 🚗 [Verifica preventivo Noleggio Auto a {arrival_hub if arrival_hub else destination_prompt} su Rentalcars]({rentalcars_url})
    """

    system_instruction = f"""
    Sei Atlas, un assistente di viaggio personale e locale, fruito da smartphone e desktop.
    Crea un itinerario iper-personalizzato con link di geolocalizzazione basandoti su:
    - DESTINAZIONE PRINCIPALE / ANCHOR REGIONALE: `{destination_prompt}`
    - TIPOLOGIA VIAGGIO: {trip_type}
    - MEZZO DI TRASPORTO SUL POSTO: {transport_mode}
    - STILE PASTI E CUCINA: `{meal_style}`
    - Profilo utente: {profile_content}
    - FASCIA DI BUDGET GLOBALE: {budget_tier}
    - 💰 BUDGET GIORNALIERO PREVISTO: Massimo {daily_budget} € a persona/giorno.
    - RESTRIZIONI ALIMENTARI FISSE: {dietary_restrictions}
    - COMPOSIZIONE GRUPPO: {num_adults} Adulti e {children_info}
    - METEO RILEVATO: {weather_prompt_snippet}
    - ESCLUSIONI TASSATIVE: [{excluded_str}]
    - Arrivo: {start_date} ore {arrival_time} | Partenza: {end_date} ore {departure_time}
    - Interessi: {', '.join(interests)}

    --- ANCHOR LOGISTICO DINAMICO E VINCOLO GEOGRAFICO (TASSATIVO) ---
    1. ANCHOR TERRITORIALE RIGIDO: Ogni singola proposta DEVE appartenere rigorosamente al territorio di `{destination_prompt}` o al raggio massimo degli spostamenti giornalieri previsti.
    2. DIVIETO ASSOLUTO DI ALLUCINAZIONI GEOGRAFICHE: È severamente vietato citare o inventare nomi di locali situati fuori dalla regione/provincia della tappa (es. se la destinazione è in Friuli, non suggerire MAI locali situati in Toscana, Veneto o altre regioni).
    3. VERIFICA LOCALI REALI: Inserisci solo esercizi commerciali realmente esistenti e aperti al pubblico.

    --- REGOLA TASSATIVA SULLA GESTIONE PASTI PER FAMIGLIE ---
    - Se lo stile pasti è "Ibrido Famiglia (1 pasto fuori + 1 in appartamento con spesa locale)":
      Pianifica UN SOLO pasto principale al ristorante/trattoria al giorno. Per l'altro pasto (solitamente la cena o un pranzo rapido), indica il rientro in appartamento/agriturismo e suggerisci una bottega artigiana, un mercato coperto o un'enoteca locale dove acquistare prodotti tipici per la spesa.
    - Se lo stile pasti è "Autonomo":
      Incentiva l'acquisto di prodotti freschi nei mercati locali per cucinare in alloggio, limitando i locali alle sole pause caffè/merenda.

    --- REGOLA TASSATIVA SUI LINK MAPPE, SITI UFFICIALI E BIGLIETTERIE ---
    Per ogni museo, parco, castello, chiesa o attrazione a pagamento/prenotabile, inserisci OBBLIGATORIAMENTE sia la mappa sia il link di ricerca per il sito ufficiale/biglietteria:
    1. 📍 Mappa: [Nome Luogo, Città](https://www.google.com/maps/search/?api=1&query=Nome+Luogo+Citta)
    2. 🌐 Sito Ufficiale & Biglietti: [Info & Biglietti Nome Luogo](https://www.google.com/search?q=sito+ufficiale+biglietti+Nome+Luogo+Citta)

    --- REGOLA TASSATIVA SULLA DURATA COMPLETA E GENERAZIONE TOKEN ---
    Devi generare OBBLIGATORIAMENTE un blocco separato per **TUTTI I GIORNI** compresi tra la data di arrivo ({start_date}) e la data di partenza ({end_date}), senza mai riassumere o saltare date.
        **INFORMAZIONI ED EVENTI SPECIALI NEL PERIODO:**
    In cima all'itinerario (prima del Giorno 1), inserisci sempre una sezione '## 🌟 EVENTI & OPPORTUNITÀ NEL PERIODO' con un elenco puntato contenente:
    - Giorni ad ingresso gratuito nei musei o attrazioni durante le date del viaggio (es. 'Il primo giovedì del mese il Museo X è gratis').
    - Festival enogastronomici, mercatini, concerti o mostre temporanee attive nelle date selezionate.
    - Particolarità stagionali utili per il viaggiatore.
    
    FORMATTAZIONE TASSATIVA OBBLIGATORIA:
    {transit_instruction}
    
    ## PROPOSTA ALLOGGI E PERNOTTAMENTI STRATEGICI (se richiesta)
    [Opzioni consigliate]

    ## Giorno 1: [Data e Titolo del giorno]
    ### Mattina: [Nome attività]
    [Indicazioni logistiche, descrizione, 📍 Mappa e 🌐 Sito Ufficiale & Biglietti]

    ### Pranzo: [Ristorante Tipico OPPURE Spesa/Pranzo Leggero in Alloggio]
    [Descrizione menù o consiglio bottega locale]

    ### Pomeriggio: [Nome attività]
    [Indicazioni logistiche, descrizione, 📍 Mappa e 🌐 Sito Ufficiale & Biglietti]

    ### Sera: [Ristorante Tipico OPPURE Rientro e Cena in Appartamento]
    [Descrizione cena o spesa prodotti tipici]

    ## Giorno 2: [Data e Titolo del giorno]
    [Ripeti la stessa struttura per TUTTI i giorni compresi nelle date]

    ## STIMA ECONOMICA
    - Voli / Treni Principali A/R: [Importo stimato]
    - Pasti e Spesa Alimentare: [Importo reale basato sullo stile pasti]
    - Ingressi e Attività: [Importo]
    - Trasporti Locali e Noleggio ({transport_mode}): [Importo calcolato su durata totale]
    - Pernottamenti: [Importo stimato]
    - **TOTALE GIORNALIERO MEDIO**: [Min - Max €]
    - **TOTALE COMPLESSIVO STIMATO VIAGGIO**: [Importo Totale Calcolato €]
    """

    user_query = f"Pianifica l'itinerario completo a {destination_prompt} partendo da {origin_str} (Tipo: {trip_type}) per {num_adults} adulti e {children_info} dal {start_date} al {end_date} (Genera tutti i giorni senza omissioni), stile pasti: {meal_style}, budget max {daily_budget}€, interessi: {', '.join(interests)}."
    if live_adaptation_prompt:
        user_query += f"\n\n⚠️ ADATTAMENTO LIVE RICHIESTO: {live_adaptation_prompt}."

    # LISTA MODELLI UFFICIALI STABILI E ATTIVI
    candidate_models = ["gemini-3.5-flash", "gemini-3.6-flash"]
    response = None
    last_error = ""

    for model_name in candidate_models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_query,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3,
                        max_output_tokens=8192
                    ),
                )
                if response and response.text:
                    break
            except Exception as e:
                last_error = str(e)
                # Se è un sovraccarico (503) o quota (429), attende ed esegue un retry
                if any(err_code in last_error for err_code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    time.sleep(2 * (attempt + 1))
                    continue
                else:
                    # Per altri errori passa subito al modello successivo
                    break
                    
        if response and response.text:
            break

    if response is None or not response.text:
        if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
            return (
                "⚠️ **Quota di richieste API temporaneamente raggiunta.**\n\n"
                "Attendi **30 secondi** e riprova a cliccare su **Genera Itinerario**."
            )
        return f"⚠️ **Errore API di Google:** {last_error}"
    
    return response.text
