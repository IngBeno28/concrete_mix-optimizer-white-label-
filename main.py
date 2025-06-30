# --- Imports ---
import io
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from typing import List, Dict, Optional
from branding import CLIENT_NAME, APP_TITLE, PRIMARY_COLOR, LOGO_PATH, FOOTER_NOTE

# --- Streamlit Config ---
st.set_page_config(APP_TITLE, layout="wide")

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Display client logo if available
if LOGO_PATH and os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=100)

# --- ACI Reference Tables ---
ACI_WATER_CONTENT = {
    "Non-Air-Entrained": {10: 205, 20: 185, 40: 160},
    "Air-Entrained": {10: 180, 20: 160, 40: 140}
}

ACI_CA_VOLUME = {
    2.4: {10: 0.44, 20: 0.60, 40: 0.68},
    2.7: {10: 0.49, 20: 0.66, 40: 0.74},
    3.0: {10: 0.53, 20: 0.72, 40: 0.80}
}

ACI_EXPOSURE = {
    "Mild": {"max_wcm": 0.55, "min_cement": 250},
    "Moderate": {"max_wcm": 0.50, "min_cement": 300},
    "Severe": {"max_wcm": 0.45, "min_cement": 335}
}

# --- Input UI ---
st.markdown(f"<h2 style='color:{PRIMARY_COLOR};'>{APP_TITLE}</h2>", unsafe_allow_html=True)

project_name = st.text_input("📌 Project Name", "Unnamed Project")

with st.expander("📋 ACI Design Inputs", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        fck = st.number_input("f'c (MPa)", 10.0, 80.0, 25.0)
        std_dev = st.number_input("Standard deviation (MPa)", 3.0, 10.0, 5.0)
        exposure = st.selectbox("Exposure Class", list(ACI_EXPOSURE))

    with col2:
        max_agg_size = st.selectbox("Max Aggregate Size (mm)", [10, 20, 40])
        slump = st.slider("Slump (mm)", 25, 200, 75)
        air_entrained = st.checkbox("Air Entrained", False)
        air_content = st.slider("Target Air Content (%)", 1.0, 8.0, 5.0) if air_entrained else 0.0

    with col3:
        wcm = st.number_input("w/c Ratio", 0.3, 0.7, 0.5)
        admixture = st.number_input("Admixture (%)", 0.0, 5.0, 0.0)
        fm = st.slider("FA Fineness Modulus", 2.4, 3.0, 2.7, step=0.1)

with st.expander("🔬 Material Properties"):
    sg_cement = st.number_input("Cement SG", 2.0, 3.5, 3.15)
    sg_fa = st.number_input("Fine Aggregate SG", 2.4, 2.8, 2.65)
    sg_ca = st.number_input("Coarse Aggregate SG", 2.4, 2.8, 2.65)
    unit_weight_ca = st.number_input("CA Unit Weight (kg/m³)", 1400, 1800, 1600)
    moist_fa = st.number_input("FA Moisture (%)", 0.0, 10.0, 2.0)
    moist_ca = st.number_input("CA Moisture (%)", 0.0, 10.0, 1.0)

# --- Mix Design Logic ---
@st.cache_data
def calculate_mix():
    """Calculate concrete mix design based on ACI method"""
    try:
        ft = fck + 1.34 * std_dev
        if wcm > ACI_EXPOSURE[exposure]['max_wcm']:
            st.warning("w/c exceeds max for exposure class")

        water = ACI_WATER_CONTENT["Air-Entrained" if air_entrained else "Non-Air-Entrained"][max_agg_size]
        water += (slump - 75) * 0.3
        if admixture:
            water *= 1 - min(0.15, admixture * 0.05)

        cement = max(water / wcm, ACI_EXPOSURE[exposure]['min_cement'])

        try:
            ca_vol = ACI_CA_VOLUME[round(fm,1)][max_agg_size]
        except:
            ca_vol = ACI_CA_VOLUME[2.7][max_agg_size]

        ca_mass = ca_vol * unit_weight_ca

        cement_vol = cement / (sg_cement * 1000)
        water_vol = water / 1000
        air_vol = air_content / 100 if air_entrained else 0.01
        ca_vol_abs = ca_mass / (sg_ca * 1000)
        fa_vol = 1 - (cement_vol + water_vol + air_vol + ca_vol_abs)
        fa_mass = fa_vol * sg_fa * 1000

        fa_mass_adj = fa_mass * (1 + moist_fa / 100)
        ca_mass_adj = ca_mass * (1 + moist_ca / 100)
        water -= (fa_mass * moist_fa / 100 + ca_mass * moist_ca / 100)

        return {
            "Target Mean Strength": round(ft,2),
            "Water": round(water,1),
            "Cement": round(cement,1),
            "Fine Aggregate": round(fa_mass_adj,1),
            "Coarse Aggregate": round(ca_mass_adj,1),
            "Air Content": round(air_content,1),
            "Admixture": round(cement * admixture / 100,2)
        }
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return None

def generate_pie_chart(data):
    """Generate pie chart of material composition"""
    try:
        material_components = {
            k: v for k, v in data.items() 
            if k in ["Water", "Cement", "Fine Aggregate", "Coarse Aggregate"] and v > 0
        }
        
        if not material_components:
            return None
            
        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            material_components.values(),
            labels=material_components.keys(),
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10}
        )
        ax.axis('equal')
        ax.set_title('Mix Composition', fontsize=12, pad=10)
        
        plt.setp(autotexts, size=10, weight="bold")
        plt.setp(texts, size=10)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        st.error(f"Chart error: {str(e)}")
        return None

