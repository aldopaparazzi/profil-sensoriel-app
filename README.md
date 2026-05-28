# Profil Sensoriel App

## Objectif

Application permettant aux psychomotriciennes de visualiser facilement les profils sensoriels des patients à partir de questionnaires en ligne (Tally.so). Remplace les tableurs Excel graphiquement archaïques.

- Collecte les réponses utilisateurs
- Calcule les scores sensoriels selon règles cliniques
- Affiche un profil sensoriel multi-dimensionnel
- Prépare le terrain pour un historique patient et des exports éventuels

## Fonctionnalités actuelles

1. **Import des réponses Tally.so**
   - Scripts Python pour formater les fichiers CSV.
   - Gestion multi-population : `enfant`, `jeune_enfant`, `scolaire`.
2. **Pipeline de transformation**
   - Split des données par population
   - Mapping des réponses selon quadrants et domaines sensoriels
   - Filtrage des réponses utilisables pour le calcul
   - Export CSV pour debug
3. **Stockage**
   - Actuellement debug CSV
   - SQLite prévu pour centraliser les patients et résultats

## Roadmap

- [ ] Calcul des scores sensoriels globaux et par dimension
- [ ] UI simple pour consultation rapide par patient et bilan
- [ ] API FastAPI pour intégration future
- [ ] Historique et visualisation multi-bilan
- [ ] Éventuel export PDF ou reporting simple

## Installation (One-click friendly)

```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python main.py
```

## Structure

```text
app/
├─ data/
│  ├─ raw/
│  ├─ debug/
│
├─ mapping/
├─ scripts/
├─ main.py
├─ venv/
```

### future -->

```text
app/
├─ core/
├─ data/
├─ domain/
├─ pipelines/
├─ main.py
```

---

### Notes

- Les données brutes Tally.so sont transformées avant tout calcul.
- Chaque population a sa structure propre : normalisation future nécessaire.
- UI n’est pas encore implémentée.
