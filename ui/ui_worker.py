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

from PySide6.QtCore import QThread, Signal

from main import import_forms


class FetchWorker(QThread):
    """Exécute import_forms() en arrière-plan."""

    finished_ok = Signal(int)
    finished_error = Signal(str)

    def __init__(self, force_refresh: bool = False, parent=None):
        super().__init__(parent)
        self.force_refresh = force_refresh

    def run(self):
        try:
            count = import_forms(self.force_refresh)
            self.finished_ok.emit(count or 0)
        except Exception as e:  # noqa: BLE001
            self.finished_error.emit(str(e))
