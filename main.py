# D:\Documents\CAO\VSCode\profil-sensoriel-app\main.py
from config import DEBUG_DIR
from ingestion.import_data import run as run_import
from pathlib import Path
from pipeline.split import split_patient_responses
from pipeline.map import map_questions
from config.sources import GOOGLE_SHEETS

def main():

    # =========================================================
    # IMPORT
    # =========================================================

    print("=== IMPORT ===")

    datasets = run_import()

    # datasets =
    # {
    #   "enfant": df,
    #   "jeune_enfant": df,
    #   "scolaire": df
    # }

    # =========================================================
    # PIPELINE
    # =========================================================

    print("\n=== PIPELINE ===")

    for form_type, df in datasets.items():

        print(f"\n--- {form_type} ---")

        # -----------------------------------------------------
        # SPLIT
        # -----------------------------------------------------

        patients, responses = split_patient_responses(
            df,
            debug=True,
            name=form_type
        )

        print(f"patients: {len(patients)}")
        print(f"responses: {len(responses)}")

        # -----------------------------------------------------
        # MAP
        # -----------------------------------------------------

        print(f"\n=== MAP {form_type} ===")

        mapped = map_questions(
            responses,
            form_type=form_type,
            debug=True
        )

        print(mapped.head())
        # =====================================================
        # DEBUG EXPORT (AJOUT ICI)
        # =====================================================

        debug_dir = Path("data/debug")
        debug_dir.mkdir(parents=True, exist_ok=True)

        output_path = debug_dir / f"{form_type}_mapped.csv"
        mapped.to_csv(output_path, index=False, encoding="utf-8")

        print(f"[DEBUG] mapped saved → {output_path}")
        
    print("\nOK pipeline terminé")


if __name__ == "__main__":
    main()