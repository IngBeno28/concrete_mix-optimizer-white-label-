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

def create_pdf_report(dataframe, pie_chart_buf=None, title="Concrete Mix Design Report"):
    """Create a professional PDF report with mix design results and pie chart."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Set document properties
        pdf.set_title(title)
        pdf.set_author("Concrete Mix Optimizer")
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.ln(10)
        
        # Add pie chart if available
        if pie_chart_buf:
            try:
                # Save the BytesIO buffer to a temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                    tmpfile.write(pie_chart_buf.getvalue())
                    tmp_path = tmpfile.name
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Mix Composition", ln=True, align='C')
                pdf.image(tmp_path, x=50, w=110)
                pdf.ln(5)
                
                # Clean up the temporary file
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"Error adding pie chart to PDF: {str(e)}")
        
        # Add mix design table
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Mix Design Parameters", ln=True, align='C')
        pdf.ln(5)
        
        # Create table header
        pdf.set_font("Arial", 'B', 10)
        col_width = 40
        row_height = 8
        for col in dataframe.columns:
            pdf.cell(col_width, row_height, str(col), border=1, align='C')
        pdf.ln(row_height)
        
        # Add table rows
        pdf.set_font("Arial", '', 10)
        for _, row in dataframe.iterrows():
            for col in dataframe.columns:
                pdf.cell(col_width, row_height, str(row[col]), border=1)
            pdf.ln(row_height)
        
        # Add footer
        pdf.set_y(-15)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 0, 'C')
        
        return pdf.output(dest='S').encode('latin1')
        
    except Exception as e:
        st.error(f"Error generating PDF report: {str(e)}")
        return None
        
# --- Main UI Logic ---
if st.button("🧪 Compute Mix Design"):
    result = calculate_mix()
    st.write("### 📊 Mix Proportions:")

    # Create DataFrame safely
    if not isinstance(result, dict):
        st.error("Invalid mix calculation results")
        st.stop()
    
    df = pd.DataFrame.from_dict(result, orient='index', columns=['Value'])
    
    col_table, col_chart = st.columns([2, 1])

    with col_table:
        st.dataframe(df.style.format(precision=2), height=min(len(result) * 45 + 50, 400), use_container_width=True)

    with col_chart:
        chart_type = st.radio("📈 Chart Type", ["Pie", "Bar"], horizontal=True)
        
        # Filter and prepare chart data
        chart_data = {
            k.split(" (")[0]: v for k, v in result.items() 
            if isinstance(v, (int, float)) and "kg/m³" in k and "Admixture" not in k
        }
        
        if not chart_data:
            st.warning("No valid data for chart generation")
        else:
            fig_width = 4 if st.session_state.get('is_mobile', False) else 5
            fig, ax = plt.subplots(figsize=(fig_width, fig_width*0.75))
            
            if chart_type == "Pie":
                ax.pie(chart_data.values(), labels=chart_data.keys(), autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
            else:
                bars = ax.bar(chart_data.keys(), chart_data.values(), color='skyblue')
                ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=8)
                ax.set_ylabel("Mass (kg/m³)")
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # CSV Download
    csv = df.to_csv().encode('utf-8')
    st.download_button(
        label="📥 Download CSV", 
        data=csv, 
        file_name="aci_mix.csv", 
        mime='text/csv'
    )

    # PDF Download (only if we have valid data)
    if chart_data:
        pie_buf = generate_pie_chart_image(chart_data)
        if pie_buf:
            pdf_bytes = create_pdf_report(df, pie_buf)
            if pdf_bytes:
                st.download_button(
                    "📄 Download PDF Report", 
                    pdf_bytes, 
                    file_name="mix_design_report.pdf", 
                    mime="application/pdf"
                )
            else:
                st.warning("Failed to generate PDF report")
        else:
            st.warning("Failed to generate chart for PDF report")
    else:
        st.warning("No valid data available for PDF report generation")

# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)

st.session_state.is_mobile = st.checkbox("Mobile view", False, disabled=True, label_visibility="collapsed")
