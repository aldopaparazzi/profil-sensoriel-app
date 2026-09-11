# ui_progress_dialog.py
"""
Popup de progression avec mode "détails" déroulant (logs en direct).

Style inspiré du gestionnaire de mise à jour de Linux Mint :
- Mode réduit : barre + message principal
- Mode détails : affiche l'historique des logs en direct
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class ProgressDialog(QDialog):
    """Popup de progression avec logs optionnels (déroulants)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Récupération des formulaires")
        self.setMinimumWidth(500)
        self.setMinimumHeight(140)
        self.expanded = False

        layout = QVBoxLayout(self)

        # --------
        # Message
        # --------
        self.label_message = QLabel("Connexion à Tally...")
        layout.addWidget(self.label_message)

        # --------
        # Barre
        # --------
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indéterminé
        layout.addWidget(self.progress_bar)

        # --------
        # Bouton détails + fermeture
        # --------
        button_row = QHBoxLayout()

        self.btn_details = QPushButton("Détails ▼")
        self.btn_details.setMaximumWidth(100)
        self.btn_details.clicked.connect(self._toggle_details)
        button_row.addWidget(self.btn_details)

        button_row.addStretch()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setMaximumWidth(80)
        self.btn_cancel.clicked.connect(self.reject)
        button_row.addWidget(self.btn_cancel)

        layout.addLayout(button_row)

        # --------
        # Logs (caché par défaut)
        # --------
        self.text_logs = QPlainTextEdit()
        self.text_logs.setReadOnly(True)
        self.text_logs.setStyleSheet(
            "background:#111; color:#ddd; font-family: Consolas, monospace; font-size: 9pt;"
        )
        self.text_logs.setMaximumHeight(200)
        self.text_logs.setVisible(False)
        layout.addWidget(self.text_logs)

        # self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def set_message(self, message: str):
        """Met à jour le message principal."""
        self.label_message.setText(message)

    def append_log(self, line: str):
        """Ajoute une ligne aux logs + scrolle en bas."""
        self.text_logs.appendPlainText(line)
        # Scroll to bottom
        bar = self.text_logs.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _toggle_details(self):
        """Affiche/masque les logs."""
        self.expanded = not self.expanded

        if self.expanded:
            self.text_logs.setVisible(True)
            self.btn_details.setText("Détails ▲")
            self.setMinimumHeight(400)
        else:
            self.text_logs.setVisible(False)
            self.btn_details.setText("Détails ▼")
            self.setMinimumHeight(140)

    def done(self, result):
        """Au fermeture, reset les dimensions."""
        self.setMinimumHeight(140)
        super().done(result)
