# ui.py
"""
Application Qt pour consulter les rapports HTML du Profil Sensoriel 2.

Version 1.5
date: 2026-09-11

Ce programme permet de consulter les rapports HTML générés par le Profil Sensoriel 2.
Il est prévu pour être utilisé sur un ordinateur local, sans serveur web.


"""

import json  # Importe le module JSON pour lire et écrire des fichiers JSON  # noqa: I001
import logging  # Importe le module logging pour gérer les messages de journalisation
import sys  # Importe le module système Python pour gérer les arguments et la fermeture de l'application
from ui.ui_home import HomePage

# Permet de manipuler facilement les chemins de fichiers et dossiers
from pathlib import (
    Path,  # Importe les classes et méthodes nécessaires pour gérer les chemins de fichiers et dossiers de manière portable
)

# QUrl sert à créer des URLs compatibles avec Qt (ici pour charger un fichier HTML local)
from PySide6.QtCore import (
    Qt,  # Qt est le module central de Qt,
    QUrl,  # QUrl permet de manipuler des URLs,
    QTimer, # QTimer permet de créer des temporisateurs pour exécuter du code après un délai ou à intervalles réguliers
)
from PySide6.QtGui import (
    QIcon,  # Permet de définir une icône pour la fenêtre principale
)

# Composant Qt capable d'afficher une page web HTML dans une fenêtre native
from PySide6.QtWebEngineWidgets import (
    QWebEngineView,  # Fenêtre Web qui affiche le contenu du rapport HTML
)

# Widgets Qt utilisés pour construire l'interface graphique
from PySide6.QtWidgets import (
    QApplication,  # Objet principal qui gère l'application Qt
    QHBoxLayout,  # Gestionnaire de mise en page horizontale
    QLineEdit,  # Champ de saisie texte pour la recherche
    QListWidget,  # Liste graphique avec éléments sélectionnables
    QListWidgetItem,  # Élément individuel dans une QListWidget
    QMainWindow,  # Fenêtre principale d'une application Qt
    QPushButton,  # Bouton cliquable Qt
    QSplitter,  # Permet de séparer deux widgets avec une barre ajustable
    QVBoxLayout,  # Gestionnaire de mise en page verticale
    QWidget,  # Widget de base Qt
    QFileDialog,  # Fenêtre de dialogue pour sélectionner des fichiers ou dossiers
    QMessageBox,  # Fenêtre de dialogue pour afficher des messages à l'utilisateur
    QInputDialog,  # Fenêtre de dialogue pour saisir des informations
    QProgressBar,  # Fenêtre de dialogue pour afficher une barre de progression
    QDialog,  # Fenêtre de dialogue modale Qt
    QStackedWidget, # Permet d'empiler plusieurs widgets et d'en afficher un à la fois
)

# from config.settings import load_config, sauvegarder_token
# from ingestion.fetch_tally import check_token_valid
# from main import import_forms

# from reporting.html import generate_html_report
from reporting.odt import generate_bilan, open_odt, is_locked
from storage.paths import paths
from storage.init import load_runtime, save_runtime, ensure_env
from ui.ui_logging import StatusBarLogger
from ui.ui_progress_dialog import ProgressDialog
from ui.ui_settings import SettingsDialog
from ui.ui_splash import show_splash
from ui.ui_worker import FetchWorker
from utils.logger import logger, configure_logging
from reporting.bilan_odt import build_bilan_odt
from reporting.bilan_strategies import select_strategy_candidates
from ui.ui_strategies_dialog import StrategiesDialog


def load_report_metadata(html_file):
    """
    Charge les informations associées
    à un rapport HTML.
    Convention :
    un rapport HTML "dupont_jean.html"
    possède un fichier associé "dupont_jean.json"
    """

    json_file = paths.json_dir / f"{html_file.stem}.json"
    if not json_file.exists():
        return None
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

def reload_reports():
    """
    Recharge la liste des rapports HTML.
    Re-sélectionne le rapport actif si possible.
    """
    current_path = window.current_report

    window.report_list.clear()
    window.load_reports()

    if current_path is None:
        return

    for index in range(window.report_list.count()):
        item = window.report_list.item(index)
        if item.data(Qt.UserRole) == current_path:
            window.report_list.setCurrentItem(item)
            break

