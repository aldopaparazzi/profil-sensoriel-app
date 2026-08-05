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

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from config.settings import get_tally_token, save_tally_token
from ingestion.fetch_tally import check_token_valid
from storage.init import load_runtime, save_runtime
from storage.paths import paths
from utils.logger import logger


class SettingsDialog(QDialog):
    """Fenêtre de configuration de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setMinimumWidth(520)

        self.runtime = load_runtime()

        layout = QVBoxLayout(self)
        form = QFormLayout()

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

        layout.addLayout(form)

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
        layout.addWidget(self.chk_html)
        layout.addWidget(self.chk_odt)
        layout.addWidget(self.chk_debug)

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
        self.token_field.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )

    def _browse_workspace(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier data perso", self.workspace_field.text()
        )
        if folder:
            self.workspace_field.setText(folder)

    def _browse_libreoffice(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Choisir soffice.exe", self.libreoffice_field.text()
        )
        if file:
            self.libreoffice_field.setText(file)

    def _test_token(self):
        token = self.token_field.text().strip()
        if not token:
            QMessageBox.warning(self, "Token", "Champ vide.")
            return
        ok = check_token_valid(token)
        if ok:
            QMessageBox.information(self, "Token", "✅ Token valide.")
        else:
            QMessageBox.critical(self, "Token", "❌ Token invalide.")

    # ======================================================
    # Sauvegarde
    # ======================================================

    def _save_and_close(self):
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
        save_runtime(self.runtime)
        logger.info("runtime.json mis à jour : %s", self.runtime)

        # Recrée les dossiers si le workspace a changé
        paths.ensure_workspace()

        self.accept()
