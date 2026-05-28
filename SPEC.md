# 📐 Sensorial Tool — Specification produit

---

## 1. Vision produit

Créer un outil local permettant de remplacer un fichier Excel utilisé pour l’analyse de profils sensoriels en psychomotricité.

L’objectif est de :

- automatiser le calcul
- structurer les résultats
- améliorer la lisibilité clinique
- faciliter la comparaison de bilans

---

## 2. Problème actuel

Utilisation d’Excel :

- lecture difficile
- manque de structuration patient
- remplissage lent
- analyse lente
- faible visualisation des tendances
- outil non spécialisé

---

## 3. Objectif MVP

Permettre :

- import de données de questionnaire
- calcul automatique des scores
- génération de profils sensoriels
- visualisation simple par patient

---

## 4. Pipeline système

```mermaid id="p9k2sd"
flowchart TD
    A[Tally.so - Questionnaire] --> B[Script Python import]
    B --> C[Calcul scores]
    C --> D[Création profil sensoriel]
    D --> E[Stockage local]
    E --> F[Interface utilisateur]
    F --> G[Visualisation patient]
    F --> H[Comparaison bilans]
````

---

## 5. Modèle de données (conceptuel)

### Patient

- id
- nom (optionnel)
- métadonnées simples

### Bilan

- date
- réponses questionnaire
- score global
- profil sensoriel

### Résultat

- score
- catégorie de profil
- interprétation

---

## 6. Logique de calcul (MVP)

- agrégation des réponses
- score global = somme ou moyenne pondérée
- classification en niveaux :

  - faible
  - modéré
  - élevé

---

## 7. Interface utilisateur (non définie encore)

Fonctions nécessaires :

- liste des patients
- sélection d’un patient
- affichage des bilans associés
- visualisation des profils
- comparaison entre bilans

Critère clé :
→ lisibilité clinique immédiate

---

## 8. Contraintes produit

- usage local
- zéro complexité pour l’utilisateur final
- rapide à ouvrir / utiliser
- pas de dépendance serveur obligatoire
- fonctionnement hors ligne possible

---

## 9. Hors scope actuel

- API publique
- architecture distribuée
- authentification complexe
- cloud

---

## 10. Évolution possible

- visualisations graphiques avancées
- export PDF
- enrichissement modèle sensoriel
- historisation avancée
