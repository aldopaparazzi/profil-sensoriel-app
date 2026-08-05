# ui/ui_strategies_dialog.py
"""
Popup de sélection des stratégies de compensation.
Affiche les items proposés (au-dessus du seuil) sous forme de cases à cocher,
groupées par quadrant puis par domaine.
"""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class StrategiesDialog(QDialog):
    GENERATE_ONLY = 1
    GENERATE_AND_OPEN = 2
    OPEN_ONLY = 3
    """
    candidates: dict retourné par select_strategies()
        {quadrant: {"z":, "direction":, "objectif":, "items": {domaine: [str, ...]}}}
    """

    def __init__(self, candidates: dict, parent=None):
        super().__init__(parent)
        self.action = None
        self.setWindowTitle("Sélection des stratégies de compensation")
        self.setMinimumSize(600, 500)

        self._checkboxes: list[tuple[str, str, str, QCheckBox]] = []
        # (quadrant, domaine, texte_item, checkbox)

        layout = QVBoxLayout(self)

        if not candidates:
            layout.addWidget(QLabel("Aucun écart significatif au-delà du seuil."))
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            content_layout = QVBoxLayout(content)

            for quadrant, data in candidates.items():
                header = QLabel(
                    f"<b>{quadrant.capitalize()}</b> "
                    f"(z = {data['z']:+.2f}) — {data['objectif']}"
                )
                header.setWordWrap(True)
                content_layout.addWidget(header)

                for domaine, items in data["items"].items():
                    domain_label = QLabel(domaine.replace("_", " ").capitalize())
                    domain_label.setStyleSheet("color: gray; margin-left: 8px;")
                    content_layout.addWidget(domain_label)

                    for item_text in items:
                        cb = QCheckBox(item_text)
                        cb.setStyleSheet("margin-left: 16px;")
                        content_layout.addWidget(cb)
                        self._checkboxes.append((quadrant, domaine, item_text, cb))

            content_layout.addStretch()
            scroll.setWidget(content)
            layout.addWidget(scroll)

        """
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Valider")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        """
        button_row = QHBoxLayout()

        btn_generate = QPushButton("Générer seulement")
        btn_generate_open = QPushButton("Générer et ouvrir")
        btn_open_only = QPushButton("Ouvrir seulement")
        btn_cancel = QPushButton("Annuler")

        btn_generate.clicked.connect(lambda: self._choose(self.GENERATE_ONLY))
        btn_generate_open.clicked.connect(lambda: self._choose(self.GENERATE_AND_OPEN))
        btn_open_only.clicked.connect(lambda: self._choose(self.OPEN_ONLY))
        btn_cancel.clicked.connect(self.reject)

        button_row.addWidget(btn_generate)
        button_row.addWidget(btn_generate_open)
        button_row.addWidget(btn_open_only)
        button_row.addStretch()
        button_row.addWidget(btn_cancel)
        layout.addLayout(button_row)

    def _choose(self, action: int):
        self.action = action
        self.accept()

    def selected_strategies(self) -> dict:
        """
        Retourne uniquement les items cochés, même structure imbriquée :
        {quadrant: {domaine: [item, ...]}}
        """
        result: dict[str, dict[str, list[str]]] = {}
        for quadrant, domaine, item_text, cb in self._checkboxes:
            if cb.isChecked():
                result.setdefault(quadrant, {}).setdefault(domaine, []).append(
                    item_text
                )
        return result
