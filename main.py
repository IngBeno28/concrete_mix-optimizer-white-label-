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
from branding import CLIENT_NAME, APP_TITLE, PRIMARY_COLOR, LOGO_PATH, FOOTER_NOTE

# --- Streamlit Config ---
st.set_page_config(APP_TITLE, layout="wide")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Optional: Display client logo
if LOGO_PATH:
    st.image("assets/Zhongmei Logo.jpg", width=100)

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
def calculate_mix():
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

def generate_pie_chart_image(data):
    """Generate a pie chart image from composition data."""
    try:
        # Filter only material components for the pie chart
        material_components = {
            k: v for k, v in data.items() 
            if k in ["Water", "Cement", "Fine Aggregate", "Coarse Aggregate"]
        }
        
        if not material_components:
            return None
            
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            material_components.values(),
            labels=material_components.keys(),
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 12}
        )
        ax.axis('equal')
        ax.set_title('Concrete Mix Composition', fontsize=14, pad=20)
        
        plt.setp(autotexts, size=12, weight="bold")
        plt.setp(texts, size=12)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        st.error(f"Error generating pie chart: {str(e)}")
        return None

def create_pdf_report(data, pie_chart_buf=None, project_name="Unnamed Project"):
    """Create a professional PDF report with centered table and clean formatting"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Set document properties
        pdf.set_title(f"Concrete Mix Design Report - {project_name}")
        pdf.set_author("Zhongmei Engineering Group")
        
        # --- Header Section ---
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            pdf.image("assets/client_logo.png", x=10, y=8, w=30)
            
        # Report title and project info
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Concrete Mix Design Report", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Project: {project_name}", ln=True, align='C')
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
        pdf.ln(15)

        # --- Mix Design Table (Centered) ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Mix Design Parameters", ln=True, align='C')
        pdf.ln(5)
        
        # Table settings
        col_widths = [70, 30, 30]  # Parameter, Value, Unit columns
        row_height = 8
        
        # Header row (centered)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(col_widths[0], row_height, "Parameter", border=1, align='C')
        pdf.cell(col_widths[1], row_height, "Value", border=1, align='C')
        pdf.cell(col_widths[2], row_height, "Unit", border=1, align='C')
        pdf.ln(row_height)
        
        # Table content (centered)
        pdf.set_font("Arial", '', 10)
        units_mapping = {
            "Target Mean Strength": "MPa",
            "Water": "kg/m³",
            "Cement": "kg/m³",
            "Fine Aggregate": "kg/m³",
            "Coarse Aggregate": "kg/m³",
            "Air Content": "%",
            "Admixture": "kg/m³"
        }
        
        for param, value in data.items():
            unit = units_mapping.get(param, "")
            pdf.cell(col_widths[0], row_height, param, border=1, align='C')
            pdf.cell(col_widths[1], row_height, f"{value:.2f}", border=1, align='C')
            pdf.cell(col_widths[2], row_height, unit, border=1, align='C')
            pdf.ln(row_height)
        
        pdf.ln(10)

        # --- Pie Chart Section ---
        if pie_chart_buf:
            try:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                    tmpfile.write(pie_chart_buf.getvalue())
                    tmp_path = tmpfile.name
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Mix Composition by Weight", ln=True, align='C')
                pdf.image(tmp_path, x=50, w=110)
                
                # Simplified composition list (removed redundant key section)
                pdf.ln(5)
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 10, "- Water: {:.1f}%".format(data["Water"]/sum([
                    data["Water"], data["Cement"], 
                    data["Fine Aggregate"], data["Coarse Aggregate"]
                ])*100), ln=True, align='L')
                pdf.cell(0, 10, "- Cement: {:.1f}%".format(data["Cement"]/sum([
                    data["Water"], data["Cement"], 
                    data["Fine Aggregate"], data["Coarse Aggregate"]
                ])*100), ln=True, align='L')
                pdf.cell(0, 10, "- Fine Aggregate: {:.1f}%".format(data["Fine Aggregate"]/sum([
                    data["Water"], data["Cement"], 
                    data["Fine Aggregate"], data["Coarse Aggregate"]
                ])*100), ln=True, align='L')
                pdf.cell(0, 10, "- Coarse Aggregate: {:.1f}%".format(data["Coarse Aggregate"]/sum([
                    data["Water"], data["Cement"], 
                    data["Fine Aggregate"], data["Coarse Aggregate"]
                ])*100), ln=True, align='L')
                
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"Error adding pie chart: {str(e)}")

        # --- Footer ---
        pdf.set_y(-15)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, f"Generated by {CLIENT_NAME} | {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 0, 'C')
        
        return pdf.output(dest='S').encode('latin1')
        
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None

# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)# --- Main UI Logic ---
if st.button("🧪 Compute Mix Design",  key="compute_mix_button"):
    try:
        result = calculate_mix()
        if not isinstance(result, dict):
            raise ValueError("Invalid mix calculation results")
        
        st.write("### 📊 Mix Proportions:")
        
        # Create DataFrame for display
        df = pd.DataFrame.from_dict(result, orient='index', columns=['Value'])
        styled_df = (
            df.style
            .set_properties(**{'text-align': 'left'})  # Left-align index (material names)
            .set_properties(subset=['Value'], **{'text-align': 'right'})  # Right-align values
            .set_table_styles([{
                'selector': 'th.col_heading',  # Target only the "Value" header
                'props': [('text-align', 'right')]
            }])
            .format({'Value': '{:.1f}'})  # Format to 1 decimal place
        )
        
        # Display in Streamlit
        st.dataframe(styled_df)
         
        # Display results in two columns
        col_table, col_chart = st.columns([1, 1])

        with col_table:
           pass
            
        with col_chart:
            pie_chart_buf = generate_pie_chart_image(result)
            if pie_chart_buf:
                st.image(pie_chart_buf, caption="Mix Composition", use_column_width=True)

        # CSV Download
        csv = df.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Download CSV", 
            data=csv, 
            file_name="concrete_mix.csv", 
            mime='text/csv'
        )

        # PDF Generation
        if pie_chart_buf:
            pdf_bytes = create_pdf_report(result, pie_chart_buf, project_name)
            if pdf_bytes:
                st.download_button(
                    "📄 Download PDF Report", 
                    pdf_bytes, 
                    file_name=f"mix_design_{project_name.replace(' ', '_')}.pdf", 
                    mime="application/pdf"
                )
                
    except Exception as e:
        st.error(f"An error occurred during mix calculation: {str(e)}")

# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)
