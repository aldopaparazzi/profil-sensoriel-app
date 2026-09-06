# ui_settings.py
"""
Dialogue de configuration (bouton "⚙ Configuration").

Édite :
- le token Tally (.env, via storage.init/config.settings)
- runtime.json :
    - workspace
    - libreoffice
    - debug
    - generate_html
    - generate_odt
    - strategy_threshold
    - paramètres d'affichage des graphiques SVG

IMPORTANT
---------
La génération des graphiques est désormais basée sur du SVG
et non plus sur Matplotlib/PNG.

L'interface de configuration a donc été adaptée au nouveau moteur
SVG utilisé par reporting.bilan_odt.generate_chart().

Compatibilité legacy
--------------------
Certaines anciennes clés de configuration peuvent encore exister
dans runtime.json :

    bar_height
    row_height
    show_x_axis

Elles ne sont plus utilisées directement par l'interface.

La clé "row_height" reste conservée car elle a encore un sens
dans le nouveau moteur SVG, mais son unité est désormais le pixel
et non plus une valeur Matplotlib en pouces.

Les anciennes clés "show_x_axis" sont conservées dans
runtime.json si elles existaient déjà, afin de ne pas casser
les anciennes configurations.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
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
from reporting.bilan_charts import generate_chart
from reporting.chart_style import DEFAULT_CHART_SETTINGS
from storage.init import load_runtime, save_runtime
from storage.paths import paths
from utils.logger import logger

LEGACY_CHART_KEYS = ("show_x_axis",)


class SettingsDialog(QDialog):
    """Fenêtre de configuration de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configuration")
        self.setMinimumWidth(560)

        # ----------------------------------------------------
        # Chargement du runtime actuel
        # ----------------------------------------------------

        self.runtime = load_runtime()

        # ----------------------------------------------------
        # Layout principal
        # ----------------------------------------------------

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ====================================================
        # ONGLET GÉNÉRAL
        # ====================================================

        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        tabs.addTab(general_tab, "Général")

        # ----------------------------------------------------
        # Formulaire général
        # ----------------------------------------------------

        form = QFormLayout()

        # ====================================================
        # Token Tally
        # ====================================================

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

        form.addRow(
            "Token Tally :",
            token_row,
        )

        # ====================================================
        # Dossier data perso / workspace
        # ====================================================

        self.workspace_field = QLineEdit(
            str(
                self.runtime.get(
                    "workspace",
                    paths.workspace,
                )
            )
        )

        workspace_row = self._path_row(
            self.workspace_field,
            self._browse_workspace,
        )

        form.addRow(
            "Dossier data perso :",
            workspace_row,
        )

        # ====================================================
        # LibreOffice
        # ====================================================

        self.libreoffice_field = QLineEdit(
            str(
                self.runtime.get(
                    "libreoffice",
                    "",
                )
                or ""
            )
        )

        libreoffice_row = self._path_row(
            self.libreoffice_field,
            self._browse_libreoffice,
        )

        form.addRow(
            "LibreOffice :",
            libreoffice_row,
        )

        # ====================================================
        # Dossier config
        # ====================================================
        #
        # Lecture seule.
        #
        # Le dossier config appartient à l'application.
        # Les données utilisateur restent dans workspace.
        #

        config_label = QLabel(str(paths.config_dir))

        config_label.setStyleSheet("color: gray;")

        config_label.setToolTip(
            "Dossier interne à l'application (non modifiable).\n"
            "Les données utilisateur vivent dans le dossier "
            "data perso ci-dessus."
        )

        form.addRow(
            "Dossier config :",
            config_label,
        )

        # ----------------------------------------------------
        # Ajout du formulaire général
        # ----------------------------------------------------

        general_layout.addLayout(form)

        # ====================================================
        # OPTIONS DE RAPPORT
        # ====================================================

        options_group = QGroupBox("Rapports")
        options_layout = QVBoxLayout(options_group)

        self.chk_html = QCheckBox("Générer les rapports HTML")

        self.chk_html.setChecked(
            bool(
                self.runtime.get(
                    "generate_html",
                    True,
                )
            )
        )

        self.chk_odt = QCheckBox("Générer les rapports ODT")

        self.chk_odt.setChecked(
            bool(
                self.runtime.get(
                    "generate_odt",
                    True,
                )
            )
        )

        self.chk_debug = QCheckBox("Mode debug")

        self.chk_debug.setChecked(
            bool(
                self.runtime.get(
                    "debug",
                    False,
                )
            )
        )

        options_layout.addWidget(self.chk_html)

        options_layout.addWidget(self.chk_odt)

        options_layout.addWidget(self.chk_debug)

        general_layout.addWidget(options_group)

        # ====================================================
        # SEUIL DES STRATÉGIES
        # ====================================================

        strategy_group = QGroupBox("Aménagements à mettre en place")

        strategy_form = QFormLayout(strategy_group)

        self.threshold_field = QDoubleSpinBox()

        self.threshold_field.setRange(
            0.5,
            3.0,
        )

        self.threshold_field.setSingleStep(0.1)

        self.threshold_field.setDecimals(1)

        self.threshold_field.setValue(
            float(
                self.runtime.get(
                    "strategy_threshold",
                    1.5,
                )
            )
        )

        strategy_form.addRow(
            "Seuil stratégies (|z| ≥) :",
            self.threshold_field,
        )

        general_layout.addWidget(strategy_group)

        general_layout.addStretch()

        # ====================================================
        # ONGLET APPARENCE
        # ====================================================

        appearance_tab = self._build_appearance_tab()

        tabs.addTab(
            appearance_tab,
            "Apparence",
        )

        # ====================================================
        # BOUTONS OK / ANNULER
        # ====================================================

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")

        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")

        buttons.accepted.connect(self._save_and_close)

        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    # ============================================================
    # HELPERS UI
    # ============================================================

    def _path_row(
        self,
        field: QLineEdit,
        browse_slot,
    ):
        """
        Construit une ligne :

            [ champ texte ] [ Parcourir… ]
        """

        row = QHBoxLayout()

        btn = QPushButton("Parcourir…")

        btn.clicked.connect(browse_slot)

        row.addWidget(field)
        row.addWidget(btn)

        return row

    # ============================================================
    # TOKEN
    # ============================================================

    def _toggle_token_visibility(
        self,
        checked: bool,
    ):
        """Affiche ou masque le token Tally."""

        self.token_field.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )

    def _test_token(self):
        """Teste la validité du token Tally."""

        token = self.token_field.text().strip()

        if not token:
            QMessageBox.warning(
                self,
                "Token",
                "Champ vide.",
            )
            return

        ok = check_token_valid(token)

        if ok:
            QMessageBox.information(
                self,
                "Token",
                "✅ Token valide.",
            )

        else:
            QMessageBox.critical(
                self,
                "Token",
                "❌ Token invalide.",
            )

    # ============================================================
    # WORKSPACE / LIBREOFFICE
    # ============================================================

    def _browse_workspace(self):
        """Choisit le dossier data perso."""

        folder = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier data perso",
            self.workspace_field.text(),
        )

        if folder:
            self.workspace_field.setText(folder)

    def _browse_libreoffice(self):
        """Choisit l'exécutable LibreOffice."""

        file, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir soffice.exe",
            self.libreoffice_field.text(),
        )

        if file:
            self.libreoffice_field.setText(file)

    # ============================================================
    # ONGLET APPARENCE
    # ============================================================

    def _build_appearance_tab(self) -> QWidget:
        """
        Construit l'onglet Apparence.

        Les paramètres correspondent directement aux propriétés
        utilisées pour construire le SVG.

        L'objectif est d'avoir :

            aperçu UI
                 ↓
            mêmes paramètres
                 ↓
            graphique final ODT
        """

        tab = QWidget()

        layout = QVBoxLayout(tab)

        charts = self._chart_settings()

        # ====================================================
        # GROUPE : AFFICHAGE
        # ====================================================

        display_group = QGroupBox("Éléments affichés")

        display_layout = QVBoxLayout(display_group)

        # ----------------------------------------------------
        # Valeurs
        # ----------------------------------------------------

        self.chk_chart_show_values = QCheckBox("Afficher les valeurs")

        self.chk_chart_show_values.setChecked(
            charts.get(
                "show_values",
                DEFAULT_CHART_SETTINGS["show_values"],
            )
        )

        # ----------------------------------------------------
        # Marqueur
        # ----------------------------------------------------

        self.chk_chart_show_marker = QCheckBox("Afficher le marqueur")

        self.chk_chart_show_marker.setChecked(
            charts.get(
                "show_marker",
                DEFAULT_CHART_SETTINGS["show_marker"],
            )
        )

        # ----------------------------------------------------
        # Ligne centrale
        # ----------------------------------------------------

        self.chk_chart_show_zero_line = QCheckBox("Afficher la ligne centrale")

        self.chk_chart_show_zero_line.setChecked(
            charts.get(
                "show_zero_line",
                DEFAULT_CHART_SETTINGS["show_zero_line"],
            )
        )

        display_layout.addWidget(self.chk_chart_show_values)

        display_layout.addWidget(self.chk_chart_show_marker)

        display_layout.addWidget(self.chk_chart_show_zero_line)

        layout.addWidget(display_group)

        # ====================================================
        # GROUPE : TEXTE
        # ====================================================

        text_group = QGroupBox("Texte")

        text_form = QFormLayout(text_group)

        # ----------------------------------------------------
        # Taille des labels
        # ----------------------------------------------------

        self.label_font_size = QSpinBox()

        self.label_font_size.setRange(
            12,
            32,
        )

        self.label_font_size.setSingleStep(1)

        self.label_font_size.setSuffix(" px")

        self.label_font_size.setValue(
            charts.get(
                "label_font_size",
                DEFAULT_CHART_SETTINGS["label_font_size"],
            )
        )

        # ----------------------------------------------------
        # Taille des valeurs
        # ----------------------------------------------------

        self.value_font_size = QSpinBox()

        self.value_font_size.setRange(
            10,
            28,
        )

        self.value_font_size.setSingleStep(1)

        self.value_font_size.setSuffix(" px")

        self.value_font_size.setValue(
            charts.get(
                "value_font_size",
                DEFAULT_CHART_SETTINGS["value_font_size"],
            )
        )

        text_form.addRow(
            "Taille des libellés :",
            self.label_font_size,
        )

        text_form.addRow(
            "Taille des valeurs :",
            self.value_font_size,
        )

        layout.addWidget(text_group)

        # ====================================================
        # GROUPE : BARRES
        # ====================================================

        bars_group = QGroupBox("Barres")

        bars_form = QFormLayout(bars_group)

        # ----------------------------------------------------
        # Espacement vertical
        # ----------------------------------------------------

        self.row_height = QSpinBox()

        self.row_height.setRange(
            25,
            80,
        )

        self.row_height.setSingleStep(1)

        self.row_height.setSuffix(" px")

        self.row_height.setToolTip(
            "Hauteur totale de chaque ligne du graphique.\n"
            "Une valeur faible rend le graphique plus compact."
        )

        self.row_height.setValue(
            charts.get(
                "row_height",
                DEFAULT_CHART_SETTINGS["row_height"],
            )
        )

        # ----------------------------------------------------
        # Hauteur de la cellule contenant chaque graphique.
        # ----------------------------------------------------


        self.chart_cell_height = QDoubleSpinBox()
        self.chart_cell_height.setRange(0.8, 3.0)
        self.chart_cell_height.setSingleStep(0.1)
        self.chart_cell_height.setDecimals(1)
        self.chart_cell_height.setSuffix(" cm")
        self.chart_cell_height.setToolTip(
            "Hauteur de la cellule contenant chaque graphique.\n"
            "Sous 0,8 cm, le texte des autres colonnes devient trop serré."
        )
        self.chart_cell_height.setValue(
            charts.get("chart_cell_height_cm", DEFAULT_CHART_SETTINGS["chart_cell_height_cm"])
        )
        # ----------------------------------------------------
        # Piste grise
        # ----------------------------------------------------

        self.bar_height = QSpinBox()

        self.bar_height.setRange(
            4,
            24,
        )

        self.bar_height.setSingleStep(1)

        self.bar_height.setSuffix(" px")

        self.bar_height.setToolTip("Épaisseur de la piste grise.")

        self.bar_height.setValue(
            charts.get(
                "bar_height",
                DEFAULT_CHART_SETTINGS["bar_height"],
            )
        )

        # ----------------------------------------------------
        # Barre colorée
        # ----------------------------------------------------

        self.fill_height = QSpinBox()

        self.fill_height.setRange(
            2,
            20,
        )

        self.fill_height.setSingleStep(1)

        self.fill_height.setSuffix(" px")

        self.fill_height.setToolTip("Épaisseur de la barre colorée.")

        self.fill_height.setValue(
            charts.get(
                "fill_height",
                DEFAULT_CHART_SETTINGS["fill_height"],
            )
        )

        # ----------------------------------------------------
        # Ligne zéro
        # ----------------------------------------------------

        self.zero_line_height = QSpinBox()

        self.zero_line_height.setRange(
            10,
            35,
        )

        self.zero_line_height.setSingleStep(1)

        self.zero_line_height.setSuffix(" px")

        self.zero_line_height.setToolTip("Hauteur de la ligne centrale.")

        self.zero_line_height.setValue(
            charts.get(
                "zero_line_height",
                DEFAULT_CHART_SETTINGS["zero_line_height"],
            )
        )

        # ----------------------------------------------------
        # Marqueur
        # ----------------------------------------------------

        self.marker_size = QSpinBox()

        self.marker_size.setRange(
            8,
            24,
        )

        self.marker_size.setSingleStep(1)

        self.marker_size.setSuffix(" px")

        self.marker_size.setToolTip("Diamètre du marqueur.")

        self.marker_size.setValue(
            charts.get(
                "marker_size",
                DEFAULT_CHART_SETTINGS["marker_size"],
            )
        )

        bars_form.addRow(
            "Espacement des lignes :",
            self.row_height,
        )
        bars_form.addRow(
            "Hauteur de cellule graphique :",
            self.chart_cell_height
        )

        bars_form.addRow(
            "Épaisseur de la piste :",
            self.bar_height,
        )

        bars_form.addRow(
            "Épaisseur de la barre :",
            self.fill_height,
        )

        bars_form.addRow(
            "Hauteur de la ligne centrale :",
            self.zero_line_height,
        )

        bars_form.addRow(
            "Taille du marqueur :",
            self.marker_size,
        )

        layout.addWidget(bars_group)

        # ====================================================
        # APERÇU
        # ====================================================

        preview_group = QGroupBox("Aperçu")

        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel()

        self.preview_label.setAlignment(Qt.AlignCenter)

        self.preview_label.setMinimumHeight(180)

        self.preview_label.setStyleSheet(
            """
            QLabel {
                background: white;
                border: 1px solid #e7e5e4;
                border-radius: 4px;
            }
            """
        )

        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        # ====================================================
        # RESTAURATION DES VALEURS PAR DÉFAUT
        # ====================================================

        self.btn_restore_defaults = QPushButton("Restaurer les valeurs par défaut")

        self.btn_restore_defaults.clicked.connect(self._restore_chart_defaults)

        layout.addWidget(self.btn_restore_defaults)

        # ====================================================
        # CONNEXIONS POUR L'APERÇU
        # ====================================================

        checkbox_widgets = [
            self.chk_chart_show_values,
            self.chk_chart_show_marker,
            self.chk_chart_show_zero_line,
        ]

        for widget in checkbox_widgets:
            widget.toggled.connect(self._update_preview)

        spin_widgets = [
            self.label_font_size,
            self.value_font_size,
            self.row_height,
            self.bar_height,
            self.fill_height,
            self.zero_line_height,
            self.marker_size,
            self.chart_cell_height,
        ]

        for widget in spin_widgets:
            widget.valueChanged.connect(self._update_preview)

        # Premier rendu.
        self._update_preview()

        return tab

    # ============================================================
    # VALEURS PAR DÉFAUT
    # ============================================================

    def _restore_chart_defaults(self):
        """Réinitialise tous les paramètres graphiques."""

        self.chk_chart_show_values.setChecked(DEFAULT_CHART_SETTINGS["show_values"])

        self.chk_chart_show_marker.setChecked(DEFAULT_CHART_SETTINGS["show_marker"])

        self.chk_chart_show_zero_line.setChecked(
            DEFAULT_CHART_SETTINGS["show_zero_line"]
        )

        self.label_font_size.setValue(
            DEFAULT_CHART_SETTINGS["label_font_size"]
            )

        self.value_font_size.setValue(
            DEFAULT_CHART_SETTINGS["value_font_size"]
            )

        self.row_height.setValue(
            DEFAULT_CHART_SETTINGS["row_height"]
            )

        self.bar_height.setValue(
            DEFAULT_CHART_SETTINGS["bar_height"]
            )

        self.fill_height.setValue(
            DEFAULT_CHART_SETTINGS["fill_height"]
            )

        self.zero_line_height.setValue(
            DEFAULT_CHART_SETTINGS["zero_line_height"]
         )

        self.marker_size.setValue(
            DEFAULT_CHART_SETTINGS["marker_size"]
            )

        self.chart_cell_height.setValue(
            DEFAULT_CHART_SETTINGS["chart_cell_height_cm"]
        )

    # ============================================================
    # PARAMÈTRES GRAPHIQUES
    # ============================================================

    def _chart_settings(self) -> dict:
        """
        Retourne le dictionnaire des paramètres graphiques.

        setdefault() permet de travailler avec un ancien
        runtime.json qui ne contient pas encore les nouvelles clés.
        """

        ui = self.runtime.setdefault(
            "ui",
            {},
        )

        charts = ui.setdefault(
            "charts",
            {},
        )

        return charts

    # ============================================================
    # APERÇU SVG
    # ============================================================

    def _update_preview(self):
        """
        Met à jour l'aperçu du graphique.

        IMPORTANT
        ---------
        generate_chart() retourne maintenant du SVG.

        On n'utilise donc plus :

            QPixmap.loadFromData(png)

        mais :

            QSvgRenderer

        pour rasteriser temporairement le SVG dans le QLabel.

        Le graphique réel du rapport reste bien vectoriel.
        """

        preview_scores = {
            "auditif": {"z": 1.2},
        }

        # ----------------------------------------------------
        # Configuration identique à celle utilisée par l'ODT
        # ----------------------------------------------------

        chart_cfg = {
            "show_values": (self.chk_chart_show_values.isChecked()),
            "show_marker": (self.chk_chart_show_marker.isChecked()),
            "show_zero_line": (self.chk_chart_show_zero_line.isChecked()),
            "label_font_size": (self.label_font_size.value()),
            "value_font_size": (self.value_font_size.value()),
            "row_height": (self.row_height.value()),
            "bar_height": (self.bar_height.value()),
            "fill_height": (self.fill_height.value()),
            "zero_line_height": (self.zero_line_height.value()),
            "marker_size": (self.marker_size.value()),
        }

        # ----------------------------------------------------
        # Génération SVG
        # ----------------------------------------------------

        svg_bytes, _ = generate_chart(
            section="preview",
            scores_for_type=preview_scores,
            chart_config=chart_cfg,
        )

        # ----------------------------------------------------
        # Rendu SVG → QPixmap
        # ----------------------------------------------------

        renderer = QSvgRenderer(svg_bytes)

        if not renderer.isValid():
            logger.warning("Impossible de rendre l'aperçu SVG.")

            self.preview_label.clear()

            return

        # ----------------------------------------------------
        # Taille d'aperçu
        # ----------------------------------------------------
        #
        # On utilise une largeur confortable pour l'UI.
        # La hauteur est calculée en conservant le ratio SVG.
        #

        preview_width = 700

        default_size = renderer.defaultSize()

        if default_size.isValid() and default_size.width() > 0:
            ratio = default_size.height() / default_size.width()

            preview_height = max(
                1,
                int(preview_width * ratio),
            )

        else:
            preview_height = 220

        pixmap = QPixmap(
            preview_width,
            preview_height,
        )

        pixmap.fill(Qt.transparent)

        # ----------------------------------------------------
        # Peinture du SVG dans le pixmap
        # ----------------------------------------------------

        painter = QPainter(pixmap)

        renderer.render(painter)

        painter.end()

        # ----------------------------------------------------
        # Affichage
        # ----------------------------------------------------

        self.preview_label.setPixmap(pixmap)

    # ============================================================
    # SAUVEGARDE
    # ============================================================

    def _save_and_close(self):
        """
        Sauvegarde les paramètres et ferme le dialogue.

        Les anciennes clés présentes dans runtime.json sont
        conservées volontairement.
        """

        # ====================================================
        # TOKEN TALLY
        # ====================================================

        new_token = self.token_field.text().strip()

        if new_token and new_token != get_tally_token():
            save_tally_token(new_token)

            logger.info("Token Tally mis à jour")

        # ====================================================
        # PARAMÈTRES GÉNÉRAUX
        # ====================================================

        self.runtime["workspace"] = self.workspace_field.text().strip()

        self.runtime["libreoffice"] = self.libreoffice_field.text().strip()

        self.runtime["generate_html"] = self.chk_html.isChecked()

        self.runtime["generate_odt"] = self.chk_odt.isChecked()

        self.runtime["debug"] = self.chk_debug.isChecked()

        self.runtime["strategy_threshold"] = self.threshold_field.value()

        # ====================================================
        # PARAMÈTRES GRAPHIQUES
        # ====================================================

        charts = self._chart_settings()

        # ----------------------------------------------------
        # Affichage
        # ----------------------------------------------------

        charts["show_values"] = self.chk_chart_show_values.isChecked()

        charts["show_marker"] = self.chk_chart_show_marker.isChecked()

        charts["show_zero_line"] = self.chk_chart_show_zero_line.isChecked()

        # ----------------------------------------------------
        # Texte
        # ----------------------------------------------------

        charts["label_font_size"] = self.label_font_size.value()

        charts["value_font_size"] = self.value_font_size.value()

        # ----------------------------------------------------
        # Géométrie
        # ----------------------------------------------------

        charts["row_height"] = self.row_height.value()

        charts["bar_height"] = self.bar_height.value()

        charts["fill_height"] = self.fill_height.value()

        charts["zero_line_height"] = self.zero_line_height.value()

        charts["marker_size"] = self.marker_size.value()

        charts["chart_cell_height_cm"] = self.chart_cell_height.value()

        # ====================================================
        # SAUVEGARDE
        # ====================================================

        save_runtime(self.runtime)

        logger.info(
            "runtime.json mis à jour : %s",
            self.runtime,
        )

        # ====================================================
        # WORKSPACE
        # ====================================================

        # Recrée les dossiers nécessaires si le workspace
        # a changé.
        paths.ensure_workspace()

        self.accept()
