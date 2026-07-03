# app\dashboard.py
"""
📊 PROFIL SENSORIEL - TABLEAU DE BORD STREAMLIT

Application Streamlit pour visualiser les rapports générés par le pipeline.
Fonctionnalités :
- Liste des rapports disponibles (scannage du dossier data/report/html/)
- Filtrage par nom, formulaire, date
- Visualisation HTML dans un iframe
- Statistiques sur les rapports
- Régénération à la demande

Auteur: Profil Sensoriel Team
Version: 1.0
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from datetime import datetime
#import re
import json
import webbrowser
from typing import Dict #, List, Optional
from main import import_forms

# ============================================================================
# 1. CONFIGURATION DE LA PAGE
# ============================================================================

st.set_page_config(
    page_title="Profil Sensoriel - Tableau de bord",
    page_icon="favicon_io/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 2. CHEMINS ET CONSTANTES
# ============================================================================

# Dossier contenant les rapports HTML générés
HTML_DIR = Path("data/report/html")
# Dossier contenant les rapports JSON (pour la régénération)
REPORT_DIR = Path("data/report/json")
# Dossier des données brutes (pour les stats)
RAW_DIR = Path("data/raw")

# Types de formulaires
FORM_TYPES = {
    "enfant": "🧒 Enfant",
    "jeune_enfant": "👶 Jeune enfant",
    "scolaire": "🎓 Scolaire"
}

# ============================================================================
# 3. FONCTIONS DE CHARGEMENT DES DONNÉES
# ============================================================================

@st.cache_data(ttl=60)  # Cache de 60 secondes
def scan_reports() -> pd.DataFrame:
    """
    Scanne le dossier des rapports HTML et retourne un DataFrame.
    Extraction des infos depuis les fichiers JSON associés.
    """
    reports = []
    
    if not HTML_DIR.exists():
        return pd.DataFrame()
    
    # Parcourir tous les fichiers HTML
    for html_file in HTML_DIR.glob("*.html"):
        filename = html_file.stem
        
        # Essayer de charger le JSON correspondant
        json_path = REPORT_DIR / f"{filename}.json"
        
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                patient = data.get("patient", {})
                nom = patient.get("nom", "Inconnu").capitalize()
                prenom = patient.get("prenom", "Inconnu").capitalize()
                form_type = patient.get("form_type") or patient.get("form_name") or "unknown"
                date_str = patient.get("evaluation_date") or patient.get("submitted_at") or "unknown_date"
                
                # Parser la date
                date = None             # La bonne pratique consiste à initialiser date avant le if
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
                    "has_json": True
                })
                continue  # Traité avec succès
            except (OSError, json.JSONDecodeError):
                pass  # Fallback au parsing du nom
        
        # Fallback: parsing du nom de fichier
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
            "has_json": json_path.exists()
        })
    
    # Trier par date décroissante
    df = pd.DataFrame(reports)
    if not df.empty and "date" in df.columns:
        df = df.sort_values("date", ascending=False)
    
    return df

@st.cache_data(ttl=60)
def get_stats() -> Dict:
    """
    Calcule les statistiques globales.
    
    Returns:
        Dict: Statistiques (total, par formulaire, etc.)
    """
    df = scan_reports()
    
    stats = {
        "total": len(df),
        "by_form": {},
        "last_update": None
    }
    
    if not df.empty:
        stats["by_form"] = df["form_label"].value_counts().to_dict()
        
        if "date" in df.columns:
            latest = df["date"].max()
            if latest:
                stats["last_update"] = latest.strftime("%d/%m/%Y")
    
    return stats

def load_html_content(html_path: Path) -> str:
    """
    Charge le contenu d'un fichier HTML.
    
    Args:
        html_path: Chemin vers le fichier HTML
    
    Returns:
        str: Contenu HTML
    """
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"Erreur lors du chargement du HTML: {e}")
        return ""

def regenerate_report(filename: str) -> bool:
    """
    Régénère un rapport à partir de son JSON.
    
    Args:
        filename: Nom du fichier (sans extension)
    
    Returns:
        bool: True si réussi, False sinon
    """
    json_path = REPORT_DIR / f"{filename}.json"
    
    if not json_path.exists():
        st.error(f"Fichier JSON non trouvé: {json_path}")
        return False
    
    try:
        # Importer la fonction de génération HTML
        from reporting.generate_html import generate_html_report
        
        # Charger les données
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Charger la référence
        ref_path = Path("data/reference/reference.json")
        with open(ref_path, "r", encoding="utf-8") as f:
            reference = json.load(f)
        
        # Générer le HTML
        output_path = HTML_DIR / f"{filename}.html"
        generate_html_report(data, reference, output_path)
        
        return True
    except Exception as e:
        st.error(f"Erreur lors de la régénération: {e}")
        return False

def regenerate_all_reports() -> int:
    """
    Régénère tous les rapports à partir des JSON existants.
    
    Returns:
        int: Nombre de rapports régénérés
    """
    success_count = 0
    
    for json_file in REPORT_DIR.glob("*.json"):
        filename = json_file.stem
        if regenerate_report(filename):
            success_count += 1
    
    return success_count

# ============================================================================
# 4. INTERFACE PRINCIPALE
# ============================================================================

def dashboard():
    """
    Fonction principale de l'application.
    """
    # --- En-tête ---
    #st.title("📊 Profil Sensoriel - Tableau de bord")
    #st.markdown("*Visualisation et gestion des rapports générés*")
    
    # --- Barre latérale ---
    with st.sidebar:
        #st.header("🔍 Filtres")
        
        # Chargement des données
        df = scan_reports()

        if df.empty:
            st.warning("Aucun rapport trouvé. Lancez `main.py` pour générer des rapports.")
            if st.button("Télécharger"):
                count = import_forms()  
                st.success(f"✅ {count} rapport(s) téléchargé(s)")
                st.cache_data.clear()
                st.rerun()
            return
        
        # Filtre: Recherche par nom
        search_term = st.text_input(
            "🔎 Rechercher",
            placeholder="Nom ou prénom...",
            help="Recherche dans les noms et prénoms"
        )
        
        # Filtre: Formulaire
        form_options = ["Tous"] + list(FORM_TYPES.values())
        selected_form = st.selectbox("📋 Formulaire", form_options)
        
        ## Filtre: Date (si disponible)
        #if "date" in df.columns and not df["date"].isna().all():
        #    min_date = df["date"].min()
        #    max_date = df["date"].max()
        #    date_range = st.date_input(
        #        "📅 Période",
        #        value=(min_date, max_date),
        #        min_value=min_date,
        #        max_value=max_date
        #    )
        #else:
        #    date_range = None
        
        # --- Actions ---
        #st.divider()
        st.header("⚡ Actions")
        
        # Bouton de rafraîchissement
        if st.button("🔄 Rafraîchir la liste", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            st.toast("✅ Cache data cleared",duration="short")

        # Bouton de téléchargement
        if st.button("📥 Télécharger les nouveaux rapports", use_container_width=True):
            with st.spinner("Téléchargement..."):
                count = import_forms()
            st.success(f"✅ {count} rapport(s) téléchargé(s)")
            st.toast(f"✅ {count} rapports téléchargés",duration="short")
            st.cache_data.clear()
            #st.rerun()

        # Bouton de régénération
#        if st.button("🔁 Régénérer le rapport sélectionné", use_container_width=True):
#            if "selected_report" in st.session_state:
#                filename = st.session_state.selected_report
#                if regenerate_report(filename):
#                    st.success(f"✅ Rapport régénéré: {filename}")
#                    st.cache_data.clear()
#                    st.rerun()
#            else:
#                st.warning("Veuillez sélectionner un rapport d'abord")
        
        # Bouton de régénération en lot
        if st.button("🔄 Régénérer tous les rapports", use_container_width=True):
            with st.spinner("Régénération en cours..."):
                count = regenerate_all_reports()
            st.success(f"✅ {count} rapport(s) régénéré(s)")
            st.cache_data.clear()
            #st.rerun()
        
        # --- Statistiques ---
        #st.divider()
        st.header("📊 Statistiques")
        
        stats = get_stats()
        #col1, col2 = st.columns(2)
        #col1.
        if stats["by_form"]:
            st.write("**Par formulaire:**")
            for form, count in stats["by_form"].items():
                st.write(f"  • {form}: {count}")
        st.metric("Dernière mise à jour", stats.get("last_update", "N/A"))
        #col1.
        st.metric("Total rapports", stats["total"])
        

    
    # --- Corps principal ---
    
    # Application des filtres
    filtered_df = df.copy()
    
    if search_term:
        mask = (
            filtered_df["nom"].str.contains(search_term, case=False, na=False) |
            filtered_df["prenom"].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if selected_form != "Tous":
        filtered_df = filtered_df[filtered_df["form_label"] == selected_form]
    
    #if date_range and len(date_range) == 2:
    #    start_date, end_date = date_range
    #    mask = (filtered_df["date"] >= pd.Timestamp(start_date)) & \
    #           (filtered_df["date"] <= pd.Timestamp(end_date))
    #    filtered_df = filtered_df[mask]
    
    # --- Affichage des résultats ---
    
    if filtered_df.empty:
        st.info("Aucun rapport ne correspond aux filtres sélectionnés.")
        return
    
    # Séparer l'écran en deux colonnes
    col_view, col_list = st.columns([3, 1]) # [ratio]
    
    # Colonne de gauche: Liste des rapports
    
    with col_list:
        st.subheader(f"📄 Rapports ({len(filtered_df)})")
        
        # Créer les options
        options = []
        for _, row in filtered_df.iterrows():
            label = f"{row['prenom']} {row['nom']}"
            #if row["date"]:
            if pd.notna(row["date"]):
                label += f" ({row['date'].strftime('%d/%m/%Y')})"
            label += f" - {row['form_label']}"
            options.append((row["filename"], label))
        
        if options:
            # Sélection radio avec format personnalisé
            selected_option = st.radio(
                "Sélectionner un rapport",
                options,
                format_func=lambda x: x[1],
                key="report_radio"
            )
            
            if selected_option:
                st.session_state.selected_report = selected_option[0]
        
        # Bouton pour ouvrir dans le navigateur
        if "selected_report" in st.session_state:
            filename = st.session_state.selected_report
            html_path = HTML_DIR / f"{filename}.html"
            if html_path.exists():
                if st.button("🌐 Ouvrir dans le navigateur", use_container_width=True):
                    webbrowser.open(str(html_path))

    # Colonne de droite: Visualisation HTML
    with col_view:
        #st.subheader("👁️ Aperçu du rapport")
        
        if "selected_report" in st.session_state:
            filename = st.session_state.selected_report
            html_path = HTML_DIR / f"{filename}.html"
            
            if html_path.exists():
                html_content = load_html_content(html_path)
                # Afficher dans un iframe
                # height = int(st.session_state.get("window_height", 900))
                #st.components.v1.html(html_content, height=700, scrolling=True)
                #st.iframe(html_content, height=600)
                components.html(html_content, height=1590, scrolling=True)
                #st.iframe(html_content, height=height)
            else:
                st.error(f"Fichier HTML non trouvé: {html_path}")
        else:
            st.info("Sélectionnez un rapport dans la liste à gauche")

# ============================================================================
# 5. POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    dashboard()