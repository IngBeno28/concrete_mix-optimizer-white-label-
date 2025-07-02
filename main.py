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
st.set_page_config(layout="wide")

# Initialize session state
if 'mix_designs' not in st.session_state:
    st.session_state.mix_designs = []
if 'show_new_design' not in st.session_state:
    st.session_state.show_new_design = False
if 'default_params' not in st.session_state:
    st.session_state.default_params = {
        'fck': 25.0,
        'std_dev': 5.0,
        'exposure': 'Moderate',
        'max_agg_size': 20,
        'slump': 75,
        'air_entrained': False,
        'air_content': 5.0,
        'wcm': 0.5,
        'admixture': 0.0,
        'fm': 2.7,
        'sg_cement': 3.15,
        'sg_fa': 2.65,
        'sg_ca': 2.65,
        'unit_weight_ca': 1600,
        'moist_fa': 2.0,
        'moist_ca': 1.0
    }

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Display heading and logo in the same row with vertical alignment
col1, col2 = st.columns([1, 5])
with col1:
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=100)
with col2:
    st.markdown(
        f"<h2 style='color:{PRIMARY_COLOR}; margin-top: 15px;'>{APP_TITLE}</h2>", 
        unsafe_allow_html=True
    )

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
project_name = st.text_input("📌 Project Name", "Unnamed Project")

# Get current parameters based on whether we're showing a new design or modifying
if st.session_state.show_new_design and st.session_state.mix_designs:
    current_params = st.session_state.mix_designs[-1]['inputs']
else:
    current_params = st.session_state.default_params

with st.expander("📋 ACI Design Inputs", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        fck = st.number_input("f'c (MPa)", 10.0, 80.0, current_params['fck'])
        std_dev = st.number_input("Standard deviation (MPa)", 3.0, 10.0, current_params['std_dev'])
        exposure = st.selectbox("Exposure Class", list(ACI_EXPOSURE), 
                              index=list(ACI_EXPOSURE).index(current_params['exposure']))

    with col2:
        max_agg_size = st.selectbox("Max Aggregate Size (mm)", [10, 20, 40], 
                                  index=[10, 20, 40].index(current_params['max_agg_size']))
        slump = st.slider("Slump (mm)", 25, 200, current_params['slump'])
        air_entrained = st.checkbox("Air Entrained", current_params['air_entrained'])
        air_content = st.slider("Target Air Content (%)", 1.0, 8.0, current_params['air_content']) if air_entrained else 0.0

    with col3:
        wcm = st.number_input("w/c Ratio", 0.3, 0.7, current_params['wcm'])
        admixture = st.number_input("Admixture (%)", 0.0, 5.0, current_params['admixture'])
        fm = st.slider("FA Fineness Modulus", 2.4, 3.0, current_params['fm'], step=0.1)

with st.expander("🔬 Material Properties"):
    sg_cement = st.number_input("Cement SG", 2.0, 3.5, current_params['sg_cement'])
    sg_fa = st.number_input("Fine Aggregate SG", 2.4, 2.8, current_params['sg_fa'])
    sg_ca = st.number_input("Coarse Aggregate SG", 2.4, 2.8, current_params['sg_ca'])
    unit_weight_ca = st.number_input("CA Unit Weight (kg/m³)", 1400, 1800, current_params['unit_weight_ca'])
    moist_fa = st.number_input("FA Moisture (%)", 0.0, 10.0, current_params['moist_fa'])
    moist_ca = st.number_input("CA Moisture (%)", 0.0, 10.0, current_params['moist_ca'])

# --- Mix Design Logic ---
def calculate_mix(
    fck, std_dev, exposure, max_agg_size, slump, air_entrained,
    air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
    unit_weight_ca, moist_fa, moist_ca
):
    """Calculate concrete mix design based on ACI method"""
    try:
        # Calculate target mean strength
        ft = fck + 1.34 * std_dev
        
        # Check w/c ratio against exposure limits
        if wcm > ACI_EXPOSURE[exposure]['max_wcm']:
            st.warning("w/c ratio exceeds maximum recommended for selected exposure class")
        
        # Determine water content based on aggregate size and air entrainment
        water_table = ACI_WATER_CONTENT["Air-Entrained" if air_entrained else "Non-Air-Entrained"]
        water = water_table[max_agg_size]
        
        # Adjust water for slump
        water += (slump - 75) * 0.3
        
        # Adjust water for admixture
        if admixture:
            water *= 1 - min(0.15, admixture * 0.05)
        
        # Calculate cement content
        cement = max(water / wcm, ACI_EXPOSURE[exposure]['min_cement'])
        
        # Determine coarse aggregate volume
        try:
            ca_vol = ACI_CA_VOLUME[round(fm, 1)][max_agg_size]
        except KeyError:
            ca_vol = ACI_CA_VOLUME[2.7][max_agg_size]  # Default to FM=2.7 if exact match not found
        
        # Calculate coarse aggregate mass
        ca_mass = ca_vol * unit_weight_ca
        
        # Calculate absolute volumes
        cement_vol = cement / (sg_cement * 1000)
        water_vol = water / 1000
        air_vol = air_content / 100 if air_entrained else 0.01
        ca_vol_abs = ca_mass / (sg_ca * 1000)
        
        # Calculate fine aggregate volume and mass
        fa_vol = 1 - (cement_vol + water_vol + air_vol + ca_vol_abs)
        fa_mass = fa_vol * sg_fa * 1000
        
        # Adjust for moisture content
        fa_mass_adj = fa_mass * (1 + moist_fa / 100)
        ca_mass_adj = ca_mass * (1 + moist_ca / 100)
        water -= (fa_mass * moist_fa / 100 + ca_mass * moist_ca / 100)
        
        # Calculate admixture amount
        admix_amount = cement * admixture / 100
        
        return {
            "Target Mean Strength": round(ft, 2),
            "Water": round(water, 1),
            "Cement": round(cement, 1),
            "Fine Aggregate": round(fa_mass_adj, 1),
            "Coarse Aggregate": round(ca_mass_adj, 1),
            "Air Content": round(air_content, 1),
            "Admixture": round(admix_amount, 2)
        }
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return None

def generate_pie_chart(data):
    """Generate pie chart of material composition"""
    try:
        # Filter relevant components
        material_components = {
            k: v for k, v in data.items() 
            if k in ["Water", "Cement", "Fine Aggregate", "Coarse Aggregate"] and v > 0
        }
        
        if not material_components:
            return None
            
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            material_components.values(),
            labels=material_components.keys(),
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10}
        )
        
        # Style the chart
        ax.axis('equal')
        ax.set_title('Mix Composition', fontsize=12, pad=10)
        plt.setp(autotexts, size=10, weight="bold")
        plt.setp(texts, size=10)
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        st.error(f"Chart generation error: {str(e)}")
        return None

