# ui\ui_worker.py
"""
Exécute le pipeline (récupération Tally + traitement) dans un thread séparé.

Pourquoi : si le pipeline tourne dans le thread principal (celui de l'UI),
Qt ne peut pas redessiner la fenêtre pendant l'exécution -> la status bar
ne se met à jour qu'à la toute fin, d'un coup, au lieu d'afficher chaque
étape en direct.

Les logs (via les signaux Qt de ui_logging.py) fonctionnent automatiquement
entre threads : Qt les met en file d'attente et les délivre au thread
principal sans rien à faire de plus.
"""

from threading import Event

from PySide6.QtCore import QMutex, QThread, QWaitCondition, Signal

from main import import_forms
from utils.logger import logger


class FetchWorker(QThread):
    """Exécute import_forms() en arrière-plan."""

    finished_ok = Signal(int)
    finished_error = Signal(str)
    request_token = Signal()

    def __init__(
        self,
        force_refresh: bool = False,
        token_callback=None,
        parent=None,
    ):
        super().__init__(parent)
        self.force_refresh = force_refresh
        self.token_callback = token_callback

        self.token = None
        self.token_event = Event()

    def provide_token(self, token):
        self.token = token
        self.token_event.set()

    def ask_token(self):
        self.token = None
        self.token_event.clear()

        self.request_token.emit()

        self.token_event.wait()

        return self.token


    def run(self):
        
        try:
            count = import_forms(
                self.force_refresh,
                request_token=self.ask_token,
            )


            self.finished_ok.emit(count or 0)
        except Exception as e:  # noqa: BLE001
            self.finished_error.emit(str(e))
