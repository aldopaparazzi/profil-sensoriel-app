#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dunn.py
Dashboard Profil Sensoriel
Usage :
    python dunn.py
        Démarrage rapide
    python dunn.py --install
        Installation / mise à jour environnement
    python dunn.py --port 8502
"""
from pathlib import Path
import argparse
import subprocess
import shutil
import sys
import os
import time
import socket
import webview
import psutil

# ---------------------------------------------------------
# Arguments
# ---------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument(
    "--install",
    action="store_true",
    help="Créer / mettre à jour l'environnement"
)
parser.add_argument(
    "--port",
    type=int,
    default=8501
)
args = parser.parse_args()

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
VENV = ROOT / ".venv"

if os.name == "nt":
    PYTHON = VENV / "Scripts" / "python.exe"
else:
    PYTHON = VENV / "bin" / "python"

# ---------------------------------------------------------
# Installation uniquement avec --install
# ---------------------------------------------------------
def install_environment():
    python = shutil.which("python")
    if python is None:
        raise RuntimeError(
            "Python introuvable"
        )

    if not VENV.exists():
        print("🔧 Création du venv")
        subprocess.run(
            [
                python,
                "-m",
                "venv",
                str(VENV)
            ],
            check=True
        )

    print("⬆ Mise à jour pip")
    subprocess.run(
        [
            str(PYTHON),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip"
        ],
        check=True
    )

    requirements = ROOT / "requirements.txt"
    if requirements.exists():
        print("📦 Installation des dépendances")
        subprocess.run(
            [
                str(PYTHON),
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements)
            ],
            check=True
        )

    print("✅ Environnement prêt\n")

# ---------------------------------------------------------
# Vérification minimale
# ---------------------------------------------------------
if args.install:
    install_environment()

if not PYTHON.exists():
    print(
        "❌ Environnement absent.\n"
        "Lancez une première fois : python dunn.py --install"
    )
    sys.exit(1)

# ---------------------------------------------------------
# Nettoyage port
# ---------------------------------------------------------
def free_port(port):

    for proc in psutil.process_iter():
        try:
            for conn in proc.net_connections("inet"):
                if (
                    conn.laddr.port == port
                    and "python" in proc.name().lower()
                ):
                    proc.kill()
        except Exception:
            pass

free_port(args.port)

# ---------------------------------------------------------
# Attente serveur
# ---------------------------------------------------------
def wait_server(port, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            socket.create_connection(
                ("localhost", port),
                timeout=1
            )
            return True
        except OSError:
            time.sleep(.3)

    return False

# ---------------------------------------------------------
# Lancement Streamlit
# ---------------------------------------------------------
print(
    f"🚀 Dashboard Profil Sensoriel "
    f"http://localhost:{args.port}"
)

cmd = [
    str(PYTHON),
    "-m",
    "streamlit",
    "run",
    "dashboard.py",
    "--server.port",
    str(args.port),
    "--server.headless",
    "true"
]

process = subprocess.Popen(cmd)

if wait_server(args.port):
    print("✅ Serveur prêt")
    try:
        webview.create_window(
            title="Profil Sensoriel",
            url=f"http://localhost:{args.port}",
            width=1200,
            height=800,
            maximized=True,
            resizable=True,
            min_size=(900, 600),
            text_select=True
        )

        webview.start()

    finally:
        print("Arrêt serveur")

        process.terminate()
else:
    print("❌ Streamlit ne répond pas")
    process.kill()
    sys.exit(1)

# ---------------------------------------------------------
# Arrêt
# ---------------------------------------------------------
'''
try:
    input(
        "\nAppuyez sur Entrée pour arrêter..."
    )
except KeyboardInterrupt:
    pass
'''
print("\n🧹 Arrêt serveur")

try:
    process.terminate()
    process.wait(5)
except Exception:
    process.kill()

free_port(args.port)
print("✅ Terminé")