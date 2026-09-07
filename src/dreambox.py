import os
import json

INBOX_DIR = "inbox_drop"
DREAM_FILE = os.path.join("data", "dream_box.json")

def get_inbox_items():
    """Legge i file di testo o appunti grezzi lasciati nella cartella inbox_drop."""
    items = []
    if not os.path.exists(INBOX_DIR):
        os.makedirs(INBOX_DIR)
        
    for filename in os.listdir(INBOX_DIR):
        file_path = os.path.join(INBOX_DIR, filename)
        if os.path.isfile(file_path) and filename.endswith((".txt", ".md")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    items.append({"title": filename, "content": content})
            except Exception as e:
                print(f"Errore nella lettura del file {filename}: {e}")
    return items

def get_dream_notes():
    """Legge tutte le note salvate in dream_box.json."""
    if not os.path.exists(DREAM_FILE):
        return []
    try:
        with open(DREAM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_dream_note(note_text: str):
    """Permette di aggiungere un'ispirazione direttamente dall'interfaccia."""
    dreams = get_dream_notes()
    dreams.append({"note": note_text})
    
    os.makedirs(os.path.dirname(DREAM_FILE), exist_ok=True)
    with open(DREAM_FILE, "w", encoding="utf-8") as f:
        json.dump(dreams, f, indent=4, ensure_ascii=False)

def delete_dream_note(index: int):
    """Elimina una nota specifica dalla Dream Box in base al suo indice."""
    dreams = get_dream_notes()
    if 0 <= index < len(dreams):
        dreams.pop(index)
        with open(DREAM_FILE, "w", encoding="utf-8") as f:
            json.dump(dreams, f, indent=4, ensure_ascii=False)