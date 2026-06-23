# 📦 SCRIPT DE REPRISE — PIPELINE PROFIL SENSORIEL (VERSION CONSOLIDÉE)

### 🧭 OBJECTIF DU PROJET

Construire un pipeline déterministe et traçable qui :

* ingère des submissions JSON (type Tally)
* transforme les données brutes en structure métier stable
* enrichit les réponses avec une référence contrôlée
* prépare un scoring statistique basé sur des normes
* permet un accès final par `submission_id` pour reporting

---

## 🧱 ARCHITECTURE DU PIPELINE

### 1. INGESTION (Tally API)

#### 🎯 Rôle

Récupérer les données sans transformation.

#### 📥 INPUT

API Tally

#### 📤 OUTPUT

```json
{
  "submissions": [...]
}
```

#### ⚠️ RÈGLES

* aucune transformation
* aucune suppression de données
* structure JSON brute conservée

---

### 2. VALIDATION (pipeline/validate.py)

#### 🎯 Rôle

Garantir une structure minimale exploitable.

#### 📥 INPUT

```python
raw["submissions"]
```

#### 📤 OUTPUT

```python
{
  "submissions": [...]
}
```

#### ⚠️ RÈGLES STRICTES

* ne pas modifier les données métier
* ne pas filtrer silencieusement
* toute anomalie doit être loggée dans `context`
* les submissions sans `responses` sont conservées mais signalées

---

### 3. SPLIT (pipeline/split.py)

#### 🎯 Rôle

Transformer les JSON bruts en structure métier stable.

#### 📤 OUTPUT PAR SUBMISSION

```python
{
    "metadata": {...},
    "patient": {...},
    "respondent": {...},
    "sensory_responses": [
        {
            "question_id": "1",
            "score": 3
        }
    ],
    "comments": {...}
}
```

---

#### ⚠️ RÈGLES STRICTES

* aucune logique métier
* aucun scoring
* aucun mapping de labels
* aucune suppression silencieuse de données
* champs inconnus stockés dans `ignored_fields`

---

#### 👤 PATIENT

* champs `Patient_*` extraits dans un dictionnaire
* `Patient_Date_naissance` utilisé pour calcul âge

---

#### 📅 ÂGE

```python
compute_age(birth_date, submitted_at)
```

* retourne `None` si invalide
* tolérant aux erreurs

---

#### 💬 COMMENTAIRES VALIDES

```python
COMMENT_KEYS = {
    "Auditif", "Visuel", "Tactile", "Mouvement",
    "Position_corps", "Oral", "Comportemental",
    "Conduites", "Socio-émotionnel", "Attentionnel",
    "Global_Scolaire", "Traitement_Global"
}
```

---

## 🧠 4. MAPPING (pipeline/mapping.py)

### 🎯 Rôle

Enrichir les réponses avec les métadonnées de référence.

---

### 📥 INPUT

* `context["split"]`
* `data/reference/<form_name>.json`

---

### 📤 OUTPUT

```python
context["mapped"] = {
    "scolaire": [
        {
            "metadata": {...},
            "patient": {...},
            "respondent": {...},
            "items": [...],
            "comments": {...}
        }
    ]
}
```

---

### 📌 STRUCTURE ITEM

```python
{
    "question_id": "1",
    "score": 3,
    "label": "...",
    "quadrant": "recherche",
    "domaine_sensoriel": "auditif",
    "composante_scolaire": "1",
    "pour_calcul": true,
    "valid": true
}
```

---

### ⚠️ RÈGLES CRITIQUES MAPPING

* toutes les questions sont conservées
* question inconnue autorisée mais `valid=False`
* aucune erreur silencieuse
* toutes anomalies loggées dans `context`

---

### 🧼 NORMALISATION OBLIGATOIRE

#### 🔴 RÈGLE STRUCTURELLE

Toutes les valeurs suivantes sont normalisées en **lowercase strict** :

* `quadrant`
* `domaine_sensoriel`

---

#### ⚠️ CONSÉQUENCE

* aucun matching basé sur la casse
* aucune transformation dans scoring
* comparaison stricte uniquement

---

### 📌 RÉFÉRENCE QUESTIONS

```text
data/reference/reference.json
```

Structure :

```json
{
  "enfant": {
    "questions": {
      "1": {
        "label": "...",
        "quadrant": "...",
        "domaine_sensoriel": "...",
        "domaine_label": "...",
        "composante_scolaire": "...",
        "pour_calcul": true
      }
    }
  },

  "jeune_enfant": {
    "questions": {
      "1": {
        "label": "...",
        "quadrant": "...",
        "domaine_sensoriel": "...",
        "composante_scolaire": "...",
        "pour_calcul": true
      }
    }
  },

  "scolaire": {
    "questions": {
      "1": {
        "label": "...",
        "quadrant": "...",
        "domaine_sensoriel": "...",
        "composante_scolaire": "1",
        "pour_calcul": true
      }
    }
  }
}
```

