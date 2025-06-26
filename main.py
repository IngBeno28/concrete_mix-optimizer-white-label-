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
        "Target Mean Strength f't (MPa)": round(ft,2),
        "Water (kg/m³)": round(water,1),
        "Cement (kg/m³)": round(cement,1),
        "Fine Aggregate (kg/m³)": round(fa_mass_adj,1),
        "Coarse Aggregate (kg/m³)": round(ca_mass_adj,1),
        "Air Content (%)": round(air_content,1),
        "Admixture (kg/m³)": round(cement * admixture / 100,2)
    }


def generate_pie_chart_image(data):
    """
    Generate a pie chart image from composition data and return as bytes buffer.
    
    Args:
        data (dict): Dictionary containing material names and quantities
        
    Returns:
        BytesIO: Buffer containing PNG image of the pie chart
    """
    try:
        # Convert the input data to proper format if needed
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
            
        # Extract labels and values
        labels = []
        values = []
        for k, v in data.items():
            if isinstance(v, (int, float)):
                labels.append(k)
                values.append(v)
        
        if not labels or not values:
            raise ValueError("No valid data found for chart generation")
            
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
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

def create_pdf_report(dataframe, pie_chart_buf=None, project_name="Unnamed Project"):
    """Create a professional PDF report with improved formatting."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Set document properties
        pdf.set_title(f"Concrete Mix Design Report - {project_name}")
        pdf.set_author("Concrete Mix Optimizer")
        
        # Add logo if available
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            pdf.image(LOGO_PATH, x=10, y=8, w=30)
        
        # Add title and project info
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Concrete Mix Design Report", ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Project: {project_name}", ln=True, align='C')
        pdf.ln(10)
        
        # Add pie chart if available
        if pie_chart_buf:
            try:
                # Save chart to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                    tmpfile.write(pie_chart_buf.getvalue())
                    tmp_path = tmpfile.name
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Mix Composition by Weight", ln=True, align='C')
                pdf.image(tmp_path, x=50, w=110)
                pdf.ln(10)
                
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"Error adding pie chart to PDF: {str(e)}")
        
        # Add mix design table with improved formatting
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Mix Design Parameters", ln=True, align='C')
        pdf.ln(5)
        
        # Table header
        pdf.set_font("Arial", 'B', 10)
        col_widths = [70, 30]  # Parameter and Value columns
        row_height = 8
        
        # Header row
        pdf.cell(col_widths[0], row_height, "Parameter", border=1, align='C')
        pdf.cell(col_widths[1], row_height, "Value", border=1, align='C')
        pdf.ln(row_height)
        
        # Table rows with proper units
        pdf.set_font("Arial", '', 10)
        for index, row in dataframe.iterrows():
            # Format parameter names
            param_name = index.replace(" (kg/m³)", "").replace(" (%)", "")
            unit = "kg/m³" if "kg/m³" in index else "%" if "%" in index else ""
            
            pdf.cell(col_widths[0], row_height, param_name, border=1)
            pdf.cell(col_widths[1], row_height, f"{row['Value']} {unit}", border=1, align='C')
            pdf.ln(row_height)
        
        # Add footer
        pdf.set_y(-15)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | {CLIENT_NAME}", 0, 0, 'C')
        
        return pdf.output(dest='S').encode('latin1')
        
    except Exception as e:
        st.error(f"Error generating PDF report: {str(e)}")
        return None
        
# --- Main UI Logic ---
if st.button("🧪 Compute Mix Design"):
    try:
        result = calculate_mix()
        if not isinstance(result, dict):
            raise ValueError("Invalid mix calculation results")
        
        st.write("### 📊 Mix Proportions:")
        
        # Create DataFrame with cleaned labels
        df = pd.DataFrame.from_dict(result, orient='index', columns=['Value'])
        df.index = df.index.str.replace(r' \(.*\)', '', regex=True)
        
        # Display results in two columns
        col_table, col_chart = st.columns([2, 1])

        with col_table:
            # Apply custom styling for right-aligned values
            st.dataframe(
                df.style.format("{:.1f}").set_properties(**{'text-align': 'right'}),
                height=min(len(result) * 45 + 50, 400),
                use_container_width=True
            )

        with col_chart:
            chart_type = st.radio("📈 Chart Type", ["Pie", "Bar"], horizontal=True)
            
            # Prepare chart data (exclude non-material entries)
            chart_data = {
                k.split(" (")[0]: v for k, v in result.items() 
                if isinstance(v, (int, float)) and 
                any(x in k for x in ["Water", "Cement", "Fine Aggregate", "Coarse Aggregate"])
            }
            
            if chart_data:
                fig, ax = plt.subplots(figsize=(5, 5))
                
                if chart_type == "Pie":
                    ax.pie(
                        chart_data.values(),
                        labels=chart_data.keys(),
                        autopct='%1.1f%%',  # Simpler percentage only
                        startangle=90,
                        textprops={'fontsize': 9}
                    )
                    ax.axis('equal')
                    ax.set_title("Mix Composition", pad=10)
                else:
                    bars = ax.bar(chart_data.keys(), chart_data.values(), color='skyblue')
                    ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=8)
                    ax.set_ylabel("Mass (kg/m³)")
                    plt.xticks(rotation=45, ha='right')
                
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.warning("No material data for chart")

        # CSV Download
        csv = df.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Download CSV", 
            data=csv, 
            file_name="concrete_mix.csv", 
            mime='text/csv'
        )

        # PDF Generation (simplified)
        if chart_data:
            try:
                # Create simple PDF without pie chart if issues persist
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Concrete Mix Design Report", ln=True, align='C')
                pdf.ln(10)
                
                # Add table
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Mix Design Parameters", ln=True, align='C')
                pdf.ln(5)
                
                pdf.set_font("Arial", 'B', 10)
                col_width = 60
                pdf.cell(col_width, 8, "Parameter", border=1)
                pdf.cell(col_width-20, 8, "Value", border=1, align='R')
                pdf.ln(8)
                
                pdf.set_font("Arial", '', 10)
                for index, row in df.iterrows():
                    pdf.cell(col_width, 8, index, border=1)
                    pdf.cell(col_width-20, 8, f"{row['Value']:.1f}", border=1, align='R')
                    pdf.ln(8)
                
                pdf_bytes = pdf.output(dest='S').encode('latin1')
                
                st.download_button(
                    "📄 Download PDF Report", 
                    pdf_bytes, 
                    file_name="mix_design.pdf", 
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"PDF generation error: {str(e)}")
                
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        
# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)

st.session_state.is_mobile = st.checkbox("Mobile view", False, disabled=True, label_visibility="collapsed")
