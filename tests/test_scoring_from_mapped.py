import json
from pprint import pprint
from pipeline.scoring import compute_domain_scores


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
test_scoring_from_mapped_file()