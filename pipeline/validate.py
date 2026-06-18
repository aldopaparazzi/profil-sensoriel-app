# pipeline/validate.py

# Responsabilité :
#   vérifier
#   nettoyer
#   garantir la cohérence minimale

#from utils.logger import log

def filter_empty_submissions(raw: dict, context: dict) -> dict:
    if not raw:
        raise ValueError("Dataset vide")
    if "submissions" not in raw:
        raise ValueError("Structure invalide: missing submissions")
    cleaned = {
        "submissions": []
    }
    for sub in raw["submissions"]:
        if not sub.get("responses"):
                print("⚠️ submission sans responses :", sub.get("id"))
                #continue
        cleaned["submissions"].append(sub)
    return cleaned