def create_pdf_report_multiple(designs: list, project_name: str) -> bytes:
    """Generate a comprehensive PDF report with all mix designs including parameter tables"""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Helper function to safely encode text
        def safe_text(text):
            if not isinstance(text, str):
                text = str(text)
            return text.encode('latin-1', errors='replace').decode('latin-1')

        # --- Cover Page with Logo ---
        pdf.add_page()
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                with Image.open(LOGO_PATH) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    temp_logo_path = os.path.join(tempfile.gettempdir(), 
                                                f"temp_logo_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
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
        pdf.cell(0, 10, safe_text(f"Project: {project_name}"), 0, 1, 'C')
        pdf.cell(0, 10, safe_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), 0, 1, 'C')
        pdf.ln(20)
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, safe_text(f"Total Designs: {len(designs)}"), 0, 1, 'C')

        # --- Design Pages ---
        for i, design in enumerate(designs, 1):
            pdf.add_page()
            
            # Design header
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, safe_text(f"Design #{i}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, safe_text(f"Target Strength: {design['data']['Target Mean Strength']} MPa"), 0, 1, 'C')
            pdf.cell(0, 8, safe_text(f"Calculated: {design['timestamp']}"), 0, 1, 'C')
            pdf.ln(10)

            # --- Results Table ---
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, safe_text("Mix Design Results"), 0, 1, 'C')
            
            col_widths = [70, 30, 30]
            pdf.set_font("Arial", 'B', 10)
            pdf.set_x((pdf.w - sum(col_widths))/2)
            pdf.cell(col_widths[0], 8, safe_text("Parameter"), 1, 0, 'C')
            pdf.cell(col_widths[1], 8, safe_text("Value"), 1, 0, 'C')
            pdf.cell(col_widths[2], 8, safe_text("Unit"), 1, 1, 'C')
            
            pdf.set_font("Arial", '', 10)
            for param, value in design['data'].items():
                pdf.set_x((pdf.w - sum(col_widths))/2)
                pdf.cell(col_widths[0], 8, safe_text(param), 1)
                pdf.cell(col_widths[1], 8, safe_text(f"{value:.2f}"), 1, 0, 'C')
                pdf.cell(col_widths[2], 8, safe_text({
                    "Target Mean Strength": "MPa",
                    "Water": "kg/m³",
                    "Cement": "kg/m³",
                    "Fine Aggregate": "kg/m³",
                    "Coarse Aggregate": "kg/m³",
                    "Air Content": "%",
                    "Admixture": "kg/m³"
                }.get(param, "-")), 1, 0, 'C')
                pdf.ln(8)

            # --- Design Parameters Table ---
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, safe_text("Design Parameters"), 0, 1, 'C')
            
            # Prepare parameter data
            params = design['inputs']
            parameter_data = [
                ["Material Properties", "", ""],
                [f"Cement SG", f"{params['sg_cement']}", ""],
                [f"Fine Aggregate SG", f"{params['sg_fa']}", ""],
                [f"Coarse Aggregate SG", f"{params['sg_ca']}", ""],
                [f"CA Unit Weight", f"{params['unit_weight_ca']} kg/m³", ""],
                [f"FA Moisture", f"{params['moist_fa']}%", ""],
                [f"CA Moisture", f"{params['moist_ca']}%", ""],
                ["", "", ""],
                ["Mix Parameters", "", ""],
                [f"f'c", f"{params['fck']} MPa", ""],
                [f"Standard Deviation", f"{params['std_dev']} MPa", ""],
                [f"Exposure Class", f"{params['exposure']}", ""],
                [f"Max Aggregate Size", f"{params['max_agg_size']} mm", ""],
                [f"Slump", f"{params['slump']} mm", ""],
                [f"Air Entrained", f"{'Yes' if params['air_entrained'] else 'No'}", ""],
                [f"Target Air Content", f"{params['air_content']}%" if params['air_entrained'] else "N/A", ""],
                [f"w/c Ratio", f"{params['wcm']}", ""],
                [f"Admixture", f"{params['admixture']}%", ""],
                [f"FA Fineness Modulus", f"{params['fm']}", ""]
            ]

            # Create parameter table
            param_col_widths = [70, 50, 30]
            pdf.set_font("Arial", '', 10)
            
            for row in parameter_data:
                pdf.set_x((pdf.w - sum(param_col_widths))/2)
                
                # Style headers differently
                if row[0] in ["Material Properties", "Mix Parameters"]:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(sum(param_col_widths), 8, safe_text(row[0]), 1, 1, 'C')
                    pdf.set_font("Arial", '', 10)
                else:
                    pdf.cell(param_col_widths[0], 8, safe_text(row[0]), 1)
                    pdf.cell(param_col_widths[1], 8, safe_text(row[1]), 1)
                    pdf.cell(param_col_widths[2], 8, safe_text(row[2]), 1)
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

        # Generate final PDF
        return pdf.output(dest='S').encode('latin-1', errors='replace')
            
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None

# --- Main Application Logic ---
if not st.session_state.show_new_design:
    if st.button("🧪 Compute Mix Design", key="compute_mix_button"):
        result = calculate_mix(
            fck, std_dev, exposure, max_agg_size, slump, air_entrained,
            air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
            unit_weight_ca, moist_fa, moist_ca
        )
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
            st.rerun()
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
            result = calculate_mix(
                fck, std_dev, exposure, max_agg_size, slump, air_entrained,
                air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
                unit_weight_ca, moist_fa, moist_ca
            )
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
                st.rerun()
    
    with col2:
        if st.button("🆕 Start Fresh Design", key="fresh_design"):
            st.session_state.show_new_design = False
            st.session_state.mix_designs = []  # Clear all previous designs
            st.rerun()

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
            st.rerun()
        
# --- Footer ---
st.markdown("---")
st.caption(FOOTER_NOTE)
