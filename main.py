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
from branding import CLIENT_NAME, APP_TITLE, PRIMARY_COLOR, LOGO_PATH, FOOTER_NOTE, LOGO_CONFIG, LOGO_ALT_TEXT

# --- Streamlit Config ---
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏗️",
    layout="wide"
)

# Initialize session state keys if not present
if 'mix_designs' not in st.session_state:
    st.session_state['mix_designs'] = []
if 'show_new_design' not in st.session_state:
    st.session_state['show_new_design'] = False
if 'default_params' not in st.session_state:
    st.session_state['default_params'] = {
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
        'moist_ca': 1.0,
        'construction_type': 'Traditional Cast-in-Place',
        'production_method': 'Batch Plant',
        'early_strength_required': False,
        'steam_curing': False,
        'target_demould_time': 18
    }

# --- Enhanced CSS Loading with Error Handling ---
try:
    with open("style.css") as f:
        css_content = f.read()
        css_content = f":root {{ --primary: {PRIMARY_COLOR}; }}\n" + css_content
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Custom stylesheet not found. Using default styles.")
    st.markdown(f"""
    <style>
        :root {{
            --primary: {PRIMARY_COLOR};
            --gold: #FFD700;
            --gold-dark: #D4AF37;
            --black: #121212;
            --black-light: #1E1E1E;
            --white: #FFFFFF;
            --gray: #B0B0B0;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--black);
            color: var(--white);
        }}
        .stButton>button {{
            background-color: var(--primary);
            color: white !important;
        }}
        h1, h2, h3 {{
            color: var(--primary) !important;
        }}
        /* Ensure tables are visible and styled */
        .stDataFrame {{
            color: var(--white) !important;
            background-color: var(--black-light) !important;
            border: 1px solid var(--gray) !important;
        }}
        .stDataFrame td, .stDataFrame th {{
            border: 1px solid var(--gray) !important;
            padding: 5px !important;
            font-weight: bold !important; /* Apply bold to all cells */
        }}
    </style>
    """, unsafe_allow_html=True)

# --- Industrialized Construction Parameters ---
CONSTRUCTION_TYPES = {
    'Traditional Cast-in-Place': {
        'slump_range': (75, 150),
        'strength_gain': 'Normal',
        'curing_method': 'Standard',
        'demould_time': '18-24 hours'
    },
    'Precast Elements': {
        'slump_range': (25, 75),
        'strength_gain': 'Rapid',
        'curing_method': 'Accelerated',
        'demould_time': '8-12 hours',
        'wcm_reduction': 0.05
    },
    'Modular Construction': {
        'slump_range': (50, 100),
        'strength_gain': 'High Early',
        'curing_method': 'Controlled',
        'demould_time': '6-10 hours',
        'wcm_reduction': 0.07
    },
    'Tilt-Up Panels': {
        'slump_range': (75, 125),
        'strength_gain': 'Moderate',
        'curing_method': 'Standard',
        'demould_time': '16-20 hours'
    }
}

PRODUCTION_METHODS = {
    'Batch Plant': {'quality_control': 'High', 'consistency': 'Excellent'},
    'Mobile Mixer': {'quality_control': 'Medium', 'consistency': 'Good'},
    'Ready-Mix': {'quality_control': 'High', 'consistency': 'Excellent'},
    'Site Batching': {'quality_control': 'Variable', 'consistency': 'Fair'}
}

# --- Enhanced Logo Display ---
def display_header():
    """Display a minimal, professional header with properly scaled logo"""
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if LOGO_PATH:
            try:
                if os.path.exists(LOGO_PATH):
                    logo_width = 120
                    try:
                        with Image.open(LOGO_PATH) as img:
                            img.verify()
                        st.image(
                            LOGO_PATH,
                            width=logo_width,
                            use_container_width=False,
                            caption=LOGO_ALT_TEXT if st.secrets.get("DEBUG_MODE", False) else ""
                        )
                    except (IOError, SyntaxError) as e:
                        st.error(f"Invalid image file: {str(e)}")
                        st.markdown(f"**{CLIENT_NAME}**")
                else:
                    st.warning(f"Logo file not found at: {LOGO_PATH}")
                    st.markdown(f"**{CLIENT_NAME}**")
            except Exception as e:
                st.error(f"Logo loading error: {str(e)}")
                st.markdown(f"**{CLIENT_NAME}**")
        else:
            st.warning("No logo path configured")
            st.markdown(f"**{CLIENT_NAME}**")
    
    with col2:
        st.markdown(
            f"""
            <h2 style='color:{PRIMARY_COLOR}; margin-top: 5px; font-size: 1.5rem; font-weight: 500;'>
                {APP_TITLE}
            </h2>
            <p style='color: var(--gray); font-size: 0.9rem; margin-top: -5px;'>
                Industrialized Construction Ready Mix Designs
            </p>
            """, 
            unsafe_allow_html=True
        )

