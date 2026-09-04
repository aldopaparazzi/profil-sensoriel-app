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


# Dimensions générales du SVG
SVG_WIDTH = 1000

LEFT_MARGIN = 40
RIGHT_MARGIN = 90
TOP_MARGIN = 4
BOTTOM_MARGIN = 4

# Dimensions du graphique dans l'ODT
ODT_CHART_WIDTH_CM = 10.0
ODT_CHART_HEIGHT_CM = 0.7
MIN_CHART_HEIGHT_CM = 0.7

# Échelle des scores
MAX_Z = 3.0

# Géométrie interne du graphique
BAR_HEIGHT = 12
FILL_HEIGHT = 10
ZERO_LINE_HEIGHT = 21
MARKER_SIZE = 14

# Typographie interne du graphique
VALUE_FONT_SIZE = 18
VALUE_OFFSET = 18

# legacy
DEFAULT_CHART_SETTINGS = {
    "show_values": True,
    "show_marker": True,
    "show_zero_line": True,
}
ODT_CHART_ROW_PADDING_CM = 0.15