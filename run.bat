@echo off
title Profil Sensoriel - Dashboard
echo 📊 Lancement du tableau de bord Profil Sensoriel...
echo.

REM Trouver Python automatiquement
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python introuvable. Installez-le depuis https://python.org
        pause
        exit /b 1
    )
    set PYTHON=py
) else (
    set PYTHON=python
)

REM Vérifier si l'environnement virtuel existe
if not exist ".venv\" (
    echo 🔧 Création de l'environnement virtuel...
    %PYTHON% -m venv .venv
    echo ✅ Environnement créé
)

REM Activer l'environnement
echo 🔄 Activation de l'environnement...
call .venv\Scripts\activate

REM Vérifier si Streamlit est installé
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installation des dépendances...
    pip install -r requirements.txt
    echo ✅ Dépendances installées
)

REM Lancer le CLI
echo.
echo 🚀 Lancement de l'application...
echo.
python run.py

pause