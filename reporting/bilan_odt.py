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
from odf.style import (
    ParagraphProperties,
    Style,
    TableCellProperties,
    TableColumnProperties,
    TableRowProperties,
    TextProperties,
)
from odf.table import Table, TableCell, TableColumn, TableRow
from odf.text import H, List, ListItem, P

from reporting.bilan_charts import (
    QUADRANT_LABELS,
    SECTIONS,
    generate_all_item_charts,
)
from reporting.chart_style import BAR_COLOR_THRESHOLDS
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


def _add_item_chart_row(
    doc,
    table,
    label: str,
    score: float,
    svg_bytes: bytes,
    height_cm: float,
    score_styles: dict[str, str],
) -> None:

    """Ajoute une ligne Libellé / Score / Graphique au tableau."""
    # Propriétés du paragraphe contenant le libellé
    row = TableRow(stylename="ItemChartsRow")
    cell = TableCell(stylename="ItemChartsCell")
    cell.addElement(
        P(
            stylename="ItemChartsLabelParagraph",
            text=label,
        )
    )
    row.addElement(cell)

    # Propriétés du paragraphe contenant le score
    cell = TableCell(stylename="ItemChartsCell")
    distance = abs(score)
    # Détermine la couleur du score en fonction de la distance par rapport à zéro
    score_color = next(
        color
        for threshold, color in BAR_COLOR_THRESHOLDS
        if distance <= threshold
    )
    score_paragraph = P(
        stylename=score_styles[score_color],
        text=f"{score:+.2f}",
    )
    cell.addElement(score_paragraph)


    # Propriétés du paragraphe contenant le graphique
    row.addElement(cell)
    cell = TableCell(stylename="ItemChartsCell") # 
    frame = Frame(
        width="10cm",
        height="0.7cm",
        anchortype="paragraph",
    )

    href = doc.addPictureFromString(
        svg_bytes,
        "image/svg+xml",
    )

    image = Image(href=href)
    frame.addElement(image)

    paragraph = P(
        stylename="ItemChartsGraphParagraph",
    )

    paragraph.addElement(frame)
    cell.addElement(paragraph)
    row.addElement(cell)
    table.addElement(row)


def _add_item_chart_section(
    doc,
    title: str,
    items: list[tuple[str, float, bytes, float]],
) -> None:
    """Ajoute une section contenant un tableau Libellé / Score / Graphique."""
    doc.text.addElement(
        H(
            outlinelevel=1,
            text=title,
        )
    )

    table = _build_item_chart_table(doc, items)
    doc.text.addElement(table)


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
    item_charts = generate_all_item_charts(scores)

    for section_key, title in SECTIONS:
        items = item_charts.get(section_key)

        if items:
            _add_item_chart_section(
                doc,
                title,
                items,
            )

    _add_strategies(doc, selected_strategies)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc.save(str(output_path))

    logger.info(
        "✓ Bilan ODT prérempli généré : %s",
        output_path,
    )

    return output_path


def _build_item_chart_table(
    doc,
    items: list[tuple[str, float, bytes, float]],
) -> Table:
    """Construit un tableau contenant une ligne par item."""
    table = Table(name="ItemCharts")

    # Style des cellules du tableau
    cell_style = Style(
        name="ItemChartsCell",
        family="table-cell",
    )

    # Style du paragraphe contenant le graphique
    graph_paragraph_style = Style(
        name="ItemChartsGraphParagraph",
        family="paragraph",
    )
    graph_paragraph_style.addElement(
        ParagraphProperties(
            textalign="center",
            margin="0cm",
        )
    )
    doc.automaticstyles.addElement(graph_paragraph_style)

    # Style du paragraphe contenant le libellé
    label_paragraph_style = Style(
        name="ItemChartsLabelParagraph",
        family="paragraph",
    )
    label_paragraph_style.addElement(
        TextProperties(
            fontsize="10pt",
        )
    )
    doc.automaticstyles.addElement(label_paragraph_style)

    # Styles pour les paragraphes contenant les scores
    score_styles = {}

    for index, (_threshold, color) in enumerate(BAR_COLOR_THRESHOLDS):
        style_name = f"ItemChartsScoreParagraph{index}"

        score_style = Style(
            name=style_name,
            family="paragraph",
        )
        score_style.addElement(
            ParagraphProperties(
                textalign="center",
            )
        )
        score_style.addElement(
            TextProperties(
                fontsize="10pt",
                color=color,
            )
        )

        doc.automaticstyles.addElement(score_style)
        score_styles[color] = style_name

    # Propriétés des cellules
    cell_style.addElement(
        TableCellProperties(
            verticalalign="middle",
            border="0.5pt solid #000000",
            padding="0.15cm",
        )
    )
    doc.automaticstyles.addElement(cell_style)

    # Style des lignes
    row_style = Style(
        name="ItemChartsRow",
        family="table-row",
    )
    row_style.addElement(
        TableRowProperties(
            rowheight="1cm",
        )
    )
    doc.automaticstyles.addElement(row_style)

    # Style de la colonne Libellé
    label_style = Style(
        name="ItemChartsLabelCol",
        family="table-column",
    )
    label_style.addElement(
        TableColumnProperties(columnwidth="4cm")
    )
    doc.automaticstyles.addElement(label_style)

    # Style de la colonne Score
    score_style = Style(
        name="ItemChartsScoreCol",
        family="table-column",
    )
    score_style.addElement(
        TableColumnProperties(columnwidth="1.5cm")
    )
    doc.automaticstyles.addElement(score_style)

    # Style de la colonne Graphique
    graph_style = Style(
        name="ItemChartsGraphCol",
        family="table-column",
    )
    graph_style.addElement(
        TableColumnProperties(columnwidth="10cm")
    )
    doc.automaticstyles.addElement(graph_style)

    table.addElement(TableColumn(stylename="ItemChartsLabelCol"))
    table.addElement(TableColumn(stylename="ItemChartsScoreCol"))
    table.addElement(TableColumn(stylename="ItemChartsGraphCol"))

    for label, score, svg_bytes, height_cm in items:
        _add_item_chart_row(
            doc,
            table,
            label,
            score,
            svg_bytes,
            height_cm,
            score_styles,
        )


    return table


if __name__ == "__main__":
    from odf.opendocument import OpenDocumentText

    doc = OpenDocumentText()

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

    for section_key, title in SECTIONS:
        items = charts.get(section_key)

        if not items:
            continue

        _add_item_chart_section(
            doc,
            title,
            items,
        )

        print(f"{section_key}: {len(items)} lignes")

    test_path = Path("test_table.odt")
    doc.save(str(test_path))
    import zipfile

    with zipfile.ZipFile(test_path) as z:
        content = z.read("content.xml").decode("utf-8")
        print(content)

    print(f"Tableau test créé : {test_path}")