display_header()

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

# --- Industrialized Construction Inputs ---
st.markdown("**Project Name**")
project_name = st.text_input("", "Unnamed Project", key="project_name_input")

# Get current parameters
if st.session_state['show_new_design'] and st.session_state['mix_designs']:
    current_params = st.session_state['mix_designs'][-1]['inputs']
else:
    current_params = st.session_state['default_params']

with st.expander("🏭 Industrialized Construction Parameters", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Construction Type**")
        construction_type = st.selectbox(
            "", 
            list(CONSTRUCTION_TYPES.keys()),
            index=list(CONSTRUCTION_TYPES.keys()).index(current_params['construction_type']),
            key="construction_type_input"
        )
        
        st.markdown("**Production Method**")
        production_method = st.selectbox(
            "", 
            list(PRODUCTION_METHODS.keys()),
            index=list(PRODUCTION_METHODS.keys()).index(current_params['production_method']),
            key="production_method_input"
        )
    
    with col2:
        st.markdown("**Early Strength Required**")
        early_strength_required = st.checkbox(
            "", 
            current_params['early_strength_required'],
            key="early_strength_input"
        )
        
        st.markdown("**Steam Curing**")
        steam_curing = st.checkbox(
            "", 
            current_params['steam_curing'],
            key="steam_curing_input"
        )
        
        st.markdown("**Target Demould Time (hours)**")
        target_demould_time = st.slider(
            "", 
            4, 48, current_params['target_demould_time'],
            key="demould_time_input"
        )

# Display industrialized construction recommendations
construction_info = CONSTRUCTION_TYPES[construction_type]
st.info(f"""
**{construction_type} Recommendations:**
- **Slump Range:** {construction_info['slump_range'][0]} - {construction_info['slump_range'][1]} mm
- **Strength Gain:** {construction_info['strength_gain']}
- **Curing Method:** {construction_info['curing_method']}
- **Typical Demould Time:** {construction_info['demould_time']}
""")

with st.expander("📋 ACI Design Inputs", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**f'c (MPa)**")
        fck = st.number_input("", 10.0, 80.0, current_params['fck'], key="fck_input")
        
        st.markdown("**Standard deviation (MPa)**")
        std_dev = st.number_input("", 3.0, 10.0, current_params['std_dev'], key="std_dev_input")
        
        st.markdown("**Exposure Class**")
        exposure = st.selectbox("", list(ACI_EXPOSURE), 
                              index=list(ACI_EXPOSURE).index(current_params['exposure']),
                              key="exposure_input")

    with col2:
        st.markdown("**Max Aggregate Size (mm)**")
        max_agg_size = st.selectbox("", [10, 20, 40], 
                                  index=[10, 20, 40].index(current_params['max_agg_size']),
                                  key="max_agg_size_input")
        
        # Adjust slump based on construction type
        recommended_slump = construction_info['slump_range']
        st.markdown("**Slump (mm)**")
        slump = st.slider(
            "", 
            25, 200, 
            min(max(current_params['slump'], recommended_slump[0]), recommended_slump[1]),
            help=f"Recommended range for {construction_type}: {recommended_slump[0]}-{recommended_slump[1]} mm",
            key="slump_input"
        )
        
        st.markdown("**Air Entrained**")
        air_entrained = st.checkbox("", current_params['air_entrained'], key="air_entrained_input")
        if air_entrained:
            st.markdown("**Target Air Content (%)**")
            air_content = st.slider("", 1.0, 8.0, current_params['air_content'], key="air_content_input")
        else:
            air_content = 0.0

    with col3:
        # Adjust w/c ratio for industrialized construction
        base_wcm = current_params['wcm']
        if 'wcm_reduction' in construction_info:
            base_wcm = max(0.3, base_wcm - construction_info['wcm_reduction'])
        
        st.markdown("**w/c Ratio**")
        wcm = st.number_input(
            "", 
            0.3, 0.7, 
            base_wcm,
            help="Reduced for industrialized construction requirements" if 'wcm_reduction' in construction_info else "",
            key="wcm_input"
        )
        
        st.markdown("**Admixture (%)**")
        admixture = st.number_input("", 0.0, 5.0, current_params['admixture'], key="admixture_input")
        
        st.markdown("**FA Fineness Modulus**")
        fm = st.slider("", 2.4, 3.0, current_params['fm'], step=0.1, key="fm_input")

with st.expander("🔬 Material Properties"):
    st.markdown("**Cement SG**")
    sg_cement = st.number_input("", 2.0, 3.5, current_params['sg_cement'], key="sg_cement_input")
    
    st.markdown("**Fine Aggregate SG**")
    sg_fa = st.number_input("", 2.4, 2.8, current_params['sg_fa'], key="sg_fa_input")
    
    st.markdown("**Coarse Aggregate SG**")
    sg_ca = st.number_input("", 2.4, 2.8, current_params['sg_ca'], key="sg_ca_input")
    
    st.markdown("**CA Unit Weight (kg/m³)**")
    unit_weight_ca = st.number_input("", 1400, 1800, current_params['unit_weight_ca'], key="unit_weight_ca_input")
    
    st.markdown("**FA Moisture (%)**")
    moist_fa = st.number_input("", 0.0, 10.0, current_params['moist_fa'], key="moist_fa_input")
    
    st.markdown("**CA Moisture (%)**")
    moist_ca = st.number_input("", 0.0, 10.0, current_params['moist_ca'], key="moist_ca_input")

# --- Enhanced Mix Design Logic for Industrialized Construction ---
def calculate_mix(
    fck, std_dev, exposure, max_agg_size, slump, air_entrained,
    air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
    unit_weight_ca, moist_fa, moist_ca, construction_type, production_method,
    early_strength_required, steam_curing, target_demould_time
):
    """Calculate concrete mix design with industrialized construction considerations"""
    try:
        # Calculate target mean strength
        ft = fck + 1.34 * std_dev
        
        # Industrialized construction adjustments
        construction_info = CONSTRUCTION_TYPES[construction_type]
        
        # Adjust for early strength requirements
        strength_adjustment = 1.0
        if early_strength_required:
            strength_adjustment = 1.15  # 15% strength increase for early demould
            ft *= strength_adjustment
        
        # Check w/c ratio against exposure limits
        max_wcm = ACI_EXPOSURE[exposure]['max_wcm']
        if 'wcm_reduction' in construction_info:
            max_wcm -= construction_info['wcm_reduction']
        
        if wcm > max_wcm:
            st.warning(f"w/c ratio exceeds maximum recommended for {construction_type} ({max_wcm})")
        
        # Determine water content
        water_table = ACI_WATER_CONTENT["Air-Entrained" if air_entrained else "Non-Air-Entrained"]
        water = water_table[max_agg_size]
        
        # Adjust water for slump
        water += (slump - 75) * 0.3
        
        # Adjust water for admixture
        if admixture:
            water *= 1 - min(0.15, admixture * 0.05)
        
        # Calculate cement content
        cement = max(water / wcm, ACI_EXPOSURE[exposure]['min_cement'])
        
        # Increase cement for early strength
        if early_strength_required:
            cement *= 1.1  # 10% additional cement for early strength
        
        # Determine coarse aggregate volume
        try:
            ca_vol = ACI_CA_VOLUME[round(fm, 1)][max_agg_size]
        except KeyError:
            ca_vol = ACI_CA_VOLUME[2.7][max_agg_size]
        
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
        
        # Industrialized construction recommendations
        industrialized_factors = {
            'recommended_admixtures': [],
            'curing_method': 'Standard',
            'demould_strength': 10.0  # MPa
        }
        
        if early_strength_required:
            industrialized_factors['recommended_admixtures'].extend(['Superplasticizer', 'Accelerator'])
            industrialized_factors['demould_strength'] = 15.0
        
        if steam_curing:
            industrialized_factors['curing_method'] = 'Steam Curing'
            industrialized_factors['demould_strength'] = 20.0
            industrialized_factors['recommended_admixtures'].append('Steam Curing Compatible')
        
        if construction_type in ['Precast Elements', 'Modular Construction']:
            industrialized_factors['recommended_admixtures'].extend(['Water Reducer', 'Viscosity Modifier'])
        
        return {
            "Target Mean Strength": round(ft, 2),
            "Water": round(water, 1),
            "Cement": round(cement, 1),
            "Fine Aggregate": round(fa_mass_adj, 1),
            "Coarse Aggregate": round(ca_mass_adj, 1),
            "Air Content": round(air_content, 1),
            "Admixture": round(admix_amount, 2),
            "Industrialized Factors": industrialized_factors,
            "Construction Type": construction_type,
            "Production Method": production_method,
            "Demould Strength": industrialized_factors['demould_strength']
        }
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return None

def generate_pie_chart(data):
    """Generate pie chart of material composition with improved styling"""
    try:
        material_components = {
            k: v for k, v in data.items() 
            if k in ["Water", "Cement", "Fine Aggregate", "Coarse Aggregate"] and v > 0
        }
        
        if not material_components:
            return None
            
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 12))  # Increased size for better visibility
        
        colors = ['#2196F3', '#FF9800', '#4CAF50', '#F44336']  # Blue, Orange, Green, Red
        wedges, texts, autotexts = ax.pie(
            material_components.values(),
            labels=material_components.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors[:len(material_components)],
            textprops={'fontsize': 12, 'color': 'white'},
            wedgeprops={'edgecolor': 'black', 'linewidth': 1}
        )
        
        ax.axis('equal')
        ax.set_title('Mix Composition', fontsize=16, pad=20, color='white', fontweight='bold')
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)
        
        for text in texts:
            text.set_color('white')
            text.set_fontsize(12)
        
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#1E1E1E')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none', transparent=False)
        buf.seek(0)
        plt.close(fig)
        st.write(f"Debug: Chart size set to {12}x{12} inches, DPI 200")  # Debug output
        return buf
        
    except Exception as e:
        st.error(f"Chart generation error: {str(e)}")
        return None

