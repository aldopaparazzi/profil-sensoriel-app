# run.py
"""
Lanceur interactif pour le Profil Sensoriel.
Menu simple pour démarrer/arrêter les services.
"""

import os
import subprocess
import time
import platform
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.is_windows = platform.system() == "Windows"

    def clear_screen(self):
        os.system("cls" if self.is_windows else "clear")

    def print_header(self):
        self.clear_screen()
        print("=" * 60)
        print("  🧠  PROFIL SENSORIEL - GESTIONNAIRE  🧠")
        print("=" * 60)
        print()

    def print_menu(self):
        print("📋 MENU PRINCIPAL")
        print("-" * 40)
        print("  1. 🚀 Lancer le dashboard Streamlit")
        print("  2. 📥 Importer les nouveaux rapports")
        print("  3. 🔄 Régénérer tous les rapports HTML")
        print("  4. 📊 Voir les statistiques")
        print("  5. 🛑 Arrêter tous les services")
        print("  6. ❌ Quitter")
        print()

    def redraw_menu(self):
        self.print_header()
        self.print_menu()

    def start_dashboard(self):
        if "dashboard" in self.processes and self.processes["dashboard"].poll() is None:
            print("⚠️ Dashboard déjà en cours")
            input("Entrée...")
            return
        
        print("🚀 Lancement du dashboard...")
        print("📍 Accès: http://localhost:8501")
        print("⏹️  Ctrl+C pour arrêter")
        print()

        cmd = ["streamlit", "run", "dashboard.py", "--server.port", "8501"]

        if self.is_windows:
            creationflags = (
                subprocess.CREATE_NEW_CONSOLE
                if hasattr(subprocess, "CREATE_NEW_CONSOLE")
                else 0
            )
            process = subprocess.Popen(
                "streamlit run dashboard.py --server.port 8501",
                shell=True,
                creationflags=creationflags,
            )
        else:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        self.processes["dashboard"] = process
        print("✅ Dashboard lancé (PID: {})".format(process.pid))
        print()
        input("Appuyez sur Entrée pour revenir au menu...")

    def import_reports(self):
        print("📥 Importation des nouveaux rapports...")
        print()

        try:
            from main import import_forms
            import_forms(force_refresh=False)
        except Exception as e:
            print(f"❌ Erreur: {e}")

        print()

    def regenerate_html(self):
        print("🔄 Régénération des rapports HTML...")
        print()

        try:
            from reporting.html import batch_generate_html
            from pathlib import Path

            report_dir = Path("data/report")
            html_dir = Path("data/report/html")

            html_dir.mkdir(parents=True, exist_ok=True)
            batch_generate_html(report_dir, html_dir)
            print("✅ Régénération terminée")
        except Exception as e:
            print(f"❌ Erreur: {e}")

        print()

    def show_stats(self):
        print("📊 Statistiques")
        print("-" * 40)
        print()

        try:
            from dashboard import scan_reports, get_stats

            stats = get_stats()
            df = scan_reports()

            print(f"📄 Total rapports: {stats['total']}")
            print(f"📅 Dernière mise à jour: {stats.get('last_update', 'N/A')}")
            print()
            print("📋 Par formulaire:")
            for form, count in stats.get("by_form", {}).items():
                print(f"   • {form}: {count}")

            if (
                df is not None
                and hasattr(df, "empty")
                and not df.empty
                and "date" in df.columns
            ):
                print()
                print("🗓️  Répartition par date:")
                latest = df["date"].max()
                earliest = df["date"].min()
                print(
                    f"   • Plus récent: {latest.strftime('%d/%m/%Y') if latest else 'N/A'}"
                )
                print(
                    f"   • Plus ancien: {earliest.strftime('%d/%m/%Y') if earliest else 'N/A'}"
                )
        except Exception as e:
            print(f"❌ Erreur: {e}")

        print()
        input("Appuyez sur Entrée pour revenir au menu...")

    def stop_services(self, force=False):
        print("🛑 Arrêt des services...")

        for name, process in self.processes.items():
            try:
                if self.is_windows:
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                    else:
                        process.terminate()
                        time.sleep(1)
                        if process.poll() is None:
                            process.kill()
                    process.wait(timeout=2)
                print(f"✅ {name} arrêté")
            except Exception as e:
                print(f"⚠️  Erreur pour {name}: {e}")

        self.processes.clear()
        print()

    # ⚠️ IMPORTANT : Cette méthode doit être à l'intérieur de la classe
    def run(self):
        self.redraw_menu()
        import sys
        print(sys.executable)

        while True:
            try:
                choice = input("👉 Votre choix: ").strip()
            except KeyboardInterrupt:
                self.stop_services(True)
                break

            self.redraw_menu()

            if choice == "1":
                self.start_dashboard()
            elif choice == "2":
                self.import_reports()
            elif choice == "3":
                self.regenerate_html()
            elif choice == "4":
                self.show_stats()
            elif choice == "5":
                self.stop_services()
            elif choice == "6":
                print("\n👋 Au revoir !")
                self.stop_services(True)
                break
            else:
                print("❌ Choix invalide")
                time.sleep(1)

if __name__ == "__main__":
    manager = ServiceManager()
    manager.run()