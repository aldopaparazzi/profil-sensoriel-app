# 📦 SCRIPT DE REPRISE — PIPELINE PROFIL SENSORIEL

## 🧭 OBJECTIF DU PROJET

Construire un pipeline fiable qui :

* prend des submissions JSON (type Tally)
* extrait proprement les données
* mappe les questions avec des références
* prépare un scoring futur
* permet d’afficher un rapport par `submission_id`

---

## 🧱 ARCHITECTURE ACTUELLE (VALIDÉE)

### 1. SPLIT (pipeline/split.py)

#### 🎯 Rôle

Transformer le JSON brut en structure stable.

#### 📥 INPUT

```json
clean["submissions"]
```

#### 📤 OUTPUT par submission

```python
{
    "metadata": {...},
    "patient": {...},
    "respondent": {...},
    "sensory_responses": [
        {"question_id": "1", "score": 3}
    ],
    "comments": [
        {"domaine": "Visuel", "commentaire": "..."}
    ]
}
```

---

#### ⚠️ RÈGLES STRICTES SPLIT

* ne fait aucune logique métier
* ne dépend pas du formulaire
* ne fait aucun scoring
* ne fait aucun mapping de labels
* ne filtre pas les questions

---

#### 📌 CAS PARTICULIERS ACCEPTÉS

* `"zero"` → valeur UX vide (ignorée plus tard)
* champs inconnus → stockés dans `ignored_fields`
* doublons possibles dans données brutes (doivent être détectés plus tard)

---

#### 🧠 COMMENTAIRES VALIDES

```python
COMMENT_KEYS = {
    "Auditif", "Visuel", "Tactile", "Mouvement",
    "Position_corps", "Oral", "Comportemental",
    "Conduites", "Socio-émotionnel", "Attentionnel",
    "Global_Scolaire", "Traitement_Global"
}
```

---

#### 👤 PATIENT

Champs extraits :

* `Patient_*` → dictionnaire patient
* `Patient_Date_naissance` → utilisé pour âge

---

#### 📅 AGE

```python
compute_age(birth_date, submitted_at)
```

* retourne `None` si invalide
* tolérant aux erreurs

---

## 🧠 2. MAPPING (pipeline/mapping.py)

### 🎯 Rôle

Transformer les données split en données métier enrichies.

---

### 📥 INPUT

```python
context["split"]
reference JSON (par form)
```

---

## 📤 STRUCTURE FINALE

```python
context["mapped"] = {
    "scolaire": {
        "submission_id": {
            "metadata": {...},
            "patient": {...},
            "respondent": {...},
            "items": [...],
            "comments": [...]
        }
    }
}
```

---

### ⚠️ RÈGLES MAPPING

* toutes les questions doivent être conservées
* question_id inconnu = autorisé mais marqué `valid=False`
* aucune erreur silencieuse
* toutes anomalies doivent être loggées dans `context`

---

### 📌 RÉFÉRENCE QUESTIONS

Source :

```python
data/reference/<form_name>.json
```

---

## 🧠 3. VALIDATION / RÉFÉRENCES

### 🎯 Rôle

Fournir :

* labels des questions
* domaine sensoriel
* composantes scolaires
* indicateurs de calcul

---

### 📌 STRUCTURE ATTENDUE

```json
{
  "questions": {
    "1": {
      "label": "...",
      "quadrant": "...",
      "domaine_sensoriel": "...",
      "composante_scolaire": "...",
      "pour_calcul": true
    }
  }
}
```

---

## 🧮 4. SCORING (à venir)

### 🎯 Rôle

* uniquement calculs
* aucune logique de parsing
* aucune dépendance brute JSON

---

## 🚨 CONTRAINTES GLOBALES DU PROJET

### ❌ INTERDIT

* deviner des champs absents
* filtrer silencieusement des questions
* supposer un schema externe invisible
* mélanger UX et données métier
* modifier les données dans split

---

### ✔ AUTORISÉ

* logs explicites
* champs inconnus tracés
* valeurs null autorisées
* tolérance aux incohérences

---

## 🧪 ÉTAT ACTUEL CONNU

### ✔ SPLIT

* fonctionne
* stable
* 44 questions constantes
* patient extrait correctement
* commentaires détectés

---

### ✔ DONNÉES UX

* `"zero"` = champ vide volontaire
* doit être ignoré plus tard

---

### ⚠️ POINTS À SURVEILLER

* doublons de domaine (normalement ne devrait pas arriver)
* submissions partielles (patient incomplet)
* champs inconnus (ignored_fields)

---

## 🎯 OBJECTIF FINAL DU PIPELINE

Permettre :

```text
GET /report/{submission_id}
```

et obtenir :

* patient propre
* réponses enrichies
* commentaires structurés
* scoring futur

---

## 🚀 PROCHAINE PHASE (APRÈS REPRISE)

Quand tu relances le projet :

1. stabiliser mapping (anti-erreurs silencieuses)
2. normaliser "zero" + doublons
3. préparer scoring sans ambiguïté
4. exposer report par submission_id
