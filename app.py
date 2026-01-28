from datetime import date
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from engine.ahp_logic import AHPEngine
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import time
from engine.data_loader import get_zone_context, get_available_zones

# --- ÉCRAN DE CHARGEMENT ---
def show_loading_screen():
    """Affiche un écran de chargement avec animations"""
    st.markdown("""
    <style>
    .loading-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    
    .geometric-loader {
        width: 80px;
        height: 80px;
        position: relative;
        margin-bottom: 30px;
    }
    
    .geometric-loader div {
        position: absolute;
        width: 16px;
        height: 16px;
        background: #0066cc;
        border-radius: 50%;
        animation: geometric-move 1.2s linear infinite;
    }
    
    .geometric-loader div:nth-child(1) {
        top: 8px;
        left: 8px;
        animation-delay: 0s;
    }
    
    .geometric-loader div:nth-child(2) {
        top: 8px;
        left: 32px;
        animation-delay: -0.4s;
    }
    
    .geometric-loader div:nth-child(3) {
        top: 8px;
        left: 56px;
        animation-delay: -0.8s;
    }
    
    .geometric-loader div:nth-child(4) {
        top: 32px;
        left: 8px;
        animation-delay: -0.4s;
    }
    
    .geometric-loader div:nth-child(5) {
        top: 32px;
        left: 32px;
        animation-delay: -0.8s;
    }
    
    .geometric-loader div:nth-child(6) {
        top: 32px;
        left: 56px;
        animation-delay: -1.2s;
    }
    
    .geometric-loader div:nth-child(7) {
        top: 56px;
        left: 8px;
        animation-delay: -0.8s;
    }
    
    .geometric-loader div:nth-child(8) {
        top: 56px;
        left: 32px;
        animation-delay: -1.2s;
    }
    
    .geometric-loader div:nth-child(9) {
        top: 56px;
        left: 56px;
        animation-delay: -1.6s;
    }
    
    @keyframes geometric-move {
        0%, 100% {
            transform: scale(0);
            opacity: 0;
        }
        50% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .loading-text {
        font-size: 1.2rem;
        color: #003366;
        font-weight: 600;
        margin-top: 20px;
        text-align: center;
    }
    
    .loading-subtext {
        color: #666;
        margin-top: 10px;
        font-size: 0.9rem;
    }
    </style>
    
    <div class="loading-container">
        <div class="geometric-loader">
            <div></div><div></div><div></div>
            <div></div><div></div><div></div>
            <div></div><div></div><div></div>
        </div>
        <div class="loading-text">Chargement de l'analyse décisionnelle</div>
        <div class="loading-subtext">Initialisation des modules AHP, carte et calculs financiers...</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Pause pour montrer l'animation (optionnel)
    time.sleep(1.5)

def create_radar_chart(camwater_scores, forage_scores, hybride_scores):
    """
    Crée un graphique radar pour comparer les performances des options
    sur les 3 critères : Coût, Disponibilité, Accessibilité
    """
    categories = ['Coût', 'Disponibilité', 'Accessibilité']
    
    fig = go.Figure()
    
    # Courbe pour CAMWATER
    fig.add_trace(go.Scatterpolar(
        r=camwater_scores,
        theta=categories,
        fill='toself',
        name='CAMWATER',
        line_color='#003399',
        fillcolor='rgba(0, 51, 153, 0.2)'
    ))
    
    # Courbe pour FORAGE
    fig.add_trace(go.Scatterpolar(
        r=forage_scores,
        theta=categories,
        fill='toself',
        name='FORAGE',
        line_color='#228B22',
        fillcolor='rgba(34, 139, 34, 0.2)'
    ))
    
    # Courbe pour HYBRIDE
    fig.add_trace(go.Scatterpolar(
        r=hybride_scores,
        theta=categories,
        fill='toself',
        name='HYBRIDE',
        line_color='#FFA500',
        fillcolor='rgba(255, 165, 0, 0.2)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10),
                gridcolor='lightgray'
            ),
            angularaxis=dict(
                tickfont=dict(size=12),
                gridcolor='lightgray'
            ),
            bgcolor='white'
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        ),
        title={
            'text': 'Analyse Comparative des Performances',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=16, color='#003366')
        },
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=500,
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    return fig    
# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="HYDRO-DECISIO | SIAD", layout="wide", page_icon="💧")

# --- INITIALISATION DU SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- LOGIQUE PDF (COMPLÈTE AVEC 3 OPTIONS) ---
def generate_pdf(score_cw, score_f, score_h, weights, cr, recommendation, 
                 fin_data, zone_context=None, project_name="", 
                 uploaded_images=[], gps_coords=None):
    """
    Génère un rapport PDF complet avec :
    - Contexte de l'étude
    - Analyse AHP
    - Comparaison des options
    - Synthèse financière
    - Recommandation finale
    """
    
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margin(15)
    pdf.add_page()
    
    # ============================================
    # EN-TÊTE PROFESSIONNELLE
    # ============================================
    pdf.set_fill_color(0, 51, 102)  # Bleu marine
    pdf.rect(0, 0, 210, 45, "F")
    pdf.set_y(15)
    
    # Logo/Titre principal
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "HYDRO-DECISIO SIAD", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    # Sous-titre
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, "Système d'Aide à la Décision Hydraulique", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Rapport généré le {date.today().strftime('%d/%m/%Y')}", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_y(55)
    pdf.set_text_color(0, 0, 0)
    
    # ============================================
    # SECTION 1 : CONTEXTE DE L'ÉTUDE
    # ============================================
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_draw_color(0, 102, 204)
    pdf.set_line_width(0.5)
    pdf.cell(0, 12, "1. CONTEXTE DE L'ÉTUDE", "B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    
    # Informations du projet
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 8, "Projet :", 0, 0)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, project_name or "Non spécifié", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Informations de la zone si disponibles
    if zone_context:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(40, 8, "Quartier :", 0, 0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, zone_context.get('quartier', 'N/A'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(40, 8, "Secteur :", 0, 0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, zone_context.get('secteur', 'N/A'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(40, 8, "Description :", 0, 0)
        pdf.set_font("Helvetica", "", 10)
        # Gestion du texte long avec multi_cell
        pdf.multi_cell(0, 5, zone_context.get('description', 'Aucune description disponible'))
        pdf.ln(3)
    
    # Coordonnées GPS avec lien Google Maps
    if gps_coords:
        lat, lon = gps_coords
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(45, 8, "Coordonnées GPS :", 0, 0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"{lat:.6f}°N, {lon:.6f}°E", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Lien Google Maps
        google_maps_url = f"https://maps.google.com/?q={lat},{lon}"
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 8, f"Lien Google Maps : {google_maps_url}", 
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT, link=google_maps_url)
        pdf.set_text_color(0, 0, 0)
    
    pdf.ln(5)
    
    # ============================================
    # SECTION 2 : MÉTHODOLOGIE AHP
    # ============================================
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "2. MÉTHODOLOGIE AHP", "B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    
    # Pondération des critères
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "2.1 Pondération des Critères", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 11)
    # Tableau des poids
    pdf.set_fill_color(240, 248, 255)
    pdf.cell(60, 10, "Critère", border=1, fill=True, align="C")
    pdf.cell(40, 10, "Poids", border=1, fill=True, align="C")
    pdf.cell(40, 10, "Valeur", border=1, fill=True, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    criteria_names = ["Coût", "Disponibilité", "Accessibilité"]
    for i, (name, weight) in enumerate(zip(criteria_names, weights)):
        pdf.cell(60, 10, name, border=1)
        pdf.cell(40, 10, f"{weight:.2%}", border=1, align="C")
        pdf.cell(40, 10, f"{weight:.4f}", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Indice de cohérence
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Indice de Cohérence (CR) : {cr:.4f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if cr < 0.1:
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 8, "[OK] L'analyse est coherente (CR < 0.1)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 8, "[ATTENTION] CR eleve, revoir les comparaisons", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # ============================================
    # SECTION 3 : ANALYSE COMPARATIVE
    # ============================================
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "3. ANALYSE COMPARATIVE DES OPTIONS", "B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    
    # Tableau comparatif
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 248, 255)
    pdf.cell(70, 10, "Option", border=1, fill=True, align="C")
    pdf.cell(40, 10, "Score", border=1, fill=True, align="C")
    pdf.cell(40, 10, "Performance", border=1, fill=True, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    options = [
        ("CAMWATER (Réseau)", score_cw),
        ("FORAGE (Autonome)", score_f),
        ("HYBRIDE (Mixte)", score_h)
    ]
    
    for option_name, score in options:
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(70, 10, f" {option_name}", border=1)
        pdf.cell(40, 10, f"{score:.2%}", border=1, align="C")
        pdf.cell(40, 10, f"{score*10:.1f}/10", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(5)
    
    # Graphique en barres textuel
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Visualisation comparative :", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    max_score = max(score_cw, score_f, score_h)
    for option_name, score in options:
        bar_width = (score / max_score) * 100 if max_score > 0 else 0
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(40, 8, f"{option_name[:15]} :", 0, 0)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(bar_width, 8, "", border=0, fill=True)
        pdf.cell(5, 8, f" {score:.1%}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(5)
    
    # ============================================
    # SECTION 4 : SYNTHÈSE FINANCIÈRE
    # ============================================
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "4. SYNTHÈSE FINANCIÈRE (10 ans)", "B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Coûts cumulés sur 10 ans :", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 11)
    # Tableau des coûts
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(70, 10, "Option", border=1, fill=True, align="C")
    pdf.cell(40, 10, "CAPEX", border=1, fill=True, align="C")
    pdf.cell(40, 10, "Total 10 ans", border=1, fill=True, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Récupération des données financières
    total_cw = fin_data.get('total_cw', 0)
    total_f = fin_data.get('total_f', 0)
    total_h = fin_data.get('total_h', 0)
    
    # Trouver la meilleure option financière
    costs = {"CAMWATER": total_cw, "FORAGE": total_f, "HYBRIDE": total_h}
    best_financial = min(costs, key=costs.get)
    
    for option in ["CAMWATER", "FORAGE", "HYBRIDE"]:
        total = costs[option]
        # Estimation du CAPEX (première année)
        capex = total * 0.4 if option == "FORAGE" else total * 0.6
        
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(70, 10, f" {option}", border=1)
        pdf.cell(40, 10, f"{int(capex):,} FCFA".replace(',', ' '), border=1, align="C")
        
        if option == best_financial:
            pdf.set_text_color(0, 128, 0)
            pdf.set_font("Helvetica", "B", 10)
        else:
            pdf.set_text_color(0, 0, 0)
        
        pdf.cell(40, 10, f"{int(total):,} FCFA".replace(',', ' '), border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, f"* Option la plus économique : {best_financial}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # ============================================
    # SECTION 5 : RECOMMANDATION FINALE
    # ============================================
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "5. RECOMMANDATION FINALE", "B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    # Encadré de recommandation
    if recommendation == "CAMWATER":
        fill_color = (0, 102, 204)  # Bleu
        border_color = (0, 51, 102)
    elif recommendation == "FORAGE":
        fill_color = (0, 153, 0)    # Vert
        border_color = (0, 102, 0)
    else:  # Hybride
        fill_color = (255, 153, 0)  # Orange
        border_color = (204, 102, 0)
    
    pdf.set_fill_color(*fill_color)
    pdf.set_draw_color(*border_color)
    pdf.set_line_width(1)
    pdf.rect(15, pdf.get_y(), 180, 25, "F")
    
    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "DÉCISION PRÉCONISÉE", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 15, recommendation, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_y(pdf.get_y() + 10)
    pdf.set_text_color(0, 0, 0)
    
    # Justification
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Justification :", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    
    justification_text = ""
    if recommendation == "CAMWATER":
        justification_text = "Cette option offre le meilleur compromis coût/performance pour les zones proches du réseau existant avec une demande modérée."
    elif recommendation == "FORAGE":
        justification_text = "Recommandé pour assurer une autonomie complète et une disponibilité permanente, malgré l'investissement initial plus élevé."
    else:  # Hybride
        justification_text = "Solution optimale combinant la fiabilité du forage avec la flexibilité du réseau, idéale pour les besoins élevés et variables."
    
    pdf.multi_cell(0, 6, justification_text)
    
    # Synthèse
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Synthèse des avantages :", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 10)
    advantages = {
        "CAMWATER": ["- Coût initial réduit", "- Maintenance externalisée", "- Pas de gestion d'infrastructure"],
        "FORAGE": ["- Indépendance totale", "- Disponibilité 24h/24", "- Coût à long terme maîtrisé"],
        "HYBRIDE": ["- Redondance et sécurité", "- Flexibilité d'approvisionnement", "- Optimisation des coûts"]
    }
    
    for advantage in advantages.get(recommendation, []):
        pdf.cell(10, 6, "")
        pdf.cell(0, 6, advantage, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # ============================================
    # SECTION 6 : DOCUMENTATION PHOTOGRAPHIQUE
    # ============================================
    if uploaded_images:
        for i, img in enumerate(uploaded_images):
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_draw_color(200, 200, 200)
            pdf.cell(0, 10, f"Documentation - Vue {i+1}/{len(uploaded_images)}", "B", 
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            
            try:
                pdf.image(img, x=20, w=170)
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 10, f"Photo {i+1} - Site de {project_name}", 
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            except:
                pdf.set_text_color(255, 0, 0)
                pdf.cell(0, 10, f"Impossible de charger l'image {i+1}", 
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                pdf.set_text_color(0, 0, 0)
    
    # ============================================
    # PIED DE PAGE
    # ============================================
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Document généré par HYDRO-DECISIO SIAD - Système d'Aide à la Décision Hydraulique", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.cell(0, 5, "Confidentialité : Ce rapport est destiné à l'usage exclusif du client", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    return bytes(pdf.output())

# Modifie la fonction reset_inputs pour utiliser les valeurs de la zone :
def reset_inputs():
    zone_context = st.session_state.get('zone_context', get_zone_context())
    
    st.session_state["c_vs_d"] = 1
    st.session_state["c_vs_a"] = 1
    st.session_state["d_vs_a"] = 1
    
    # Utiliser les valeurs par défaut de la zone
    st.session_state["cw_c"] = zone_context["performances_par_defaut"]["camwater"]["cout"]
    st.session_state["cw_d"] = zone_context["performances_par_defaut"]["camwater"]["disponibilite"]
    st.session_state["cw_a"] = zone_context["performances_par_defaut"]["camwater"]["accessibilite"]
    
    st.session_state["f_c"] = zone_context["performances_par_defaut"]["forage"]["cout"]
    st.session_state["f_d"] = zone_context["performances_par_defaut"]["forage"]["disponibilite"]
    st.session_state["f_a"] = zone_context["performances_par_defaut"]["forage"]["accessibilite"]
    
    st.session_state["h_c"] = zone_context["performances_par_defaut"]["hybride"]["cout"]
    st.session_state["h_d"] = zone_context["performances_par_defaut"]["hybride"]["disponibilite"]
    st.session_state["h_a"] = zone_context["performances_par_defaut"]["hybride"]["accessibilite"]
# ==========================================
# LOGIQUE DE NAVIGATION
# ==========================================

# --- LANDING PAGE ---
if st.session_state.page == "home":

    if "selected_zone" not in st.session_state:
        st.session_state.selected_zone = "Nkolbisson"
    
    # Styles CSS professionnels
    st.markdown("""
    <style>
    /* Style professionnel pour le bouton principal */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #003366 0%, #0066cc 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 1rem 2.5rem !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        border: 2px solid #003366 !important;
        box-shadow: 0 4px 12px rgba(0, 51, 102, 0.15) !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.5px !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #004080 0%, #0073e6 100%) !important;
        border-color: #004080 !important;
        box-shadow: 0 6px 16px rgba(0, 51, 102, 0.2) !important;
        transform: translateY(-2px) !important;
    }
    
    div.stButton > button:first-child:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.1) !important;
    }
    
    /* Animation subtile pour l'icône */
    @keyframes subtlePulse {
        0% { transform: translateX(0); }
        50% { transform: translateX(3px); }
        100% { transform: translateX(0); }
    }
    
    div.stButton > button:first-child:hover .icon {
        animation: subtlePulse 0.6s ease-in-out;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. HERO SECTION
    st.markdown("""
    <div class="hero-section" style="text-align: center; padding: 60px 20px; background: linear-gradient(135deg, #f8fafc 0%, #e8f4fd 100%); 
                border-radius: 20px; border: 1px solid #e1e8f0; margin-bottom: 40px;">
        <h1 style="color: #003366; font-size: 3.5rem; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.5px;">
            HYDRO-DECISIO
        </h1>
        <div style="height: 4px; width: 100px; background: linear-gradient(90deg, #003366, #0066cc); 
                    margin: 0 auto 20px; border-radius: 2px;"></div>
        <p style="font-size: 1.3rem; color: #1e4d8c; font-weight: 500; margin-bottom: 25px;">
            Système d'Aide à la Décision Hydraulique
        </p>
        <p style="max-width: 800px; margin: 0 auto; color: #4a5568; line-height: 1.6; font-size: 1.1rem;">
            Plateforme d'analyse multicritère combinant méthodes décisionnelles (AHP) 
            et modélisation technico-économique pour un approvisionnement hydraulique optimal.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Bouton d'accès au dashboard - Version professionnelle
    st.markdown("""
    <div style="text-align: center; margin: 50px 0;">
        <div style="display: inline-block; position: relative;">
            <div style="position: absolute; top: 50%; left: -60px; transform: translateY(-50%); 
                        color: #0066cc; font-size: 1.5rem;">▶</div>
    """, unsafe_allow_html=True)
    
    # Conteneur pour centrer le bouton
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "**ACCÉDER À L'ANALYSE DÉCISIONNELLE**",
            key="dashboard_access_pro",
            use_container_width=True,
            help="Lancez l'analyse multicritère AHP et l'évaluation financière"
        ):
            # Afficher l'écran de chargement
            with st.spinner("Préparation de l'analyse..."):
                show_loading_screen()
                st.session_state.page = "dashboard"
                # Donner le temps à l'écran de chargement de s'afficher
                st.rerun()
    
    st.markdown("""
            <div style="position: absolute; top: 50%; right: -60px; transform: translateY(-50%); 
                        color: #0066cc; font-size: 1.5rem;">◀</div>
        </div>
        <p style="color: #718096; font-size: 0.9rem; margin-top: 15px; font-style: italic;">
            Interface d'analyse complète avec visualisation des résultats
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. MÉTHODOLOGIE & FEATURES
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h2 style="color: #003366; font-weight: 600; font-size: 1.8rem; display: inline-block; 
                   padding-bottom: 10px; border-bottom: 3px solid #0066cc;">
            MÉTHODOLOGIE SCIENTIFIQUE
        </h2>
    </div>
    """, unsafe_allow_html=True)

    # Cartes de fonctionnalités - Style professionnel
    f1, f2, f3 = st.columns(3)
    
    with f1:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0;
                    height: 100%; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <div style="width: 60px; height: 60px; background: #ebf5ff; border-radius: 10px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                <span style="font-size: 1.8rem; color: #0066cc;">📊</span>
            </div>
            <h3 style="color: #003366; font-size: 1.2rem; font-weight: 600; margin-bottom: 15px;">
                AHP Multicritère
            </h3>
            <p style="color: #4a5568; font-size: 0.95rem; line-height: 1.5;">
                Méthode analytique hiérarchique pour pondérer objectivement 
                coûts, disponibilité et accessibilité.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0;
                    height: 100%; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <div style="width: 60px; height: 60px; background: #f0f9ff; border-radius: 10px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                <span style="font-size: 1.8rem; color: #0066cc;">💰</span>
            </div>
            <h3 style="color: #003366; font-size: 1.2rem; font-weight: 600; margin-bottom: 15px;">
                Analyse Financière
            </h3>
            <p style="color: #4a5568; font-size: 0.95rem; line-height: 1.5;">
                Modélisation ROI et calcul du point mort sur horizon 10 ans 
                pour optimisation budgétaire.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f3:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0;
                    height: 100%; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <div style="width: 60px; height: 60px; background: #f7fafc; border-radius: 10px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                <span style="font-size: 1.8rem; color: #0066cc;">📍</span>
            </div>
            <h3 style="color: #003366; font-size: 1.2rem; font-weight: 600; margin-bottom: 15px;">
                Contexte Local
            </h3>
            <p style="color: #4a5568; font-size: 0.95rem; line-height: 1.5;">
                Adaptation aux spécificités du quartier choisis 
                et contraintes spatiales identifiées.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 3. SECTION OBJECTIF / VALEUR AJOUTÉE
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #003366; color: white; padding: 40px; border-radius: 15px; 
                border-left: 6px solid #0066cc; margin-top: 40px;">
        <div style="display: flex; align-items: flex-start;">
            <div style="flex: 0 0 50px; margin-right: 20px;">
                <div style="width: 50px; height: 50px; background: rgba(255,255,255,0.1); 
                            border-radius: 10px; display: flex; align-items: center; 
                            justify-content: center; font-size: 1.5rem;">
                    🎯
                </div>
            </div>
            <div style="flex: 1;">
                <h3 style="color: white; font-weight: 600; font-size: 1.5rem; margin-bottom: 15px;">
                    Objectif Stratégique
                </h3>
                <p style="color: rgba(255,255,255,0.9); line-height: 1.6; font-size: 1.1rem;">
                    Optimiser les investissements hydrauliques par une approche scientifique, 
                    réduisant les coûts de 25-30% tout en garantissant la pérennité 
                    de l'approvisionnement en eau.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # --- DASHBOARD PAGE ---
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Sélection de la zone
        available_zones = get_available_zones()
        selected_zone = st.selectbox(
            "📍 Zone d'étude",
            options=available_zones,
            index=available_zones.index(st.session_state.get('selected_zone', 'Nkolbisson')),
            key="zone_selector"
        )
        
        # Charger le contexte de la zone sélectionnée
        zone_context = get_zone_context(selected_zone)
        st.session_state.zone_context = zone_context
        st.session_state.selected_zone = selected_zone
        
        # Afficher les informations de la zone
        st.info(f"""
        **Zone :** {zone_context['quartier']}
        **Secteur :** {zone_context['secteur']}
        **Description :** {zone_context['description'][:100]}...
        """)

        c_vs_d = st.select_slider("Coût vs Dispo", options=[1/9, 1/5, 1, 5, 9], value=1, key="c_vs_d")
        c_vs_a = st.select_slider("Coût vs Accès", options=[1/9, 1/5, 1, 5, 9], value=1, key="c_vs_a")
        d_vs_a = st.select_slider("Dispo vs Accès", options=[1/9, 1/5, 1, 5, 9], value=1, key="d_vs_a")
        st.button("🔄 Réinitialiser", on_click=reset_inputs)
        st.divider()
        st.info(f"📍 **Zone d'étude :** {zone_context['quartier']}, {zone_context['secteur']}")

    # Moteur AHP
    matrix = np.array([[1, c_vs_d, c_vs_a], [1/c_vs_d, 1, d_vs_a], [1/c_vs_a, 1/d_vs_a, 1]])
    engine = AHPEngine()
    weights, cr = engine.compute_weights(matrix)

    zone_context = st.session_state.get('zone_context', get_zone_context())
    st.title(f"Tableau de Bord Expert 💧 - {zone_context['quartier']}")

    with st.expander("📸 Informations Projet & Photos"):
        col_p1, col_p2 = st.columns([2, 1])
        project_name = col_p1.text_input("Nom du Projet", value=f"{zone_context['quartier']} - Lotissement X")
        site_photos = col_p2.file_uploader("Photos du terrain", accept_multiple_files=True, 
                                          type=['jpg', 'jpeg', 'png'])
        if site_photos:
            cols = st.columns(4)
            for idx, img in enumerate(site_photos):
                cols[idx % 4].image(img, use_container_width=True)

    c_m, c_d = st.columns([2, 1])
    
    with c_m:
        st.markdown(f"##### 📍 Localisation du site - {zone_context['quartier']}")
        
        # Utiliser les coordonnées de la zone sélectionnée
        lat = zone_context['coordonnees']['latitude']
        lon = zone_context['coordonnees']['longitude']
        zoom = zone_context['coordonnees']['zoom']
        
        m = folium.Map(location=[lat, lon], zoom_start=zoom)
        m.add_child(folium.LatLngPopup())
        
        # Ajouter un marqueur pour la zone
        folium.Marker(
            [lat, lon],
            popup=f"<b>{zone_context['quartier']}</b><br>{zone_context['description'][:50]}...",
            tooltip=zone_context['quartier'],
            icon=folium.Icon(color='blue', icon='tint', prefix='fa')
        ).add_to(m)
        
        map_data = st_folium(m, width=700, height=300, returned_objects=["last_clicked"])
        
        selected_lat, selected_lon = lat, lon
        if map_data and map_data["last_clicked"]:
            selected_lat = map_data["last_clicked"]["lat"]
            selected_lon = map_data["last_clicked"]["lng"]
            st.success(f"Point capturé : {selected_lat:.5f}, {selected_lon:.5f}")

    with c_d:
        st.markdown("##### 📊 Poids des Critères")
        fig_donut = px.pie(values=weights, names=['Coût', 'Dispo', 'Accès'], hole=0.5)
        st.plotly_chart(fig_donut, use_container_width=True)

    # 1. ÉVALUATION TECHNIQUE
    st.header("1️⃣ Évaluation Technique")
    t1, t2, t3 = st.tabs(["🏢 CAMWATER", "🚰 FORAGE", "🔄 HYBRIDE"])
    
    with t1:
        cw1, cw2, cw3 = st.columns(3)
        vc_cw = cw1.slider("Coût (CW)", 1, 10, 
                          value=st.session_state.get("cw_c", zone_context["performances_par_defaut"]["camwater"]["cout"]), 
                          key="cw_c")
        vd_cw = cw2.slider("Dispo (CW)", 1, 10, 
                          value=st.session_state.get("cw_d", zone_context["performances_par_defaut"]["camwater"]["disponibilite"]), 
                          key="cw_d")
        va_cw = cw3.slider("Accès (CW)", 1, 10, 
                          value=st.session_state.get("cw_a", zone_context["performances_par_defaut"]["camwater"]["accessibilite"]), 
                          key="cw_a")
    
    with t2:
        f1, f2, f3 = st.columns(3)
        vc_f = f1.slider("Coût (F)", 1, 10, 
                        value=st.session_state.get("f_c", zone_context["performances_par_defaut"]["forage"]["cout"]), 
                        key="f_c")
        vd_f = f2.slider("Dispo (F)", 1, 10, 
                        value=st.session_state.get("f_d", zone_context["performances_par_defaut"]["forage"]["disponibilite"]), 
                        key="f_d")
        va_f = f3.slider("Accès (F)", 1, 10, 
                        value=st.session_state.get("f_a", zone_context["performances_par_defaut"]["forage"]["accessibilite"]), 
                        key="f_a")
    
    with t3:
        h1, h2, h3 = st.columns(3)
        vc_h = h1.slider("Coût (H)", 1, 10, 
                        value=st.session_state.get("h_c", zone_context["performances_par_defaut"]["hybride"]["cout"]), 
                        key="h_c")
        vd_h = h2.slider("Dispo (H)", 1, 10, 
                        value=st.session_state.get("h_d", zone_context["performances_par_defaut"]["hybride"]["disponibilite"]), 
                        key="h_d")
        va_h = h3.slider("Accès (H)", 1, 10, 
                        value=st.session_state.get("h_a", zone_context["performances_par_defaut"]["hybride"]["accessibilite"]), 
                        key="h_a")

    scw = (weights[0]*vc_cw + weights[1]*vd_cw + weights[2]*va_cw) / 10
    sf = (weights[0]*vc_f + weights[1]*vd_f + weights[2]*va_f) / 10
    sh = (weights[0]*vc_h + weights[1]*vd_h + weights[2]*va_h) / 10
    
    # 2. VERDICT
    st.header("2️⃣ Verdict de Performance")
    r1, r2, r3 = st.columns(3)
    r1.metric("CAMWATER", f"{scw:.2%}")
    r2.metric("FORAGE", f"{sf:.2%}")
    r3.metric("HYBRIDE", f"{sh:.2%}")
    
     
    
    # Petite explication
    st.caption("⚠️ Note : Ces scores sont pondérés par les critères AHP. Voir ci-dessous pour l'analyse détaillée par critère.")

        # 3. ANALYSE RADAR (VISUALISATION DES PERFORMANCES)
    st.markdown("---")
    st.markdown("<h3 style='color: #003366;'>📊 Analyse Radar des Performances</h3>", unsafe_allow_html=True)
    
    col_radar, col_table = st.columns([2, 1])
    
    with col_radar:
        # Préparer les données pour le radar
        camwater_radar = [vc_cw, vd_cw, va_cw]
        forage_radar = [vc_f, vd_f, va_f]
        hybride_radar = [vc_h, vd_h, va_h]
        
        # Créer le graphique radar
        radar_fig = create_radar_chart(camwater_radar, forage_radar, hybride_radar)
        st.plotly_chart(radar_fig, use_container_width=True)
    
    with col_table:
        st.markdown("##### 📋 Scores détaillés (sur 10)")
        
        # Créer un DataFrame pour le tableau
        import pandas as pd
        
        data = {
            'Critère': ['Coût', 'Disponibilité', 'Accessibilité', '**Score total (pondéré)**'],
            'CAMWATER': [vc_cw, vd_cw, va_cw, f"{scw*100:.1f}%"],
            'FORAGE': [vc_f, vd_f, va_f, f"{sf*100:.1f}%"],
            'HYBRIDE': [vc_h, vd_h, va_h, f"{sh*100:.1f}%"]
        }
        
        df = pd.DataFrame(data)
        
        # Afficher le tableau stylisé
        st.dataframe(
            df,
            column_config={
                "Critère": st.column_config.TextColumn("Critère", width="medium"),
                "CAMWATER": st.column_config.NumberColumn(
                    "CAMWATER",
                    help="Score CAMWATER (1-10)",
                    format="%d",
                ),
                "FORAGE": st.column_config.NumberColumn(
                    "FORAGE",
                    help="Score FORAGE (1-10)",
                    format="%d",
                ),
                "HYBRIDE": st.column_config.NumberColumn(
                    "HYBRIDE",
                    help="Score HYBRIDE (1-10)",
                    format="%d",
                ),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Indicateur de performance - LOGIQUE CORRIGÉE
        st.markdown("##### 🎯 Synthèse par critère")
        
        # CORRECTION : Pour le coût, MAX = meilleur (car note haute = coût faible)
        # Pour disponibilité et accessibilité, MAX = meilleur
        best_cost = max([vc_cw, vc_f, vc_h])
        best_dispo = max([vd_cw, vd_f, vd_h])
        best_access = max([va_cw, va_f, va_h])
        
        # Détecter les égalités
        cost_options = []
        dispo_options = []
        access_options = []
        
        if vc_cw == best_cost:
            cost_options.append("CAMWATER")
        if vc_f == best_cost:
            cost_options.append("FORAGE")
        if vc_h == best_cost:
            cost_options.append("HYBRIDE")
            
        if vd_cw == best_dispo:
            dispo_options.append("CAMWATER")
        if vd_f == best_dispo:
            dispo_options.append("FORAGE")
        if vd_h == best_dispo:
            dispo_options.append("HYBRIDE")
            
        if va_cw == best_access:
            access_options.append("CAMWATER")
        if va_f == best_access:
            access_options.append("FORAGE")
        if va_h == best_access:
            access_options.append("HYBRIDE")
        
        # Afficher avec formatage
        st.markdown(f"""
        - **Meilleur coût** : {', '.join(cost_options) if cost_options else 'Aucun'}
        - **Meilleure disponibilité** : {', '.join(dispo_options) if dispo_options else 'Aucun'}
        - **Meilleure accessibilité** : {', '.join(access_options) if access_options else 'Aucun'}
        """)
        
        # Explication des résultats
        st.markdown("##### ℹ️ Comment interpréter")
        st.markdown("""
        - **Score total** = moyenne pondérée par l'AHP
        - **Scores bruts** = évaluation directe (1-10)
        - Le radar montre les performances brutes
        - Le verdict final intègre les préférences (poids)
        """)









    # 3. FINANCE
    st.markdown("---")
    st.markdown("<h2 style='color: #1b5e20;'>📈 Rentabilité sur 10 ans</h2>", unsafe_allow_html=True)
    
    with st.expander("💰 Paramètres Financiers"):
        col_f1, col_f2 = st.columns(2)
        capex_cw = col_f1.number_input("CAPEX Camwater", value=150000)
        opex_cw = col_f1.number_input("Facture réseau/mois", value=15000)
        capex_f = col_f2.number_input("CAPEX Forage", value=2500000)
        opex_f = col_f2.number_input("Maintenance forage/mois", value=5000)
        
        # Logique hybride : Somme des installs, OPEX partagé
        capex_h = capex_cw + capex_f
        opex_h = (opex_cw * 0.4) + (opex_f * 0.6)

    annees = np.arange(0, 11)
    costs_cw = [capex_cw + (opex_cw * 12 * a) for a in annees]
    costs_f = [capex_f + (opex_f * 12 * a) for a in annees]
    costs_h = [capex_h + (opex_h * 12 * a) for a in annees]

    fig_fin = go.Figure()
    fig_fin.add_trace(go.Scatter(x=annees, y=costs_cw, name="Camwater", line=dict(color="#003399", width=4)))
    fig_fin.add_trace(go.Scatter(x=annees, y=costs_f, name="Forage", line=dict(color="#228B22", width=4)))
    fig_fin.add_trace(go.Scatter(x=annees, y=costs_h, name="Hybride", line=dict(color="#FFA500", width=3, dash='dash')))
    fig_fin.update_layout(template="plotly_white", xaxis_title="Années", yaxis_title="CFA")
    st.plotly_chart(fig_fin, use_container_width=True)
    
    # EXPORT PDF
    st.divider()
    scores = {"CAMWATER": scw, "FORAGE": sf, "HYBRIDE": sh}
    best_option = max(scores, key=scores.get)
    
    final_fin_data = {
        'total_cw': costs_cw[-1],
        'total_f': costs_f[-1],
        'total_h': costs_h[-1]
    }
    
    st.download_button(
        label="📥 Télécharger le Rapport PDF Complet", 
        data=generate_pdf(
            score_cw=scw, 
            score_f=sf, 
            score_h=sh,
            weights=weights, 
            cr=cr, 
            recommendation=best_option, 
            fin_data=final_fin_data,
            zone_context=zone_context,
            project_name=project_name,
            uploaded_images=site_photos,
            gps_coords=(selected_lat, selected_lon)
        ),
        file_name=f"Rapport_HYDRO_{project_name}_{date.today().strftime('%Y%m%d')}.pdf",
        use_container_width=True,
        type="primary"
    )