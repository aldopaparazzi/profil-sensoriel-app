# 🧠 Sensorial Tool

Outil local destiné à la collecte, au calcul et à la visualisation de profils sensoriels pour un usage en psychomotricité.

---

## 🎯 Objectif

Remplacer un usage Excel existant par un outil :

- plus lisible
- plus rapide à utiliser
- plus adapté à l’analyse clinique
- accessible sans compétence technique

---

## 👩‍⚕️ Utilisateurs

Psychomotriciennes réalisant des bilans sensoriels.

Contraintes utilisateurs :

- pas de logique technique
- besoin de lecture rapide
- comparaison de bilans par patient
- usage quotidien simple

---

## 🧩 Fonctionnement global

1. Les réponses sont collectées via Tally.so
2. Un script Python récupère les données
3. Les scores et profils sont calculés
4. Les résultats sont stockés localement
5. Une interface permet de :
   - sélectionner un patient
   - visualiser ses profils
   - comparer plusieurs bilans

---

## 📊 Fonctionnalités MVP

- Import de réponses Tally.so
- Calcul de score sensoriel
- Attribution de profil
- Stockage local des résultats
- Visualisation simple des profils
- Navigation par patient

---

## 🧠 Fonctionnalités futures

- comparaison multi-bilans
- graphiques de profils
- export PDF simple
- amélioration du modèle de scoring

---

## ⚙️ Stack technique (ouverte)

- Python
- traitement de données (pandas possible)
- stockage local (JSON / CSV / SQLite)
- interface utilisateur locale (non définie encore)

---

## 📦 Philosophie

- simplicité maximale
- zéro complexité inutile
- outil local rapide
- priorité à la lisibilité clinique
