# reporting/utils.py
from datetime import datetime
import unicodedata

def slugify(text: str) -> str:
    """Nettoie une chaîne pour l'utiliser dans un nom de fichier."""
    if not text:
        return "unknown"
    
    # Normalisation Unicode et suppression des accents
    text = unicodedata.normalize('NFKD', str(text).lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Remplacement des caractères spéciaux
    return (text
            .replace(' ', '_')
            .replace("'", "")
            .replace('"', "")
            .replace('/', '_')
            .replace('\\', '_')
            .replace(':', '_')
            .replace('*', '_')
            .replace('?', '_')
            .replace('|', '_')
            .replace('<', '_')
            .replace('>', '_'))

def safe_date(date_str):
    """Convertit une date ISO en format YYYY-MM-DD, gère les erreurs."""
    if not date_str:
        return "unknown_date"
    
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", ""))
        return dt.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return "unknown_date"

def build_report_filename(patient: dict, extension: str = "json") -> str:
    """Construit le nom de fichier à partir des données patient."""
    nom = slugify(patient.get("nom", "unknown"))
    prenom = slugify(patient.get("prenom", "unknown"))
    form_type = patient.get("form_name") or patient.get("form_type") or "unknown"
    date = patient.get("submitted_at") or patient.get("evaluation_date") or "unknown_date"
    date_clean = safe_date(date)
    
    return f"{nom}_{prenom}_{form_type}_{date_clean}.{extension}"

# reporting/utils.py

def get_score_label(z_score):
    """
    Retourne le libellé en fonction du z-score.
    
    z < -2     → "Beaucoup moins que les autres"
    -2 < z < -1 → "Moins que les autres"
    -1 < z < 1  → "Comme la plupart des autres"
    1 < z < 2   → "Plus que les autres"
    z > 2       → "Beaucoup plus que les autres"
    """
    if z_score is None:
        return "Non évalué"
    if z_score < -2:
        return "Beaucoup moins que les autres"
    elif z_score < -1:
        return "Moins que les autres"
    elif z_score < 1:
        return "Comme la plupart des autres"
    elif z_score < 2:
        return "Plus que les autres"
    else:
        return "Beaucoup plus que les autres"

def get_score_color(z_score):
    """Retourne la couleur pour le graphique."""
    if z_score is None:
        return "#95a5a6"
    if z_score < -2:
        return "#e74c3c"      # Rouge - Très atypique
    elif z_score < -1:
        return "#f39c12"      # Orange - Atypique
    elif z_score < 1:
        return "#2ecc71"      # Vert - Norme
    elif z_score < 2:
        return "#f39c12"      # Orange - Atypique
    else:
        return "#e74c3c"      # Rouge - Très atypique
    
    