# Add to imports
from typing import List, Dict, Optional

# --- New PDF Generator ---
def create_multi_design_pdf(designs: List[Dict], project_name: str) -> Optional[bytes]:
    """Generate PDF with all designs from current session"""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Cover Page
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 40, "Concrete Mix Design Compendium", 0, 1, 'C')
        pdf.set_font("Arial", '', 16)
        pdf.cell(0, 10, f"Project: {project_name}", 0, 1, 'C')
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
        pdf.ln(20)
        pdf.cell(0, 10, f"Total Designs: {len(designs)}", 0, 1, 'C')
        
        # Design Sections
        for idx, design in enumerate(designs, 1):
            pdf.add_page()
            
            # Header
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"Design #{idx}", 0, 1)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Target Strength: {design['data']['Target Mean Strength']} MPa", 0, 1)
            pdf.ln(5)
            
            # Parameters Table
            col_width = 60
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(col_width, 8, "Parameter", 1)
            pdf.cell(col_width, 8, "Value", 1)
            pdf.cell(col_width, 8, "Unit", 1)
            pdf.ln(8)
            
            pdf.set_font("Arial", '', 10)
            units = {
                "Target Mean Strength": "MPa",
                "Water": "kg/m³",
                "Cement": "kg/m³",
                "Fine Aggregate": "kg/m³", 
                "Coarse Aggregate": "kg/m³",
                "Air Content": "%",
                "Admixture": "kg/m³"
            }
            
            for param, value in design['data'].items():
                pdf.cell(col_width, 8, param, 1)
                pdf.cell(col_width, 8, f"{value:.2f}", 1)
                pdf.cell(col_width, 8, units.get(param, "-"), 1)
                pdf.ln(8)
            
            # Chart
            if design.get('chart'):
                try:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        Image.open(design['chart']).save(tmp.name)
                        pdf.image(tmp.name, x=50, y=pdf.get_y()+5, w=100)
                        os.unlink(tmp.name)
                except Exception as e:
                    st.error(f"Chart rendering error: {e}")
            
            # Page Footer
            pdf.set_y(-15)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(0, 10, f"Design {idx} of {len(designs)}", 0, 0, 'C')
        
        return pdf.output(dest='S').encode('latin1')
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None

# --- Modified Main Logic ---
if 'mix_designs' not in st.session_state:
    st.session_state.mix_designs = []

if st.button("🧪 Compute Mix Design"):
    result = calculate_mix()
    if result:
        chart = generate_pie_chart(result)
        st.session_state.mix_designs.append({
            'data': result,
            'chart': chart,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        st.success(f"Design added! Total: {len(st.session_state.mix_designs)}")

# Display current designs
if st.session_state.mix_designs:
    st.subheader("Accumulated Designs")
    for i, design in enumerate(st.session_state.mix_designs, 1):
        with st.expander(f"Design #{i} - {design['data']['Target Mean Strength']} MPa"):
            st.write(design['data'])
            if design.get('chart'):
                st.image(design['chart'])
    
    # PDF Generation
    if st.button("📄 Generate Master PDF"):
        with st.spinner(f"Compiling {len(st.session_state.mix_designs)} designs..."):
            pdf_bytes = create_multi_design_pdf(
                st.session_state.mix_designs,
                project_name
            )
            if pdf_bytes:
                st.download_button(
                    "💾 Download Full Report",
                    pdf_bytes,
                    f"concrete_mix_designs_{project_name}.pdf",
                    "application/pdf"
                )
    
    if st.button("🧹 Clear Designs"):
        st.session_state.mix_designs = []
        st.rerun()
        
# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)
