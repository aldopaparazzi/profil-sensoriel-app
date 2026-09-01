# ui_logging.py

"""
Pont entre le logger applicatif (utils.logger) et l'interface Qt.

Fournit :
- QtLogHandler       : handler logging -> signal Qt (thread-safe)
- ClickableStatusBar : QStatusBar qui émet un signal au clic
- LogConsoleDialog   : fenêtre "console" affichant l'historique en direct
- StatusBarLogger    : orchestration des 3 éléments ci-dessus

Fonctionnalités de la console :
- affichage des logs en direct ;
- effacement de la console ;
- copie des logs ;
- enregistrement des logs dans un fichier.

Utilisation dans ui.py :

    from ui_logging import StatusBarLogger
    from utils.logger import logger

    class ReportViewer(QMainWindow):
        def __init__(self):
            super().__init__()
            self.status_logger = StatusBarLogger(self, logger)
            ...
"""

import logging
from collections import deque
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
)

MAX_HISTORY = 1000  # nombre maximum de lignes conservées


# ==========================================================
# Signal Qt
# ==========================================================


class _LogSignal(QObject):
    new_record = Signal(str, int, bool)
    # message formaté, levelno, is_status


# ==========================================================
# Handler logging -> Qt
# ==========================================================


class QtLogHandler(logging.Handler):
    """
    Handler logging standard qui émet un signal Qt à chaque log.

    Le signal traverse la boucle d'évènements Qt et permet
    de recevoir les logs provenant également de threads secondaires.

    "is_status" distingue les messages destinés à la status bar.

    Exemple :

        logger.info(
            "Téléchargement des données",
            extra={"status": True},
        )
    """

    def __init__(self, level=logging.INFO):
        super().__init__(level)

        self.signals = _LogSignal()

        self.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                "%H:%M:%S",
            )
        )

    def emit(self, record):
        try:
            msg = self.format(record)
        except Exception:  # noqa: BLE001
            msg = record.getMessage()

        is_status = getattr(record, "status", False)

        self.signals.new_record.emit(
            msg,
            record.levelno,
            is_status,
        )


# ==========================================================
# Barre de statut cliquable
# ==========================================================


class ClickableStatusBar(QStatusBar):
    """Barre de statut standard + signal clicked."""

    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ==========================================================
# Fenêtre console
# ==========================================================


class LogConsoleDialog(QDialog):
    """
    Affiche l'historique complet des logs.

    Fonctionnalités :
        - affichage en direct ;
        - effacer ;
        - copier ;
        - enregistrer.
    """

    def __init__(self, history, parent=None):
        super().__init__(parent)

        self.history = history

        self.setWindowTitle("Console")
        self.resize(900, 500)

        # --------------------------------------------------
        # Layout principal
        # --------------------------------------------------

        layout = QVBoxLayout(self)

        # --------------------------------------------------
        # Barre de boutons
        # --------------------------------------------------

        buttons_layout = QHBoxLayout()

        self.clear_button = QPushButton("Effacer")
        self.copy_button = QPushButton("Copier")
        self.save_button = QPushButton("Enregistrer")

        self.clear_button.setToolTip("Effacer tous les logs")
        self.copy_button.setToolTip("Copier tous les logs")
        self.save_button.setToolTip("Enregistrer les logs dans un fichier")

        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.save_button)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # --------------------------------------------------
        # Zone de texte
        # --------------------------------------------------

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)

        self.text.setStyleSheet(
            """
            QPlainTextEdit {
                background: #111;
                color: #ddd;
                font-family: Consolas, "Courier New", monospace;
                font-size: 10pt;
            }
            """
        )

        layout.addWidget(self.text)

        # --------------------------------------------------
        # Connexions
        # --------------------------------------------------

        self.clear_button.clicked.connect(self.clear_logs)
        self.copy_button.clicked.connect(self.copy_logs)
        self.save_button.clicked.connect(self.save_logs)

        # --------------------------------------------------
        # Historique initial
        # --------------------------------------------------

        for line in history:
            self.text.appendPlainText(line)

        self._scroll_to_bottom()

    # ======================================================
    # Ajout d'un log
    # ======================================================

    def append_line(self, message: str):
        """
        Ajoute une ligne à la console.
        """

        self.text.appendPlainText(message)
        self._scroll_to_bottom()

    # ======================================================
    # Effacer
    # ======================================================

    def clear_logs(self):
        """
        Efface l'affichage et l'historique en mémoire.
        """

        self.text.clear()

        # self.history est le deque partagé avec StatusBarLogger
        self.history.clear()

    # ======================================================
    # Copier
    # ======================================================

    def copy_logs(self):
        """
        Copie tous les logs dans le presse-papiers.
        """

        QApplication = __import__(
            "PySide6.QtWidgets",
            fromlist=["QApplication"],
        ).QApplication

        clipboard = QApplication.clipboard()

        clipboard.setText(self.text.toPlainText())

    # ======================================================
    # Enregistrer
    # ======================================================

    def save_logs(self):
        """
        Enregistre les logs dans un fichier texte.
        """

        default_name = "profil_sensoriel.log"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer les logs",
            str(Path.home() / default_name),
            "Fichiers log (*.log);;Fichiers texte (*.txt);;Tous les fichiers (*)",
        )

        if not file_path:
            return

        try:
            Path(file_path).write_text(
                self.text.toPlainText(),
                encoding="utf-8",
            )

        except OSError as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'enregistrer les logs :\n\n{e}",
            )
            return

        QMessageBox.information(
            self,
            "Logs enregistrés",
            f"Les logs ont été enregistrés dans :\n\n{file_path}",
        )

    # ======================================================
    # Scroll
    # ======================================================

    def _scroll_to_bottom(self):
        bar = self.text.verticalScrollBar()
        bar.setValue(bar.maximum())


