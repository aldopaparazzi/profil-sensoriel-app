# dunn.ps1
# Lance le dashboard Profil Sensoriel
#
# Usage :
#   .\dunn.ps1
#   .\dunn.ps1 -NoBrowser
#   .\dunn.ps1 -Port 8502

param(
    [switch]$NoBrowser,
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

#----------------------------------------------------------
# Se placer dans le dossier du script
#----------------------------------------------------------
Set-Location $PSScriptRoot
Write-Host "📂 Projet : $PSScriptRoot" -ForegroundColor DarkGray
Write-Host ""

#----------------------------------------------------------
# Détection de Python
#----------------------------------------------------------
Write-Host "🐍 Recherche de Python..." -ForegroundColor Cyan

$pythonCmd = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
}
else {
    Write-Host ""
    Write-Host "❌ Python n'est pas installé." -ForegroundColor Red
    Write-Host "Téléchargement : https://www.python.org/downloads/"
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

#----------------------------------------------------------
# Création du venv
#----------------------------------------------------------
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {

    Write-Host ""
    Write-Host "🔧 Création de l'environnement virtuel..." -ForegroundColor Yellow

    & $pythonCmd -m venv .venv

    Write-Host "✅ Environnement créé." -ForegroundColor Green
}

$python = Resolve-Path ".\.venv\Scripts\python.exe"

#----------------------------------------------------------
# Mise à jour de pip
#----------------------------------------------------------
Write-Host ""
Write-Host "📦 Vérification de pip..." -ForegroundColor Yellow

& $python -m pip install --upgrade pip --quiet

#----------------------------------------------------------
# Vérification des dépendances
#----------------------------------------------------------
Write-Host "📦 Vérification des dépendances..." -ForegroundColor Yellow

$needInstall = $false

try {
    & $python -c "import streamlit" 2>$null
}
catch {
    $needInstall = $true
}

if ($LASTEXITCODE -ne 0) {
    $needInstall = $true
}

if ($needInstall) {

    Write-Host "Installation des dépendances..." -ForegroundColor Yellow

    & $python -m pip install -r requirements.txt

    Write-Host "✅ Dépendances installées." -ForegroundColor Green
}
else {

    Write-Host "✅ Dépendances déjà présentes." -ForegroundColor Green
}

#----------------------------------------------------------
# Nettoyage du port
#----------------------------------------------------------
Write-Host ""
Write-Host "🧹 Vérification du port $Port..." -ForegroundColor Yellow

$processOnPort = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

foreach ($pid in $processOnPort) {

    Write-Host "Arrêt du processus PID $pid"

    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
}

$streamlitProcess = $null

try {

    #------------------------------------------------------
    # Lancement
    #------------------------------------------------------

    Write-Host ""
    Write-Host "🚀 Démarrage du dashboard..." -ForegroundColor Green

    $streamlitProcess = Start-Process `
        -FilePath $python `
        -ArgumentList `
            "-m",
            "streamlit",
            "run",
            "dashboard.py",
            "--server.port",
            $Port `
        -PassThru

    Write-Host "⏳ Attente du démarrage..."

    $timeout = 30
    $elapsed = 0

    do {

        Start-Sleep 1
        $elapsed++

        $ready = Test-NetConnection `
            -ComputerName localhost `
            -Port $Port `
            -InformationLevel Quiet

    } until ($ready -or $elapsed -ge $timeout)

    if (-not $ready) {
        throw "Le serveur Streamlit ne répond pas après $timeout secondes."
    }

    Write-Host ""
    Write-Host "✅ Dashboard disponible :" -ForegroundColor Green
    Write-Host "   http://localhost:$Port"
    Write-Host ""

    if (-not $NoBrowser) {
        Start-Process "http://localhost:$Port"
    }

    Write-Host "Fermez cette fenêtre ou appuyez sur Entrée pour arrêter le serveur." -ForegroundColor Yellow

    Read-Host | Out-Null

}
finally {

    Write-Host ""
    Write-Host "🧹 Arrêt du serveur..." -ForegroundColor Yellow

    if ($streamlitProcess) {

        try {

            if (-not $streamlitProcess.HasExited) {
                Stop-Process -Id $streamlitProcess.Id -Force
            }

        }
        catch {
        }

    }

    $processOnPort = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique

    foreach ($pid in $processOnPort) {

        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
        catch {
        }

    }

    Write-Host ""
    Write-Host "✅ Dashboard arrêté." -ForegroundColor Green
}