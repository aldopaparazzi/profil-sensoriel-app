/**
 * Conversion du fichier CSV de normes du Profil Sensoriel
 * vers un JSON hiérarchique orienté calcul.
 *
 * Structure cible :
 *
 * {
 *   "jeune_enfant": {
 *     "7": {
 *       "quadrants": {},
 *       "domaines_sensoriels": {}
 *     }
 *   },
 *
 *   "enfant": {
 *     "3": {
 *       "quadrants": {},
 *       "domaines_sensoriels": {}
 *     }
 *   },
 *
 *   "scolaire": {
 *     "3": {
 *       "quadrants": {},
 *       "composantes_scolaires": {},
 *       "domaines_sensoriels": {}
 *     }
 *   }
 * }
 */

const fs = require("fs");

/**
 * Correspondance entre les sections du CSV
 * et la structure JSON cible.
 */
const SECTION_MAPPING = {
  jeune_enfant_quadrant: {
    instrument: "jeune_enfant",
    category: "quadrants"
  },

  jeune_enfant_domaine_sensoriel: {
    instrument: "jeune_enfant",
    category: "domaines_sensoriels"
  },

  enfant_quadrant: {
    instrument: "enfant",
    category: "quadrants"
  },

  enfant_domaine_sensoriel: {
    instrument: "enfant",
    category: "domaines_sensoriels"
  },

  scolaire_quadrant: {
    instrument: "scolaire",
    category: "quadrants"
  },

  scolaire_composante_scolaire: {
    instrument: "scolaire",
    category: "composantes_scolaires"
  },

  scolaire_domaine_sensoriel: {
    instrument: "scolaire",
    category: "domaines_sensoriels"
  }
};

/**
 * Normalise un libellé vers une clé JSON.
 *
 * Exemple :
 *
 * "Traitement Auditif"
 * => "traitement_auditif"
 *
 * "Réponses Socio-émotionnelles"
 * => "reponses_socio_emotionnelles"
 */
function slugify(label) {
  return label
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[()]/g, "")
    .replace(/[^\w]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

/**
 * Détermine si une ligne correspond
 * au début d'une nouvelle section.
 */
function isSectionLine(line) {
  const sectionName = line
    .split(";")[0]
    .trim();

  return sectionName in SECTION_MAPPING;
}

/**
 * Extrait les dimensions depuis
 * la ligne d'en-tête.
 *
 * Exemple :
 *
 * Recherche;;Évitement;;Sensibilité;;
 *
 * devient :
 *
 * [
 *   { key: "recherche", column: 2 },
 *   { key: "evitement", column: 4 },
 *   { key: "sensibilite", column: 6 }
 * ]
 */
function extractDimensions(headerColumns) {
  const dimensions = [];

  for (let col = 2; col < headerColumns.length; col += 2) {
    const label = headerColumns[col]?.trim();

    if (!label) {
      continue;
    }

    dimensions.push({
      key: slugify(label),
      column: col
    });
  }

  return dimensions;
}

/**
 * Convertit une valeur CSV vers Number.
 *
 * Gère :
 * 15.4
 * 15,4
 */
function toNumber(value) {
  if (!value) {
    return null;
  }

  return Number(
    value
      .trim()
      .replace(",", ".")
  );
}

/**
 * Parse une section complète.
 */
function parseSection(lines, startIndex, result) {

  const sectionName =
    lines[startIndex]
      .split(";")[0]
      .trim();

  const mapping =
    SECTION_MAPPING[sectionName];

  const instrument =
    mapping.instrument;

  const category =
    mapping.category;

  /**
   * Ligne contenant les noms
   * des dimensions.
   */
  const headerColumns =
    lines[startIndex + 1]
      .split(";");

  const dimensions =
    extractDimensions(
      headerColumns
    );

  /**
   * On saute :
   *
   * ligne section
   * ligne labels
   * ligne m/σ
   */
  let rowIndex =
    startIndex + 3;

  while (rowIndex < lines.length) {

    const line =
      lines[rowIndex];

    if (!line.trim()) {
      break;
    }

    if (isSectionLine(line)) {
      break;
    }

    const cols =
      line.split(";");

    /**
     * Colonne 1 = âge clé
     *
     * Ex :
     * 3
     * 4
     * 10
     * 13
     */
    const ageKey =
      cols[1]?.trim();

    if (!ageKey) {
      rowIndex++;
      continue;
    }

    /**
     * Création de la structure
     * instrument > âge
     */
    if (!result[instrument]) {
      result[instrument] = {};
    }

    if (!result[instrument][ageKey]) {
      result[instrument][ageKey] = {};
    }

    if (
      !result[instrument][ageKey][category]
    ) {
      result[instrument][ageKey][category] = {};
    }

    /**
     * Remplissage des dimensions
     */
    dimensions.forEach(dim => {

      result[instrument][ageKey][category][dim.key] = {
        m: toNumber(
          cols[dim.column]
        ),

        sigma: toNumber(
          cols[dim.column + 1]
        )
      };

    });

    rowIndex++;
  }

  return rowIndex;
}

/**
 * Fonction principale.
 */
function convertCsvToJson(csvContent) {

  const result = {};

  const lines = csvContent
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);

  let i = 0;

  while (i < lines.length) {

    if (isSectionLine(lines[i])) {

      i = parseSection(
        lines,
        i,
        result
      );

      continue;
    }

    i++;
  }

  return result;
}

/**
 * Programme principal
 */

const csvContent =
  fs.readFileSync(
    "./normes.csv",
    "utf8"
  );

const json =
  convertCsvToJson(
    csvContent
  );

fs.writeFileSync(
  "./normes.json",
  JSON.stringify(
    json,
    null,
    2
  )
);

console.log(
  "Conversion terminée."
);
