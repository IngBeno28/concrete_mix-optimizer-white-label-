from branding import CLIENT_NAME, APP_TITLE, PRIMARY_COLOR, LOGO_PATH, FOOTER_NOTE
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
from PIL import Image
import tempfile
import os
from datetime import datetime

# --- Streamlit Config ---
st.set_page_config(APP_TITLE, layout="wide")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Optional: Display client logo
if LOGO_PATH:
    st.image("assets/Zenith logo.jpg", width=120)

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

# --- PDF Helpers ---
def generate_pie_chart_image(data):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
    ax.axis('equal')
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)  # Close the figure to free memory
    return buf

def create_pdf_report(dataframe, pie_chart_buf):
    """Create a PDF report with centered logo and table-formatted data"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add centered logo if available
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        try:
            with Image.open(LOGO_PATH) as img:
                width, height = img.size
                aspect = height / width
                logo_width_mm = 40  # Adjust this to change logo size
                logo_height_mm = logo_width_mm * aspect
                x_position = (210 - logo_width_mm) / 2  # Center calculation
                pdf.image(LOGO_PATH, x=x_position, y=10, w=logo_width_mm, h=logo_height_mm)
                pdf.set_y(10 + logo_height_mm + 10)  # Position content below logo
        except Exception as e:
            st.warning(f"Could not add logo to PDF: {str(e)}")
            pdf.set_y(10)
    else:
        pdf.set_y(10)

    # Header information
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(0, 10, txt=f"Project: {project_name}", ln=True, align='C')
    pdf.cell(0, 10, txt=f"Report Generated: {now}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=APP_TITLE, ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(15)

    # Create table with mix proportions
    col_widths = [100, 50]  # Column widths (Parameter and Value)
    row_height = 8
    
    # Table Header
    pdf.set_fill_color(200, 220, 255)  # Light blue background
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(col_widths[0], row_height, "Parameter", border=1, fill=True)
    pdf.cell(col_widths[1], row_height, "Value", border=1, fill=True, ln=True)
    pdf.set_font("Arial", size=12)
    pdf.set_fill_color(255, 255, 255)  # White background

    # Table Rows
    fill = False  # Alternate row shading
    for index, row in dataframe.iterrows():
        # Alternate row colors for better readability
        fill = not fill
        pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(col_widths[0], row_height, str(index), border=1, fill=True)
        pdf.cell(col_widths[1], row_height, str(row['Value']), border=1, fill=True, ln=True)

    pdf.ln(10)  # Add space after table

    # Add pie chart if available
    if pie_chart_buf:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                pie_chart_buf.seek(0)
                tmp_file.write(pie_chart_buf.read())
                tmp_file.flush()
                
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Mix Composition Visualization", ln=True, align='C')
                pdf.image(tmp_file.name, x=55, y=None, w=100)  # Center chart
                
            os.unlink(tmp_file.name)
        except Exception as e:
            pdf.ln(5)
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 8, txt="Note: Visual chart is available in the web interface", ln=True, align='C')

    # Footer with watermark and note
    pdf.set_y(-30)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, txt=f"Generated by {CLIENT_NAME} | {FOOTER_NOTE}", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

# --- Main UI Logic ---
if st.button("🧪 Compute Mix Design"):
    result = calculate_mix()
    st.write("### 📊 Mix Proportions:")

    df = pd.DataFrame.from_dict(result, orient='index', columns=['Value'])
    col_table, col_chart = st.columns([2, 1])

    with col_table:
        st.dataframe(df.style.format(precision=2), height=min(len(result) * 45 + 50, 400), use_container_width=True)

    with col_chart:
        chart_type = st.radio("📈 Chart Type", ["Pie", "Bar"], horizontal=True)
        chart_data = {k.split(" (")[0]: v for k, v in result.items() if "kg/m³" in k and "Admixture" not in k}

        fig_width = 4 if st.session_state.get('is_mobile', False) else 5
        fig, ax = plt.subplots(figsize=(fig_width, fig_width*0.75))

        if chart_type == "Pie":
            ax.pie(chart_data.values(), labels=chart_data.keys(), autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
            ax.axis('equal')
        else:
            bars = ax.bar(chart_data.keys(), chart_data.values(), color='skyblue')
            ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=8)
            ax.set_ylabel("Mass (kg/m³)")
            ax.set_title("Mix Composition")
            plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)  # Close the figure to free memory

    csv = df.to_csv().encode('utf-8')
    st.download_button(label="📥 Download CSV", data=csv, file_name="aci_mix.csv", mime='text/csv', use_container_width=True)

    pie_buf = generate_pie_chart_image(chart_data)
    pdf_bytes = create_pdf_report(df, pie_buf)
    st.download_button("📄 Download PDF Report", pdf_bytes, file_name="mix_design_report.pdf", mime="application/pdf")

# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)

st.session_state.is_mobile = st.checkbox("Mobile view", False, disabled=True, label_visibility="collapsed")
