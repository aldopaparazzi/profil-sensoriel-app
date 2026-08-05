# reporting/bilan_odt.py
"""
Génère le bilan ODT prérempli :
- identité patient
- graphes à barres colorées (par type de score)
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
from storage.paths import paths
from utils.logger import get_logger

logger = get_logger(__name__)

CHART_TITLES = {
    "domains": "Domaines sensoriels",
    "quadrants": "Quadrants",
    "composantes_scolaires": "Composantes scolaires",
}


def load_strategies() -> dict:
    with paths.strategies_path.open(encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# 1. GRAPHES
# =========================================================
def generate_chart(scores_for_type: dict, title: str) -> bytes:
    labels, values, colors = [], [], []

    for key, v in scores_for_type.items():
        z = v.get("z")
        labels.append(key)
        values.append(z if z is not None else 0)
        colors.append(get_score_color(z))

    fig, ax = plt.subplots(figsize=(6, 0.5 * max(len(labels), 1) + 1))
    ax.barh(labels, values, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Écart-type (z)")
    ax.set_title(title)
    ax.set_xlim(-3, 3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def generate_all_charts(scores: dict) -> dict[str, bytes]:
    return {
        metric_type: generate_chart(scores[metric_type], title)
        for metric_type, title in CHART_TITLES.items()
        if scores.get(metric_type)
    }


# =========================================================
# 2. CANDIDATS (pour alimenter la popup, aucune écriture ODT ici)
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

    # --- Identité ---
    doc.text.addElement(H(outlinelevel=1, text="Profil Sensoriel — Bilan"))
    doc.text.addElement(
        P(text=f"Nom : {patient.get('nom', '')} {patient.get('prenom', '')}")
    )
    doc.text.addElement(P(text=f"Âge : {patient.get('age', '')} ans"))
    doc.text.addElement(P(text=f"Niveau : {patient.get('niveau', '')}"))
    doc.text.addElement(
        P(text=f"Date d'évaluation : {patient.get('evaluation_date', '')}")
    )

    # --- Graphes ---
    doc.text.addElement(H(outlinelevel=1, text="Résultats"))
    for metric_type, png_bytes in generate_all_charts(scores).items():
        href = doc.addPicture(f"{metric_type}.png", "image/png", png_bytes)
        frame = Frame(width="16cm", height="6cm")
        frame.addElement(Image(href=href))
        doc.text.addElement(P())
        doc.text.addElement(frame)

    # --- Stratégies validées ---
    doc.text.addElement(H(outlinelevel=1, text="Stratégies de compensation"))

    if not selected_strategies:
        doc.text.addElement(P(text="Aucune stratégie sélectionnée."))
    else:
        for quadrant, domaines in selected_strategies.items():
            doc.text.addElement(H(outlinelevel=2, text=quadrant.capitalize()))
            for domaine, items in domaines.items():
                doc.text.addElement(P(text=domaine.replace("_", " ").capitalize()))
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
