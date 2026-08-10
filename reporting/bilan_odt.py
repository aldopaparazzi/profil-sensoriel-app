# reporting/bilan_odt.py
"""
Génère le bilan ODT prérempli, avec un rendu inspiré de template.html :
- identité patient
- quadrants / domaines / composantes scolaires en barres colorées divergentes
- stratégies de compensation validées par le praticien (via popup)
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from odf.draw import Frame, Image
from odf.opendocument import load
from odf.text import H, List, ListItem, P

from reporting.utils import get_score_color
from storage.init import load_runtime
from storage.paths import paths
from utils.logger import get_logger

logger = get_logger(__name__)

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

FONT_FAMILY = ["IBM Plex Sans", "DejaVu Sans"]  # repli si IBM Plex absente


def _bar_color(z: float | None) -> str:
    """Couleur selon |z|, mêmes seuils que CONFIG.bar.colors du template.html."""
    if z is None:
        return MUTED_COLOR
    abs_z = abs(z)
    for limit, color in BAR_COLOR_THRESHOLDS:
        if abs_z < limit:
            return color
    return BAR_COLOR_THRESHOLDS[-1][1]


# Ordre et titres identiques à template.html
SECTIONS = [
    ("quadrants", "Quadrants sensoriels"),
    ("domains", "Domaines sensoriels"),
    ("composantes_scolaires", "Composantes scolaires"),
]

# Labels lisibles (repris de CONFIG.quadrants.label / CONFIG.domains.label du HTML)
QUADRANT_LABELS = {
    "recherche": "Recherche",
    "evitement": "Évitement",
    "sensibilite": "Sensibilité",
    "enregistrement": "Enregistrement",
}
QUADRANT_ORDER = ["recherche", "evitement", "sensibilite", "enregistrement"]

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


def load_strategies() -> dict:
    with paths.strategies_path.open(encoding="utf-8") as f:
        return json.load(f)


def _get_label(section: str, key: str) -> str:
    return LABEL_MAPS.get(section, {}).get(key, key)


def _ordered_keys(section: str, data: dict) -> list[str]:
    """Respecte l'ordre fixe des quadrants (comme le HTML) ; sinon ordre naturel."""
    if section == "quadrants":
        return [k for k in QUADRANT_ORDER if k in data]
    return list(data.keys())

    # =========================================================
    # 1. GRAPHES (barres divergentes colorées, style template.html)
    # =========================================================
    """
    Retourne (image_png_bytes, height_cm).
    Style calqué sur template.html : police IBM Plex, couleurs identiques,
    palier de couleur à 5 niveaux, sans fond.
    """


def generate_chart(
    section: str,
    scores_for_type: dict,
    chart_config: dict | None = None,
) -> tuple[bytes, float]:

    if chart_config is None:
        runtime = load_runtime()
        chart_config = runtime.get("ui", {}).get("charts", {})

    show_values = chart_config.get("show_values", True)
    show_marker = chart_config.get("show_marker", True)
    show_zero_line = chart_config.get("show_zero_line", True)
    show_x_axis = chart_config.get("show_x_axis", False)

    bar_height = chart_config.get("bar_height", 0.35)
    row_height = chart_config.get("row_height", 0.42)
    dpi = chart_config.get("dpi", 150)

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = FONT_FAMILY

    keys = _ordered_keys(section, scores_for_type)
    labels, values, colors = [], [], []

    for key in keys:
        v = scores_for_type[key]
        z = v.get("z")
        labels.append(_get_label(section, key))
        values.append(z if z is not None else 0)
        colors.append(_bar_color(z))

    n = max(len(labels), 1)
    fig_height_in = row_height * n + 0.8
    fig, ax = plt.subplots(figsize=(6.5, fig_height_in))
    fig.patch.set_alpha(0)  # pas de fond
    ax.set_facecolor("none")

    y_pos = range(len(labels))

    # Bordures façon --border du HTML (garder seulement le bas, léger)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BORDER_COLOR)

    # Barres plus fines
    ax.barh(y_pos, values, color=colors, height=bar_height, zorder=3)

    # Ligne centrale conservée
    if show_zero_line:
        ax.axvline(
            0,
            color=TEXT_COLOR,
            linewidth=1,
            alpha=0.25,
            zorder=2,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_COLOR, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(-3, 3)

    # Suppression complète de l'axe X
    if show_x_axis:
        ax.set_xlabel("Écart-type (DS)", color=MUTED_COLOR, fontsize=8)
        ax.tick_params(axis="x", labelsize=8, colors=MUTED_COLOR)
    else:
        ax.set_xlabel("")
        ax.set_xticks([])
        ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
        ax.spines["bottom"].set_visible(False)

    ax.tick_params(axis="y", length=0)

    # Bordures
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    # Étiquette DS en bout de barre, colorée comme la barre
    # Valeur + marqueur rond
    for i, (z, color) in enumerate(zip(values, colors)):
        offset = 0.08 if z >= 0 else -0.08
        ha = "left" if z >= 0 else "right"

        # Marqueur rond au bout de la barre
        if show_marker:
            ax.scatter(
                z,
                i,
                s=45,
                color=color,
                edgecolor="white",
                linewidth=1,
                zorder=4,
            )

        # Valeur juste après le rond
        if show_values:
            ax.text(
                z + offset,
                i,
                f"{z:+.2f}",
                va="center",
                ha=ha,
                fontsize=8,
                color=color,
                fontweight="medium",
                zorder=5,
            )

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True)
    plt.close(fig)
    buf.seek(0)

    height_cm = round(fig_height_in * 2.54, 1)
    return buf.read(), height_cm


