# reporting/chart_style.py
"""Configuration visuelle et de présentation des graphiques."""

FONT_FAMILY = ["IBM Plex Sans", "DejaVu Sans"]

BAR_COLOR_THRESHOLDS = [
    (0.5, "#5fae61"),
    (1.0, "#32a836"),
    (1.5, "#d6b43c"),
    (2.0, "#d88932"),
    (2.5, "#c94a3f"),
    (float("inf"), "#a32d2d"),
]

TEXT_COLOR = "#1a1916"
MUTED_COLOR = "#6b6860"
BORDER_COLOR = "#e7e5e4"

SECTIONS = [
    ("quadrants", "Quadrants sensoriels"),
    ("domains", "Domaines sensoriels"),
    ("composantes_scolaires", "Composantes scolaires"),
]

QUADRANT_LABELS = {
    "recherche": "Recherche",
    "evitement": "Évitement",
    "sensibilite": "Sensibilité",
    "enregistrement": "Enregistrement",
}

QUADRANT_ORDER = [
    "recherche",
    "evitement",
    "sensibilite",
    "enregistrement",
]

DOMAIN_LABELS = {
    "auditif": "Auditif",
    "visuel": "Visuel",
    "tactile": "Tactile",
    "mouvement": "Mouvement",
    "position_corps": "Position du corps",
    "sensoriel_oral": "Sensoriel oral",
    "comportemental": "Comportemental",
    "conduites": "Conduites",
    "socio_emotionnel": "Socio-émotionnel",
    "attentionnel": "Attentionnel",
    "traitement_global": "Traitement global",
}

COMPOSANTE_LABELS = {
    "1": "Composante scolaire 1",
    "2": "Composante scolaire 2",
    "3": "Composante scolaire 3",
    "4": "Composante scolaire 4",
}

LABEL_MAPS = {
    "quadrants": QUADRANT_LABELS,
    "domains": DOMAIN_LABELS,
    "composantes_scolaires": COMPOSANTE_LABELS,
}

SVG_WIDTH = 1000

LEFT_MARGIN = 260
RIGHT_MARGIN = 90
TOP_MARGIN = 4
BOTTOM_MARGIN = 4

DISPLAY_WIDTH_CM = 16.0
MAX_Z = 3.0
