import requests

# Mappatura rapida delle principali destinazioni/paesi alla relativa valuta
CURRENCY_MAP = {
    "giappone": "JPY", "tokyo": "JPY", "kyoto": "JPY", "osaka": "JPY",
    "usa": "USD", "stati uniti": "USD", "new york": "USD", "miami": "USD", "los angeles": "USD",
    "regno unito": "GBP", "londra": "GBP", "uk": "GBP", "scozia": "GBP",
    "svizzera": "CHF", "zurigo": "CHF", "ginevra": "CHF",
    "brasile": "BRL", "rio de janeiro": "BRL", "san paolo": "BRL",
    "australia": "AUD", "sydney": "AUD",
    "canada": "CAD", "toronto": "CAD",
    "messico": "MXN", "emirati arabi": "AED", "dubai": "AED"
}

def detect_currency(destination: str) -> str:
    """Rileva la valuta principale basandosi sulla destinazione inserita dall'utente."""
    dest_clean = destination.lower().strip()
    for key, val in CURRENCY_MAP.items():
        if key in dest_clean:
            return val
    return "EUR"

def get_exchange_rate(base_currency: str = "EUR", target_currency: str = "USD") -> float:
    """Recupera il tasso di cambio aggiornato tramite Frankfurter API (gratuita e senza API key)."""
    if base_currency == target_currency:
        return 1.0
    try:
        url = f"https://api.frankfurter.app/latest?from={base_currency}&to={target_currency}"
        resp = requests.get(url, timeout=3).json()
        return resp.get("rates", {}).get(target_currency, 1.0)
    except Exception as e:
        print(f"Errore recupero tasso di cambio: {e}")
        return 1.0