import os
import json

PROFILE_PATH = os.path.join("data", "taste_graph.json")

def record_user_feedback(feedback_type: str, item_name: str, reason: str = ""):
    """
    Registra un feedback dinamico (es. 'già visto', 'imprevisto', 'cambio piano')
    e lo salva direttamente nel profilo taste_graph.json dell'utente.
    """
    if not os.path.exists(PROFILE_PATH):
        return False
    
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if "user_profile" in data:
            if "dynamic_feedback_history" not in data["user_profile"]:
                data["user_profile"]["dynamic_feedback_history"] = []
                
            new_entry = {
                "type": feedback_type,
                "item": item_name,
                "reason": reason
            }
            data["user_profile"]["dynamic_feedback_history"].append(new_entry)
            
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
    except Exception as e:
        print(f"Errore durante il salvataggio del feedback: {e}")
    
    return False