# 🧠 Profil Sensoriel App

API backend permettant de calculer et analyser un profil sensoriel à partir de réponses utilisateur.

---

## 🎯 Objectif du projet

Cette application a pour but de :

- Collecter des réponses à un questionnaire sensoriel
- Calculer un score global et des sous-scores
- Déterminer un profil sensoriel associé
- Fournir une API simple pour exploitation (web / app / outils externes)

---

## 🧩 Fonctionnalités prévues

### 📥 Entrée de données

- Réponses utilisateur sous forme de liste de valeurs numériques
- Support futur de questionnaires structurés (JSON)

### 🧠 Traitement

- Calcul de score global
- Analyse par catégories sensorielles (à définir)
- Classification en profil

### 📤 Sortie

- Score global
- Niveau ou type de profil
- Interprétation simplifiée
- (optionnel futur) recommandations personnalisées

---

## ⚙️ Stack technique

- Python
- FastAPI
- Pydantic
- Pandas (analyse de données)
- Requests (extensions API externes éventuelles)
- Uvicorn (serveur ASGI)

---

## 🏗️ Architecture cible

````plaintext

app/
├── main.py              # point d'entrée FastAPI
├── api/                 # routes HTTP
├── services/            # logique métier
├── schemas/             # validation des données
├── core/                # config globale

````

---

## 📡 API actuelle (MVP)

### POST `/profile/compute`

#### Input

```json
{
  "answers": [1, 2, 3, 4]
}
```

#### Output

```json
{
  "result": {
    "score": 10,
    "level": "modéré"
  }
}
```

---

## 🧠 Règles métier (actuelles)

- Somme simple des réponses
- Classification par seuils :

  - score < 10 → faible
  - 10–19 → modéré
  - ≥ 20 → élevé

---

## 🚧 Évolutions prévues

### Phase 2

- Segmentation des profils sensoriels
- Ajout de dimensions (auditif, visuel, tactile…)

### Phase 3

- Base de données utilisateurs
- Historique des profils

### Phase 4

- Interface web (frontend)
- Visualisation des résultats

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

---

## ▶️ Lancement

```bash
uvicorn app.main:app --reload
```

---

## 📌 Philosophie du projet

- Code simple et lisible
- Séparation logique métier / API
- Évolution progressive (MVP → produit complet)
