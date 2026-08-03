# ui_logging.py
"""
Pont entre le logger applicatif (utils.logger) et l'interface Qt.

Fournit :
- QtLogHandler     : handler logging -> signal Qt (thread-safe)
- ClickableStatusBar : QStatusBar qui émet un signal au clic
- LogConsoleDialog : fenêtre "console" affichant l'historique en direct
- StatusBarLogger  : orchestration des 3 éléments ci-dessus

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

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QStatusBar, QDialog, QVBoxLayout, QPlainTextEdit

from utils.logger import logger

MAX_HISTORY = 1000  # nb de lignes conservées pour la console


# ==========================================================
# Signal Qt (thread-safe) alimenté par le handler logging
# ==========================================================
class _LogSignal(QObject):
    """
    Signal émis par le QtLogHandler à chaque log.
    Le signal traverse la boucle d'évènements Qt -> thread-safe,
    même si le log vient d'un thread secondaire.
    """

    new_record = Signal(str, int, bool)  # message formaté, levelno, is_status

    def log(self, message, levelno):
        if levelno == 10:  # DEBUG
            logger.debug(message)
        elif levelno == 20:  # INFO
            logger.info(message)
        elif levelno == 30:  # WARNING
            logger.warning(message)
        elif levelno == 40:  # ERROR
            logger.error(message)
        elif levelno == 50:  # CRITICAL
            logger.critical(message)


class QtLogHandler(logging.Handler):
    """
    Handler logging standard qui émet un signal Qt à chaque log.
    Le signal traverse la boucle d'évènements Qt -> thread-safe,
    même si le log vient d'un thread secondaire.

    "is_status" distingue les messages "étape" (destinés à la status bar)
    des messages normaux (console uniquement). Pour marquer un message :

        logger.info("Téléchargement des données", extra={"status": True})
    """

    def __init__(self, level=logging.INFO):
        super().__init__(level)
        self.signals = _LogSignal()
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S")
        )

    def emit(self, record):
        try:
            msg = self.format(record)
        except Exception:  # noqa: BLE001
            msg = record.getMessage()
        is_status = getattr(record, "status", False)
        self.signals.new_record.emit(msg, record.levelno, is_status)


# ==========================================================
# Barre de statut cliquable
# ==========================================================
class ClickableStatusBar(QStatusBar):
    """Barre de statut standard + signal `clicked` au clic."""

    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ==========================================================
# Fenêtre console (historique complet, live)
# ==========================================================
class LogConsoleDialog(QDialog):
    """Affiche l'historique complet des logs, mis à jour en direct."""

    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Console")
        self.resize(800, 400)

        layout = QVBoxLayout(self)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet(
            "background:#111; color:#ddd; font-family: Consolas, monospace;"
        )
        layout.addWidget(self.text)

        for line in history:
            self.text.appendPlainText(line)
        self._scroll_to_bottom()

    def append_line(self, message: str):
        self.text.appendPlainText(message)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        bar = self.text.verticalScrollBar()
        bar.setValue(bar.maximum())


# ==========================================================
# Orchestration
# ==========================================================
LEVEL_COLORS = {
    logging.DEBUG: "gray",
    logging.INFO: "white",
    logging.WARNING: "#f39c12",
    logging.ERROR: "#e74c3c",
    logging.CRITICAL: "#e74c3c",
}


class StatusBarLogger:
    """
    Branche un QtLogHandler sur un logger Python et alimente :
    - une ClickableStatusBar (1 ligne, la plus récente)
    - un LogConsoleDialog (historique complet, ouvert au clic sur la barre)
    """

    def __init__(self, main_window, logger: logging.Logger, level=logging.INFO):
        self.main_window = main_window
        self.history = deque(maxlen=MAX_HISTORY)
        self.console_dialog = None

        self.status_bar = ClickableStatusBar()
        self.status_bar.setToolTip("Cliquer pour voir la console complète")
        main_window.setStatusBar(self.status_bar)
        self.status_bar.clicked.connect(self.show_console)

        self.handler = QtLogHandler(level)
        self.handler.signals.new_record.connect(self._on_record)
        logger.addHandler(self.handler)

    def _on_record(self, message: str, levelno: int, is_status: bool):
        self.history.append(message)

        # Status bar : uniquement les messages "étape" (extra={"status": True})
        # + toujours les warnings/erreurs (trop important pour les rater)
        if is_status or levelno >= logging.WARNING:
            self.status_bar.showMessage(message, 8000)  # reste affiché 8s
            color = LEVEL_COLORS.get(levelno, "white")
            self.status_bar.setStyleSheet(f"color: {color};")

        # Console : tout, sans exception
        if self.console_dialog is not None:
            self.console_dialog.append_line(message)

    def show_console(self):
        if self.console_dialog is None:
            self.console_dialog = LogConsoleDialog(list(self.history), self.main_window)
            self.console_dialog.finished.connect(self._on_console_closed)
        self.console_dialog.show()
        self.console_dialog.raise_()
        self.console_dialog.activateWindow()

    def _on_console_closed(self, _result):
        self.console_dialog = None
