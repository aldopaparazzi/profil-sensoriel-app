# Reprise de projet – Profil Sensoriel App

## Contexte général

Nous développons un pipeline Python qui transforme les exports JSON de Tally en données exploitables pour le calcul du profil sensoriel.

Le projet est volontairement découpé en étapes simples et lisibles :

```text
Raw Tally JSON
    ↓
fetch_tally.py
    ↓
validate.py
    ↓
split.py
    ↓
mapping.py
    ↓
scoring.py
    ↓
report.py
```

L'objectif actuel est de fiabiliser entièrement le pipeline avant de construire le scoring.

---

## Contraintes importantes

### 1. Pas de jargon inutile

Les explications doivent rester simples et orientées métier.

Toujours privilégier :

* ce qui entre
* ce qui sort
* ce qui peut casser
* comment on le détecte

plutôt que des considérations théoriques.

---

### 2. Éviter les silences dangereux

Le pipeline ne doit jamais :

* perdre une question
* supprimer une donnée sans le dire
* ignorer une erreur silencieusement

Toute anomalie doit être :

* conservée
* tracée
* loggée

---

### 3. Ne jamais spéculer sur les données

Si une information n'est pas visible dans les exemples fournis :

* demander confirmation
* ne pas inventer de schéma
* ne pas supposer de structure

---

## Format actuel des données

### Après split.py

Une submission devient :

```python
{
    "patient": {...},

    "respondent": {...},

    "comments": {
        "Auditif": "...",
        "Tactile": "...",
    },

    "sensory_responses": [
        {
            "question_id": "1",
            "score": 4
        }
    ],

    "metadata": {
        "submission_id": "...",
        "form_id": "...",
        "submitted_at": "...",
        ...
    }
}
```

---

### Après mapping.py

Chaque réponse est enrichie avec le JSON de référence.

```python
{
    "metadata": {...},

    "patient": {...},

    "respondent": {...},

    "comments": {...},

    "items": [
        {
            "question_id": "1",
            "score": 4,

            "label": "...",

            "quadrant": "EV",

            "domaine_sensoriel": "...",

            "composante_scolaire": "...",

            "pour_calcul": False,

            "valid": True
        }
    ]
}
```

---

## Références

Les références ne sont plus des CSV.

Elles sont désormais stockées dans :

```text
data/reference/enfant.json
data/reference/jeune_enfant.json
data/reference/scolaire.json
```

Structure :

```python
{
    "questions": {
        "1": {
            "label": "...",
            "quadrant": "...",
            "domaine_sensoriel": "...",
            "composante_scolaire": "...",
            "pour_calcul": false
        }
    }
}
```

Le chargement des références est centralisé dans main.py.

mapping.py ne charge plus de fichiers.

---

## Structure actuelle du contexte

Le choix retenu est un dictionnaire plutôt qu'une liste.

Objectif :

* accès direct à une submission
* génération future d'un rapport par submission_id

Structure cible :

```python
context["mapped"] = {

    "scolaire": {

        "jex1RA1": {

            "metadata": {...},

            "patient": {...},

            "respondent": {...},

            "comments": {...},

            "items": [...]
        }
    },

    "enfant": {},

    "jeune_enfant": {}
}
```

Ce format a été choisi parce qu'il est plus cohérent pour :

* rechercher une submission
* afficher un rapport
* déboguer

---

## Décisions prises sur les commentaires

Ancien format :

```python
[
    {
        "domaine": "Auditif",
        "commentaire": "..."
    }
]
```

Nouveau format :

```python
{
    "Auditif": "...",
    "Tactile": "..."
}
```

Pourquoi :

* un seul commentaire possible par domaine
* plus lisible
* accès direct

Les doublons de domaine ont été corrigés à la source dans Tally.

---

## Particularités Tally identifiées

### Champ UX "zero"

Certaines réponses contiennent :

```python
{
    "zero": ...
}
```

Ce champ sert uniquement à l'interface Tally.

Il est ignoré par le pipeline.

---

### Commentaires vides

Les commentaires vides génèrent des clés présentes mais sans contenu.

Ils sont ignorés dans split.py.

---

## Logs souhaités

Les logs doivent être utiles à l'exécution.

Exemple :

```text
3.✂️ Split

   └── jex1RA1
       ├── patient: 8 champs
       ├── questions: 44
       ├── commentaires: 5
       ├── ignorés: 3

✔ scolaire: 4 submission(s) structurées
```

Puis :

```text
4.🧠 Mapping

📥 scolaire

 └── mon prénom mon nom (jex1RA1)

✔ scolaire: 4 submission(s) mappées
```

Les logs doivent rester lisibles humainement.

---

## État actuel du pipeline

### fetch_tally.py

Considéré stable.

---

### validate.py

Doit uniquement vérifier la structure minimale.

Il ne doit pas filtrer agressivement les données.

__Objectif__ :

* détecter les anomalies
* pas supprimer des submissions

---

### split.py

Considéré quasiment stable.

__Fonctions__ :

* extraction patient
* extraction répondant
* extraction réponses
* extraction commentaires
* calcul âge

__Sécurités__ :

* calcul d'âge protégé
* champs ignorés tracés
* conservation de toutes les questions

---

### mapping.py

En cours de stabilisation.

__Objectif__ :

* enrichir chaque question avec la référence JSON
* conserver les questions inconnues
* enregistrer les erreurs de mapping
* ne jamais perdre une donnée

Le chargement des références est fait uniquement dans main.py.

---

## Étape suivante

Construire scoring.py.

__Principe attendu :__

1. travailler uniquement sur les items mappés
2. ignorer les items avec :

    ```python
    pour_calcul = False
    ```

3. calculer :

   * scores par quadrant
   * scores par domaine sensoriel
   * scores par composante scolaire

4. produire une structure propre pour report.py

Le scoring ne doit plus relire les références JSON.

Toutes les informations nécessaires sont déjà présentes dans les items issus du mapping.
