# ui.py
"""
Application Qt pour consulter les rapports HTML du Profil Sensoriel 2.

Version 2.0.1
date: 2026-07-27

Ce programme permet de consulter les rapports HTML générés par le Profil Sensoriel 2.
Il est prévu pour être utilisé sur un ordinateur local, sans serveur web.


"""

import json  # Importe le module JSON pour lire et écrire des fichiers JSON  # noqa: I001
import sys  # Importe le module système Python pour gérer les arguments et la fermeture de l'application

# Permet de manipuler facilement les chemins de fichiers et dossiers
from pathlib import (
    Path,  # Importe les classes et méthodes nécessaires pour gérer les chemins de fichiers et dossiers de manière portable
)

# QUrl sert à créer des URLs compatibles avec Qt (ici pour charger un fichier HTML local)
from PySide6.QtCore import (
    Qt,  # Qt est le module central de Qt,
    QUrl,  # QUrl permet de manipuler des URLs,
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
)

# from config.settings import load_config, sauvegarder_token
# from ingestion.fetch_tally import check_token_valid
from main import import_forms

# from reporting.html import generate_html_report
from reporting.odt import generate_bilan

from storage.paths import paths

from storage.init import load_runtime, save_runtime, ensure_env

from ui_logging import StatusBarLogger
from ui_settings import SettingsDialog

