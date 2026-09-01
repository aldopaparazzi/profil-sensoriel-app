# reporting/bilan_charts.py

from storage.init import load_runtime
from storage.paths import paths

FONT_FAMILY = ["IBM Plex Sans", "DejaVu Sans"]  # repli si IBM Plex absente

# Palette reprise de template.html (CONFIG.bar.colors)
BAR_COLOR_THRESHOLDS = [
    (0.5, "#5fae61"),  # vert - neutre
    (1.0, "#32a836"),  # vert foncé (greenDark du HTML)
    (1.5, "#d6b43c"),  # jaune
    (2.0, "#d88932"),  # orange clair
    (2.5, "#c94a3f"),  # rouge clair
    (float("inf"), "#a32d2d"),  # rouge foncé
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
TOP_MARGIN = 12
BOTTOM_MARGIN = 12

DISPLAY_WIDTH_CM = 16.0
MAX_Z = 3.0


def _get_chart_config(chart_config: dict | None) -> dict:
    if chart_config is None:
        runtime = load_runtime()
        chart_config = runtime.get("ui", {}).get("charts", {})

    return {
        "show_values": chart_config.get("show_values", True),
        "show_marker": chart_config.get("show_marker", True),
        "show_zero_line": chart_config.get("show_zero_line", True),
        "label_font_size": chart_config.get("label_font_size", 21),
        "value_font_size": chart_config.get("value_font_size", 18),
        "row_height": chart_config.get("row_height", 42),
        "bar_height": chart_config.get("bar_height", 12),
        "fill_height": chart_config.get("fill_height", 10),
        "zero_line_height": chart_config.get("zero_line_height", 21),
        "marker_size": chart_config.get("marker_size", 14),
    }


def _bar_color(z: float | None) -> str:
    """Couleur selon |z|, mêmes seuils que CONFIG.bar.colors du template.html."""
    if z is None:
        return MUTED_COLOR
    abs_z = abs(z)
    for limit, color in BAR_COLOR_THRESHOLDS:
        if abs_z < limit:
            return color
    return BAR_COLOR_THRESHOLDS[-1][1]


def _get_label(section: str, key: str) -> str:
    return LABEL_MAPS.get(section, {}).get(key, key)


def _ordered_keys(section: str, data: dict) -> list[str]:
    """Respecte l'ordre fixe des quadrants ; sinon ordre naturel."""
    if section == "quadrants":
        return [k for k in QUADRANT_ORDER if k in data]

    return list(data.keys())


def generate_item_chart(
    section: str,
    key: str,
    values: dict,
    chart_config: dict | None = None,
) -> tuple[bytes, float]:

    return generate_chart(
        section=section,
        scores_for_type={key: values},
        chart_config=chart_config,
    )


def _build_chart_rows(
    section: str,
    scores_for_type: dict,
) -> list[dict]:
    """Prépare les données nécessaires au rendu de chaque ligne."""
    rows = []

    for key in _ordered_keys(section, scores_for_type):
        values = scores_for_type.get(key, {})
        z = values.get("z")

        numeric_z = float(z) if z is not None else 0.0
        z_clamped = max(-MAX_Z, min(MAX_Z, numeric_z))

        rows.append({
            "key": key,
            "label": _get_label(section, key),
            "z": numeric_z,
            "z_clamped": z_clamped,
            "color": _bar_color(z),
        })

    return rows


def generate_chart(
    section: str,
    scores_for_type: dict,
    chart_config: dict | None = None,
) -> tuple[bytes, float]:
    """
    Génère un graphique SVG reproduisant le style des barres
    présentes dans template.html.

    Le graphique est composé directement en SVG :
        - une ligne/barre de fond grise (.bar-track)
        - une barre colorée (.bar-fill)
        - un trait vertical central (.bar-zero)
        - un point circulaire (.bar-dot)
        - éventuellement la valeur DS à droite/gauche


    Paramètres
    ----------
    section:
        Type de section :
            - "quadrants"
            - "domains"
            - "composantes_scolaires"

    scores_for_type:
        Dictionnaire contenant les scores.

        Exemple :
            {
                "recherche": {"z": 0.72},
                "evitement": {"z": -1.15},
                ...
            }

    chart_config:
        Configuration optionnelle provenant du runtime.

    Retour
    ------
    tuple[bytes, float]
        - SVG sous forme de bytes
        - hauteur recommandée en cm pour LibreOffice
    """
    config = _get_chart_config(
        chart_config
    )  # Récupère la configuration graphique (taille police, hauteur ligne, etc.)

    rows = _build_chart_rows(section, scores_for_type)

    # ---------------------------------------------------------
    # Dimensions SVG
    # ---------------------------------------------------------

    # Zone disponible pour les barres.
    BAR_WIDTH = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

    # Hauteur totale.
    n = max(len(rows), 1)

    svg_height = (
        TOP_MARGIN + n * config["row_height"] + BOTTOM_MARGIN
    )  # Calcul de la hauteur totale du SVG en fonction du nombre de lignes et des marges.

    # ---------------------------------------------------------
    # Construction du SVG
    # ---------------------------------------------------------

    svg = []

    # En-tête XML.
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')

    # Élément SVG principal.
    svg.append(
        f'''
    <svg xmlns="http://www.w3.org/2000/svg"
     width="{SVG_WIDTH}"
     height="{svg_height}"
     viewBox="0 0 {SVG_WIDTH} {svg_height}"
     preserveAspectRatio="xMidYMid meet">

    <!--
        Style global du graphique.

        Les couleurs et polices reprennent celles de template.html.
    -->
    <style>
        .label {{
            font-family: "IBM Plex Sans", "DejaVu Sans", sans-serif;
            font-size: {config["label_font_size"]}px;
            fill: {TEXT_COLOR};
        }}

        .value {{
            font-family: "IBM Plex Mono", "DejaVu Sans Mono", monospace;
            font-size: {config["value_font_size"]}px;
            font-weight: 500;
        }}

        .track {{
            fill: {BORDER_COLOR};
        }}

        .zero {{
            fill: {TEXT_COLOR};
            opacity: 0.25;
        }}
    </style>
    '''
    )

    # ---------------------------------------------------------
    # Dessin des lignes
    # ---------------------------------------------------------

    for index, row in enumerate(rows):
        label = row["label"]
        z = row["z"]
        z_clamped = row["z_clamped"]
        color = row["color"]

        # Position verticale de la ligne.
        y_center = TOP_MARGIN + index * config["row_height"] + config["row_height"] / 2

        # Position du zéro
        x_zero = LEFT_MARGIN + BAR_WIDTH * 0.5

        # Largeur de la barre
        pct_fill = min(
            (abs(z_clamped) / MAX_Z) * 50.0,
            50.0,
        )

        # Conversion du pourcentage en pixels.
        fill_width = BAR_WIDTH * pct_fill / 100.0

        # Position de départ de la barre.
        if z_clamped >= 0:
            fill_x = x_zero
        else:
            fill_x = x_zero - fill_width

        # Position du point final.
        if z_clamped >= 0:
            dot_x = x_zero + fill_width
        else:
            dot_x = x_zero - fill_width

        # -----------------------------------------------------
        # LABEL
        # -----------------------------------------------------

        svg.append(
            f'''
            <!-- Ligne {index + 1} : {label} -->

            <text
                class="label"
                x="{LEFT_MARGIN - 20}"
                y="{y_center + 6:.2f}"
                text-anchor="end">
                {label}
            </text>
            '''
        )

        # -----------------------------------------------------
        # BAR TRACK
        # -----------------------------------------------------
        #
        # Équivalent HTML :
        #
        # .bar-track {{
        #     height: 8px;
        #     background: var(--border);
        #     border-radius: 4px;
        # }}
        #

        track_y = y_center - config["bar_height"] / 2

        svg.append(
            f'''
            <rect
                class="track"
                x="{LEFT_MARGIN}"
                y="{track_y:.2f}"
                width="{BAR_WIDTH}"
                height="{config["bar_height"]:.2f}" 
                rx="{config["bar_height"] / 2:.2f}"
                ry="{config["bar_height"] / 2:.2f}"/>
        '''
        )

        # -----------------------------------------------------
        # BAR FILL
        # -----------------------------------------------------

        if fill_width > 0:
            fill_y = y_center - config["fill_height"] / 2

            svg.append(
                f'''
                <rect
                    x="{fill_x:.2f}"
                    y="{fill_y:.2f}"
                    width="{fill_width:.2f}"
                    height="{config["fill_height"]:.2f}"
                    rx="{config["fill_height"] / 2:.2f}"
                    ry="{config["fill_height"] / 2:.2f}"

                    fill="{color}"/>
                '''
            )

        # -----------------------------------------------------
        # ZERO LINE
        # -----------------------------------------------------

        if config["show_zero_line"]:
            zero_y = y_center - config["zero_line_height"] / 2

            svg.append(
                f'''
                <rect
                    class="zero"
                    x="{x_zero - 0.75:.2f}"
                    y="{zero_y:.2f}"
                    width="1.5"
                    height="{config["zero_line_height"]:.2f}"/>
            '''
            )

        # -----------------------------------------------------
        # POINT
        # -----------------------------------------------------

        if config["show_marker"]:
            # Cercle blanc extérieur.
            marker_radius = config["marker_size"] / 2
            svg.append(
                f'''
                <circle
                    cx="{dot_x:.2f}"
                    cy="{y_center:.2f}"
                    r="{marker_radius:.2f}"
                    fill="white"/>
                '''
            )

            # Cercle coloré.
            inner_radius = max(marker_radius - 2, 1)

            svg.append(
                f'''
                <circle
                    cx="{dot_x:.2f}"
                    cy="{y_center:.2f}"
                    r="{inner_radius:.2f}"
                    fill="{color}"
                    stroke="white"
                    stroke-width="2"/>

                '''
            )

            # Petit contour extérieur très léger.
            # Cela reproduit :
            # box-shadow: 0 0 0 1px rgba(0,0,0,.15)
            # En SVG, on le fait avec un cercle supplémentaire.
            svg.append(
                f'''
                <circle
                    cx="{dot_x:.2f}"
                    cy="{y_center:.2f}"
                    r="{marker_radius:.2f}"
                    fill="none"
                    stroke="#000000"
                    stroke-opacity="0.15"
                    stroke-width="1"/>
                '''
            )

        # -----------------------------------------------------
        # VALEUR DS
        # -----------------------------------------------------
        #
        # Dans template.html, la valeur est affichée à côté
        # du point.
        #

        if config["show_values"]:
            # Formatage identique à fmtDS() :
            #
            # +0.72
            # -1.15
            # +2.00
            #
            value_text = f"{z:+.2f}"

            # Décalage de la valeur par rapport au point.
            value_offset = 18

            if z_clamped >= 0:
                value_x = dot_x + value_offset
                anchor = "start"
            else:
                value_x = dot_x - value_offset
                anchor = "end"

            svg.append(
                f'''
                <text
                    class="value"
                    x="{value_x:.2f}"
                    y="{y_center + 5:.2f}"
                    text-anchor="{anchor}"
                    fill="{color}">
                    {value_text}
                </text>
            '''
            )

    # ---------------------------------------------------------
    # Fermeture du SVG
    # ---------------------------------------------------------

    svg.append("</svg>")

    # Conversion en bytes UTF-8.
    svg_bytes = "".join(svg).encode("utf-8")

    # ---------------------------------------------------------
    # Hauteur pour LibreOffice
    # ---------------------------------------------------------
    #
    # Le calcul reprend l'idée de l'ancien generate_chart().
    #
    # On ajoute une petite marge pour le haut/bas.
    #

    height_cm = DISPLAY_WIDTH_CM * (svg_height / SVG_WIDTH)
    height_cm = round(height_cm, 2)
    height_cm = max(height_cm, 1.5)

    return svg_bytes, height_cm


def generate_all_charts(
    scores: dict,
) -> dict[str, tuple[bytes, float]]:
    """
    Génère tous les graphiques SVG nécessaires au bilan.

    Retourne :

        {
            "quadrants": (svg_bytes, height_cm),
            "domains": (svg_bytes, height_cm),
            "composantes_scolaires": (svg_bytes, height_cm),
        }

    Les sections absentes ou vides ne produisent pas de graphique.
    """

    charts = {}

    for section_key, _title in SECTIONS:
        data = scores.get(section_key)

        if not data:
            continue

        charts[section_key] = generate_chart(
            section_key,
            data,
        )

    return charts