def create_tooltip(data):
    """
    Transforme les données JSON
    en texte lisible.
    """

    if not data:
        return "Informations indisponibles"
    patient = data.get("patient", {})
    lines = []
    lines.append("Profil Sensoriel 2")
    lines.append(f"\nÉvaluation : {patient.get('evaluation_date', '')[:10]}")
    lines.append(f"Naissance : {patient.get('birth_date', '')}")
    lines.append(f"Âge : {patient.get('age', '')} ans")
    lines.append(f"Niveau : {patient.get('niveau', '')}")
    lines.append("\nDomaines :")
    domains = data.get("domains", {})
    for name, values in domains.items():
        z = values.get("z")
        if z is not None and abs(z) > 0.5:
            lines.append(f"• {name} : {z:+.2f} DS")
            """ Affiche uniquement les écarts significatifs
            (supérieurs à 0,5 écart-type) afin d'éviter
            une infobulle trop longue.
            """
    quadrants = data.get("quadrants", {})
    lines.append("\nQuadrants :")
    for name, values in quadrants.items():
        z = values.get("z")
        if z is not None and abs(z) > 0.5:
            lines.append(f"• {name} : {z:+.2f} DS")
    return "\n".join(lines)

# Création d'une classe représentant notre fenêtre principale
# Elle hérite de QMainWindow pour avoir une fenêtre Qt complète
class ReportViewer(QMainWindow):
    """Fenêtre principale de consultation des profils sensoriels.
    """

    # Constructeur appelé automatiquement lors de la création de la fenêtre
    def __init__(self):

        # ============================================================
        # Initialisation de la fenêtre
        # ============================================================

        super().__init__()

        runtime = load_runtime()

        # Configure le niveau de journalisation avant de créer
        # les composants qui utilisent les logs.
        configure_logging(runtime.get("debug", False))

        # Branche le système de logs sur la barre d'état.
        self.status_logger = StatusBarLogger(
            self,
            logging.getLogger(),
        )

        # Configure la barre de progression dans la barre d'état.
        self._setup_progress_bar()

        # Vérifie qu'un espace de travail utilisateur existe.
        self.ensure_workspace()

        self.current_report = None

        self.setWindowTitle("Profil Sensoriel")

        if paths.favicon_path.exists():
            self.setWindowIcon(QIcon(str(paths.favicon_path)))

        self.resize(1400, 900)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("font-size: 16px;")

        # ============================================================
        # Zone de contenu : accueil / rapport HTML
        # ============================================================

        # Navigateur HTML intégré.
        self.viewer = QWebEngineView()

        # Évite que Qt repeigne inutilement l'arrière-plan
        # lors de l'apparition de la surface Chromium.
        self.viewer.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.viewer.setAttribute(Qt.WA_NoSystemBackground, True)

        # Signal émis lorsque l'impression PDF est terminée.
        self.viewer.pdfPrintingFinished.connect(
            self._on_pdf_printing_finished
        )

        # Initialise le moteur WebEngine avant que l'utilisateur
        # ouvre son premier rapport.
        self.viewer.setHtml(
            "<html><body></body></html>"
        )


        # Page d'accueil.
        self.home_page = HomePage(self)

        # Connexion des boutons de la page d'accueil.
        self.home_page.fetch_requested.connect(self.fetch_reports)
        self.home_page.settings_requested.connect(self.open_settings)
        self.home_page.open_report_requested.connect(
            self.open_report_folder
        )

        # Le QStackedWidget permet d'afficher une seule vue à la fois :
        #
        #   index 0 = page d'accueil
        #   index 1 = rapport HTML
        #
        # Les deux widgets restent présents dans l'interface.
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.home_page)
        self.content_stack.addWidget(self.viewer)

        # Au démarrage, afficher la page d'accueil.
        self.content_stack.setCurrentIndex(0)
        self.viewer.hide()


        # ============================================================
        # Conteneur principal
        # ============================================================

        container = QWidget()

        layout = QVBoxLayout(container)

        # ============================================================
        # Barre d'outils
        # ============================================================

        layout.addLayout(self.create_toolbar())

        # ============================================================
        # Liste des rapports
        # ============================================================

        self.report_list = QListWidget()

        # Charge les rapports disponibles dans le workspace.
        self.load_reports()

        # Lorsqu'un rapport est sélectionné,
        # il est affiché dans le navigateur HTML.
        self.report_list.itemClicked.connect(
            self.open_report
        )

        # ============================================================
        # Zone principale : liste + contenu
        # ============================================================

        splitter = QSplitter()

        # ------------------------------------------------------------
        # Colonne gauche : recherche + liste des rapports
        # ------------------------------------------------------------

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addLayout(self.create_filterbar())
        left_layout.addWidget(self.report_list)

        splitter.addWidget(left_panel)

        # ------------------------------------------------------------
        # Colonne droite : accueil ou rapport HTML
        # ------------------------------------------------------------

        splitter.addWidget(self.content_stack)

        # Largeurs initiales :
        #   300 px pour la liste
        #   1100 px pour le contenu
        splitter.setSizes([
            300,
            1100,
        ])

        layout.addWidget(splitter)

        # Définit le conteneur comme zone centrale de la fenêtre.
        self.setCentralWidget(container)

        # ============================================================
        # Connexions des commandes
        # ============================================================

        # Recherche des rapports.
        self.search.textChanged.connect(
            self.filter_reports
        )

        # Effacement de la recherche.
        self.clear_button.clicked.connect(
            self.search.clear
        )

        # Actualisation de la liste.
        self.btn_refresh.clicked.connect(
            self.refresh_reports
        )

        # Récupération des formulaires.
        self.btn_fetch.clicked.connect(
            self.fetch_reports
        )

        # Génération / ouverture du bilan ODT.
        self.btn_odt.clicked.connect(
            self.generate_odt
        )

        # Ouverture de la configuration.
        self.btn_settings.clicked.connect(
            self.open_settings
        )

        # Impression du rapport en PDF.
        self.btn_print.clicked.connect(
            self.print_report
        )

        # Initialise WebEngine après l'affichage de l'interface.
        # L'accueil peut ainsi apparaître rapidement.
        QTimer.singleShot(
            500,  # 500 ms après le démarrage
            self._warmup_webengine,
        )

    def _warmup_webengine(self):
        """
        Initialise le moteur WebEngine après le démarrage
        de l'interface, afin de ne pas ralentir l'affichage
        de la page d'accueil.
        """

        if self.viewer.url().isEmpty():
            self.viewer.setHtml(
                "<html><body></body></html>"
            )

    # Fonction appelée lors de la fermeture de la fenêtre
    def closeEvent(self, event):
        """
        Gère la fermeture de la fenêtre.
        """
        logger.info("Fermeture de l'application")
        event.accept()  # Accepte la fermeture de la fenêtre

    # Fonction pour vérifier et créer un espace de travail utilisateur
    def ensure_workspace(self) -> Path | None:
        """
        Vérifie qu'un espace de travail utilisateur est défini.
        """
        config = load_runtime()
        workspace = config.get("workspace", "")
        if workspace and Path(workspace).exists():
            logger.info("Workspace utilisé : %s", workspace)
            ensure_env()
            return Path(workspace)

        QMessageBox.information(
            self,
            "Premier démarrage",
            "Choisissez le dossier qui contiendra "
            "les rapports et les données utilisateur.",
        )
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier Profil Sensoriel", str(Path.home() / "Documents")
        )
        if not folder:
            return None
        config["workspace"] = folder
        save_runtime(config)
        logger.info("Workspace enregistré : %s", folder)
        return Path(folder)

    # Fonction appelée pour rechercher les rapports disponibles
    def load_reports(self):
        # Documentation de la fonction
        """
        Charge tous les rapports HTML
        """
        logger.info("Recherche rapports dans : %s", paths.html_dir)
        # Vérifie que le dossier existe
        if not paths.html_dir.exists():
            self.report_list.addItem(  # Ajoute un message dans la liste si le dossier est absent
                "Dossier rapports absent"
            )
            return  # Arrête l'exécution de la fonction
        # Recherche tous les fichiers terminant par .html
        # sorted() trie les résultats par ordre alphabétique
        reports = sorted(paths.html_dir.glob("*.html"))
        # print("Rapports trouvés :", len(reports))
        logger.info("Rapports trouvés : %s", len(reports))

        # Parcourt chaque fichier trouvé
        for report in reports:
            data = load_report_metadata(report)
            """ Le JSON contient les informations patient utilisées pour rendre la liste plus lisible.
            Si le JSON manque, on affiche simplement le nom du fichier.
            """
            item = QListWidgetItem()
            if data:
                patient = data.get("patient", {})
                nom = patient.get("nom", "")
                prenom = patient.get("prenom", "")
                form_type = patient.get("form_type", "")
                item.setText(f"{prenom} {nom} ({form_type})")
                item.setToolTip(create_tooltip(data))
            else:
                item.setText(report.stem)
                item.setToolTip("Données JSON absentes")
            # Stocke le fichier réel derrière l'élément
            item.setData(Qt.UserRole, report)
            self.report_list.addItem(item)

    # Fonction appelée lorsqu'un utilisateur clique sur un rapport
    def open_report(self, item):
        """
        Affiche le rapport HTML sélectionné.
        """

        self.current_report = item.data(Qt.UserRole)
        html_path = self.current_report

        if not html_path or not html_path.exists():
            return

        self.viewer.load(
            QUrl.fromLocalFile(str(html_path))
        )

        self.content_stack.setCurrentIndex(1)

        self.btn_odt.setEnabled(True)
        self.btn_print.setEnabled(True)


    # Fonction appelée lorsqu'un utilisateur tape dans le champ de recherche
    def filter_reports(self, text):
        """
        Filtre la liste des rapports.
        """
        text = text.lower()
        for index in range(self.report_list.count()):
            item = self.report_list.item(index)
            visible = text in item.text().lower()
            """Recherche simple par inclusion de texte 
            exemple :
            "mar" retrouve "Martin" ou "Marie".
            """
            item.setHidden(not visible)

    # Fonction du bouton "Ouvrir rapport"
    def open_selected_report(self):
        """
        Ouvre le rapport actuellement sélectionné.
        """
        item = self.report_list.currentItem()
        if item:
            self.open_report(item)

    # Fonction du bouton "Actualiser liste"
    def refresh_reports(self):
        """
        Recharge la liste des rapports.
        """
        reload_reports()
        logger.info("Liste des rapports actualisée", extra={"status": True})

    # Fonction du bouton "Imprimer PDF"
    def print_report(self):
        """
        Génère un PDF à partir du rapport HTML actuellement affiché.
        """
        if not self.current_report or not self.current_report.exists():
            logger.warning("Aucun rapport à imprimer")
            return
        self.pdf_path = paths.pdf_dir / f"{self.current_report.stem}.pdf"
        paths.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.viewer.printToPdf(str(self.pdf_path))

    # Fonction appelée lorsque la génération du PDF est terminée
    def _on_pdf_printing_finished(self, file_path, success):
        """
        Appelé par Qt lorsque la génération du PDF est terminée.
        """
        if not success:
            logger.error("Échec génération PDF dans : %s", Path(file_path).parent)

            QMessageBox.warning(
                self,
                "Impression",
                "Impossible de générer le PDF.",
            )
            return

        pdf_dir = Path(file_path).parent

        logger.info(
            "PDF généré dans : %s",
            pdf_dir,
            extra={"status": True},
        )

        try:
            import os

            os.startfile(file_path)
        except OSError:
            logger.exception("Impossible d'ouvrir le PDF")
            QMessageBox.warning(
                self,
                "Impression",
                "Le PDF a été généré mais impossible de l'ouvrir.",
            )


    def fetch_reports(self):
        """
        Récupère les nouveaux formulaires Tally (en arrière-plan,
        pour que la status bar affiche chaque étape en direct).
        """
        self.progress_dialog = ProgressDialog(self)
        self.status_logger.set_progress_dialog(self.progress_dialog)  # branche les logs
        self.progress_dialog.show()
        self.btn_fetch.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.worker = FetchWorker()
        self.worker.finished_ok.connect(self._on_fetch_done)
        self.worker.finished_error.connect(self._on_fetch_error)
        # Branche les logs à la popup
        # self.status_logger.log_signal.connect(self._on_log_for_progress)
        self.worker.start()

    def _on_fetch_done(self, count):
        logger.info("%s formulaire(s) récupéré(s)", count, extra={"status": True})
        if self.progress_dialog:
            self.progress_dialog.accept()
            self.status_logger.set_progress_dialog(None)  # débranche
        self.btn_fetch.setEnabled(True)
        self.progress_bar.setVisible(False)
        reload_reports()

    # Fonction de callback pour le worker en cas d'erreur
    def _on_fetch_error(self, message):
        logger.error("Erreur lors de l'import Tally : %s", message)
        if self.progress_dialog:
            self.progress_dialog.reject()
            self.status_logger.set_progress_dialog(None)  # débranche
        self.btn_fetch.setEnabled(True)
        self.progress_bar.setVisible(False)

    # fonction de saisir un token
    def ask_tally_token(self):
        """Demande à l'utilisateur de saisir un token Tally."""
        token, ok = QInputDialog.getText(
            self,
            "Token Tally",
            "Nouveau token :",
            QLineEdit.EchoMode.Password,
        )

        if not ok:
            return None

        token = token.strip()

        return token or None


    # Fonction pour créer le bandeau de boutons
    def create_toolbar(self):
        """
        Crée le bandeau des boutons métier.
        """

        toolbar = QHBoxLayout()
        self.btn_fetch = QPushButton("📥 Récupérer formulaires")
        self.btn_refresh = QPushButton("🔄 Actualiser liste")
        self.btn_odt = QPushButton("📄 Générer / ouvrir le Bilan")
        self.btn_settings = QPushButton("⚙ Configuration")
        self.btn_print = QPushButton("🖨 PDF")

        toolbar.addWidget(self.btn_fetch)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_print)
        toolbar.addWidget(self.btn_odt)

        self.btn_print.setEnabled(self.current_report is not None)
        self.btn_odt.setEnabled(self.current_report is not None)
        # self.btn_export.setEnabled(self.current_report is not None)

        # espace libre avant les paramètres
        toolbar.addStretch()
        toolbar.addWidget(self.btn_settings)
        return toolbar

    # Fonction pour créer la barre de progression
    def _setup_progress_bar(self):
        """Barre de progression indéterminée, dans la status bar."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # mode indéterminé (va-et-vient)
        self.progress_bar.setMaximumWidth(160)
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setVisible(False)
        self.status_logger.status_bar.addPermanentWidget(self.progress_bar)

    # Fonction pour créer la barre de filtre
    def create_filterbar(self):
        """
        Crée la barre de filtre avec le champ de recherche et le bouton d'effacement.
        """
        filter_bar = QHBoxLayout()  # Crée un layout horizontal pour la barre de filtre
        self.search = QLineEdit()  # Crée un champ de saisie texte pour la recherche
        self.search.setPlaceholderText("🔎 Rechercher un patient...")
        self.clear_button = QPushButton("Effacer")
        self.clear_button.setToolTip("Effacer le texte de recherche")
        filter_bar.addWidget(self.search)
        filter_bar.addWidget(self.clear_button)
        return filter_bar

    def generate_odt(self):
        """
        Génère et/ou ouvre le bilan ODT, selon le choix du praticien.
        """
        item = self.report_list.currentItem()
        if not item:
            logger.warning("Aucun rapport sélectionné")
            return

        html_path = item.data(Qt.UserRole)
        filename = html_path.stem
        output_path = paths.bilan_dir / f"{filename}_bilan.odt"

        data = load_report_metadata(html_path)
        if not data:
            QMessageBox.warning(
                self, "Bilan ODT", "Données JSON introuvables pour ce rapport."
            )
            return

        patient = data.get("patient", {})
        scores = {
            "domains": data.get("domains", {}),
            "quadrants": data.get("quadrants", {}),
            "composantes_scolaires": data.get("composantes_scolaires", {}),
        }

        runtime = load_runtime()
        threshold = float(runtime.get("strategy_threshold", 1.5))
        candidates = select_strategy_candidates(scores, threshold)

        dialog = StrategiesDialog(candidates, self)
        if dialog.exec() != QDialog.Accepted:
            logger.info("Génération ODT annulée")
            return

        # --- Ouvrir seulement : pas de génération ---
        if dialog.action == StrategiesDialog.OPEN_ONLY:
            if not output_path.exists():
                QMessageBox.warning(
                    self,
                    "Bilan ODT",
                    "Aucun bilan existant à ouvrir. Générez-le d'abord.",
                )
                return
            open_odt(output_path)
            return

        # --- Vérification du verrou avant génération ---
        if is_locked(output_path):
            QMessageBox.warning(
                self,
                "Fichier ouvert",
                f"« {output_path.name} » est actuellement ouvert dans LibreOffice.\n\n"
                "Fermez-le avant de générer une nouvelle version.\n"
                "⚠️ Le document n'a PAS été mis à jour.",
            )
            return

        # --- Confirmation d'écrasement ---
        if output_path.exists():
        #    reply = QMessageBox.question(
        #        self,
        #        "Écraser le fichier existant ?",
        #        f"« {output_path.name} » existe déjà.\n\nLe remplacer ?",
        #        QMessageBox.Yes | QMessageBox.No,
        #        QMessageBox.No,
        #    )
        #    if reply != QMessageBox.Yes:
        #        logger.info("Génération ODT annulée (écrasement refusé)")
        #        return

            box = QMessageBox(self)
            box.setWindowTitle("Écraser le fichier existant ?")
            box.setText(f"« {output_path.name} » existe déjà.\n\nLe remplacer ?")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText("Oui")
            box.button(QMessageBox.No).setText("Non")
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                logger.info("Génération annulée (écrasement refusé)")
                return

        # --- Génération ---
        selected = dialog.selected_strategies()
        try:
            build_bilan_odt(patient, scores, output_path, selected)
            logger.info("✓ Bilan ODT généré : %s", output_path.parent, extra={"status": True})
        except Exception:  # noqa: BLE001
            logger.exception("Erreur génération bilan ODT")
            QMessageBox.critical(
                self,
                "Bilan ODT",
                "Échec de la génération. Voir la console pour le détail.",
            )
            return

        if dialog.action == StrategiesDialog.GENERATE_AND_OPEN:
            open_odt(output_path)

    # Fonction obsolette du bouton "Générer / ouvrir ODT"

    def open_report_folder(self):
        """Ouvre le dossier Rapports de l'espace de travail."""
        data_dir = paths.report_dir

        if not data_dir.exists():
            QMessageBox.warning(
                self,
                "Dossier Rapports",
                "Le dossier Rapports n'existe pas.",
            )
            return

        try:
            import os

            os.startfile(data_dir)
        except OSError:
            logger.exception("Impossible d'ouvrir le dossier Rapports")
            QMessageBox.warning(
                self,
                "Dossier Rapports",
                "Impossible d'ouvrir le dossier Rapports.",
            )


    # Fonction du bouton "Configuration"
    def open_settings(self):
        """
        Ouvre la fenêtre de configuration.
        Placeholder en attendant le dialogue Qt complet.
        """
        dialog = SettingsDialog(self) # ouvrir la fenêtre de configuration

        if dialog.exec():
            logger.info("Configuration mise à jour", extra={"status": True})
            reload_reports()  # optionnel : si le workspace a changé

        logger.info("Ouverture des paramètres", extra={"status": True})

# Point d'entrée classique d'un programme Python
if __name__ == "__main__":
    logger.info("Début du programme")
    # Création de l'application Qt, QApplication doit exister avant tous les widgets
    app = QApplication(sys.argv)
    splash = show_splash(app, "Chargement de l'interface...")
    logger.info(  # Messages de diagnostic utiles uniquement en développement
        "Recherche rapports dans : %s", paths.html_dir
    )
    paths.debug()
    # Création de notre fenêtre principale
    logger.info("Création de la fenêtre")
    logger.info("Création de la fenêtre principale")
    window = ReportViewer()
    # Rend la fenêtre visible
    window.showMaximized()
    # Lance la boucle événementielle Qt, L'application reste active jusqu'à fermeture de la fenêtre
    splash.finish(window)  # ferme le splash dès que la fenêtre principale est prête
    sys.exit(app.exec())