from utils.logger import logger, configure_logging


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

    Elle permet :
    - de rechercher un patient ;
    - de sélectionner un rapport ;
    - d'afficher le HTML associé dans un navigateur intégré.
    """

    # Constructeur appelé automatiquement lors de la création de la fenêtre
    def __init__(self):

        # Appelle le constructeur de la classe parent QMainWindow
        super().__init__()  # Appelle le constructeur de la classe parent QMainWindow pour initialiser la fenêtre principale
        runtime = load_runtime()
        configure_logging(runtime.get("debug", False))
        self.status_logger = StatusBarLogger(
            self, logger
        )  # Crée un logger pour afficher les messages dans la barre de statut
        self.ensure_workspace()  # Vérifie qu'un dossier de travail est défini
        self.current_report = None
        self.setWindowTitle("Profil Sensoriel")  # Titre de la fenêtre principale
        if paths.favicon_dir.exists():
            self.setWindowIcon(QIcon(str(paths.favicon_dir)))
        self.resize(1400, 900)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("font-size: 16px;")

        # ==========================
        # Affichage HTML
        # ==========================
        # Création du navigateur web intégré Qt, Il utilise Chromium en interne
        self.viewer = QWebEngineView()

        # ==========================
        # Layout principal
        # ==========================

        container = QWidget()  # Crée un widget conteneur pour organiser les autres widgets dans la fenêtre principale
        # Crée un gestionnaire de mise en page verticale pour organiser les widgets dans le conteneur
        layout = QVBoxLayout(container)

        # ==========================
        # Bandeau boutons
        # ==========================

        layout.addLayout(self.create_toolbar())

        # ==========================
        # Liste des rapports
        # ==========================

        # Création d'une liste graphique vide
        # self permet de conserver l'objet pour l'utiliser dans toute la classe
        self.report_list = QListWidget()
        # Remplit la liste avec les fichiers HTML disponibles
        self.load_reports()
        # Connecte l'évènement "clic sur un élément"  au fonctionnement open_report
        self.report_list.itemClicked.connect(self.open_report)

        # ==========================
        # Zone principale
        # ==========================

        splitter = QSplitter()  # Séparateur permettant à l'utilisateur d'ajuster la largeur de la liste et du visualiseur HTML.

        # ==========================
        # Colonne gauche
        # ==========================

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        # Barre de recherche en haut
        left_layout.addLayout(self.create_filterbar())
        # Liste des rapports dessous
        left_layout.addWidget(self.report_list)

        # Ajoute le panneau gauche au sépar
        splitter.addWidget(left_panel)

        # ==========================
        # Colonne droite
        # ==========================
        splitter.addWidget(self.viewer)  # Ajoute le visualiseur HTML au séparateur
        splitter.setSizes([
            300,
            1100,
        ])  # Définit les tailles initiales des deux panneaux
        # Ajoute le séparateur (contenant la liste et le visualiseur HTML) au layout principal
        layout.addWidget(splitter)
        # Définit le widget conteneur comme widget central de la fenêtre principale, ce qui permet d'afficher tous les widgets organisés dans le layout principal
        self.setCentralWidget(container)
        # ==========================
        # Layout
        # ==========================

        self.search.textChanged.connect(
            self.filter_reports
        )  # Connecte l'évènement "texte modifié" du champ de recherche à la fonction filter_reports() pour filtrer la liste des rapports en fonction du texte saisi
        self.clear_button.clicked.connect(
            self.search.clear
        )  # Connecte l'évènement "clic sur le bouton d'effacement" à la fonction clear() du champ de recherche pour effacer le texte saisi
        self.btn_refresh.clicked.connect(self.refresh_reports)
        self.btn_fetch.clicked.connect(self.fetch_reports)
        self.btn_odt.clicked.connect(self.generate_odt)
        self.btn_settings.clicked.connect(self.open_settings)

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
        Affiche le rapport sélectionné.
        Stocke également le rapport courant pour
        les actions métier (ODT, export, etc.).
        """
        self.current_report = item.data(Qt.UserRole)
        html_path = self.current_report
        if html_path and html_path.exists():
            url = QUrl.fromLocalFile(str(html_path))
            self.viewer.load(url)
            self.btn_odt.setEnabled(True)
            # self.btn_export.setEnabled(True)

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
        self.report_list.clear()
        self.load_reports()
        logger.info("Liste des rapports actualisée")

    # Fonction du bouton "Récupérer formulaires"
    def fetch_reports(self):
        """
        Récupère les nouveaux formulaires Tally.
        """
        logger.info("Début récupération Tally")
        try:
            count = import_forms(request_token=self.ask_tally_token)
            logger.info("%s formulaire(s) récupéré(s)", count)
            self.refresh_reports()
        except Exception:  # noqa: BLE001, RUF100
            logger.exception("Erreur lors de l'import Tally")

    # fonction de saisir un token
    def ask_tally_token(self):
        """Demande à l'utilisateur de saisir un token"""
        token, ok = QInputDialog.getText(
            self,
            "Token Tally",
            "Nouveau token :",
        )
        if ok:
            return token.strip()
        return None

    # Fonction pour créer le bandeau de boutons
    def create_toolbar(self):
        """
        Crée le bandeau des boutons métier.
        """

        toolbar = QHBoxLayout()
        self.btn_fetch = QPushButton("📥 Récupérer formulaires")
        self.btn_refresh = QPushButton("🔄 Actualiser liste")
        self.btn_odt = QPushButton("📄 Générer / ouvrir ODT")
        self.btn_settings = QPushButton("⚙ Configuration")
        toolbar.addWidget(self.btn_fetch)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_odt)
        self.btn_odt.setEnabled(self.current_report is not None)
        # self.btn_export.setEnabled(self.current_report is not None)

        # espace libre avant les paramètres
        toolbar.addStretch()
        toolbar.addWidget(self.btn_settings)
        return toolbar

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

    # Fonction du bouton "Générer / ouvrir ODT"
    def generate_odt(self):
        """
        Génère le bilan ODT du rapport sélectionné.
        """
        item = self.report_list.currentItem()
        if not item:
            logger.warning("Aucun rapport sélectionné")
            return
        html_path = item.data(Qt.UserRole)
        filename = html_path.stem
        try:
            result = generate_bilan(filename)
            logger.info("Résultat génération ODT : %s", result)
        except Exception:  # noqa: BLE001
            logger.exception("Erreur génération ODT")

    # Fonction du bouton "Configuration"
    def open_settings(self):
        """
        Ouvre la fenêtre de configuration.
        Placeholder en attendant le dialogue Qt complet.
        """
        dialog = SettingsDialog(self)
        if dialog.exec():
            logger.info("Configuration mise à jour")
            self.refresh_reports()  # optionnel : si le workspace a changé

        logger.info("Ouverture des paramètres")


# Point d'entrée classique d'un programme Python
if __name__ == "__main__":
    print("Début du programme")
    logger.info(  # Messages de diagnostic utiles uniquement en développement
        "Recherche rapports dans : %s", paths.html_dir
    )
    paths.debug()
    # Création de l'application Qt, QApplication doit exister avant tous les widgets
    app = QApplication(sys.argv)
    # Création de notre fenêtre principale
    print("Création de la fenêtre")
    logger.info("Création de la fenêtre principale")
    window = ReportViewer()
    # Rend la fenêtre visible
    window.showMaximized()
    # Lance la boucle événementielle Qt, L'application reste active jusqu'à fermeture de la fenêtre
    sys.exit(app.exec())