def generate_all_charts(scores: dict) -> dict[str, tuple[bytes, float]]:
    """{section_key: (image_png_bytes, height_cm)}, dans l'ordre de SECTIONS."""
    charts = {}
    for section_key, _title in SECTIONS:
        data = scores.get(section_key)
        if data:
            charts[section_key] = generate_chart(section_key, data)
    return charts


# =========================================================
# 2. CANDIDATS STRATEGIES (pour alimenter la popup)
# =========================================================
def select_strategy_candidates(scores: dict, threshold: float) -> dict:
    """
    Filtre à deux niveaux :
    - le quadrant doit dépasser le seuil (détermine plus/moins)
    - chaque domaine d'items n'est inclus que si SON PROPRE z-score dépasse aussi le seuil
      Exception : "general" n'a pas de score dédié, inclus dès que le quadrant dépasse le seuil.
    """
    strategies = load_strategies()
    quadrants = scores.get("quadrants", {})
    domains = scores.get("domains", {})
    candidates = {}

    for quadrant, values in quadrants.items():
        z = values.get("z")
        if z is None or abs(z) < threshold:
            continue

        direction = "plus" if z > 0 else "moins"
        block = strategies.get(quadrant, {}).get(direction)
        if not block:
            continue

        filtered_items = {}
        for domaine, items in block.get("items", {}).items():
            if domaine == "general":
                filtered_items[domaine] = items
                continue

            domain_z = domains.get(domaine, {}).get("z")
            if domain_z is not None and abs(domain_z) >= threshold:
                filtered_items[domaine] = items

        if filtered_items:
            candidates[quadrant] = {
                "z": z,
                "direction": direction,
                "objectif": block.get("objectif"),
                "items": filtered_items,
            }

    return candidates


# =========================================================
# 3. GENERATION ODT
# =========================================================
def build_bilan_odt(
    patient: dict,
    scores: dict,
    output_path: str | Path,
    selected_strategies: dict,
) -> Path:
    """
    selected_strategies: items déjà validés par le praticien
        {quadrant: {domaine: [item, ...]}}
    """
    doc = load(str(paths.odt_template))

    # --- Identité (équivalent du <header> du HTML) ---
    fullname = f"{patient.get('prenom', '')} {patient.get('nom', '')}".strip()
    doc.text.addElement(H(outlinelevel=1, text=fullname or "Profil Sensoriel — Bilan"))
    doc.text.addElement(P(text=f"Évaluation du {patient.get('evaluation_date', '—')}"))
    doc.text.addElement(P(text=f"Né(e) le {patient.get('birth_date', '—')}"))
    age_label = (
        f"tranche {patient['age_group']}"
        if patient.get("age_group")
        else f"{patient.get('age', '—')} ans"
    )
    doc.text.addElement(P(text=f"Âge : {age_label}"))
    if patient.get("niveau"):
        doc.text.addElement(P(text=f"Niveau : {patient['niveau']}"))

    # --- Sections scores (quadrants, domains, composantes_scolaires) ---
    charts = generate_all_charts(scores)
    for section_key, title in SECTIONS:
        chart = charts.get(section_key)
        if not chart:
            continue

        png_bytes, height_cm = chart

        doc.text.addElement(H(outlinelevel=1, text=title))
        href = doc.addPictureFromString(png_bytes, "image/png")
        frame = Frame(width="16cm", height=f"{height_cm}cm", anchortype="paragraph")
        frame.addElement(Image(href=href))
        image_paragraph = P()
        image_paragraph.addElement(frame)
        doc.text.addElement(image_paragraph)

    # --- Stratégies validées (en fin, comme demandé) ---
    doc.text.addElement(H(outlinelevel=1, text="Stratégies de compensation"))

    if not selected_strategies:
        doc.text.addElement(P(text="Aucune stratégie sélectionnée."))
    else:
        for quadrant, domaines in selected_strategies.items():
            label = QUADRANT_LABELS.get(quadrant, quadrant.capitalize())
            doc.text.addElement(H(outlinelevel=2, text=label))
            for domaine, items in domaines.items():
                domaine_label = _get_label("domains", domaine)
                doc.text.addElement(P(text=domaine_label))
                strategy_list = List()
                for item in items:
                    li = ListItem()
                    li.addElement(P(text=item))
                    strategy_list.addElement(li)
                doc.text.addElement(strategy_list)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    logger.info("✓ Bilan ODT prérempli généré : %s", output_path)
    return output_path
