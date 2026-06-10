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


class TallyAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def fetch_tally(form_id: str, token: str) -> dict:
    """
    Ingestion pure de l'API Tally.

    Règles :
    - aucune transformation
    - aucune sauvegarde
    - aucune logique métier
    """

    url = f"https://api.tally.so/forms/{form_id}/submissions"

    headers = {
        "Authorization": f"Bearer {token}"
    }

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