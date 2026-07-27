# Supprimer l'ancien environnement virtuel
if (Test-Path .venv) {
    Remove-Item .venv -Recurse -Force
}

# Créer un nouvel environnement virtuel
python -m venv .venv

# Activer l'environnement
.\.venv\Scripts\Activate.ps1

# Mettre à jour pip
python -m pip install --upgrade pip

# Installer les dépendances
python -m pip install -r requirements.txt

# Vérification
python --version
python -m pip list