def generate_bar_chart(data):
    """Generate bar chart of material composition with improved styling"""
    try:
        material_components = {
            k: v for k, v in data.items() 
            if k in ["Water", "Cement", "Fine Aggregate", "Coarse Aggregate"] and v > 0
        }
        
        if not material_components:
            return None
            
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))  # Adjusted size for better visibility
        
        colors = ['#2196F3', '#FF9800', '#4CAF50', '#F44336']  # Blue, Orange, Green, Red
        bars = ax.bar(material_components.keys(), material_components.values(), color=colors[:len(material_components)])
        
        ax.set_title('Mix Composition', fontsize=16, pad=20, color='white', fontweight='bold')
        ax.set_ylabel('Quantity (kg/m³)', fontsize=12, color='white')
        ax.set_facecolor('#1E1E1E')
        fig.patch.set_facecolor('#121212')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=10, color='white', fontweight='bold')
        
        ax.tick_params(axis='x', colors='white', labelsize=12)
        ax.tick_params(axis='y', colors='white', labelsize=12)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none', transparent=False)
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        st.error(f"Bar chart generation error: {str(e)}")
        return None

def create_pdf_report_multiple(designs: list, project_name: str) -> bytes:
    """Generate a comprehensive PDF report with all mix designs including parameter tables"""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
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
                pdf.ln(80)  # Increased space between logo and title
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
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, safe_text(f"Design #{i}"), 0, 1, 'C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, safe_text(f"Target Strength: {design['data']['Target Mean Strength']} MPa"), 0, 1, 'C')
            pdf.cell(0, 8, safe_text(f"Construction Type: {design['data']['Construction Type']}"), 0, 1, 'C')
            pdf.cell(0, 8, safe_text(f"Calculated: {design['timestamp']}"), 0, 1, 'C')
            pdf.ln(10)

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
                if param not in ['Industrialized Factors', 'Construction Type', 'Production Method', 'Demould Strength']:
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

            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, safe_text("Industrialized Construction Recommendations"), 0, 1, 'C')
            
            industrialized_factors = design['data']['Industrialized Factors']
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 8, safe_text(f"Recommended Admixtures: {', '.join(industrialized_factors['recommended_admixtures']) or 'Standard mix'}"))
            pdf.multi_cell(0, 8, safe_text(f"Curing Method: {industrialized_factors['curing_method']}"))
            pdf.multi_cell(0, 8, safe_text(f"Target Demould Strength: {industrialized_factors['demould_strength']} MPa"))
            pdf.multi_cell(0, 8, safe_text(f"Production Method: {design['data']['Production Method']}"))
            pdf.ln(5)

            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, safe_text("Design Parameters"), 0, 1, 'C')
            
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
                [f"FA Fineness Modulus", f"{params['fm']}", ""],
                ["", "", ""],
                ["Industrialized Parameters", "", ""],
                [f"Construction Type", f"{params['construction_type']}", ""],
                [f"Production Method", f"{params['production_method']}", ""],
                [f"Early Strength", f"{'Yes' if params['early_strength_required'] else 'No'}", ""],
                [f"Steam Curing", f"{'Yes' if params['steam_curing'] else 'No'}", ""],
                [f"Target Demould Time", f"{params['target_demould_time']} hours", ""]
            ]

            param_col_widths = [70, 50, 30]
            pdf.set_font("Arial", '', 10)
            
            for row in parameter_data:
                pdf.set_x((pdf.w - sum(param_col_widths))/2)
                if row[0] in ["Material Properties", "Mix Parameters", "Industrialized Parameters"]:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(sum(param_col_widths), 8, safe_text(row[0]), 1, 1, 'C')
                    pdf.set_font("Arial", '', 10)
                else:
                    pdf.cell(param_col_widths[0], 8, safe_text(row[0]), 1)
                    pdf.cell(param_col_widths[1], 8, safe_text(row[1]), 1)
                    pdf.cell(param_col_widths[2], 8, safe_text(row[2]), 1)
                    pdf.ln(8)

            if design.get('chart'):
                try:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        img = Image.open(design['chart'])
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.save(tmp.name, format='PNG', quality=95)
                        y_position = pdf.get_y() + 5
                        if y_position > 200:
                            pdf.add_page()
                            y_position = 20
                        pdf.image(tmp.name, x=(pdf.w - 80)/2, y=y_position, w=80)
                        os.unlink(tmp.name)
                except Exception as e:
                    st.error(f"Chart rendering error: {str(e)}")

        return pdf.output(dest='S').encode('latin-1', errors='replace')
            
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None

