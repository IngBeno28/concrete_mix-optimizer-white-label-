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

def create_pdf_report(data, chart_buf=None, project_name="Project"):
    """Generate PDF report with guaranteed logo display"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # --- Logo Implementation ---
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                # Debugging: Print absolute path
                abs_logo_path = os.path.abspath(LOGO_PATH)
                print(f"Attempting to load logo from: {abs_logo_path}")  # Check console output
                
                # Convert to RGB and save as temporary JPEG
                with Image.open(LOGO_PATH) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Create temporary file path
                    temp_logo_path = os.path.join(tempfile.gettempdir(), f"temp_logo_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    img.save(temp_logo_path, format='JPEG', quality=100)
                
                # Insert logo (centered, 30mm width)
                pdf.image(temp_logo_path, 
                        x=(pdf.w - 30)/2,  # Center calculation
                        y=10, 
                        w=30)
                
                # Verify temporary file
                print(f"Temporary logo exists: {os.path.exists(temp_logo_path)}")  # Debug
                
                # Cleanup
                try:
                    os.unlink(temp_logo_path)
                except:
                    pass
                
                pdf.ln(25)  # Space after logo
                
            except Exception as e:
                st.error(f"Logo Error: {str(e)}\nPath: {LOGO_PATH}\nExists: {os.path.exists(LOGO_PATH)}")
                
                        # --- Header ---
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Concrete Mix Design Report", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Project: {project_name}", ln=True, align='C')
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
        pdf.ln(15)
        
            # Table settings 
        col_widths = [70, 30, 30]  
        row_height = 8
        total_width = sum(col_widths)
        
        # Calculate left margin to center the table
        left_margin = (pdf.w - total_width) / 2
        
        # Table header - Centered
        pdf.set_font("Arial", 'B', 10)
        pdf.set_x(left_margin)  # This is the key line for centering
        pdf.cell(col_widths[0], row_height, "Parameter", border=1, align='C')
        pdf.cell(col_widths[1], row_height, "Value", border=1, align='C')
        pdf.cell(col_widths[2], row_height, "Unit", border=1, align='C')
        pdf.ln(row_height)
        
        # Table content - Centered
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
        
        for param, value in data.items():
            pdf.set_x(left_margin)  # Reset to center position for each row
            pdf.cell(col_widths[0], row_height, param, border=1)
            pdf.cell(col_widths[1], row_height, f"{value:.2f}", border=1, align='C')
            pdf.cell(col_widths[2], row_height, units.get(param, ""), border=1, align='C')
            pdf.ln(row_height)
        
        pdf.ln(10)

        # Pie Chart Section
        if chart_buf:
            try:
                # Convert BytesIO to PIL Image
                img = Image.open(chart_buf)
                
                # Convert RGBA to RGB if needed
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    img.save(tmp, format='JPEG', quality=95)
                    tmp_path = tmp.name
                
                # Add chart title and image to PDF
                pdf.set_font("Arial", 'B', 12)
                #pdf.cell(0, 10, "Mix Composition", ln=True, align='C')
                pdf.image(tmp_path, x=50, w=110)
                
                # Clean up
                img.close()
                os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"Chart image error: {str(e)}")


        # --- Footer ---
        # Calculate remaining space on page
        remaining_space = pdf.h - pdf.get_y() - 15  # 15mm margin from bottom
        
        # Add spacer if needed to keep footer on same page
        if remaining_space < 10:  
            pdf.add_page()  
        
        # Add footer at fixed position
        pdf.set_y(-15)  # 15mm from bottom
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, f"Generated by {CLIENT_NAME}", 0, 0, 'C')
        
        return pdf.output(dest='S').encode('latin1')
        
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None
   
   
# --- Main Application Logic ---
if st.button("🧪 Compute Mix Design", key="compute_mix_button"):
    with st.spinner("Calculating optimal mix..."):
        result = calculate_mix()
        
        if result:
            st.success("Mix design calculated successfully!")
            
            # Create DataFrame
            df = pd.DataFrame.from_dict(result, orient='index', columns=['Value'])
            df = df.reset_index().rename(columns={'index': 'Material'})
            
            # Format DataFrame
            styled_df = (
                df.style
                .set_properties(subset=['Value'], **{'text-align': 'right'})
                .format({'Value': '{:.1f}'})
            )
            
            # Generate chart
            chart_buf = generate_pie_chart(result)
            
            # Display results
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Concrete Mix Composition")
                st.dataframe(
                    styled_df,
                    height=min(len(result)*35 + 50, 400),
                    use_container_width=True
                )
                
                # CSV Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "concrete_mix.csv",
                    "text/csv"
                )
            
            with col2:
                if chart_buf:
                    st.image(chart_buf, use_container_width=True)
                else:
                    st.warning("No chart data available")
                
                # PDF Download - THIS IS THE CRUCIAL RESTORED SECTION
                if chart_buf:
                    with st.spinner("Generating PDF report..."):
                        pdf_bytes = create_pdf_report(result, chart_buf, project_name)
                        if pdf_bytes:
                            st.download_button(
                                "📄 Download PDF Report",
                                pdf_bytes,
                                f"mix_design_{project_name.replace(' ', '_')}.pdf",
                                "application/pdf"
                            )

# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)
