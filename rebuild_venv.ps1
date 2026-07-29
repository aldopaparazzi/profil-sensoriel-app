
# Désactiver l'environnement virtuel s'il est actif
Write-Host "Désactivation de l'environnement virtuel..."
deactivate

# Supprimer l'ancien environnement virtuel
Write-Host "Suppression de l'ancien environnement virtuel..."
if (Test-Path .venv) {
    $answer = Read-Host "Voulez-vous supprimer l'ancien environnement virtuel ? (o/n)"
    if ($answer -eq "o") {
        Remove-Item .venv -Recurse -Force
    }
}

# Créer un nouvel environnement virtuel
Write-Host "Création de l'environnement virtuel..."
python -m venv .venv

# Activer l'environnement
Write-Host "Activation de l'environnement virtuel..."
.\.venv\Scripts\Activate.ps1

# Mettre à jour pip
Write-Host "Mise à jour de pip..."
python -m pip install --upgrade pip

# Installer les dépendances
Write-Host "Installation des dépendances..."
python -m pip install -r requirements.txt

# Vérification

Write-Host "Vérification de l'environnement..."
python --version
python -m pip list