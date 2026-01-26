from datetime import date
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from engine.ahp_logic import AHPEngine
from streamlit_folium import folium_static
import folium
from fpdf import FPDF
from datetime import  date

def generate_pdf(score_cw, score_f, weights, cr, recommendation, fin_data):
    pdf = FPDF()
    pdf.add_page()
    
# --- HEADER ---

    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 51, 153) # Bleu HYDRO-DECISIO
    pdf.cell(0, 15, "RAPPORT D'EXPERTISE : HYDRO-DECISIO", ln=True, align="C")

    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Analyse SIAD pour le quartier Nkolbisson - Genere le {date.today()}", ln=True, align="C")
    pdf.ln(10)
    # Section 1 : Analyse Technique
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "1. Analyse des Criteres (Methode AHP)", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"- Poids du Cout : {weights[0]:.2%}", ln=True)
    pdf.cell(0, 10, f"- Poids de la Disponibilite : {weights[1]:.2%}", ln=True)
    pdf.cell(0, 10, f"- Poids de l'Accessibilite : {weights[2]:.2%}", ln=True)
    pdf.cell(0, 10, f"- Indice de Coherence (CR) : {cr:.4f}", ln=True)
    pdf.ln(5)

    # Section 2 : Projection Financiere (NOUVEAU)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "2. Analyse Financiere sur 10 ans", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"- Investissement Initial CAMWATER : {fin_data['capex_cw']:,} FCFA", ln=True)
    pdf.cell(0, 10, f"- Investissement Initial FORAGE : {fin_data['capex_f']:,} FCFA", ln=True)
    pdf.cell(0, 10, f"- Cout total cumule (10 ans) Camwater : {fin_data['total_10y_cw']:,} FCFA", ln=True)
    pdf.cell(0, 10, f"- Cout total cumule (10 ans) Forage : {fin_data['total_10y_f']:,} FCFA", ln=True)
    
    if fin_data['roi_years'] > 0:
        pdf.set_font("Arial", "I", 11)
        pdf.cell(0, 10, f"Note : Rentabilite du forage atteinte apres {fin_data['roi_years']:.1f} ans.", ln=True)
    pdf.ln(5)

    # Verdict Final
    pdf.ln(10)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, f"VERDICT : OPTION {recommendation}", ln=True, align="C", fill=True)

    # Footer
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Document genere par HYDRO-DECISIO SIAD - Logiciel d'Aide a la Decision Hydraulique.", align="C")
    return bytes(pdf.output())

def reset_inputs():
    # On réinitialise chaque clé au dictionnaire session_state
    # Remplace ces noms de clés par ceux que tu as mis dans tes widgets
    st.session_state["c_vs_d"] = 1
    st.session_state["c_vs_a"] = 1
    st.session_state["d_vs_a"] = 1
    st.session_state["cw_c"] = 8
    st.session_state["cw_d"] = 3        
    st.session_state["cw_a"] = 6
    st.session_state["f_c"] = 4
    st.session_state["f_d"] = 9
    st.session_state["f_a"] = 8

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="SIAD Hydraulique", layout="wide", page_icon="💧")

# Chargement du CSS personnalisé
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- SIDEBAR : CONTRÔLE DES PARAMÈTRES (LES SIGNAUX) ---
with st.sidebar:
    # Affichage du logo et du nom
    col_logo, col_name = st.columns([1, 2])
    with col_logo:
        st.image("assets/logo.png", width=70)
    with col_name:
        st.markdown("<h2 style='color: white; margin-top: 10px;'>HYDRO-DECISIO</h2>", unsafe_allow_html=True)
    
    st.caption("HYDRO-DECISIO - Solution d'aide à la décision hydraulique pour zones périurbaines")
    st.markdown("---")
    if st.button("Réinitialiser le dispositif", use_container_width=True):
        reset_inputs()
    st.subheader("⚖️ Pondération des Critères")
    st.caption("Définissez l'importance relative selon la méthode AHP")

    c_vs_d = st.select_slider("Coût vs Disponibilité", options=[1/9, 1/5, 1, 5, 9], value=1, key="c_vs_d")
    c_vs_a = st.select_slider("Coût vs Accessibilité", options=[1/9, 1/5, 1, 5, 9], value=1, key="c_vs_a")
    d_vs_a = st.select_slider("Dispo vs Accessibilité", options=[1/9, 1/5, 1, 5, 9], value=1, key="d_vs_a")

    st.markdown("---")
    st.info("📍 **Zone d'étude :** Nkolbisson, Yaoundé")


# --- CALCULS AHP (LOGIQUE INTERNE) ---
matrix = np.array([
    [1, c_vs_d, c_vs_a],
    [1/c_vs_d, 1, d_vs_a],
    [1/c_vs_a, 1/d_vs_a, 1]
])
engine = AHPEngine()
weights, cr = engine.compute_weights(matrix)

