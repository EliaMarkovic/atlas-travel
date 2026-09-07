import os

SAVED_TRIPS_DIR = "saved_trips"

def get_saved_trips():
    """
    Restituisce la lista di tutti gli itinerari salvati nella cartella saved_trips,
    ordinati dai più recenti ai meno recenti.
    """
    if not os.path.exists(SAVED_TRIPS_DIR):
        return []
    
    files = [f for f in os.listdir(SAVED_TRIPS_DIR) if f.endswith(".md")]
    files.sort(reverse=True)
    
    trips = []
    for f in files:
        trips.append({
            "filename": f,
            "path": os.path.join(SAVED_TRIPS_DIR, f)
        })
    return trips

def load_trip_content(file_path: str) -> str:
    """
    Legge e restituisce il contenuto di un file di itinerario.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Errore durante la lettura del file: {e}"
    return "Errore: File dell'itinerario non trovato."

def delete_trip_file(file_path: str) -> bool:
    """
    Elimina definitivamente un file di itinerario salvato.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Errore durante l'eliminazione del file: {e}")
    return False