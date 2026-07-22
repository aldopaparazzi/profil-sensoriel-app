"""
📊 PROFIL SENSORIEL - TABLEAU DE BORD STREAMLIT
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import webbrowser
from typing import Dict

from main import import_forms
from reporting.html import generate_html_report
from reporting.odt import generate_bilan
from reporting.paths import HTML_DIR, JSON_DIR, BILAN_DIR
from config.settings import load_config, sauvegarder_token
from ingestion.fetch_tally import check_token_valid

st.set_page_config(
    page_title="Profil Sensoriel - Tableau de bord",
    page_icon="favicon_io/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

FORM_TYPES = {
    "enfant": "🧒 Enfant",
    "jeune_enfant": "👶 Jeune enfant",
    "scolaire": "🎓 Scolaire",
}

@st.cache_data(ttl=300)
def verifier_token_cached(token: str) -> bool:
    """Vérifie le token avec mise en cache de 5 minutes."""
    if not token:
        return False
    return check_token_valid(token)

@st.cache_data(ttl=60)
def scan_reports() -> pd.DataFrame:
    """Scanne le dossier des rapports HTML et retourne un DataFrame."""
    reports = []
    if not HTML_DIR.exists():
        return pd.DataFrame()
    
    for html_file in HTML_DIR.glob("*.html"):
        filename = html_file.stem
        json_path = JSON_DIR / f"{filename}.json"
        
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                patient = data.get("patient", {})
                nom = patient.get("nom", "Inconnu").capitalize()
                prenom = patient.get("prenom", "Inconnu").capitalize()
                form_type = patient.get("form_type") or patient.get("form_name") or "unknown"
                date_str = patient.get("evaluation_date") or patient.get("submitted_at") or "unknown_date"
                
                date = None
                if isinstance(date_str, str):
                    try:
                        date = datetime.fromisoformat(date_str.replace("Z", ""))
                    except ValueError:
                        pass
                
                reports.append({
                    "nom": nom,
                    "prenom": prenom,
                    "form_type": form_type,
                    "form_label": FORM_TYPES.get(form_type, form_type),
                    "date": date,
                    "date_str": date_str,
                    "path": html_file,
                    "filename": filename,
                    "has_json": True,
                })
                continue
            except (OSError, json.JSONDecodeError):
                pass
        
        # Fallback si le JSON n'existe pas
        parts = filename.split("_")
        nom = parts[0].capitalize() if len(parts) > 0 and parts[0] != "unknown" else "Inconnu"
        prenom = parts[1].capitalize() if len(parts) > 1 and parts[1] != "unknown" else "Inconnu"
        form_type = parts[2] if len(parts) > 2 and parts[2] in FORM_TYPES else "unknown"
        date_str = parts[3] if len(parts) > 3 else "unknown_date"
        
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date = None
        
        reports.append({
            "nom": nom,
            "prenom": prenom,
            "form_type": form_type,
            "form_label": FORM_TYPES.get(form_type, form_type),
            "date": date,
            "date_str": date_str,
            "path": html_file,
            "filename": filename,
            "has_json": json_path.exists(),
        })
    
    df = pd.DataFrame(reports)
    if not df.empty and "date" in df.columns:
        df = df.sort_values("date", ascending=False)
    return df

@st.cache_data(ttl=60)
def get_stats() -> Dict:
    """Calcule les statistiques globales."""
    df = scan_reports()
    stats = {"total": len(df), "by_form": {}, "last_update": None}
    if not df.empty:
        stats["by_form"] = df["form_label"].value_counts().to_dict()
        if "date" in df.columns:
            latest = df["date"].max()
            if latest:
                stats["last_update"] = latest.strftime("%d/%m/%Y")
    return stats

def load_html_content(html_path: Path) -> str:
    """Charge le contenu d'un fichier HTML."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"Erreur lors du chargement du HTML: {e}")
        return ""

