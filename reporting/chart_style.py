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

# Dimensions du graphique dans l'ODT
ODT_CHART_WIDTH_CM = 8.0
MIN_CHART_HEIGHT_CM = 0.0

CHART_CELL_HEIGHT_CM = 1.0  # Espacement de la cellule ODT (remplace ODT_CHART_HEIGHT_CM + ODT_CHART_ROW_PADDING_CM
TABLE_BORDER_WIDTH_PT = 0.0  # Bordure du tableau ODT (0 = pas de bordure)


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

# Colonnes du tableau ODT (Sujet B2)
TABLE_TOTAL_WIDTH_MIN_CM = 8.0  # 3.5 (label) + 1.0 (score) + 3.5 (graphique)
TABLE_TOTAL_WIDTH_MAX_CM = 19.0
TABLE_TOTAL_WIDTH_DEFAULT_CM = 17.0

LABEL_COL_MIN_CM = 3.5
SCORE_COL_MIN_CM = 1.2
GRAPH_COL_MIN_CM = 3.5

GRAPH_MARGIN_PCT = 0.10  # marge gauche+droite dans la cellule graphique

# legacy — compatibilité temporaire avec ui_settings.py
DEFAULT_CHART_SETTINGS = {
    # Réglages encore utilisés par le moteur SVG
    "show_values": True,
    "show_marker": True,
    "show_zero_line": True,
    # Réglages legacy — seront supprimés avec les contrôles UI correspondants
    "label_font_size": 18,
    "value_font_size": VALUE_FONT_SIZE,
    "bar_height": BAR_HEIGHT,
    "fill_height": FILL_HEIGHT,
    "zero_line_height": ZERO_LINE_HEIGHT,
    "marker_size": MARKER_SIZE,
    "chart_cell_height_cm": 1.0,
    "border_width_pt": TABLE_BORDER_WIDTH_PT,
    "table_total_width_cm": TABLE_TOTAL_WIDTH_DEFAULT_CM,
    "label_col_width_cm": 4.0,
    "score_col_width_cm": 1.5,
    "show_strategy_group_names": True,
}
