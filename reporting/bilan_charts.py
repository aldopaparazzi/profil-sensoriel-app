# reporting/bilan_charts.py

from reporting.chart_style import (
    BAR_COLOR_THRESHOLDS,
    BORDER_COLOR,
    BOTTOM_MARGIN,
    COMPOSANTE_LABELS,
    DISPLAY_WIDTH_CM,
    DOMAIN_LABELS,
    FONT_FAMILY,
    LABEL_MAPS,
    LEFT_MARGIN,
    MAX_Z,
    MUTED_COLOR,
    QUADRANT_LABELS,
    QUADRANT_ORDER,
    RIGHT_MARGIN,
    SECTIONS,
    SVG_WIDTH,
    TEXT_COLOR,
    TOP_MARGIN,
)
from storage.init import load_runtime

#from storage.paths import paths


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

def generate_item_charts(
    section: str,
    scores_for_type: dict,
    chart_config: dict | None = None,
) -> list[tuple[str, float, bytes, float]]:

    """     Génère un graphique SVG par item. """

    rows = _build_chart_rows(section, scores_for_type)
    items = []
    for row in rows:
        key = row["key"]
        values = scores_for_type[key]
        svg_bytes, height_cm = generate_item_chart(
            section=section,
            key=key,
            values=values,
            chart_config=chart_config,
        )

        items.append(
            (
                row["label"],
                row["z"],
                svg_bytes,
                height_cm,
            )
        )

    return items

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

def _get_chart_dimensions(rows, config):
    """
    Calcule les dimensions du SVG à partir du nombre de lignes
    et de la configuration graphique.
    """
    bar_width = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    n = max(len(rows), 1)

    svg_height = (
        TOP_MARGIN
        + n * config["row_height"]
        + BOTTOM_MARGIN
    )

    return bar_width, svg_height

def _get_row_geometry(index, row, config, bar_width):
    """
    Calcule les positions et dimensions nécessaires au rendu
    d'une ligne du graphique SVG.
    """
    z_clamped = row["z_clamped"]

    # Position verticale de la ligne.
    y_center = (
        TOP_MARGIN
        + index * config["row_height"]
        + config["row_height"] / 2
    )

    # Position du zéro.
    x_zero = LEFT_MARGIN + bar_width * 0.5

    # Largeur de la barre.
    pct_fill = min(
        (abs(z_clamped) / MAX_Z) * 50.0,
        50.0,
    )

    # Conversion du pourcentage en pixels.
    fill_width = bar_width * pct_fill / 100.0

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

    return y_center, x_zero, fill_width, fill_x, dot_x

def _render_chart_label(svg, index, label, y_center):
    """
    Ajoute le label d'une ligne au SVG.
    """
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

def _render_bar_track(svg, y_center, config, bar_width):
    """
    Ajoute la barre de fond grise d'une ligne au SVG.
    """
    track_y = y_center - config["bar_height"] / 2

    svg.append(
        f'''
        <rect
            class="track"
            x="{LEFT_MARGIN}"
            y="{track_y:.2f}"
            width="{bar_width}"
            height="{config["bar_height"]:.2f}"
            rx="{config["bar_height"] / 2:.2f}"
            ry="{config["bar_height"] / 2:.2f}"/>
        '''
    )

def _render_bar_fill(svg, y_center, fill_width, fill_x, color, config):
    """
    Ajoute la barre colorée correspondant au score.
    """
    if fill_width <= 0:
        return

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

def _render_zero_line(svg, y_center, x_zero, config):
    """
    Ajoute la ligne verticale centrale du graphique.
    """
    if not config["show_zero_line"]:
        return

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

def _render_marker(svg, y_center, dot_x, color, config):
    """
    Ajoute le marqueur circulaire à l'extrémité de la barre.
    """
    if not config["show_marker"]:
        return

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

def _render_value(svg, y_center, dot_x, z, z_clamped, color, config):
    """
    Ajoute la valeur DS à côté du marqueur.
    """
    if not config["show_values"]:
        return

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

def _build_chart_svg_style(config):
    """
    Construit le bloc <style> du graphique SVG.
    """
    return f'''
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

    BAR_WIDTH, svg_height = _get_chart_dimensions(rows, config)

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
     preserveAspectRatio="xMidYMid meet"
     >
    '''
    )

    svg.append(_build_chart_svg_style(config))

    # Dessin des lignes
    for index, row in enumerate(rows):
        label = row["label"]
        z = row["z"]
        z_clamped = row["z_clamped"]
        color = row["color"]

        y_center, x_zero, fill_width, fill_x, dot_x = _get_row_geometry(
            index,
            row,
            config,
            BAR_WIDTH,
        )

        # LABEL
        _render_chart_label(
            svg,
            index,
            label,
            y_center,
        )

        # BAR TRACK
        _render_bar_track(
            svg,
            y_center,
            config,
            BAR_WIDTH,
        )

        # BAR FILL
        _render_bar_fill(
            svg,
            y_center,
            fill_width,
            fill_x,
            color,
            config
        )

        # ZERO LINE
        _render_zero_line(
            svg,
            y_center,
            x_zero,
            config
        )

        # POINT
        _render_marker(
            svg,
            y_center,
            dot_x,
            color,
            config,
        )


        # VALEUR DS
        _render_value(
            svg,
            y_center,
            dot_x,
            z,
            z_clamped,
            color,
            config,
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

def generate_all_item_charts(
    scores: dict,
    chart_config: dict | None = None,
) -> dict[str, list[tuple[str, float, bytes, float]]]:
    """
    Génère un graphique SVG par item pour chaque section.

    Retourne :

        {
            "quadrants": [
                (libellé, score, svg_bytes, height_cm),
                ...
            ],
            "domains": [
                ...
            ],
            "composantes_scolaires": [
                ...
            ],
        }

    Les sections absentes ou vides ne produisent pas d'items.
    """
    charts = {}

    for section_key, _title in SECTIONS:
        data = scores.get(section_key)

        if not data:
            continue

        charts[section_key] = generate_item_charts(
            section=section_key,
            scores_for_type=data,
            chart_config=chart_config,
        )

    return charts


if __name__ == "__main__":
    test_scores = {
        "quadrants": {
            "recherche": {"z": 0.51},
            "evitement": {"z": -1.39},
            "sensibilite": {"z": 0.85},
        },
        "domains": {
            "auditif": {"z": -0.19},
            "visuel": {"z": 0.54},
            "tactile": {"z": 0.68},
        },
        "composantes_scolaires": {
            "1": {"z": 0.72},
        },
    }

    charts = generate_all_item_charts(test_scores)

    for section, items in charts.items():
        print(f"\n{section} : {len(items)} items")

        for label, score, svg_bytes, height_cm in items:
            print(
                f"  {label}: {score:+.2f}"
            )