# ==========================================================
# Couleurs
# ==========================================================

LEVEL_COLORS = {
    logging.DEBUG: "gray",
    logging.INFO: "white",
    logging.WARNING: "#f39c12",
    logging.ERROR: "#e74c3c",
    logging.CRITICAL: "#e74c3c",
}


# ==========================================================
# Orchestration
# ==========================================================


class StatusBarLogger:
    """
    Branche un QtLogHandler sur un logger Python et alimente :

    - ClickableStatusBar
    - LogConsoleDialog
    - optionnellement une ProgressDialog

    La console conserve jusqu'à MAX_HISTORY lignes.
    """

    def __init__(
        self,
        main_window,
        logger: logging.Logger,
        level=logging.INFO,
    ):
        self.main_window = main_window

        # IMPORTANT :
        # le même deque est partagé avec LogConsoleDialog.
        self.history = deque(maxlen=MAX_HISTORY)

        self.console_dialog = None
        self.progress_dialog = None

        # --------------------------------------------------
        # Status bar
        # --------------------------------------------------

        self.status_bar = ClickableStatusBar()

        self.status_bar.setToolTip("Cliquer pour voir la console complète")

        main_window.setStatusBar(self.status_bar)

        self.status_bar.clicked.connect(self.show_console)

        # --------------------------------------------------
        # Handler Qt
        # --------------------------------------------------

        self.handler = QtLogHandler(level)

        self.handler.signals.new_record.connect(self._on_record)

        logger.addHandler(self.handler)

    # ======================================================
    # Progress dialog
    # ======================================================

    def set_progress_dialog(self, progress_dialog):
        """
        Branche une popup de progression.
        """

        self.progress_dialog = progress_dialog

    # ======================================================
    # Réception des logs
    # ======================================================

    def _on_record(
        self,
        message: str,
        levelno: int,
        is_status: bool,
    ):
        self.history.append(message)

        # --------------------------------------------------
        # Status bar
        # --------------------------------------------------

        if is_status or levelno >= logging.WARNING:
            self.status_bar.showMessage(
                message,
                8000,
            )

            color = LEVEL_COLORS.get(
                levelno,
                "white",
            )

            self.status_bar.setStyleSheet(f"color: {color};")

        # --------------------------------------------------
        # Console
        # --------------------------------------------------

        if self.console_dialog is not None:
            self.console_dialog.append_line(message)

        # --------------------------------------------------
        # Progress dialog
        # --------------------------------------------------

        if self.progress_dialog is not None:
            self.progress_dialog.append_log(message)

            if is_status:
                self.progress_dialog.set_message(message)

    # ======================================================
    # Afficher console
    # ======================================================

    def show_console(self):
        """
        Affiche la console.

        Si elle n'existe pas encore, elle est créée
        avec l'historique actuel.
        """

        if self.console_dialog is None:
            self.console_dialog = LogConsoleDialog(
                self.history,
                self.main_window,
            )

            self.console_dialog.finished.connect(self._on_console_closed)

        self.console_dialog.show()
        self.console_dialog.raise_()
        self.console_dialog.activateWindow()

    # ======================================================
    # Fermeture console
    # ======================================================

    def _on_console_closed(self, _result):
        self.console_dialog = None