# --- Main Application Logic ---
if not st.session_state['show_new_design']:
    if st.button("🧪 Compute Industrialized Mix Design", key="compute_mix_button"):
        result = calculate_mix(
            fck, std_dev, exposure, max_agg_size, slump, air_entrained,
            air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
            unit_weight_ca, moist_fa, moist_ca, construction_type, production_method,
            early_strength_required, steam_curing, target_demould_time
        )
        if result:
            chart_buf = generate_pie_chart(result)
            st.session_state['mix_designs'].append({
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
                    'moist_ca': moist_ca,
                    'construction_type': construction_type,
                    'production_method': production_method,
                    'early_strength_required': early_strength_required,
                    'steam_curing': steam_curing,
                    'target_demould_time': target_demould_time
                }
            })
            st.success("Industrialized mix design calculated and saved!")
            st.session_state['show_new_design'] = True
            st.rerun()
else:
    # Display current parameters with option to modify
    with st.expander("⚙️ Current Parameters (Click to Modify)", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**f'c (MPa)**")
            fck = st.number_input("", 10.0, 80.0, 
                                st.session_state['mix_designs'][-1]['inputs']['fck'],
                                key="mod_fck")
            
            st.markdown("**Standard deviation (MPa)**")
            std_dev = st.number_input("", 3.0, 10.0, 
                                    st.session_state['mix_designs'][-1]['inputs']['std_dev'],
                                    key="mod_std_dev")
            
            st.markdown("**Exposure Class**")
            exposure = st.selectbox("", list(ACI_EXPOSURE), 
                                  index=list(ACI_EXPOSURE).index(st.session_state['mix_designs'][-1]['inputs']['exposure']),
                                  key="mod_exposure")

        with col2:
            st.markdown("**Max Aggregate Size (mm)**")
            max_agg_size = st.selectbox("", [10, 20, 40], 
                                      index=[10, 20, 40].index(st.session_state['mix_designs'][-1]['inputs']['max_agg_size']),
                                      key="mod_max_agg_size")
            
            st.markdown("**Slump (mm)**")
            slump = st.slider("", 25, 200, 
                            st.session_state['mix_designs'][-1]['inputs']['slump'],
                            key="mod_slump")
            
            st.markdown("**Air Entrained**")
            air_entrained = st.checkbox("", 
                                      st.session_state['mix_designs'][-1]['inputs']['air_entrained'],
                                      key="mod_air_entrained")
            if air_entrained:
                st.markdown("**Target Air Content (%)**")
                air_content = st.slider("", 1.0, 8.0, 
                                      st.session_state['mix_designs'][-1]['inputs']['air_content'],
                                      key="mod_air_content")
            else:
                air_content = 0.0

        with col3:
            st.markdown("**w/c Ratio**")
            wcm = st.number_input("", 0.3, 0.7, 
                                st.session_state['mix_designs'][-1]['inputs']['wcm'],
                                key="mod_wcm")
            
            st.markdown("**Admixture (%)**")
            admixture = st.number_input("", 0.0, 5.0, 
                                      st.session_state['mix_designs'][-1]['inputs']['admixture'],
                                      key="mod_admixture")
            
            st.markdown("**FA Fineness Modulus**")
            fm = st.slider("", 2.4, 3.0, 
                          st.session_state['mix_designs'][-1]['inputs']['fm'], 
                          step=0.1,
                          key="mod_fm")

    # Material Properties (collapsed by default)
    with st.expander("🔬 Material Properties (Click to Modify)"):
        st.markdown("**Cement SG**")
        sg_cement = st.number_input("", 2.0, 3.5, 
                                  st.session_state['mix_designs'][-1]['inputs']['sg_cement'],
                                  key="mod_sg_cement")
        
        st.markdown("**Fine Aggregate SG**")
        sg_fa = st.number_input("", 2.4, 2.8, 
                              st.session_state['mix_designs'][-1]['inputs']['sg_fa'],
                              key="mod_sg_fa")
        
        st.markdown("**Coarse Aggregate SG**")
        sg_ca = st.number_input("", 2.4, 2.8, 
                              st.session_state['mix_designs'][-1]['inputs']['sg_ca'],
                              key="mod_sg_ca")
        
        st.markdown("**CA Unit Weight (kg/m³)**")
        unit_weight_ca = st.number_input("", 1400, 1800, 
                                       st.session_state['mix_designs'][-1]['inputs']['unit_weight_ca'],
                                       key="mod_unit_weight_ca")
        
        st.markdown("**FA Moisture (%)**")
        moist_fa = st.number_input("", 0.0, 10.0, 
                                 st.session_state['mix_designs'][-1]['inputs']['moist_fa'],
                                 key="mod_moist_fa")
        
        st.markdown("**CA Moisture (%)**")
        moist_ca = st.number_input("", 0.0, 10.0, 
                                 st.session_state['mix_designs'][-1]['inputs']['moist_ca'],
                                 key="mod_moist_ca")

    # Industrialized Construction Parameters (collapsed by default)
    with st.expander("🏭 Industrialized Construction Parameters (Click to Modify)"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Construction Type**")
            construction_type = st.selectbox(
                "", 
                list(CONSTRUCTION_TYPES.keys()),
                index=list(CONSTRUCTION_TYPES.keys()).index(st.session_state['mix_designs'][-1]['inputs']['construction_type']),
                key="mod_construction_type"
            )
            
            st.markdown("**Production Method**")
            production_method = st.selectbox(
                "", 
                list(PRODUCTION_METHODS.keys()),
                index=list(PRODUCTION_METHODS.keys()).index(st.session_state['mix_designs'][-1]['inputs']['production_method']),
                key="mod_production_method"
            )
        
        with col2:
            st.markdown("**Early Strength Required**")
            early_strength_required = st.checkbox(
                "", 
                st.session_state['mix_designs'][-1]['inputs']['early_strength_required'],
                key="mod_early_strength_required"
            )
            
            st.markdown("**Steam Curing**")
            steam_curing = st.checkbox(
                "", 
                st.session_state['mix_designs'][-1]['inputs']['steam_curing'],
                key="mod_steam_curing"
            )
            
            st.markdown("**Target Demould Time (hours)**")
            target_demould_time = st.slider(
                "", 
                4, 48, 
                st.session_state['mix_designs'][-1]['inputs']['target_demould_time'],
                key="mod_target_demould_time"
            )

    # Display current mix design results
    current_design = st.session_state['mix_designs'][-1]
    
    st.markdown("---")
    st.subheader("📊 Current Mix Design Results")
    
    # Display results in columns with adjusted layout
    col1, col2 = st.columns([1.5, 1])  # Give more space to the table column
    
    with col1:
        st.markdown("**Mix Proportions:**")
        results_data = {
            "Parameter": ["Target Mean Strength ft (MPa)", "Water (kg/m³)", "Cement (kg/m³)", 
                         "Fine Aggregate (kg/m³)", "Coarse Aggregate (kg/m³)", "Air Content (%)", 
                         "Admixture (kg/m³)"],
            "Value": [str(current_design['data']['Target Mean Strength']),
                     str(current_design['data']['Water']),
                     str(current_design['data']['Cement']),
                     str(current_design['data']['Fine Aggregate']),
                     str(current_design['data']['Coarse Aggregate']),
                     str(current_design['data']['Air Content']),
                     str(current_design['data']['Admixture'])]
        }
        if not all(results_data["Parameter"]) or not all(results_data["Value"]):
            st.error("Error: Table data is empty or invalid. Please check the mix design calculation.")
        else:
            # Convert to DataFrame and apply bold styling
            df = pd.DataFrame(results_data)
            styled_df = df.style.set_properties(**{'font-weight': 'bold', 'text-align': 'center'})
            st.dataframe(styled_df, use_container_width=True)

    with col2:
        # Chart type selection
        chart_type = st.radio("Chart Type", ["Pie", "Bar"], index=0, key="chart_type_radio")
        
        if chart_type == "Pie" and current_design['chart']:
            try:
                st.image(current_design['chart'], caption="Mix Composition", use_column_width=False, width=400)
            except Exception as e:
                st.error(f"Error displaying pie chart: {str(e)}")
        elif chart_type == "Bar":
            bar_chart_buf = generate_bar_chart(current_design['data'])
            if bar_chart_buf:
                try:
                    st.image(bar_chart_buf, caption="Mix Composition", use_column_width=False, width=400)
                except Exception as e:
                    st.error(f"Error displaying bar chart: {str(e)}")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Recalculate with Modified Parameters"):
            result = calculate_mix(
                fck, std_dev, exposure, max_agg_size, slump, air_entrained,
                air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
                unit_weight_ca, moist_fa, moist_ca, construction_type, production_method,
                early_strength_required, steam_curing, target_demould_time
            )
            if result:
                chart_buf = generate_pie_chart(result) if chart_type == "Pie" else generate_bar_chart(result)
                st.session_state['mix_designs'][-1] = {
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
                        'moist_ca': moist_ca,
                        'construction_type': construction_type,
                        'production_method': production_method,
                        'early_strength_required': early_strength_required,
                        'steam_curing': steam_curing,
                        'target_demould_time': target_demould_time
                    }
                }
                st.success("Mix design recalculated!")
                st.rerun()
    
    with col2:
        if st.button("➕ Create New Design"):
            st.session_state['show_new_design'] = False
            st.rerun()
    
    with col3:
        if st.button("📄 Generate PDF Report"):
            if st.session_state['mix_designs']:
                pdf_data = create_pdf_report_multiple(st.session_state['mix_designs'], project_name)
                if pdf_data:
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_data,
                        file_name=f"concrete_mix_designs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("No mix designs to generate report")

# --- Display saved designs ---
if len(st.session_state['mix_designs']) > 0:
    st.markdown("---")
    st.subheader("📋 Saved Mix Designs")
    
    for i, design in enumerate(st.session_state['mix_designs']):
        with st.expander(f"Design #{i+1} - {design['timestamp']} - {design['data']['Construction Type']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Target Strength:** {design['data']['Target Mean Strength']} MPa")
                st.markdown(f"**Construction Type:** {design['data']['Construction Type']}")
                st.markdown(f"**Water:** {design['data']['Water']} kg/m³")
                st.markdown(f"**Cement:** {design['data']['Cement']} kg/m³")
                st.markdown(f"**Fine Aggregate:** {design['data']['Fine Aggregate']} kg/m³")
                st.markdown(f"**Coarse Aggregate:** {design['data']['Coarse Aggregate']} kg/m³")
                st.markdown(f"**Air Content:** {design['data']['Air Content']}%")
                st.markdown(f"**Admixture:** {design['data']['Admixture']} kg/m³")
            
            with col2:
                if design['chart']:
                    try:
                        st.image(design['chart'], caption="Mix Composition", use_container_width=True)
                    except Exception as e:
                        st.error(f"Error displaying chart: {str(e)}")

# --- Footer ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: var(--gray); font-size: 0.8rem;'>
    {FOOTER_NOTE} | {CLIENT_NAME} | Generated on {datetime.now().strftime('%Y-%m-%d')}
</div>
""", unsafe_allow_html=True)
