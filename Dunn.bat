@echo off
title Profil Sensoriel - Dashboard

echo 📊 Lancement du tableau de bord Profil Sensoriel...
echo.

REM --------------------------------------------------------
REM 1. Détection de Python
REM --------------------------------------------------------
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
REM --------------------------------------------------------
REM 2. Environnement virtuel
REM --------------------------------------------------------
if not exist ".venv\" (
    echo 🔧 Création de l'environnement virtuel...
    %PYTHON% -m venv .venv
    echo ✅ Environnement créé
)

echo 🔄 Activation de l'environnement...
call .venv\Scripts\activate

REM --------------------------------------------------------
REM 3. Dépendances
REM --------------------------------------------------------
python.exe -m pip install --upgrade pip
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installation des dépendances...
    pip install -r requirements.txt
    echo ✅ Dépendances installées
)

REM --------------------------------------------------------
REM 4. Tuer les anciens processus Streamlit
REM --------------------------------------------------------
echo 🧹 Nettoyage des anciens processus...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do (
    echo    Arrêt du processus %%a...
    taskkill /PID %%a /F >nul 2>&1
)

REM --------------------------------------------------------
REM 5. Lancement
REM --------------------------------------------------------
echo.
echo 🚀 Lancement du dashboard sur http://localhost:8501
echo    (Fermez cette fenêtre pour arrêter le serveur)
echo.

REM Lancer Streamlit en arrière-plan et garder le contrôle
start "" /B .venv\Scripts\streamlit.exe run dashboard.py --server.port 8501

REM Attendre que le serveur démarre
timeout /t 3 /nobreak >nul

REM Ouvrir le navigateur
REM start http://localhost:8501

REM --------------------------------------------------------
REM 6. Attente et nettoyage à la fermeture
REM --------------------------------------------------------
echo.
echo Appuyez sur une touche pour arrêter le serveur...
pause >nul

echo.
echo 🧹 Arrêt du serveur...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo ✅ Serveur arrêté.

REM Nettoyage final de tous les processus Streamlit orphelins
taskkill /IM streamlit.exe /F >nul 2>&1
taskkill /IM python.exe /FI "WINDOWTITLE eq Streamlit*" /F >nul 2>&1

REM pause