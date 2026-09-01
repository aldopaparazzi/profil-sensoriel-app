# reporting/bilan_odt.py
"""Génère le bilan ODT prérempli, avec un rendu inspiré de template.html :
- Identité du patient
- Date d'évaluation
- Date de naissance
- Âge
- Niveau scolaire éventuel
- Quadrants sensoriels
- Domaines sensoriels
- Composantes scolaires
- Aménagements à mettre en place validées
"""

from __future__ import annotations

from pathlib import Path

from odf.draw import Frame, Image
from odf.opendocument import load
from odf.text import H, List, ListItem, P

from reporting.bilan_charts import (
    QUADRANT_LABELS,
    SECTIONS,
    generate_all_charts,
)
from storage.paths import paths
from utils.logger import get_logger

logger = get_logger(__name__)

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


def _get_domain_label(key: str) -> str:
    return DOMAIN_LABELS.get(key, key)


def _add_patient_identity(doc, patient: dict) -> None:
    """Ajoute les informations d'identité du patient au document."""
    fullname = (f"{patient.get('prenom', '')} {patient.get('nom', '')}").strip()
    doc.text.addElement(
        H(
            outlinelevel=1,
            text=fullname or "Profil Sensoriel — Bilan",
        )
    )
    doc.text.addElement(P(text=f"Évaluation du {patient.get('evaluation_date', '—')}"))
    doc.text.addElement(P(text=f"Né(e) le {patient.get('birth_date', '—')}"))
    if patient.get("age_group"):
        age_label = f"tranche {patient['age_group']}"
    else:
        age_label = f"{patient.get('age', '—')} ans"
    doc.text.addElement(P(text=f"Âge : {age_label}"))
    if patient.get("niveau"):
        doc.text.addElement(P(text=f"Niveau : {patient['niveau']}"))


def _add_chart_section(
    doc,
    title: str,
    chart: tuple[bytes, float],
) -> None:
    svg_bytes, height_cm = chart
    doc.text.addElement(
        H(
            outlinelevel=1,
            text=title,
        )
    )
    href = doc.addPictureFromString(
        svg_bytes,
        "image/svg+xml",
    )
    frame = Frame(
        width="16cm",
        height=f"{height_cm}cm",
        anchortype="paragraph",
    )
    frame.addElement(Image(href=href))
    paragraph = P()
    paragraph.addElement(frame)
    doc.text.addElement(paragraph)


def _add_strategies(doc, selected_strategies: dict) -> None:
    doc.text.addElement(
        H(
            outlinelevel=1,
            text="Aménagements à mettre en place",
        )
    )

    if not selected_strategies:
        doc.text.addElement(P(text="Aucune stratégie sélectionnée."))
        return

    for quadrant, domains in selected_strategies.items():
        _add_strategy_quadrant(doc, quadrant, domains)


def _add_strategy_quadrant(
    doc,
    quadrant: str,
    domains: dict,
) -> None:
    label = QUADRANT_LABELS.get(
        quadrant,
        quadrant.capitalize(),
    )

    doc.text.addElement(
        H(
            outlinelevel=2,
            text=label,
        )
    )

    for domaine, items in domains.items():
        doc.text.addElement(P(text=_get_domain_label(domaine)))

        strategy_list = List()

        for item in items:
            list_item = ListItem()
            list_item.addElement(P(text=item))
            strategy_list.addElement(list_item)

        doc.text.addElement(strategy_list)


def build_bilan_odt(
    patient: dict,
    scores: dict,
    output_path: str | Path,
    selected_strategies: dict,
) -> Path:
    """Génère le bilan ODT prérempli."""
    doc = load(str(paths.odt_template))

    _add_patient_identity(doc, patient)

    charts = generate_all_charts(scores)

    for section_key, title in SECTIONS:
        chart = charts.get(section_key)

        if chart:
            _add_chart_section(doc, title, chart)

    _add_strategies(doc, selected_strategies)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc.save(str(output_path))

    logger.info(
        "✓ Bilan ODT prérempli généré : %s",
        output_path,
    )

    return output_path