def regenerate_report(filename: str) -> bool:
    """Régénère un rapport à partir de son JSON."""
    json_path = JSON_DIR / f"{filename}.json"
    if not json_path.exists():
        st.error(f"Fichier JSON non trouvé: {json_path}")
        return False
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        output_path = HTML_DIR / f"{filename}.html"
        generate_html_report(data, output_path)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la régénération: {e}")
        return False

def regenerate_all_reports() -> int:
    """Régénère tous les rapports à partir des JSON existants."""
    success_count = 0
    for json_file in JSON_DIR.glob("*.json"):
        filename = json_file.stem
        if regenerate_report(filename):
            success_count += 1
    return success_count

def dashboard():
    """Fonction principale de l'application."""
    df = scan_reports()
    config = load_config()
    
    # --- SIDEBAR ---
    with st.sidebar:
        # ---- SECTION TOKEN TALLY (repliable) ----
        token_actuel = config.get("tally_token", "")

        # Vérifier l'état du token (avec cache)
        token_valide = verifier_token_cached(token_actuel) if token_actuel else False

        if token_valide:
            # Token valide → section repliée par défaut, juste un indicateur vert
            with st.expander("🔑 Token Tally 🟢", expanded=False):
                
                afficher = False #st.checkbox("👁 Afficher le token", value=False)
                
                if afficher:
                    nouveau_token = st.text_input(
                        "Token API",
                        value=token_actuel,
                        type="default",
                        key="token_visible_valid"
                    )
                else:
                    nouveau_token = st.text_input(
                        "Token API",
                        value="••••••••••••••••",
                        type="password",
                        key="token_hidden_valid"
                    )
                    if nouveau_token == "••••••••••••••••":
                        nouveau_token = token_actuel
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🧪 Tester", use_container_width=True, key="test_valid"):
                        if nouveau_token and check_token_valid(nouveau_token):
                            st.success("✅ Token valide !")
                            verifier_token_cached.clear()
                        else:
                            st.error("❌ Token invalide")
                
                with col2:
                    if st.button("💾 Sauvegarder", use_container_width=True, key="save_valid"):
                        if nouveau_token and nouveau_token != token_actuel:
                            if sauvegarder_token(nouveau_token):
                                st.success("✅ Token sauvegardé !")
                                verifier_token_cached.clear()
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la sauvegarde")
                        else:
                            st.info("ℹ️ Token inchangé")

                st.success("✅ Token configuré et valide")

        else:
            # Token absent ou invalide → section dépliée, avec avertissement visible
            with st.expander("🔑 Token Tally 🔴", expanded=True):
                if not token_actuel:
                    st.warning("🟡 Aucun token configuré")
                else:
                    st.error("🔴 Token configuré mais invalide")
                
                nouveau_token = st.text_input(
                    "Token API",
                    value="",
                    type="password",
                    placeholder="Collez votre token Tally ici...",
                    key="token_input_new"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🧪 Tester", use_container_width=True, key="test_invalid"):
                        if not nouveau_token:
                            st.warning("⚠️ Aucun token saisi")
                        elif check_token_valid(nouveau_token):
                            st.success("✅ Token valide !")
                        else:
                            st.error("❌ Token invalide")
                
                with col2:
                    if st.button("💾 Sauvegarder", use_container_width=True, type="primary", key="save_invalid"):
                        if not nouveau_token:
                            st.warning("⚠️ Aucun token à sauvegarder")
                        elif sauvegarder_token(nouveau_token):
                            st.success("✅ Token sauvegardé !")
                            verifier_token_cached.clear()
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la sauvegarde")
        
        st.divider()
        
        # ---- SECTION ACTIONS ----
        st.header("⚡ Actions")
        
        if df.empty:
            st.warning("Aucun rapport trouvé. Lancez l'importation pour générer des rapports.")
        
        if st.button("🔄 Rafraîchir la liste", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("📥 Télécharger les nouveaux rapports", use_container_width=True):
            if not token_actuel:
                st.error("❌ Configurez d'abord un token Tally valide")
            else:
                with st.spinner("Téléchargement en cours..."):
                    count = import_forms()
                st.success(f"✅ {count} rapport(s) téléchargé(s)")
                st.cache_data.clear()
                st.rerun()
        
        if st.button("🔄 Régénérer tous les rapports", use_container_width=True):
            with st.spinner("Régénération en cours..."):
                count = regenerate_all_reports()
            st.success(f"✅ {count} rapport(s) régénéré(s)")
            st.cache_data.clear()
        
        if st.button("📄 Générer le bilan", use_container_width=True):
            filename = st.session_state.get("selected_report")
            if not filename:
                st.warning("Aucun rapport sélectionné")
            else:
                result = generate_bilan(filename)
                if result["status"] == "ok":
                    st.success("✅ Bilan généré et ouvert dans LibreOffice")
                elif result["status"] == "warning":
                    st.warning("⚠️ Bilan généré mais LibreOffice n'a pas pu s'ouvrir")
                    st.write("📁 Fichier :", result["file"])
                    with open(result["file"], "rb") as f:
                        st.download_button(
                            "📥 Télécharger le bilan",
                            f,
                            file_name=result["file"].name
                        )
                else:
                    st.error(f"❌ Erreur : {result['error']}")
        
        st.divider()
        st.header("📊 Statistiques")
        stats = get_stats()
        if stats["by_form"]:
            st.write("**Par formulaire:**")
            for form, count in stats["by_form"].items():
                st.write(f"• {form}: {count}")
        st.metric("Dernière mise à jour", stats.get("last_update", "N/A"))
        st.metric("Total rapports", stats["total"])
    
    # --- CONTENU PRINCIPAL ---
    col_view, col_list = st.columns([3, 1])
    
    with col_list:
        st.subheader(f"📄 Rapports ({len(df)})")
        
        search_term = st.text_input(
            "🔎 Rechercher",
            placeholder="Nom ou prénom...",
            help="Recherche dans les noms et prénoms",
        )
        
        form_options = ["Tous"] + list(FORM_TYPES.values())
        selected_form = st.selectbox("📋 Formulaire", form_options)
        
        st.divider()
        
        # Application des filtres
        filtered_df = df.copy()
        if search_term:
            mask = filtered_df["nom"].str.contains(search_term, case=False, na=False) | \
                   filtered_df["prenom"].str.contains(search_term, case=False, na=False)
            filtered_df = filtered_df[mask]
        if selected_form != "Tous":
            filtered_df = filtered_df[filtered_df["form_label"] == selected_form]
        
        # Liste des rapports
        options = []
        for _, row in filtered_df.iterrows():
            label = f"{row['prenom']} {row['nom']}"
            if pd.notna(row["date"]):
                label += f" ({row['date'].strftime('%d/%m/%Y')})"
            label += f" - {row['form_label']}"
            options.append((row["filename"], label))
        
        if options:
            selected_option = st.radio(
                "Sélectionner un rapport",
                options,
                index=None,
                format_func=lambda x: x[1],
                key="report_radio",
            )
            if selected_option:
                st.session_state.selected_report = selected_option[0]
                if st.button("🔄 Régénérer ce rapport", use_container_width=True):
                    if regenerate_report(selected_option[0]):
                        st.success("✅ Rapport régénéré")
                        st.cache_data.clear()
                        st.rerun()
        
        if "selected_report" in st.session_state:
            filename = st.session_state.selected_report
            html_path = HTML_DIR / f"{filename}.html"
            if html_path.exists():
                if st.button("🌐 Ouvrir dans le navigateur", use_container_width=True):
                    webbrowser.open(str(html_path))
    
    # --- AFFICHAGE DU RAPPORT ---
    with col_view:
        if "selected_report" in st.session_state:
            filename = st.session_state.selected_report
            html_path = HTML_DIR / f"{filename}.html"
            if html_path.exists():
                html_content = load_html_content(html_path)
                components.html(html_content, height=1590, scrolling=True)
            else:
                st.error(f"❌ Fichier HTML non trouvé: {html_path}")
        else:
            st.info("Sélectionnez un rapport dans la liste à droite 👉")

if __name__ == "__main__":
    dashboard()