# scripts/show_last_seen.py

#!/usr/bin/env python
"""Affiche les derniers IDs vus."""

from storage.last_seen import load_last_seen

def main():
    data = load_last_seen()
    
    if not data:
        print("📭 Aucun ID enregistré")
        return
    
    print("\n📋 DERNIERS IDs VUS\n")
    print("-" * 70)
    print(f"{'Formulaire':<15} {'Dernier ID':<25} {'Date':<25}")
    print("-" * 70)
    
    for form_name, info in data.items():
        last_id = info.get("last_id", "inconnu")
        last_date = info.get("last_date", "inconnue")
        print(f"{form_name:<15} {last_id:<25} {last_date:<25}")
    
    print("-" * 70)

if __name__ == "__main__":
    main()