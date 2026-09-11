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

import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import get_tally_token, save_tally_token
from ingestion.fetch_tally import check_token_valid
from reporting.chart_style import (
    BAR_COLOR_THRESHOLDS,
    DEFAULT_CHART_SETTINGS,
    GRAPH_MARGIN_PCT,
    LABEL_COL_MIN_CM,
    SCORE_COL_MIN_CM,
    TABLE_TOTAL_WIDTH_MAX_CM,
    TABLE_TOTAL_WIDTH_MIN_CM,
)
from storage.init import load_runtime, save_runtime
from storage.paths import paths
from ui import APP_BUILD, APP_NAME, APP_VERSION
from utils.logger import logger

LEGACY_CHART_KEYS = ("show_x_axis",)
SPINBOX_WIDTH = 130
HAUTEUR_APERCU = 180

def _make_spinbox(cls, value, minimum, maximum, step=1, suffix="", decimals=None, tooltip=None):
    """Crée un QSpinBox/QDoubleSpinBox pré-configuré (largeur, alignement, valeurs)."""
    box = cls()
    box.setFixedWidth(SPINBOX_WIDTH)
    box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    box.setRange(minimum, maximum)
    box.setSingleStep(step)
    if decimals is not None:
        box.setDecimals(decimals)
    if suffix:
        box.setSuffix(suffix)
    if tooltip:
        box.setToolTip(tooltip)
    box.setValue(value)
    return box

def _right_aligned(widget):
    """Enveloppe un widget pour le coller à droite dans une QFormLayout row."""
    container = QWidget()
    box = QHBoxLayout(container)
    box.setContentsMargins(0, 0, 0, 0)
    box.addStretch()
    box.addWidget(widget)
    return container

class PreviewWorker(QThread):
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(
        self, scores, tmp_dir, chart_config=None, column_config=None, parent=None
    ):
        super().__init__(parent)
        self.scores = scores
        self.tmp_dir = tmp_dir
        self.chart_config = chart_config
        self.column_config = column_config

    def run(self):
        try:
            from reporting.preview import generate_preview_png

            png_path = generate_preview_png(
                self.scores,
                self.tmp_dir,
                chart_config=self.chart_config,
                column_config=self.column_config,
            )
            self.finished_ok.emit(png_path)
        except Exception as e:  # noqa: BLE001
            self.finished_error.emit(str(e))