---

## 🧠 5. VALIDATION / RÉFÉRENCES

#### 🎯 Rôle

Fournir les métadonnées métier des questions.

---

#### 📌 CONTRAINTE

* les clés doivent être cohérentes avec les valeurs mapping
* aucune transformation de texte en aval

---

## 🧮 6. SCORING (À VENIR)

### 🎯 Rôle

* calculs uniquement
* aucune logique de parsing
* aucune transformation de données

---

### 📥 INPUT ATTENDU

```python
mapped["items"]
normes.json
```

---

### 📌 RÈGLES STRICTES

* matching strict uniquement
* aucune correction de clé automatique
* aucune supposition si clé absente
* toute absence doit être loggée

---

### 📊 NORMALISATION STATISTIQUE

Formule :

```python
z = (raw_score - m) / sigma
```

---

### 📌 STRUCTURE NORMES

```json
{
  "scolaire": {
    "3": {
      "quadrants": {
        "recherche": {"m": 13.7, "sigma": 6.1}
      },
      "domaines_sensoriels": {
        "auditif": {"m": 11.2, "sigma": 5.3}
      },
      "composantes_scolaires": {
        "1": {"m": 19.1, "sigma": 8.9}
      }
    }
  }
}
```

---

## 🚨 CONTRAINTES GLOBALES

### ❌ INTERDIT

* deviner une clé absente
* corriger automatiquement une incohérence
* filtrer silencieusement des données
* transformer les textes métier en aval
* modifier les données dans split
* faire du fuzzy matching

---

### ✔ AUTORISÉ

* logs explicites
* conservation des données incohérentes
* tolérance aux valeurs null
* traçabilité complète des erreurs

---

## 🧪 ÉTAT ACTUEL DU SYSTÈME

### ✔ SPLIT

* stable
* reproductible
* extraction patient OK
* commentaires OK

### ✔ MAPPING

* enrichissement fonctionnel
* normalisation lowercase appliquée

### ⚠️ POINTS DE VIGILANCE

* cohérence stricte reference ↔ normes
* submissions partielles possibles
* champs inconnus (doivent être tracés)

---

## 🎯 OBJECTIF FINAL DU PIPELINE

Permettre :

```text
GET /report/{submission_id}
```

et retourner :

* patient structuré
* réponses enrichies
* commentaires organisés
* scores normalisés (z-score)
* traçabilité complète des anomalies

---

## 🚀 PROCHAINE PHASE

1. implémenter scoring strict sans ambiguïté
2. ajouter validation de cohérence reference ↔ normes
3. sécuriser les clés manquantes (mode audit)
4. construire endpoint report final

---
---
# Règle réelle de `pour_calcul`

`pour_calcul` **ne signifie pas** :

```python
inclure_la_question_dans_tous_les_calculs
```

mais plutôt :

```python
inclure_la_question_dans_le_calcul_des_domaines_sensoriels
```

---

# Calcul des quadrants

Les scores de quadrant sont calculés à partir de **toutes les questions valides** du quadrant concerné.

Exemple :

```python
if item["valid"]:
    quadrants[item["quadrant"]] += item["score"]
```

sans tenir compte de :

```python
pour_calcul
```

---

# Calcul des composantes scolaires

Même logique.

Exemple :

```python
if item["valid"]:
    composantes[item["composante_scolaire"]] += item["score"]
```

sans filtrage sur :

```python
pour_calcul
```

---

# Calcul des domaines sensoriels

Là seulement :

```python
if item["valid"] and item["pour_calcul"]:
    domaines[item["domaine_sensoriel"]] += item["score"]
```

---

# Conséquence pratique

Pour une question comme :

```json
{
    "question_id": "31",
    "score": 5,
    "quadrant": "evitement",
    "domaine_sensoriel": "mouvement",
    "composante_scolaire": "4",
    "pour_calcul": false
}
```

elle participe :

✅ au score du quadrant `evitement`

✅ au score de la composante scolaire `4`

❌ au score du domaine sensoriel `mouvement`

---

# Donc les règles de filtrage deviennent

## Quadrants

```python
valid == True
```

## Composantes scolaires

```python
valid == True
```

## Domaines sensoriels

```python
valid == True
and
pour_calcul == True
```

---

C'est d'ailleurs cohérent avec ce qu'on observe dans les questionnaires sensoriels : certaines questions sont utilisées dans les profils/quadrants globaux mais sont exclues des sous-scores de certains domaines sensoriels pour des raisons de validité psychométrique.
