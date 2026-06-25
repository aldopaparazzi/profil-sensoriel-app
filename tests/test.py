import json
from pprint import pprint
from pipeline.scoring import compute_domain_scores

from collections import Counter
import sys
from pathlib import Path

#sys.path.append(str(Path(__file__).resolve().parents[1]))

def audit_reference_vs_normes(reference_path, normes_path):
    print(reference_path)
    print(normes_path)
    with open(reference_path, "r", encoding="utf-8") as f:
        reference = json.load(f)

    with open(normes_path, "r", encoding="utf-8") as f:
        normes = json.load(f)

    print("\n=== AUDIT REFERENCE vs NORMES ===")

    total_missing_domains = 0
    total_missing_age_groups = 0

    for form_name, form_ref in reference.items():

        print(f"\n--- FORM: {form_name} ---")

        questions = form_ref.get("questions", {})

        # -----------------------------
        # 1. collect domains reference
        # -----------------------------
        ref_domains = set()
        ref_age_groups = set()

        for _, meta in questions.items():
            domain = meta.get("domaine_sensoriel")
            if domain:
                ref_domains.add(domain)

        # -----------------------------
        # 2. check norms structure
        # -----------------------------
        form_norms = normes.get(form_name)

        if not form_norms:
            print("❌ Missing form in norms")
            continue

        age_groups = form_norms.keys()

        # -----------------------------
        # 3. domain check per age group
        # -----------------------------
        for age_group, age_block in form_norms.items():

            metric_table = age_block.get("domaines_sensoriels", {})

            norm_domains = set(metric_table.keys())

            missing = ref_domains - norm_domains
            extra = norm_domains - ref_domains

            if missing:
                print(f"⚠️ AgeGroup {age_group} missing domains:")
                for d in missing:
                    print("   -", d)
                total_missing_domains += len(missing)

            if extra:
                print(f"ℹ️ AgeGroup {age_group} extra domains:")
                for d in extra:
                    print("   -", d)

            # age group tracking
            ref_age_groups.add(age_group)

        # -----------------------------
        # 4. sanity check age groups
        # -----------------------------
        expected_age_groups = set(form_norms.keys())

        print("\nAge groups in norms:", expected_age_groups)

        if not expected_age_groups:
            print("❌ No age groups found")

    print("\n=== SUMMARY ===")
    print("Missing domains total:", total_missing_domains)
    print("Missing age groups total:", total_missing_age_groups)
    if total_missing_domains == 0:
        print("\n✅ Normes cohérentes avec la référence")
    else:
        print("\n⚠️ Incohérences détectées → scoring partiel possible")

def audit_reference_vs_mapping(reference_path, mapped_path):


    import json
    from collections import Counter

    with open(reference_path, "r", encoding="utf-8") as f:
        reference = json.load(f)

    with open(mapped_path, "r", encoding="utf-8") as f:
        mapped = json.load(f)

    print("\n=== MAPPING AUDIT START ===")
    print(reference_path)
    print(mapped_path)
    # -----------------------------
    # ON BOUCLE SUR LES FORMS
    # -----------------------------
    for form_name, form_ref in reference.items():

        print(f"\n--- FORM: {form_name} ---")

        questions = form_ref.get("questions", {})

        print("Questions:", len(questions))

        pour_calcul_true = 0
        missing_fields = 0

        domains = Counter()
        quadrants = Counter()

        for qid, meta in questions.items():

            if "pour_calcul" not in meta:
                missing_fields += 1
            elif meta["pour_calcul"] is True:
                pour_calcul_true += 1

            domains[meta.get("domaine_sensoriel")] += 1
            quadrants[meta.get("quadrant")] += 1

        print("pour_calcul TRUE:", pour_calcul_true)
        print("missing pour_calcul:", missing_fields)

        print("\nDomains:")
        for k, v in domains.items():
            print(" ", k, "→", v)

        print("\nQuadrants:")
        for k, v in quadrants.items():
            print(" ", k, "→", v)

    print("\n=== AUDIT END ===")

def test_scoring_from_mapped_file():
    print("🚀 TEST START")
    # =========================================================
    # 1. charger données mapping réelles
    # =========================================================
    with open("data/mapped/scolaire.json", "r", encoding="utf-8") as f:
        mapped = json.load(f)

    # =========================================================
    # 2. charger normes
    # =========================================================
    with open("data/reference/normes.json", "r", encoding="utf-8") as f:
        norms = json.load(f)

    # =========================================================
    # 3. construire context minimal
    # =========================================================
    context = {
        "mapped": {"scolaire": mapped},
        "norms": norms,
        "scores": {}
    }
#    pprint(mapped)
#    print("type(mapped) =", type(mapped))
#    print("keys =", context["mapped"].keys())

    # =========================================================
    # 4. exécuter scoring
    # =========================================================
    result = compute_domain_scores(
        mapped_submissions=context["mapped"]["scolaire"],
        normes=norms,
        form_name="scolaire"
    )

    context["scores"]["scolaire"] = result
    # =========================================================
    # 5. assertions simples (smoke test)
    # =========================================================
    result = compute_domain_scores(
        mapped_submissions=context["mapped"]["scolaire"],
        normes=norms,
        form_name="scolaire"
    )

    assert isinstance(result, dict)
    assert len(result) > 0

    # aucun crash silencieux attendu
    for sub in result.values():
        for domain, values in sub.items():
            assert "raw" in values
            assert "z" in values

    pprint(result)

    print("\n✔ scoring OK")
    
# =========================================================
# EXECUTION DIRECTE
# =========================================================
# test_scoring_from_mapped_file()
audit_reference_vs_mapping(
    "data/reference/reference.json",
    "data/mapped/scolaire.json"
)
audit_reference_vs_normes(
    "data/reference/reference.json",
    "data/reference/normes.json"
)
