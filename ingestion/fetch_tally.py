from typing import Optional

import requests


class TallyAPIError(Exception):
    def __init__(self, message, status_code=None, error_type=None):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type


def _headers(token: str) -> dict:
    """
    Construit les headers Tally après validation du token.
    """
    token = str(token or "")

    if not token or any(char.isspace() for char in token):
        raise TallyAPIError(
            "Token Tally invalide : il contient des espaces ou retours à la ligne.",
            status_code=401,
            error_type="invalid_token",
        )

    return {"Authorization": f"Bearer {token}"}


def _request_tally(url: str, token: str, params=None):
    """
    Effectue une requête Tally et transforme les erreurs
    réseau / HTTP en TallyAPIError explicite.
    """
    headers = _headers(token)

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )
    except requests.ConnectionError as e:
        raise TallyAPIError(
            "Impossible de contacter Tally : vérifiez votre connexion Internet.",
            error_type="network",
        ) from e
    except requests.Timeout as e:
        raise TallyAPIError(
            "Le serveur Tally n'a pas répondu dans le délai imparti.",
            error_type="network",
        ) from e
    except requests.RequestException as e:
        raise TallyAPIError(
            f"Erreur de connexion à Tally : {e}",
            error_type="network",
        ) from e

    if response.status_code == 401:
        raise TallyAPIError(
            "Token Tally invalide ou expiré.",
            status_code=401,
            error_type="auth",
        )

    if 500 <= response.status_code <= 599:
        raise TallyAPIError(
            f"Erreur serveur Tally ({response.status_code}). "
            "Le service Tally rencontre probablement un problème.",
            status_code=response.status_code,
            error_type="server",
        )

    if response.status_code != 200:
        raise TallyAPIError(
            f"Erreur API Tally : {response.status_code} - {response.text}",
            status_code=response.status_code,
            error_type="api",
        )

    return response.json()


def fetch_tally(form_id: str, token: str) -> dict:
    """Récupère toutes les soumissions."""
    url = f"https://api.tally.so/forms/{form_id}/submissions"
    return _request_tally(url, token)


def fetch_new_submissions(
    form_id: str,
    token: str,
    after_id: Optional[str] = None,
) -> dict:
    """
    Récupère uniquement les nouvelles soumissions complètes.
    """
    url = f"https://api.tally.so/forms/{form_id}/submissions"

    params = {
        "filter": "completed",
        "limit": 500,
    }

    if after_id:
        params["afterId"] = after_id

    return _request_tally(url, token, params)


def fetch_all_submissions_with_pagination(
    form_id: str,
    token: str,
) -> dict[str, list[dict]]:
    """
    Récupère toutes les soumissions.
    """
    url = f"https://api.tally.so/forms/{form_id}/submissions"

    all_submissions = []
    page = 1
    limit = 500

    while True:
        params = {
            "filter": "completed",
            "limit": limit,
            "page": page,
        }

        data = _request_tally(url, token, params)

        submissions = data.get("submissions", [])
        all_submissions.extend(submissions)

        if not data.get("hasNextPage"):
            break

        page += 1

    return {"submissions": all_submissions}


def check_token_valid(token: str) -> bool:
    """
    Vérifie si un token Tally est valide.
    """
    try:
        _request_tally(
            "https://api.tally.so/forms",
            token,
        )
        return True
    except TallyAPIError:
        return False