class SettingsDialog(QDialog):
    """Fenêtre de configuration de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configuration")
        self.setMinimumWidth(750)
        self._preview_worker = None
        self._appearance_preview_generated = False

        # ----------------------------------------------------
        # Chargement du runtime actuel
        # ----------------------------------------------------

        self.runtime = load_runtime()

        # ----------------------------------------------------
        # Layout principal
        # ----------------------------------------------------

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ====================================================
        # ONGLET GÉNÉRAL
        # ====================================================

        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        self.tabs.addTab(general_tab, "Général")

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
        self.threshold_field.setFixedWidth(SPINBOX_WIDTH)

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

        self.appearance_tab = self._build_appearance_tab()

        self.tabs.addTab(
            self.appearance_tab,
            "Apparence",
        )
        self.tabs.currentChanged.connect(self._on_tab_changed) # Détection du changement d'onglet


        # ====================================================
        # ONGLET À PROPOS
        # ====================================================

        about_tab = self._build_about_tab()

        self.tabs.addTab(
            about_tab,
            "À propos",
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

    def _stop_preview_worker(self):
        """
        Attend la fin du worker de prévisualisation avant
        de détruire la fenêtre de configuration.
        """
        worker = self._preview_worker
        if worker is not None and worker.isRunning():
            logger.warning("Veuillez patienter, La fenêtre se fermera à la fin de l'opération...")
            QApplication.processEvents()
            worker.wait()
            logger.debug("Preview terminé.")

        self._preview_worker = None

    def closeEvent(self, event):
        self._stop_preview_worker()
        super().closeEvent(event)
        
    def reject(self):
        self._stop_preview_worker()
        super().reject()

    def accept(self):
        self._stop_preview_worker()
        super().accept()


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

#        # ====================================================
#        # GROUPE : TEXTE
#        # ====================================================
#
#        text_group = QGroupBox("Texte")
#        text_form = QFormLayout(text_group)
#
#        # ----------------------------------------------------
#        # Taille des labels
#        # ----------------------------------------------------
#
#        self.label_font_size = QSpinBox()
#        self.label_font_size.setFixedWidth(SPINBOX_WIDTH)
#
#        self.label_font_size.setRange(
#            12,
#            32,
#        )
#
#        self.label_font_size.setSingleStep(1)
#
#        self.label_font_size.setSuffix(" px")
#
#        self.label_font_size.setValue(
#            charts.get(
#                "label_font_size",
#                DEFAULT_CHART_SETTINGS["label_font_size"],
#            )
#        )
#
#        # ----------------------------------------------------
#        # Taille des valeurs
#        # ----------------------------------------------------
#
#        self.value_font_size = QSpinBox()
#        self.value_font_size.setFixedWidth(SPINBOX_WIDTH)
#
#        self.value_font_size.setRange(
#            10,
#            28,
#        )
#
#        self.value_font_size.setSingleStep(1)
#
#        self.value_font_size.setSuffix(" px")
#
#        self.value_font_size.setValue(
#            charts.get(
#                "value_font_size",
#                DEFAULT_CHART_SETTINGS["value_font_size"],
#            )
#        )
#
#        text_form.addRow(
#            "Taille des libellés :",
#            self.label_font_size,
#        )
#
#        text_form.addRow(
#            "Taille des valeurs :",
#            self.value_font_size,
#        )
#
#        layout.addWidget(text_group)

        # ====================================================
        # GROUPE : Tableau
        # ====================================================

        table_group = QGroupBox("Tableau")
        table_form = QFormLayout(table_group)

        # ----------------------------------------------------
        # Bordures du tableau
        # ----------------------------------------------------

        self.border_width = _make_spinbox(
            QDoubleSpinBox,
            charts.get("border_width_pt", DEFAULT_CHART_SETTINGS["border_width_pt"]),
            0.0, 3.0, step=0.5, decimals=1, suffix=" pt",
            tooltip="Épaisseur de la bordure du tableau. 0 = pas de bordure.",
        )

        table_form.addRow("Épaisseur de la bordure :", _right_aligned(self.border_width))
        # ----------------------------------------------------
        self.table_total_width = _make_spinbox(
            QDoubleSpinBox,
            charts.get("table_total_width_cm", DEFAULT_CHART_SETTINGS["table_total_width_cm"]),
            TABLE_TOTAL_WIDTH_MIN_CM, TABLE_TOTAL_WIDTH_MAX_CM, step=0.5, suffix=" cm",
        )

        self.label_col_width = _make_spinbox(
            QDoubleSpinBox,
            charts.get("label_col_width_cm", DEFAULT_CHART_SETTINGS["label_col_width_cm"]),
            LABEL_COL_MIN_CM, 10.0, step=0.1, suffix=" cm",
        )

        self.score_col_width = _make_spinbox(
            QDoubleSpinBox,
            charts.get("score_col_width_cm", DEFAULT_CHART_SETTINGS["score_col_width_cm"]),
            SCORE_COL_MIN_CM, 5.0, step=0.1, suffix=" cm",
        )

        self.graph_col_width_preview = QLabel()  # lecture seule, calculé

        table_form.addRow("Largeur totale du tableau :", _right_aligned(self.table_total_width))
        table_form.addRow("Largeur colonne Libellé :", _right_aligned(self.label_col_width))
        table_form.addRow("Largeur colonne Score :", _right_aligned(self.score_col_width))
        table_form.addRow(
            "Largeur colonne Graphique (calculée) :",
            self.graph_col_width_preview,
        )

        layout.addWidget(table_group)

        # ====================================================
        # GROUPE : BARRES
        # ====================================================

        bars_group = QGroupBox("Barres")
        bars_form = QFormLayout(bars_group)

        # ----------------------------------------------------
        # Hauteur de la cellule contenant chaque graphique.
        # ----------------------------------------------------

        self.chart_cell_height = _make_spinbox(
            QDoubleSpinBox,
            charts.get("chart_cell_height_cm", DEFAULT_CHART_SETTINGS["chart_cell_height_cm"]),
            0.8, 3.0, step=0.1, decimals=1, suffix=" cm",
            tooltip=(
                "Hauteur de la cellule contenant chaque graphique.\n"
                "Sous 0,8 cm, le texte des autres colonnes devient trop serré."
            ),
        )
        # ----------------------------------------------------
        # Piste grise
        # ----------------------------------------------------

        self.bar_height = _make_spinbox(
            QSpinBox,
            charts.get("bar_height", DEFAULT_CHART_SETTINGS["bar_height"]),
            4, 24, suffix=" px",
            tooltip="Épaisseur de la piste grise.",
        )

        # ----------------------------------------------------
        # Barre colorée
        # ----------------------------------------------------

        self.fill_height = _make_spinbox(
            QSpinBox,
            charts.get("fill_height", DEFAULT_CHART_SETTINGS["fill_height"]),
            2, 20, suffix=" px",
            tooltip="Épaisseur de la barre colorée.",
        )
        # ----------------------------------------------------
        # Ligne zéro
        # ----------------------------------------------------

        self.zero_line_height = _make_spinbox(
            QSpinBox,
            charts.get("zero_line_height", DEFAULT_CHART_SETTINGS["zero_line_height"]),
            10, 35, suffix=" px",
            tooltip="Hauteur de la ligne centrale.",
        )

        # ----------------------------------------------------
        # Marqueur
        # ----------------------------------------------------

        self.marker_size = _make_spinbox(
            QSpinBox,
            charts.get("marker_size", DEFAULT_CHART_SETTINGS["marker_size"]),
            8, 24, suffix=" px",
            tooltip="Diamètre du marqueur.",
        )

        bars_form.addRow("Espace vertical :", _right_aligned(self.chart_cell_height))
        bars_form.addRow("Épaisseur de la piste :", _right_aligned(self.bar_height))
        bars_form.addRow("Épaisseur de la barre :", _right_aligned(self.fill_height))
        bars_form.addRow("Hauteur de la ligne centrale :", _right_aligned(self.zero_line_height))
        bars_form.addRow("Taille du marqueur :", _right_aligned(self.marker_size))

        layout.addWidget(bars_group)

        # ====================================================
        # APERÇU
        # ====================================================

        preview_group = QGroupBox("Aperçu")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_container = QWidget()
        self.preview_container.setStyleSheet(
            """
            QWidget {
                background: white;
                border: 1px solid #e7e5e4;
                border-radius: 4px;
            }
            """
        )
        self.preview_container.setFixedHeight(HAUTEUR_APERCU)

        self.preview_container_layout = QVBoxLayout(self.preview_container)

        self.btn_generate_preview = QPushButton("🔄 Générer l'aperçu")
        self.btn_generate_preview.clicked.connect(self._generate_real_preview)
        preview_layout.addWidget(self.btn_generate_preview)
        preview_layout.addWidget(self.preview_container)

        # ====================================================
        # RESTAURATION DES VALEURS PAR DÉFAUT
        # ====================================================

        self.btn_restore_defaults = QPushButton("Restaurer les valeurs par défaut")
        self.btn_restore_defaults.clicked.connect(self._restore_chart_defaults)
        preview_layout.addWidget(self.btn_restore_defaults)

        # ====================================================
        # CONNEXIONS POUR L'APERÇU
        # ====================================================

        for widget in (
            self.table_total_width,
            self.label_col_width,
            self.score_col_width,
        ):
            widget.valueChanged.connect(self._update_column_preview)

        self._update_column_preview()
        #self._generate_real_preview()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)

        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)
        outer_layout.addWidget(preview_group)

        return outer

    def _on_tab_changed(self, index: int):
        """
        Génère l'aperçu Apparence uniquement lors de sa première ouverture.
        """
        if self.tabs.widget(index) is self.appearance_tab and not self._appearance_preview_generated:
                self._generate_real_preview()
                self._appearance_preview_generated = True

    # ============================================================
    # ONGLET "À propos"
    # ============================================================

    def _build_about_tab(self) -> QWidget:
        tab = QWidget()

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ------------------------------------------------
        # Bandeau / logo de l'application
        # ------------------------------------------------

        banner = QFrame()
        banner.setFixedHeight(180)
        banner.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 10px;
            }
        """)

        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(20, 20, 20, 15)

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 36px;
                font-weight: bold;
            }
        """)

        subtitle = QLabel("Application de gestion de rapports de bilans sensoriel Dunn2.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-size: 16px;
            }
        """)

        version = QLabel(
            f"Version {APP_VERSION} • Build {APP_BUILD}"
        )
        version.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 12px;
            }
        """)

        banner_layout.addStretch()
        banner_layout.addWidget(title)
        banner_layout.addWidget(subtitle)
        banner_layout.addStretch()
        banner_layout.addWidget(version)

        layout.addWidget(banner)

        # ------------------------------------------------
        # Informations
        # ------------------------------------------------

        info = QLabel(
            "© 2026 Alex"
        )

        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)

        layout.addWidget(info)
        layout.addStretch()

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

#        self.label_font_size.setValue(DEFAULT_CHART_SETTINGS["label_font_size"])
#        self.value_font_size.setValue(DEFAULT_CHART_SETTINGS["value_font_size"])

        self.bar_height.setValue(DEFAULT_CHART_SETTINGS["bar_height"])

        self.fill_height.setValue(DEFAULT_CHART_SETTINGS["fill_height"])

        self.zero_line_height.setValue(DEFAULT_CHART_SETTINGS["zero_line_height"])

        self.marker_size.setValue(DEFAULT_CHART_SETTINGS["marker_size"])

        self.chart_cell_height.setValue(DEFAULT_CHART_SETTINGS["chart_cell_height_cm"])

        self.border_width.setValue(DEFAULT_CHART_SETTINGS["border_width_pt"])

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

    def _generate_real_preview(self):
        test_scores = {
            "quadrants": {
                "recherche": {"z": 0.3},
                "evitement": {"z": -1.2},
                "sensibilite": {"z": 2.3},
                "enregistrement": {"z": -2.8},
            },
        }

        chart_config = {
            "show_values": self.chk_chart_show_values.isChecked(),
            "show_marker": self.chk_chart_show_marker.isChecked(),
            "show_zero_line": self.chk_chart_show_zero_line.isChecked(),
#            "label_font_size": self.label_font_size.value(),
#            "value_font_size": self.value_font_size.value(),
            "bar_height": self.bar_height.value(),
            "fill_height": self.fill_height.value(),
            "zero_line_height": self.zero_line_height.value(),
            "marker_size": self.marker_size.value(),
        }

        column_config = {
            "ui": {
                "charts": {
                    "table_total_width_cm": self.table_total_width.value(),
                    "label_col_width_cm": self.label_col_width.value(),
                    "score_col_width_cm": self.score_col_width.value(),
                    "border_width_pt": self.border_width.value(),
                    "chart_cell_height_cm": self.chart_cell_height.value(),
                }
            }
        }

        tmp_dir = Path(tempfile.gettempdir()) / "profil_sensoriel_preview"

        self.btn_generate_preview.setEnabled(False)
        self.btn_generate_preview.setText("⏳ Génération en cours…")
        logger.info("Génération en cours...  patientez...", extra={"status": True})

        while self.preview_container_layout.count():
            item = self.preview_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.preview_container_layout.addWidget(QLabel("Génération en cours…"))

        self._preview_worker = PreviewWorker(
            test_scores, tmp_dir, chart_config, column_config
        )
        self._preview_worker.finished_ok.connect(self._on_preview_ready)
        self._preview_worker.finished_error.connect(self._on_preview_error)
        self._preview_worker.start()

    def _on_preview_ready(self, png_path):
        self.btn_generate_preview.setEnabled(True)
        self.btn_generate_preview.setText("🔄 Générer l'aperçu")

        while self.preview_container_layout.count():
            item = self.preview_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if png_path is None:
            self.preview_container_layout.addWidget(QLabel("Échec génération aperçu"))
            return

        pixmap = QPixmap(str(png_path))
        crop_height = min(400, pixmap.height())
        cropped = pixmap.copy(0, 0, pixmap.width(), crop_height)

        label = QLabel()
        label.setPixmap(cropped.scaledToWidth(650, Qt.SmoothTransformation))
        self.preview_container_layout.addWidget(label)

    def _on_preview_error(self, message):
        self.btn_generate_preview.setEnabled(True)
        self.btn_generate_preview.setText("🔄 Générer l'aperçu")
        logger.error("Erreur génération aperçu: %s", message)

        while self.preview_container_layout.count():
            item = self.preview_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.preview_container_layout.addWidget(QLabel(f"Erreur : {message}"))

    def _update_column_preview(self):
        total = self.table_total_width.value()
        label = self.label_col_width.value()
        score = self.score_col_width.value()
        graph = total - label - score
        self.graph_col_width_preview.setText(f"{graph:.1f} cm")

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

        charts["border_width_pt"] = self.border_width.value()

        charts["table_total_width_cm"] = self.table_total_width.value()
        charts["label_col_width_cm"] = self.label_col_width.value()
        charts["score_col_width_cm"] = self.score_col_width.value()

        # ----------------------------------------------------
        # Texte
        # ----------------------------------------------------

#        charts["label_font_size"] = self.label_font_size.value()
#        charts["value_font_size"] = self.value_font_size.value()

        # ----------------------------------------------------
        # Géométrie
        # ----------------------------------------------------

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