# --- HEADER DU DASHBOARD ---
st.title("Dashboard 💧")
st.write("Analyse comparative entre **CAMWATER** et **ALIMENTATION AUTONOME**")

# --- SECTION 1 : ÉTAT DES LIEUX & CARTE ---
col_map, col_metric = st.columns([2, 1])

with col_map:
    # On réduit un peu la taille de la carte pour le dashboard
    m = folium.Map(location=[3.8712, 11.4538], zoom_start=14, control_scale=True)
    folium.Marker([3.8712, 11.4538], popup="Quartier Nkolbisson").add_to(m)
    st.markdown("##### 📍 Localisation du secteur d'étude")
    folium_static(m, width=700, height=300)

with col_metric:
    st.markdown("##### 📊 Poids des Critères")
    # Affichage des poids sous forme de donut chart pour faire "pro"
    fig_donut = px.pie(values=weights, names=['Coût', 'Dispo', 'Accès'], hole=0.5, 
                       color_discrete_sequence=px.colors.sequential.RdBu)
    fig_donut.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=True)
    st.plotly_chart(fig_donut, use_container_width=True)

# --- SECTION 2 : SAISIE DES DONNÉES DE TERRAIN ---
st.markdown("---")
st.header("2️⃣ Évaluation des Options (Notes du Terrain)")

tab1, tab2 = st.tabs(["🏢 Option CAMWATER", "🚰 Option FORAGE"])

with tab1:
    c1, c2, c3 = st.columns(3)
    val_cost_cw = c1.select_slider("Coût (CW)", options=range(1,11), value=8, key="cw_c")
    val_disp_cw = c2.select_slider("Dispo (CW)", options=range(1,11), value=3, key="cw_d")
    val_acc_cw = c3.select_slider("Accès (CW)", options=range(1,11), value=6, key="cw_a")

with tab2:
    f1, f2, f3 = st.columns(3)
    val_cost_f = f1.select_slider("Coût (Forage)", options=range(1,11), value=4, key="f_c")
    val_disp_f = f2.select_slider("Dispo (Forage)", options=range(1,11), value=9, key="f_d")
    val_acc_f = f3.select_slider("Accès (Forage)", options=range(1,11), value=8, key="f_a")

# --- SECTION 3 : ANALYSE & RÉPONSE ---
st.markdown("---")
score_cw = (weights[0]*val_cost_cw + weights[1]*val_disp_cw + weights[2]*val_acc_cw) / 10
score_f = (weights[0]*val_cost_f + weights[1]*val_disp_f + weights[2]*val_acc_f) / 10

col_res_left, col_res_right = st.columns([1, 1])

with col_res_left:
    st.subheader("🎯 Verdict du SIAD")
    
    m1, m2 = st.columns(2)
    
    # Affichage CAMWATER
    m1.markdown(f"""
        <div class="result-card card-camwater">
            <p class="card-title">Score CAMWATER</p>
            <p class="card-value">{score_cw:.2%}</p>
        </div>
    """, unsafe_allow_html=True)

    # Affichage FORAGE
    m2.markdown(f"""
        <div class="result-card card-forage">
            <p class="card-title">Score FORAGE</p>
            <p class="card-value">{score_f:.2%}</p>
        </div>
    """, unsafe_allow_html=True)

    # Recommandation textuelle sous les cartes
    st.write("") 
    if score_f > score_cw:
        st.success(f"### ✅ RECOMMANDATION : FORAGE")
    else:
        st.info(f"### ✅ RECOMMANDATION : CAMWATER")
        st.write("Le raccordement au réseau public est jugé optimal.")

    # Radar Chart
    df_plot = {
        "Critère": ["Coût", "Dispo", "Accès"] * 2,
        "Score": [val_cost_cw, val_disp_cw, val_acc_cw, val_cost_f, val_disp_f, val_acc_f],
        "Option": ["Camwater"]*3 + ["Forage"]*3
    }
    fig_radar = px.line_polar(df_plot, r="Score", theta="Critère", color="Option", line_close=True)
    st.plotly_chart(fig_radar, use_container_width=True)

