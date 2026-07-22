
#Note importante
# 
# Si PowerShell bloque l'exécution des scripts (politique d'exécution), lancez d'abord :
# 
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#
# dunn.ps1
# Lancement du dashboard Profil Sensoriel
# Usage : .\dunn.ps1
#        .\dunn.ps1 -NoBrowser  (n'ouvre pas le navigateur)
#        .\dunn.ps1 -Port 8502   (port personnalisé)

param(
    [switch]$NoBrowser,
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

# Se placer dans le dossier du script (peu importe d'où on le lance)
Set-Location $PSScriptRoot
Write-Host "📂 Dossier projet : $PSScriptRoot" -ForegroundColor Gray

# --------------------------------------------------------
# 1. Détection de Python
# --------------------------------------------------------
Write-Host "📊 Lancement du tableau de bord Profil Sensoriel..." -ForegroundColor Cyan
Write-Host ""

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
}
else {
    Write-Host "❌ Python introuvable. Installez-le depuis https://python.org" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

# --------------------------------------------------------
# 2. Environnement virtuel
# --------------------------------------------------------
if (-not (Test-Path ".venv")) {
    Write-Host "🔧 Création de l'environnement virtuel..." -ForegroundColor Yellow
    & $pythonCmd -m venv .venv
    Write-Host "✅ Environnement créé" -ForegroundColor Green
}

Write-Host "🔄 Activation de l'environnement..." -ForegroundColor Yellow
. .\.venv\Scripts\Activate.ps1

# --------------------------------------------------------
# 3. Dépendances
# --------------------------------------------------------
Write-Host "📦 Vérification des dépendances..." -ForegroundColor Yellow
& python -m pip install --upgrade pip --quiet
$streamlitInstalled = & python -c "import streamlit" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Installation des dépendances..." -ForegroundColor Yellow
    & pip install -r requirements.txt
    Write-Host "✅ Dépendances installées" -ForegroundColor Green
}

# --------------------------------------------------------
# 4. Tuer les anciens processus sur le port
# --------------------------------------------------------
Write-Host "🧹 Nettoyage des anciens processus..." -ForegroundColor Yellow
$processOnPort = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($pidToKill in $processOnPort) {
    Write-Host "   Arrêt du processus $pidToKill..." -ForegroundColor Gray
    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
}

# Nettoyage des streamlit orphelins
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# --------------------------------------------------------
# 5. Lancement
# --------------------------------------------------------
Write-Host ""
Write-Host "🚀 Lancement du dashboard sur http://localhost:$Port" -ForegroundColor Green
Write-Host "   (Fermez cette fenêtre pour arrêter le serveur)" -ForegroundColor Gray
Write-Host ""

# Lancer Streamlit en arrière-plan
$streamlitProcess = `Start-Process -FilePath ".\.venv\Scripts\streamlit.exe" `
    -ArgumentList "run", "dashboard.py", "--server.port", $Port `
    -PassThru `
    -NoNewWindow

# Attendre le démarrage
Start-Sleep -Seconds 3

# Ouvrir le navigateur
#if (-not $NoBrowser) {
#    Start-Process "http://localhost:$Port"
#}

# --------------------------------------------------------
# 6. Attente et nettoyage à la fermeture
# --------------------------------------------------------
Write-Host "Appuyez sur Entrée pour arrêter le serveur..." -ForegroundColor Yellow
Read-Host | Out-Null

Write-Host ""
Write-Host "🧹 Arrêt du serveur..." -ForegroundColor Yellow

# Arrêter le processus Streamlit
if ($streamlitProcess -and !$streamlitProcess.HasExited) {
    $streamlitProcess.Kill()
}

# Nettoyage final du port
$processOnPort = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($pidToKill in $processOnPort) {
    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
}

# Nettoyage de tous les processus Streamlit orphelins
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.MainWindowTitle -like "*Streamlit*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "✅ Serveur arrêté.
" -ForegroundColor Green
Write-Host "Merci d'avoir utilisé le dashboard Profil Sensoriel !
" -ForegroundColor Gray

deactivate