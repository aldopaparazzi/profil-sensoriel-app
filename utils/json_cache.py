# utils/json_cache.py

import json
from functools import lru_cache

@lru_cache(maxsize=32)
def load_json_cached(path: str) -> dict:
    """
    Charge un fichier JSON avec cache.
    - Si déjà chargé → retourne la version en mémoire
    - Sinon → lit le fichier et le garde en cache
    
    Args:
        path: chemin vers le fichier JSON (ex: "data/reference/reference.json")
    
    Returns:
        dict: contenu du JSON
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def clear_cache():
    """Vide le cache des fichiers JSON (utile pour les tests)"""
    load_json_cached.cache_clear()

def get_cache_info():
    """Retourne des statistiques sur le cache"""
    return load_json_cached.cache_info()