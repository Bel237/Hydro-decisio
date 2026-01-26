from datetime import date
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from engine.ahp_logic import AHPEngine
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
from fpdf.enums import XPos, YPos # Import pour corriger les warnings PDF

# --- CONFIGURATION INITIALE (DOIT ÊTRE LA PREMIÈRE COMMANDE) ---
st.set_page_config(page_title="HYDRO-DECISIO | SIAD", layout="wide", page_icon="💧")

# --- INITIALISATION DU SESSION STATE ---
# C'est ici qu'on règle l'erreur "AttributeError: page"
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- LOGIQUE PDF (MISE À JOUR POUR ÉVITER LES WARNINGS) ---
def generate_pdf(score_cw, score_f, weights, cr, recommendation, fin_data, uploaded_images=[], gps_coords=None):
    # Initialisation
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margin(20)
    pdf.add_page()
    
    # --- EN-TÊTE ---
    pdf.set_fill_color(0, 51, 153)
    pdf.rect(0, 0, 210, 40, "F")


    pdf.set_y(15)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "RAPPORT D'EXPERTISE HYDRAULIQUE", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, f"Solution SIAD HYDRO-DECISIO | Genere le {date.today().strftime('%d/%m/%Y')}", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_y(50)
    pdf.set_text_color(0, 0, 0)

    # --- SECTION 1 : CRITÈRES AHP ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_draw_color(0, 51, 153)
    pdf.cell(0, 10, "1. Pondération des Critères (Methode AHP)", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 11)
    # CORRECTION ICI : On utilise "-" au lieu de "•"
    pdf.cell(0, 8, f"   - Cout : {weights[0]:.2%}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"   - Disponibilite : {weights[1]:.2%}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"   - Accessibilite : {weights[2]:.2%}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, f"Indice de Coherence (CR) : {cr:.4f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # --- SECTION 2 : COMPARAISON ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "2. Analyse Comparative des Options", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(85, 10, "Option", border=1, fill=True)
    pdf.cell(85, 10, "Score de Performance", border=1, fill=True, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(85, 10, " CAMWATER", border=1)
    pdf.cell(85, 10, f"{score_cw:.2%}", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(85, 10, " FORAGE AUTONOME", border=1)
    pdf.cell(85, 10, f"{score_f:.2%}", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # --- SECTION 3 : FINANCE ---
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "3. Synthese Financiere (10 ans)", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    # Utilisation de f-strings sans caractères spéciaux
    pdf.cell(0, 8, f"- Cout cumule Camwater : {int(fin_data.get('total_10y_cw', 0)):,} FCFA".replace(',', ' '), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"- Cout cumule Forage : {int(fin_data.get('total_10y_f', 0)):,} FCFA".replace(',', ' '), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # --- VERDICT FINAL ---
    if recommendation == "CAMWATER":
        pdf.set_fill_color(0, 51, 153)
    else:
        pdf.set_fill_color(34, 139, 34)
        
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 20, f"DECISION PRECONISEE : {recommendation}", align="C", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if gps_coords:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 10, f"Localisation GPS du site : {gps_coords[0]:.5f} N, {gps_coords[1]:.5f} E", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            google_url = f"https://www.google.com/maps?q={gps_coords[0]},{gps_coords[1]}"
            pdf.set_font("Helvetica", "U", 10)
            pdf.set_text_color(0, 0, 255) # Bleu lien
            pdf.cell(0, 10, "Voir sur Google Maps", link=google_url, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0) 
    if uploaded_images:
        for i, img in enumerate(uploaded_images):
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, f"4.{i+1} Documentation Photo - Vue {i+1}", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            
            # Sauvegarde temporaire avec un nom unique par image
            img_path = f"temp_site_img_{i}.png"
            with open(img_path, "wb") as f:
                f.write(img.getbuffer())
            
            # Insertion de l'image
            pdf.image(img_path, x=20, w=170)
            
            # Ajout de la légende automatique en bas de l'image
            pdf.ln(5)
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, f"Source : HYDRO-DECISIO | Document du terrain - Vue {i+1} (Nkolbisson)", align="C")
            pdf.set_text_color(0, 0, 0) # Reset couleur
    return bytes(pdf.output())

def reset_inputs():
    st.session_state["c_vs_d"] = 1
    st.session_state["c_vs_a"] = 1
    st.session_state["d_vs_a"] = 1
    st.session_state["cw_c"] = 8
    st.session_state["cw_d"] = 3        
    st.session_state["cw_a"] = 6
    st.session_state["f_c"] = 4
    st.session_state["f_d"] = 9
    st.session_state["f_a"] = 8

# Chargement du CSS personnalisé
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

# ==========================================
# AFFICHAGE CONDITIONNEL (PAGE)
# ==========================================

# --- INITIALISATION DE LA NAVIGATION ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- LANDING PAGE ---
if st.session_state.page == "home":
    # 1. HERO SECTION 
    st.markdown(""" 
        <div class="hero-section" style="text-align: center; padding: 60px 20px; background-color: #f1f8e9; border-radius: 30px;"> 
            <h1 style="color: #003399; font-size: 4rem; font-weight: 900; margin-bottom:0;">HYDRO-DECISIO</h1> 
            <p style="font-size: 1.5rem; color: #1b5e20; font-weight: 600;">Système d'Aide à la Décision Hydraulique pour Nkolbisson</p> 
            <p style="max-width: 800px; margin: 20px auto; color: #444; line-height: 1.6; font-size: 1.1rem;"> 
                Une plateforme d'expertise combinant mathématiques décisionnelles (Méthode AHP)  
                et analyses technico-financières pour garantir un approvisionnement en eau durable et rentable. 
            </p> 
        </div> 
    """, unsafe_allow_html=True) 

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
<style>
    /* On crée une règle qui ne s'applique qu'au bouton de la Home Page */
    [data-testid="stVerticalBlock"] .stButton button {
        background: linear-gradient(90deg, #003399 0%, #1b5e20 100%) !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stVerticalBlock"] .stButton button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
        background: linear-gradient(90deg, #0044cc 0%, #2e7d32 100%) !important;
    }
</style>
""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1]) 
    with c2: 
        if st.button("🚀 ACCÉDER AU DASHBOARD D'ANALYSE", use_container_width=True): 
            st.session_state.page = "dashboard" 
            st.rerun() 

    st.markdown("<br><br>", unsafe_allow_html=True) 

    # 2. MÉTHODOLOGIE & FEATURES 
    st.markdown('<h2 style="color: #003399; text-align: center; font-weight: 800; margin-bottom: 40px;">Pourquoi HYDRO-DECISIO ?</h2>', unsafe_allow_html=True) 
     
    f1, f2, f3 = st.columns(3) 
    with f1: 
        st.markdown(""" 
            <div class="feature-card" style="background: white; padding: 30px; border-radius: 15px; border: 2px solid #e8f5e9; text-align: center; height: 100%;"> 
                <div style="font-size: 2.5rem; margin-bottom: 15px;">⚖️</div> 
                <h3 style="color: #1b5e20;">Analyse Multicritère</h3> 
                <p style="color: #444;">Utilisation de la méthode <b>AHP (Analytic Hierarchy Process)</b> pour pondérer Coût, Disponibilité et Accessibilité.</p> 
            </div> 
        """, unsafe_allow_html=True) 
    with f2: 
        st.markdown(""" 
            <div class="feature-card" style="background: white; padding: 30px; border-radius: 15px; border: 2px solid #e8f5e9; text-align: center; height: 100%;"> 
                <div style="font-size: 2.5rem; margin-bottom: 15px;">📈</div> 
                <h3 style="color: #1b5e20;">Projection ROI</h3> 
                <p style="color: #444;">Calcul automatique du <b>point mort financier</b> sur 10 ans entre l'abonnement réseau et l'investissement autonome.</p> 
            </div> 
        """, unsafe_allow_html=True) 
    with f3: 
        st.markdown(""" 
            <div class="feature-card" style="background: white; padding: 30px; border-radius: 15px; border: 2px solid #e8f5e9; text-align: center; height: 100%;"> 
                <div style="font-size: 2.5rem; margin-bottom: 15px;">🗺️</div> 
                <h3 style="color: #1b5e20;">Géo-Localisation</h3> 
                <p style="color: #444;">Intégration des contraintes spatiales spécifiques au quartier <b>Nkolbisson (Yaoundé VII)</b>.</p> 
            </div> 
        """, unsafe_allow_html=True) 

    # 3. SECTION OBJECTIF / STATS
    st.markdown("<br><br>", unsafe_allow_html=True) 
    st.markdown(""" 
        <div style="background: #1b5e20; color: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1);"> 
            <h2 style="color: white; font-weight: 800;">Objectif : Zéro Pénurie</h2> 
            <p style="font-size: 1.2rem; opacity: 0.9;">En optimisant le choix de l'infrastructure, nous réduisons les coûts de 30% sur le long terme tout en garantissant la disponibilité de la ressource.</p> 
        </div> 
    """, unsafe_allow_html=True)
else:
    # ==========================================
    # DASHBOARD PAGE
    # ==========================================
    with st.sidebar:
        col_logo, col_name = st.columns([1, 2])
        with col_logo:
            st.markdown('<div class="logo-container ">', unsafe_allow_html=True)
            st.image("assets/logo.png", width=60)
           
        with col_name:
            st.markdown("<h2 style='color: black; margin-top: 10px;'>HYDRO-DECISIO</h2>", unsafe_allow_html=True)
        st.divider()
        if st.button("Réinitialiser", use_container_width=True):
            reset_inputs()
        
        st.subheader("⚖️ Pondération AHP")
        c_vs_d = st.select_slider("Coût vs Dispo", options=[1/9, 1/5, 1, 5, 9], value=1, key="c_vs_d")
        c_vs_a = st.select_slider("Coût vs Accès", options=[1/9, 1/5, 1, 5, 9], value=1, key="c_vs_a")
        d_vs_a = st.select_slider("Dispo vs Accès", options=[1/9, 1/5, 1, 5, 9], value=1, key="d_vs_a")

        st.markdown("---")
        st.info("📍 **Zone d'étude :** Nkolbisson, Yaoundé")


    # Calculs
    matrix = np.array([[1, c_vs_d, c_vs_a], [1/c_vs_d, 1, d_vs_a], [1/c_vs_a, 1/d_vs_a, 1]])
    engine = AHPEngine()
    weights, cr = engine.compute_weights(matrix)

    st.title("Dashboard 💧")


        # --- INITIALISATION ---
    site_photos = [] 
    with st.expander("📸 Informations Projet & Photos"):
        col_p1, col_p2 = st.columns([2, 1])
        project_name = col_p1.text_input("Nom du Projet", value="Nkolbisson - Lotissement X")
        site_photos = col_p2.file_uploader("Photos du terrain", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        if site_photos:
            st.write(f"✅ {len(site_photos)} photos prêtes.")
            cols = st.columns(4)
            for idx, img_file in enumerate(site_photos):
                cols[idx % 4].image(img_file, use_container_width=True)

    # 2. Ensuite on affiche la carte et le donut (qui utilise 'weights')
    c_m, c_d = st.columns([2, 1])
    with c_m:
        st.markdown("##### 📍 Localisation précise du site")
        m = folium.Map(location=[3.8712, 11.4538], zoom_start=14)
        
        # Ajout d'un outil de clic
        m.add_child(folium.LatLngPopup()) 
        
        # On capture les données de la carte
        # returned_objects=["last_clicked"] permet de récupérer le clic
        map_data = st_folium(m, width=700, height=300, returned_objects=["last_clicked"])

        # Extraction des coordonnées
        selected_lat = 3.8712 # Valeur par défaut
        selected_lon = 11.4538 # Valeur par défaut
        
        if map_data and map_data["last_clicked"]:
            selected_lat = map_data["last_clicked"]["lat"]
            selected_lon = map_data["last_clicked"]["lng"]
            st.success(f"📍 Point sélectionné : {selected_lat:.5f}, {selected_lon:.5f}")
        else:
            st.info("💡 Cliquez sur la carte pour définir la position exacte du forage.")

    with c_d:
        st.markdown("##### 📊 Poids des Critères")
        # Maintenant 'weights' existe forcément car calculé après la sidebar
        fig_donut = px.pie(values=weights, names=['Coût', 'Dispo', 'Accès'], hole=0.5)
        fig_donut.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)

    # Tabs Évaluation
    st.header("1️⃣ Évaluation Technique")
    t1, t2 = st.tabs(["🏢 CAMWATER", "🚰 FORAGE"])
    with t1:
        cw1, cw2, cw3 = st.columns(3)
        vc_cw = cw1.slider("Coût (CW)", 1, 10, 8, key="cw_c")
        vd_cw = cw2.slider("Dispo (CW)", 1, 10, 3, key="cw_d")
        va_cw = cw3.slider("Accès (CW)", 1, 10, 6, key="cw_a")
    with t2:
        f1, f2, f3 = st.columns(3)
        vc_f = f1.slider("Coût (Forage)", 1, 10, 4, key="f_c")
        vd_f = f2.slider("Dispo (Forage)", 1, 10, 9, key="f_d")
        va_f = f3.slider("Accès (Forage)", 1, 10, 8, key="f_a")

    # Scores
    scw = (weights[0]*vc_cw + weights[1]*vd_cw + weights[2]*va_cw) / 10
    sf = (weights[0]*vc_f + weights[1]*vd_f + weights[2]*va_f) / 10
    
    st.header("2️⃣ Verdict")
    r1, r2 = st.columns(2)
    r1.markdown(f'<div class="result-card card-camwater"><p class="card-title">CAMWATER</p><p class="card-value">{scw:.2%}</p></div>', unsafe_allow_html=True)
    r2.markdown(f'<div class="result-card card-forage"><p class="card-title">FORAGE</p><p class="card-value">{sf:.2%}</p></div>', unsafe_allow_html=True)

    # Finance
  # Section 4 : Finance
    st.markdown("---")
    st.markdown("<h2 style='color: #1b5e20;'>📈 Rentabilité sur 10 ans</h2>", unsafe_allow_html=True)
    with st.expander("💰 Paramètres Financiers"):
        col_f1, col_f2 = st.columns(2)
        capex_cw = col_f1.number_input("CAPEX Camwater", value=150000)
        opex_cw = col_f1.number_input("Facture/mois", value=15000)
        capex_f = col_f2.number_input("CAPEX Forage", value=2500000)
        opex_f = col_f2.number_input("Mainten./mois", value=5000)

    annees = np.arange(0, 11)
    c_cw = [capex_cw + (opex_cw * 12 * a) for a in annees]
    c_f = [capex_f + (opex_f * 12 * a) for a in annees]
    fig_fin = go.Figure()
    fig_fin.add_trace(go.Scatter(x=annees, y=c_cw, name="Camwater", line=dict(color="#003399", width=4)))
    fig_fin.add_trace(go.Scatter(x=annees, y=c_f, name="Forage", line=dict(color="#228B22", width=4)))
    fig_fin.update_layout(template="plotly_white", xaxis_title="Années", yaxis_title="CFA")
    st.plotly_chart(fig_fin, use_container_width=True)
    
    # Export PDF
    st.divider()
    seuil = (capex_f - capex_cw) / ((opex_cw - opex_f) * 12) if opex_cw > opex_f else 0
    f_data = {'capex_cw': capex_cw, 'capex_f': capex_f, 'roi_years': seuil}
    verdict = "FORAGE" if sf > scw else "CAMWATER"
        
    st.download_button(
        label="📥 Télécharger le Rapport PDF Expert", 
        data=generate_pdf(
            score_cw=scw, 
            score_f=sf, 
            weights=weights, 
            cr=cr, 
            recommendation=verdict, 
            fin_data=f_data,
            uploaded_images=site_photos,
            gps_coords=(selected_lat, selected_lon)
        ),
        file_name=f"Rapport_Expert_{project_name}.pdf",
        width="stretch"
    )

        