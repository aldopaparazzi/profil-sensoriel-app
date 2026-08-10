# ui_settings.py
"""
Dialogue de configuration (bouton "⚙ Configuration").

Édite :
- le token Tally (.env, via storage.init/config.settings)
- runtime.json (workspace, libreoffice, debug, generate_html, generate_odt)

Le dossier "config" (contenant runtime.json) est affiché en lecture seule :
il ne fait pas partie du workspace utilisateur et ne doit pas être déplaçable
depuis l'UI (voir principe : toutes les données utilisateur vivent dans le workspace).
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import get_tally_token, save_tally_token
from ingestion.fetch_tally import check_token_valid
from reporting.bilan_odt import generate_chart
from storage.init import load_runtime, save_runtime
from storage.paths import paths
from utils.logger import logger

DEFAULT_CHART_SETTINGS = {
    "bar_height": 0.35,
    "row_height": 0.42,
    "show_marker": True,
    "show_values": True,
    "show_zero_line": True,
    "show_x_axis": False,
    "dpi": 150,
}


class SettingsDialog(QDialog):
    """Fenêtre de configuration de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setMinimumWidth(520)

        self.runtime = load_runtime()

        layout = QVBoxLayout(self)
        form = QFormLayout()
        tabs = QTabWidget()
        layout.addWidget(tabs)

        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)  # onglet "Général"
        tabs.addTab(general_tab, "Général")  # onglet "Général"
        appearance_tab = self._build_appearance_tab()  # onglet "Apparence"
        tabs.addTab(appearance_tab, "Apparence")  # onglet "Apparence"

        # ------------------------------------------------
        # Token Tally
        # ------------------------------------------------
        token_row = QHBoxLayout()
        self.token_field = QLineEdit(get_tally_token())
        self.token_field.setEchoMode(QLineEdit.Password)
        self.btn_show_token = QPushButton("👁")
        self.btn_show_token.setFixedWidth(32)
        self.btn_show_token.setCheckable(True)
        self.btn_show_token.toggled.connect(self._toggle_token_visibility)
        self.btn_test_token = QPushButton("Tester")
        self.btn_test_token.clicked.connect(self._test_token)
        token_row.addWidget(self.token_field)
        token_row.addWidget(self.btn_show_token)
        token_row.addWidget(self.btn_test_token)
        form.addRow("Token Tally :", token_row)

        # ------------------------------------------------
        # Dossier data perso (workspace)
        # ------------------------------------------------
        self.workspace_field = QLineEdit(
            str(self.runtime.get("workspace", paths.workspace))
        )
        workspace_row = self._path_row(self.workspace_field, self._browse_workspace)
        form.addRow("Dossier data perso :", workspace_row)

        # ------------------------------------------------
        # LibreOffice
        # ------------------------------------------------
        self.libreoffice_field = QLineEdit(
            str(self.runtime.get("libreoffice", "") or "")
        )
        libreoffice_row = self._path_row(
            self.libreoffice_field, self._browse_libreoffice
        )
        form.addRow("LibreOffice :", libreoffice_row)

        # ------------------------------------------------
        # Dossier config (lecture seule)
        # ------------------------------------------------
        config_label = QLabel(str(paths.config_dir))
        config_label.setStyleSheet("color: gray;")
        config_label.setToolTip(
            "Dossier interne à l'application (non modifiable).\n"
            "Les données utilisateur vivent dans le dossier data perso ci-dessus."
        )
        form.addRow("Dossier config :", config_label)

        general_layout.addLayout(form)

        # ------------------------------------------------
        # Options
        # ------------------------------------------------
        self.chk_html = QCheckBox("Générer les rapports HTML")
        self.chk_html.setChecked(bool(self.runtime.get("generate_html", True)))
        self.chk_odt = QCheckBox("Générer les rapports ODT")
        self.chk_odt.setChecked(bool(self.runtime.get("generate_odt", True)))
        self.chk_debug = QCheckBox("Mode debug")
        self.chk_debug.setChecked(bool(self.runtime.get("debug", False)))
        self.threshold_field = QDoubleSpinBox()
        self.threshold_field.setRange(0.5, 3.0)
        self.threshold_field.setSingleStep(0.1)
        self.threshold_field.setValue(
            float(self.runtime.get("strategy_threshold", 1.5))
        )
        form.addRow("Seuil stratégies (|z| ≥) :", self.threshold_field)
        general_layout.addWidget(self.chk_html)
        general_layout.addWidget(self.chk_odt)
        general_layout.addWidget(self.chk_debug)

        # ------------------------------------------------
        # Boutons OK / Annuler
        # ------------------------------------------------
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        # label du bouton save
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ======================================================
    # Helpers UI
    # ======================================================

    def _path_row(self, field: QLineEdit, browse_slot):
        """Construit une ligne [champ texte] [bouton Parcourir]."""
        row = QHBoxLayout()
        btn = QPushButton("Parcourir…")
        btn.clicked.connect(browse_slot)
        row.addWidget(field)
        row.addWidget(btn)
        return row

    def _toggle_token_visibility(self, checked: bool):
        """Affiche ou masque le token Tally dans le champ texte."""
        self.token_field.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )

    def _browse_workspace(self):
        """Ouvre un dialogue pour choisir le dossier data perso (workspace)."""
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier data perso", self.workspace_field.text()
        )
        if folder:
            self.workspace_field.setText(folder)

    def _browse_libreoffice(self):
        """Ouvre un dialogue pour choisir le fichier soffice.exe (LibreOffice)."""

        file, _ = QFileDialog.getOpenFileName(
            self, "Choisir soffice.exe", self.libreoffice_field.text()
        )
        if file:
            self.libreoffice_field.setText(file)

    def _test_token(self):
        """Teste la validité du token Tally et affiche un message."""
        token = self.token_field.text().strip()
        if not token:
            QMessageBox.warning(self, "Token", "Champ vide.")
            return
        ok = check_token_valid(token)
        if ok:
            QMessageBox.information(self, "Token", "✅ Token valide.")
        else:
            QMessageBox.critical(self, "Token", "❌ Token invalide.")

    def _build_appearance_tab(self) -> QWidget:
        """Onglet Apparence."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        charts = self._chart_settings()

        group = QGroupBox("Graphiques")
        group_layout = QVBoxLayout(group)

        self.chk_chart_show_values = QCheckBox("Afficher les valeurs")
        self.chk_chart_show_values.setChecked(
            charts.get("show_values", DEFAULT_CHART_SETTINGS["show_values"])
        )

        self.chk_chart_show_marker = QCheckBox("Afficher le marqueur")
        self.chk_chart_show_marker.setChecked(
            charts.get("show_marker", DEFAULT_CHART_SETTINGS["show_marker"])
        )

        self.chk_chart_show_zero_line = QCheckBox("Afficher la ligne centrale")
        self.chk_chart_show_zero_line.setChecked(
            charts.get("show_zero_line", DEFAULT_CHART_SETTINGS["show_zero_line"])
        )

        self.chk_chart_show_x_axis = QCheckBox("Afficher l'axe horizontal")
        self.chk_chart_show_x_axis.setChecked(
            charts.get("show_x_axis", DEFAULT_CHART_SETTINGS["show_x_axis"])
        )

        group_layout.addWidget(self.chk_chart_show_values)
        group_layout.addWidget(self.chk_chart_show_marker)
        group_layout.addWidget(self.chk_chart_show_zero_line)
        group_layout.addWidget(self.chk_chart_show_x_axis)

        form = QFormLayout()

        self.bar_height = QDoubleSpinBox()
        self.bar_height.setRange(0.15, 1.0)
        self.bar_height.setSingleStep(0.05)
        self.bar_height.setDecimals(2)
        self.bar_height.setValue(
            charts.get("bar_height", DEFAULT_CHART_SETTINGS["bar_height"])
        )

        self.row_height = QDoubleSpinBox()
        self.row_height.setRange(0.25, 1.0)
        self.row_height.setSingleStep(0.02)
        self.row_height.setDecimals(2)
        self.row_height.setValue(
            charts.get("row_height", DEFAULT_CHART_SETTINGS["row_height"])
        )

        self.chart_dpi = QSpinBox()
        self.chart_dpi.setRange(72, 600)
        self.chart_dpi.setSingleStep(10)
        self.chart_dpi.setValue(charts.get("dpi", DEFAULT_CHART_SETTINGS["dpi"]))

        form.addRow("Épaisseur des barres", self.bar_height)
        form.addRow("Espacement des lignes", self.row_height)
        form.addRow("Résolution PNG (dpi)", self.chart_dpi)

        group_layout.addLayout(form)
        layout.addStretch()  # ajoute un espace flexible pour pousser les widgets vers le haut

        # Bouton "Restaurer les valeurs par défaut"
        self.btn_restore_defaults = QPushButton("Restaurer les valeurs par défaut")
        self.btn_restore_defaults.clicked.connect(self._restore_chart_defaults)
        layout.addWidget(self.btn_restore_defaults)

        layout.addWidget(group)
        layout.addStretch()

        # aperçu du rendu des graphiques
        preview_group = QGroupBox("Aperçu")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)

        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        self.chk_chart_show_values.toggled.connect(self._update_preview)
        self.chk_chart_show_marker.toggled.connect(self._update_preview)
        self.chk_chart_show_zero_line.toggled.connect(self._update_preview)
        self.chk_chart_show_x_axis.toggled.connect(self._update_preview)

        self.bar_height.valueChanged.connect(self._update_preview)
        self.row_height.valueChanged.connect(self._update_preview)
        self.chart_dpi.valueChanged.connect(self._update_preview)

        self._update_preview()

        return tab

    def _restore_chart_defaults(self):
        """Réinitialise les widgets de l'onglet Apparence."""
        self.chk_chart_show_values.setChecked(DEFAULT_CHART_SETTINGS["show_values"])
        self.chk_chart_show_marker.setChecked(DEFAULT_CHART_SETTINGS["show_marker"])
        self.chk_chart_show_zero_line.setChecked(
            DEFAULT_CHART_SETTINGS["show_zero_line"]
        )
        self.chk_chart_show_x_axis.setChecked(DEFAULT_CHART_SETTINGS["show_x_axis"])
        self.bar_height.setValue(DEFAULT_CHART_SETTINGS["bar_height"])
        self.row_height.setValue(DEFAULT_CHART_SETTINGS["row_height"])
        self.chart_dpi.setValue(DEFAULT_CHART_SETTINGS["dpi"])

    def _chart_settings(self):
        """Retourne le dictionnaire des paramètres graphiques."""
        return self.runtime.setdefault("ui", {}).setdefault("charts", {})

    def _update_preview(self):
        preview_scores = {
            "auditif": {"z": 1.2},
            "visuel": {"z": -0.8},
            "tactile": {"z": 2.1},
            "vestibulaire": {"z": -2.4},
        }

        chart_cfg = {
            "show_values": self.chk_chart_show_values.isChecked(),
            "show_marker": self.chk_chart_show_marker.isChecked(),
            "show_zero_line": self.chk_chart_show_zero_line.isChecked(),
            "show_x_axis": self.chk_chart_show_x_axis.isChecked(),
            "bar_height": self.bar_height.value(),
            "row_height": self.row_height.value(),
            "dpi": self.chart_dpi.value(),
        }

        png, _ = generate_chart(
            section="preview",
            scores_for_type=preview_scores,
            chart_config=chart_cfg,
        )

        pixmap = QPixmap()
        pixmap.loadFromData(png)

        self.preview_label.setPixmap(pixmap)

    # ======================================================
    # Sauvegarde
    # ======================================================

    def _save_and_close(self):
        """Sauvegarde les paramètres et ferme le dialogue."""
        # --- Token (.env) ---
        new_token = self.token_field.text().strip()
        if new_token and new_token != get_tally_token():
            save_tally_token(new_token)
            logger.info("Token Tally mis à jour")

        # --- runtime.json ---
        self.runtime["workspace"] = self.workspace_field.text().strip()
        self.runtime["libreoffice"] = self.libreoffice_field.text().strip()
        self.runtime["generate_html"] = self.chk_html.isChecked()
        self.runtime["generate_odt"] = self.chk_odt.isChecked()
        self.runtime["debug"] = self.chk_debug.isChecked()
        self.runtime["strategy_threshold"] = self.threshold_field.value()
        charts = self._chart_settings()

        charts["show_values"] = self.chk_chart_show_values.isChecked()
        charts["show_marker"] = self.chk_chart_show_marker.isChecked()
        charts["show_zero_line"] = self.chk_chart_show_zero_line.isChecked()
        charts["show_x_axis"] = self.chk_chart_show_x_axis.isChecked()

        charts["bar_height"] = self.bar_height.value()
        charts["row_height"] = self.row_height.value()
        charts["dpi"] = self.chart_dpi.value()

        save_runtime(self.runtime)
        logger.info("runtime.json mis à jour : %s", self.runtime)

        # Recrée les dossiers si le workspace a changé
        paths.ensure_workspace()

        self.accept()
