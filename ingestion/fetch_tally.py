#ingestion\fetch_tally.py
import requests
import pandas as pd


TALLY_URL = "https://api.tally.so/forms/{form_id}/submissions"


class TallyAPIError(Exception):
    pass


def extract_value(a):
    if isinstance(a, dict):
        return a.get("value", a.get("answer"))
    return a


def fetch_tally(form_id: str, token: str) -> pd.DataFrame:

    url = TALLY_URL.format(form_id=form_id)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code == 401:
            raise TallyAPIError("Token Tally invalide ou expiré (401)")

        if not r.ok:
            raise TallyAPIError(
                f"Erreur API Tally ({r.status_code}) : {r.text[:200]}"
            )

        data = r.json()

    except requests.exceptions.RequestException as e:
        raise TallyAPIError(f"Erreur réseau Tally : {str(e)}")

    submissions = data.get("submissions", [])

    rows = []

    for sub in submissions:

        base = {
            "submissionId": sub.get("submissionId"),
            "submittedAt": sub.get("submittedAt") or sub.get("createdAt")
        }

        answers = sub.get("answers", {})

        for q, a in answers.items():
            rows.append({
                **base,
                "question": q,
                "response": extract_value(a)
            })

    return pd.DataFrame(rows)