with col_res_right:
    st.subheader("🔍 Analyse de Fiabilité")
    # Gauge chart pour la cohérence
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = cr,
        title = {'text': "Indice de Cohérence (CR)"},
        gauge = {
            'axis': {'range': [None, 0.3]},
            'steps' : [
                {'range': [0, 0.1], 'color': "lightgreen"},
                {'range': [0.1, 0.3], 'color': "orange"}],
            'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 0.1}
        }
    ))
    fig_gauge.update_layout(height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    if cr < 0.1:
        st.write("✅ **Jugement Cohérent :** Les résultats sont mathématiquement fiables.")
    else:
        st.warning("⚠️ **Attention :** Vos préférences sont contradictoires. Le décideur devrait revoir les sliders en sidebar.")

# --- SECTION 4 : PROJECTION FINANCIÈRE ---
st.markdown("---")
st.header("📈 Projection Financière sur 10 ans")

# --- PARAMÈTRES FINANCIERS (Hypothèses) ---
with st.expander("💰 Configurer les paramètres financiers"):
    col_fin1, col_fin2 = st.columns(2)
    with col_fin1:
        capex_cw = st.number_input("Investissement initial Camwater (FCFA)", value=150000)
        opex_cw = st.number_input("Facture mensuelle moyenne (FCFA)", value=15000)
    with col_fin2:
        capex_f = st.number_input("Investissement initial Forage (FCFA)", value=2500000)
        opex_f = st.number_input("Maintenance + Électricité / mois (FCFA)", value=5000)

# --- CALCUL DES COURBES ---
annees = np.arange(0, 11) # De 0 à 10 ans
cumul_cw = [capex_cw + (opex_cw * 12 * a) for a in annees]
cumul_f = [capex_f + (opex_f * 12 * a) for a in annees]

# --- CRÉATION DU GRAPHIQUE ---
fig_finance = go.Figure()

# Courbe Camwater (Bleu Institutionnel)
fig_finance.add_trace(go.Scatter(
    x=annees, y=cumul_cw, 
    name='Cumul Camwater',
    line=dict(color='#003399', width=4) # Bleu foncé
))

# Courbe Forage (Vert Autonomie)
fig_finance.add_trace(go.Scatter(
    x=annees, y=cumul_f, 
    name='Cumul Forage',
    line=dict(color='#228B22', width=4) # Vert forêt
))

fig_finance.update_layout(
    title="Évolution du coût cumulé dans le temps",
    xaxis_title="Années",
    yaxis_title="Total dépensé (FCFA)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_finance, use_container_width=True)

# --- ANALYSE DU POINT MORT (ROI) ---
if opex_cw > opex_f:
    diff_inv = capex_f - capex_cw
    diff_mensuelle = opex_cw - opex_f
    seuil_mois = diff_inv / diff_mensuelle
    seuil_ans = seuil_mois / 12
    
    st.info(f"💡 **Analyse de rentabilité :** Le forage devient plus rentable que la Camwater après **{seuil_ans:.1f} ans** d'utilisation.")
else:
    st.warning("⚠️ Avec ces paramètres, la Camwater reste toujours moins chère, mais n'oubliez pas de pondérer avec le critère de 'Disponibilité'.")

# 

st.markdown("---")
st.header("📋 Synthèse Comparative")

col_adv1, col_adv2 = st.columns(2)

with col_adv1:
    st.subheader("🏢 CAMWATER")
    if val_cost_cw > val_cost_f: st.write("✅ **Avantage :** Faible investissement initial.")
    if val_disp_cw < 5: st.write("❌ **Inconvénient :** Faible fiabilité du réseau à Nkolbisson.")
    if val_acc_cw > 7: st.write("✅ **Avantage :** Réseau déjà à proximité.")

with col_adv2:
    st.subheader("🚰 FORAGE")
    if val_disp_f > 7: st.write("✅ **Avantage :** Autonomie et disponibilité 24h/24.")
    if val_cost_f < 5: st.write("❌ **Inconvénient :** Coût d'installation très élevé.")
    if val_acc_f > val_acc_cw: st.write("✅ **Avantage :** Indépendance vis-à-vis des extensions de réseau.")

# --- SECTION 5 : EXPORTATION DU RAPPORT ---

st.markdown("---")
st.subheader("🖨️ Exportation du Rapport")

verdict_text = "FORAGE" if score_f > score_cw else "CAMWATER"
# Préparation des données pour le PDF
fin_data = {
    'capex_cw': capex_cw,
    'capex_f': capex_f,
    'total_10y_cw': cumul_cw[10],
    'total_10y_f': cumul_f[10],
    'roi_years': seuil_ans if opex_cw > opex_f else 0
}
# On génère les bytes ici
try:
    pdf_bytes = generate_pdf(score_cw, score_f, weights, cr, verdict_text, fin_data)
    st.download_button(
    label="📥 Telecharger le Dossier de Decision Complet (PDF)",
    data=pdf_bytes,
    file_name=f"SIAD_Nkolbisson_Final.pdf",
    mime="application/pdf",
    use_container_width=True
    )
except Exception as e:
    st.error(f"Erreur lors de la génération du PDF : {e}")