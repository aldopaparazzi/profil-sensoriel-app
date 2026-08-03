# utils/privacy.py
"""
Anonymisation légère pour les logs.

Règle :
- logger.info/warning/error -> JAMAIS de nom complet, utiliser anonymize_patient()
- logger.debug -> peut contenir le chemin complet (donc le nom), car invisible
  sauf si "debug: true" est activé (voir utils/logger.py::configure_logging)
"""


def anonymize_patient(patient: dict) -> str:
    """
    Retourne des initiales pour identifier un patient dans les logs,
    sans exposer son nom complet.

    Accepte les deux conventions de clés rencontrées dans le projet
    (nom/prenom en minuscule après mapping, Nom/Prenom bruts avant mapping).

    Ex: {"nom": "Dupont", "prenom": "Jean"} -> "J.D."
    """
    prenom = (patient.get("prenom") or patient.get("Prenom") or "").strip()
    nom = (patient.get("nom") or patient.get("Nom") or "").strip()

    def initial(value: str) -> str:
        return f"{value[0].upper()}." if value else "?."

    return f"{initial(prenom)}{initial(nom)}"
