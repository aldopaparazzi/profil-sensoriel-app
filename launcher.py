# launcher.py
"""
Launcher Profil Sensoriel.

Architecture :

Mode utilisateur :
    Profil Sensoriel.exe

        |
        |
        +--> lance un second processus :
                Profil Sensoriel.exe --streamlit-server

                    |
                    +--> Streamlit
                         dashboard.py

        |
        +--> attend localhost:8501
        |
        +--> ouvre PyWebView


Mode serveur interne :
    Profil Sensoriel.exe --streamlit-server

        |
        +--> démarre Streamlit uniquement


Compatible :
- développement Python
- PyInstaller onedir
"""


from __future__ import annotations
from storage.paths import APP_DIR
from pathlib import Path
import argparse
import logging
import socket
import subprocess
import sys
import time


import webview


# ---------------------------------------------------------
# Chemins
# ---------------------------------------------------------
root = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    root = Path(sys._MEIPASS)
else:
    root = Path(__file__).resolve().parent



# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("profil_sensoriel")


def configure_logging(debug: bool) -> None:
    """
    Configuration simple des logs.
    """

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s | %(message)s",
    )


# ---------------------------------------------------------
# Arguments
# ---------------------------------------------------------


def parse_args():

    parser = argparse.ArgumentParser(
        description="Profil Sensoriel",
    )

    parser.add_argument(
        "--streamlit-runner",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port Streamlit",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mode diagnostic",
    )

    parser.add_argument(
        "--streamlit-server",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Ressources
# ---------------------------------------------------------


def get_resource_path(filename: str) -> Path:
    """
    Retourne un chemin compatible :

    - développement :
        dossier projet

    - PyInstaller :
        dossier _internal
    """

    if getattr(sys, "frozen", False):

        return Path(sys._MEIPASS) / filename

    return APP_DIR / filename


# ---------------------------------------------------------
# Démarrage Streamlit
# ---------------------------------------------------------


def run_streamlit_server(port: int):
    """
    Lance Streamlit.

    Cette fonction doit être exécutée
    dans le processus principal.

    Ne pas utiliser de Thread :
    Streamlit utilise les signaux Python.
    """


    dashboard = get_resource_path(
        "dashboard.py"
    )


    logger.info(
        "Démarrage Streamlit : %s",
        dashboard,
    )


    from streamlit.web import cli as stcli


    sys.argv = [
        "streamlit",
        "run",
        str(dashboard),
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--global.developmentMode",
        "false",
    ]


    stcli.main()



# ---------------------------------------------------------
# Lancement du serveur secondaire
# ---------------------------------------------------------


def launch_streamlit_server(
    port: int,
):
    """
    Lance Streamlit dans un processus séparé.
    """

    if getattr(sys, "frozen", False):

        command = [
            sys.executable,
            "--streamlit-runner",
            "--port",
            str(port),
        ]

    else:

        command = [
            sys.executable,
            str(APP_DIR / "streamlit_runner.py"),
        ]


    logger.info(
        "Commande serveur : %s",
        command,
    )


    return subprocess.Popen(
        command,
        cwd=str(APP_DIR),
    )

# ---------------------------------------------------------
# Attente serveur
# ---------------------------------------------------------


def wait_server(
    port: int,
    timeout: int = 30,
) -> bool:
    """
    Attend que Streamlit écoute.
    """

    start = time.monotonic()


    while time.monotonic() - start < timeout:

        try:

            with socket.create_connection(
                ("127.0.0.1", port),
                timeout=1,
            ):
                return True


        except OSError:

            time.sleep(0.5)


    return False



# ---------------------------------------------------------
# Fenêtre utilisateur
# ---------------------------------------------------------


def open_window(port: int):
    """
    Création de la fenêtre native.
    """

    webview.create_window(
        title="Profil Sensoriel",
        url=f"http://127.0.0.1:{port}",
        width=1200,
        height=800,
        min_size=(900, 600),
        resizable=True,
    )


    webview.start()



# ---------------------------------------------------------
# Arrêt
# ---------------------------------------------------------


def stop_process(
    process: subprocess.Popen,
):
    """
    Arrêt propre du serveur secondaire.
    """

    if process is None:
        return


    if process.poll() is None:

        logger.info(
            "Arrêt Streamlit"
        )

        process.terminate()


# ---------------------------------------------------------
# Mode bureau
# ---------------------------------------------------------


def run_desktop(
    port: int,
):

    server = launch_streamlit_server(
        port,
    )


    try:

        if not wait_server(port):

            logger.error(
                "Streamlit ne répond pas"
            )

            return 1


        logger.info(
            "Serveur prêt"
        )


        open_window(
            port,
        )


    finally:

        stop_process(
            server,
        )


    return 0



# ---------------------------------------------------------
# Programme principal
# ---------------------------------------------------------


def main():

    args = parse_args()

    configure_logging(
        args.debug,
    )

    logger.debug(
        "Arguments : %s",
        args,
    )

    # Mode serveur interne
    if args.streamlit_runner:
        from streamlit_runner import main as streamlit_main
        streamlit_main()
        return 0

    if args.streamlit_server:
        run_streamlit_server(args.port)
        return 0

    # Mode utilisateur
    return run_desktop(
        args.port,
    )

if __name__ == "__main__":

    raise SystemExit(
        main()
    )