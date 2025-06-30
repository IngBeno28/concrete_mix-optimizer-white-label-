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



def create_pdf_report_multiple(designs: list, project_name: str) -> bytes:
    """Generate a comprehensive PDF report with all mix designs"""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Replace bullet points with asterisks in all text
        def safe_text(text):
            return text.replace('•', '*').replace('–', '-').replace('—', '-')
        
        # Cover Page
        pdf.add_page()
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                with Image.open(LOGO_PATH) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    temp_logo_path = os.path.join(tempfile.gettempdir(), f"temp_logo_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    img.save(temp_logo_path, format='JPEG', quality=95)
                    pdf.image(temp_logo_path, x=(pdf.w - 40)/2, y=30, w=40)
                    os.unlink(temp_logo_path)
                pdf.ln(50)
            except Exception as e:
                st.error(f"Logo processing error: {str(e)}")

        # Cover page content
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 15, safe_text("Concrete Mix Design Report"), 0, 1, 'C')
        pdf.set_font("Arial", '', 16)
        pdf.cell(0, 10, f"Project: {project_name}", 0, 1, 'C')
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
        pdf.ln(20)
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, f"Total Designs: {len(designs)}", 0, 1, 'C')
        pdf.ln(15)
        pdf.set_font("Arial", 'I', 12)
        pdf.cell(0, 10, f"Generated by {CLIENT_NAME}", 0, 1, 'C')

        # --- Table of Contents ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 15, "Table of Contents", 0, 1)
        pdf.set_font("Arial", '', 12)
        pdf.ln(10)
        
        for i, design in enumerate(designs, 1):
            pdf.cell(0, 8, f"{i}. Design {i} - {design['data']['Target Mean Strength']} MPa (Page {i+2})", 0, 1)
            pdf.cell(0, 2, "", 0, 1)  # Small space between items

        # --- Design Pages ---
        for i, design in enumerate(designs, 1):
            pdf.add_page()
            
            # Page header with logo (smaller)
            if LOGO_PATH and os.path.exists(LOGO_PATH):
                try:
                    with Image.open(LOGO_PATH) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        temp_logo_path = os.path.join(tempfile.gettempdir(), f"temp_logo_small_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                        img.save(temp_logo_path, format='JPEG', quality=90)
                        pdf.image(temp_logo_path, x=10, y=8, w=20)
                        os.unlink(temp_logo_path)
                except Exception as e:
                    pass  # Skip logo if there's an error

            # Design header
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 15, f"Design #{i}", 0, 1, 'C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, f"Target Strength: {design['data']['Target Mean Strength']} MPa", 0, 1, 'C')
            pdf.cell(0, 8, f"Calculated: {design['timestamp']}", 0, 1, 'C')
            pdf.ln(10)

            # Results table
            col_widths = [70, 30, 30]
            pdf.set_font("Arial", 'B', 10)
            pdf.set_x((pdf.w - sum(col_widths))/2)  # Center table
            pdf.cell(col_widths[0], 8, "Parameter", 1, 0, 'C')
            pdf.cell(col_widths[1], 8, "Value", 1, 0, 'C')
            pdf.cell(col_widths[2], 8, "Unit", 1, 1, 'C')
            
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
                pdf.set_x((pdf.w - sum(col_widths))/2)
                pdf.cell(col_widths[0], 8, param, 1)
                pdf.cell(col_widths[1], 8, f"{value:.2f}", 1, 0, 'C')
                pdf.cell(col_widths[2], 8, units.get(param, "-"), 1, 0, 'C')
                pdf.ln(8)

            # Input parameters section
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Design Parameters:", 0, 1, 'C')
            
            # Organize parameters into 3 columns
            params = design['inputs']
            col1 = [
                f"• f'c: {params['fck']} MPa",
                f"• Std Dev: {params['std_dev']} MPa",
                f"• Exposure: {params['exposure']}",
                f"• Max Agg Size: {params['max_agg_size']} mm"
            ]
            
            col2 = [
                f"• Slump: {params['slump']} mm",
                f"• Air Entrained: {'Yes' if params['air_entrained'] else 'No'}",
                f"• Air Content: {params['air_content']}%" if params['air_entrained'] else "",
                f"• w/c Ratio: {params['wcm']}"
            ]
            
            col3 = [
                f"• Admixture: {params['admixture']}%",
                f"• FM: {params['fm']}",
                f"• Cement SG: {params['sg_cement']}",
                f"• FA SG: {params['sg_fa']}"
            ]
            
            # Print columns side by side
            pdf.set_font("Arial", '', 10)
            pdf.set_x(15)
            for i in range(max(len(col1), len(col2), len(col3))):
                if i < len(col1):
                    pdf.cell(60, 8, col1[i])
                else:
                    pdf.cell(60, 8, "")
                
                if i < len(col2):
                    pdf.cell(60, 8, col2[i])
                else:
                    pdf.cell(60, 8, "")
                
                if i < len(col3):
                    pdf.cell(60, 8, col3[i])
                else:
                    pdf.cell(60, 8, "")
                pdf.ln(8)

            # Add chart if available
            if design.get('chart'):
                try:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        Image.open(design['chart']).convert('RGB').save(tmp.name, quality=95)
                        pdf.image(tmp.name, x=(pdf.w - 100)/2, y=pdf.get_y()+5, w=100)
                        os.unlink(tmp.name)
                except Exception as e:
                    st.error(f"Chart rendering error: {str(e)}")

            # Page footer
            pdf.set_y(-15)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(0, 10, f"Page {pdf.page_no()} | {CLIENT_NAME}", 0, 0, 'C')

        return pdf.output(dest='S').encode('latin-1', errors='replace')
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None

# --- Main Application Logic ---
if 'mix_designs' not in st.session_state:
    st.session_state.mix_designs = []
if 'show_new_design' not in st.session_state:
    st.session_state.show_new_design = False

# Compute or Start New Design button
if not st.session_state.show_new_design:
    if st.button("🧪 Compute Mix Design", key="compute_mix_button"):
        result = calculate_mix()
        if result:
            chart_buf = generate_pie_chart(result)
            st.session_state.mix_designs.append({
                'data': result,
                'chart': chart_buf,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'inputs': {
                    'fck': fck,
                    'std_dev': std_dev,
                    'exposure': exposure,
                    'max_agg_size': max_agg_size,
                    'slump': slump,
                    'air_entrained': air_entrained,
                    'air_content': air_content,
                    'wcm': wcm,
                    'admixture': admixture,
                    'fm': fm,
                    'sg_cement': sg_cement,
                    'sg_fa': sg_fa,
                    'sg_ca': sg_ca,
                    'unit_weight_ca': unit_weight_ca,
                    'moist_fa': moist_fa,
                    'moist_ca': moist_ca
                }
            })
            st.success("Mix design calculated and saved!")
            st.session_state.show_new_design = True
            st.rerun()  # Fixed: Replaced experimental_rerun()
else:
    # Display current parameters with option to modify
    with st.expander("⚙️ Current Parameters (Click to Modify)", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fck = st.number_input("f'c (MPa)", 10.0, 80.0, 
                                st.session_state.mix_designs[-1]['inputs']['fck'],
                                key="mod_fck")
            std_dev = st.number_input("Standard deviation (MPa)", 3.0, 10.0, 
                                    st.session_state.mix_designs[-1]['inputs']['std_dev'],
                                    key="mod_std_dev")
            exposure = st.selectbox("Exposure Class", list(ACI_EXPOSURE), 
                                  index=list(ACI_EXPOSURE).index(st.session_state.mix_designs[-1]['inputs']['exposure']),
                                  key="mod_exposure")

        with col2:
            max_agg_size = st.selectbox("Max Aggregate Size (mm)", [10, 20, 40], 
                                      index=[10, 20, 40].index(st.session_state.mix_designs[-1]['inputs']['max_agg_size']),
                                      key="mod_max_agg_size")
            slump = st.slider("Slump (mm)", 25, 200, 
                            st.session_state.mix_designs[-1]['inputs']['slump'],
                            key="mod_slump")
            air_entrained = st.checkbox("Air Entrained", 
                                      st.session_state.mix_designs[-1]['inputs']['air_entrained'],
                                      key="mod_air_entrained")
            air_content = st.slider("Target Air Content (%)", 1.0, 8.0, 
                                  st.session_state.mix_designs[-1]['inputs']['air_content'],
                                  key="mod_air_content") if air_entrained else 0.0

        with col3:
            wcm = st.number_input("w/c Ratio", 0.3, 0.7, 
                                st.session_state.mix_designs[-1]['inputs']['wcm'],
                                key="mod_wcm")
            admixture = st.number_input("Admixture (%)", 0.0, 5.0, 
                                      st.session_state.mix_designs[-1]['inputs']['admixture'],
                                      key="mod_admixture")
            fm = st.slider("FA Fineness Modulus", 2.4, 3.0, 
                          st.session_state.mix_designs[-1]['inputs']['fm'], 
                          step=0.1,
                          key="mod_fm")

    # Material Properties (collapsed by default)
    with st.expander("🔬 Material Properties (Click to Modify)"):
        sg_cement = st.number_input("Cement SG", 2.0, 3.5, 
                                  st.session_state.mix_designs[-1]['inputs']['sg_cement'],
                                  key="mod_sg_cement")
        sg_fa = st.number_input("Fine Aggregate SG", 2.4, 2.8, 
                              st.session_state.mix_designs[-1]['inputs']['sg_fa'],
                              key="mod_sg_fa")
        sg_ca = st.number_input("Coarse Aggregate SG", 2.4, 2.8, 
                              st.session_state.mix_designs[-1]['inputs']['sg_ca'],
                              key="mod_sg_ca")
        unit_weight_ca = st.number_input("CA Unit Weight (kg/m³)", 1400, 1800, 
                                       st.session_state.mix_designs[-1]['inputs']['unit_weight_ca'],
                                       key="mod_unit_weight_ca")
        moist_fa = st.number_input("FA Moisture (%)", 0.0, 10.0, 
                                 st.session_state.mix_designs[-1]['inputs']['moist_fa'],
                                 key="mod_moist_fa")
        moist_ca = st.number_input("CA Moisture (%)", 0.0, 10.0, 
                                 st.session_state.mix_designs[-1]['inputs']['moist_ca'],
                                 key="mod_moist_ca")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Compute With Modified Parameters", key="compute_modified"):
            result = calculate_mix()
            if result:
                chart_buf = generate_pie_chart(result)
                st.session_state.mix_designs.append({
                    'data': result,
                    'chart': chart_buf,
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'inputs': {
                        'fck': fck,
                        'std_dev': std_dev,
                        'exposure': exposure,
                        'max_agg_size': max_agg_size,
                        'slump': slump,
                        'air_entrained': air_entrained,
                        'air_content': air_content,
                        'wcm': wcm,
                        'admixture': admixture,
                        'fm': fm,
                        'sg_cement': sg_cement,
                        'sg_fa': sg_fa,
                        'sg_ca': sg_ca,
                        'unit_weight_ca': unit_weight_ca,
                        'moist_fa': moist_fa,
                        'moist_ca': moist_ca
                    }
                })
                st.success("New mix design calculated!")
                st.rerun()  # Fixed: Replaced experimental_rerun()
    
    with col2:
        if st.button("🆕 Start Fresh Design", key="fresh_design"):
            st.session_state.show_new_design = False
            st.rerun()  # Fixed: Replaced experimental_rerun()

# Display accumulated designs
if st.session_state.mix_designs:
    st.subheader(f"📚 Accumulated Designs ({len(st.session_state.mix_designs)})")
    
    for i, design in enumerate(st.session_state.mix_designs, 1):
        with st.expander(f"Design #{i} - {design['data']['Target Mean Strength']} MPa (Click to View)", expanded=(i==len(st.session_state.mix_designs))):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(
                    pd.DataFrame.from_dict(design['data'], orient='index', columns=['Value']),
                    height=300,
                    use_container_width=True
                )
            
            with col2:
                if design.get('chart'):
                    st.image(design['chart'], use_container_width=True)
            
            st.caption(f"Calculated at {design['timestamp']}")

    # Master PDF and Clear options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Generate Master PDF", key="generate_pdf"):
            with st.spinner(f"Compiling {len(st.session_state.mix_designs)} designs..."):
                pdf_bytes = create_pdf_report_multiple(
                    st.session_state.mix_designs,
                    project_name
                )
                if pdf_bytes:
                    st.download_button(
                        "💾 Download Full Report",
                        pdf_bytes,
                        f"concrete_mix_designs_{project_name}.pdf",
                        "application/pdf",
                        key="download_pdf"
                    )
    
    with col2:
        if st.button("🧹 Clear All Designs", key="clear_designs"):
            st.session_state.mix_designs = []
            st.session_state.show_new_design = False
            st.success("All designs cleared!")
            st.rerun()  # Fixed: Replaced experimental_rerun()
        
# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)
