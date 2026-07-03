#ingestion\fetch_tally.py

# Entrée :
#   form_id
#   token
# 
# Sortie :
#   liste de soumissions Tally
# 
# Garanties :
#   - aucune donnée supprimée
#   - aucune donnée interprétée
#   - aucune donnée convertie
#   - structure JSON conservée
#
# Actions :
#   1. appel API
#   2. retourne raw pour clean.py - dict (JSON brut Tally)


import requests
from typing import Optional #, Dict, List

class TallyAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

def fetch_tally(form_id: str, token: str) -> dict:
    """Récupère TOUTES les soumissions (fallback)."""
    url = f"https://api.tally.so/forms/{form_id}/submissions"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as e:
        raise TallyAPIError(f"Erreur réseau : {e}")
    
    if response.status_code == 401:
        raise TallyAPIError("Token invalide", status_code=401)
    
    if response.status_code != 200:
        raise TallyAPIError(
            f"Erreur API Tally: {response.status_code} - {response.text}",
            status_code=response.status_code
        )
    
    return response.json()

def fetch_new_submissions(form_id: str, token: str, after_id: Optional[str] = None) -> dict:
    """
    Récupère uniquement les nouvelles soumissions complètes.
    
    Args:
        form_id: ID du formulaire Tally
        token: Token d'authentification
        after_id: ID de la dernière soumission traitée (optionnel)
    
    Returns:
        dict: {"submissions": [...]}
    """
    url = f"https://api.tally.so/forms/{form_id}/submissions"
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {
        "filter": "completed",
        "limit": 500  # Maximum par page
    }
    
    if after_id:
        params["afterId"] = after_id
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        raise TallyAPIError(f"Erreur réseau : {e}")
    
    if response.status_code == 401:
        raise TallyAPIError("Token invalide", status_code=401)
    
    if response.status_code != 200:
        raise TallyAPIError(
            f"Erreur API Tally: {response.status_code} - {response.text}",
            status_code=response.status_code
        )
    
    return response.json()

def fetch_all_submissions_with_pagination(
    form_id: str,
    token: str
) -> dict[str, list[dict]]:
#def fetch_all_submissions_with_pagination(form_id: str, token: str) -> List[dict]:
    """
    Récupère TOUTES les soumissions (toutes pages).
    Utilisé uniquement pour le premier run ou le refresh forcé.
    """
    url = f"https://api.tally.so/forms/{form_id}/submissions"
    headers = {"Authorization": f"Bearer {token}"}
    
    all_submissions = []
    page = 1
    limit = 500
    
    while True:
        params = {
            "filter": "completed",
            "limit": limit,
            "page": page
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        submissions = data.get("submissions", [])
        all_submissions.extend(submissions)
        
        # Vérifier s'il y a une page suivante
        if not data.get("hasNextPage"):
            break
        
        page += 1
    
    return {"submissions": all_submissions}
