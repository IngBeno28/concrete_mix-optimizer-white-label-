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
from branding import (
    CLIENT_NAME, APP_TITLE, PRIMARY_COLOR, LOGO_PATH, FOOTER_NOTE, LOGO_CONFIG, LOGO_ALT_TEXT,
    COMPANY_ADDRESS, COMPANY_PHONE, COMPANY_EMAIL, COMPANY_WEBSITE
)

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
        'auto_wcm': True,
        'admixture': 0.0,
        'fm': 2.7,
        'sg_cement': 3.15,
        'sg_fa': 2.65,
        'sg_ca': 2.65,
        'unit_weight_ca': 1600,
        'use_dual_ca': False,
        'ca_20mm_pct': 60,
        'blend_unit_weight': 1650,
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
        /* Responsive table adjustments */
        @media (max-width: 768px) {{
            .stDataFrame {{
                font-size: 0.8rem;
            }}
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

# Approximate ACI 211.1 relationship between required average compressive
# strength (f'cr, MPa) and water-cement ratio, non-air-entrained concrete.
# Used to derive a strength-governed w/c ratio that is then checked against
# the exposure-class (and industrialized-construction) maximum — whichever
# is stricter/lower governs.
ACI_WCM_VS_STRENGTH = {
    15: 0.62,
    20: 0.55,
    25: 0.48,
    30: 0.40,
    35: 0.33,
    40: 0.30
}

def wcm_from_strength(ft_value):
    """Interpolate w/c ratio from required strength using ACI 211.1 table."""
    pts = sorted(ACI_WCM_VS_STRENGTH.items())
    strengths = [p[0] for p in pts]
    if ft_value <= strengths[0]:
        return pts[0][1]
    if ft_value >= strengths[-1]:
        return pts[-1][1]
    for (s1, w1), (s2, w2) in zip(pts, pts[1:]):
        if s1 <= ft_value <= s2:
            frac = (ft_value - s1) / (s2 - s1)
            return w1 + frac * (w2 - w1)
    return pts[-1][1]

# --- Industrialized Construction Inputs ---
st.markdown("**Project Name**")
project_name = st.text_input("", "Unnamed Project", key="project_name_input")

st.markdown("**Client / Project Owner**")
client_name = st.text_input("", st.session_state.get('client_name', ''), key="client_name_input",
                             help="Who this report is prepared for — shown on the PDF cover page, separate from your firm's own branding.")
st.session_state['client_name'] = client_name

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
        
        st.markdown("**Auto-derive w/c from f'cr (ACI 211.1)**")
        auto_wcm = st.checkbox("", current_params.get('auto_wcm', True), key="auto_wcm_input")
        
        st.markdown("**w/c Ratio**")
        wcm = st.number_input(
            "", 
            0.3, 0.7, 
            base_wcm,
            help="Used only when auto-derive is off. Reduced for industrialized construction requirements" if 'wcm_reduction' in construction_info else "Used only when auto-derive is off.",
            disabled=auto_wcm,
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
    
    st.markdown("**Coarse Aggregate Blend**")
    use_dual_ca = st.checkbox(
        "Use two CA sizes (10mm + 20mm blend)",
        current_params.get('use_dual_ca', False),
        key="use_dual_ca_input"
    )

    if use_dual_ca:
        if max_agg_size != 20:
            st.warning("Dual-size blend assumes 20mm is the largest stone present — set **Max Aggregate Size** above to 20mm.")

        st.markdown("**20mm Fraction of Coarse Aggregate (%)**")
        ca_20mm_pct = st.slider(
            "", 0, 100, current_params.get('ca_20mm_pct', 60),
            help="Remainder is made up of 10mm stone. Solve this against your target grading envelope (e.g. ASTM C33) for the combined blend.",
            key="ca_20mm_pct_input"
        )

        st.markdown("**Blended CA Unit Weight (kg/m³)**")
        unit_weight_ca = st.number_input(
            "", 1400, 1900, current_params.get('blend_unit_weight', 1650),
            help="Measure the dry-rodded unit weight of the actual combined 10+20mm blend per ASTM C29 — a well-graded blend packs tighter (higher unit weight) than either single size alone.",
            key="blend_unit_weight_input"
        )
    else:
        ca_20mm_pct = 100
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
    early_strength_required, steam_curing, target_demould_time, auto_wcm=True,
    use_dual_ca=False, ca_20mm_pct=100
):
    """Calculate concrete mix design with industrialized construction considerations"""
    try:
        # Calculate target mean strength (ACI 318 Table 5.3.2.1: the GOVERNING
        # / larger result of two equations, which differ depending on whether
        # f'c is at or below 35 MPa, or above it).
        if fck <= 35:
            ft = max(fck + 1.34 * std_dev, fck + 2.33 * std_dev - 3.45)
        else:
            ft = max(fck + 1.34 * std_dev, 0.90 * fck + 2.33 * std_dev)
        
        # Industrialized construction adjustments
        construction_info = CONSTRUCTION_TYPES[construction_type]
        
        # Adjust for early strength requirements
        strength_adjustment = 1.0
        if early_strength_required:
            strength_adjustment = 1.15  # 15% strength increase for early demould
            ft *= strength_adjustment
        
        # Determine governing w/c ratio
        max_wcm = ACI_EXPOSURE[exposure]['max_wcm']
        if 'wcm_reduction' in construction_info:
            max_wcm -= construction_info['wcm_reduction']
        
        if auto_wcm:
            # Derive w/c from the (possibly early-strength-adjusted) target
            # strength, then apply the stricter of that and the exposure /
            # construction-type max w/c — whichever is lower governs.
            wcm = min(wcm_from_strength(ft), max_wcm)
        else:
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
        
        # Split combined coarse aggregate into 10mm / 20mm stock sizes.
        # ACI 211.1's table already gives the TOTAL blended CA volume for
        # the largest NMAS present (20mm) — the split below is a batching
        # breakdown only, using the same moisture correction as the total,
        # so the two fractions always sum back to ca_mass_adj.
        if use_dual_ca:
            ca_20mm_mass_adj = ca_mass_adj * (ca_20mm_pct / 100)
            ca_10mm_mass_adj = ca_mass_adj - ca_20mm_mass_adj
        
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
            "Governing w/c Ratio": round(wcm, 3),
            "Water": round(water, 1),
            "Cement": round(cement, 1),
            "Fine Aggregate": round(fa_mass_adj, 1),
            "Coarse Aggregate": round(ca_mass_adj, 1),
            **({
                "Coarse Aggregate 20mm": round(ca_20mm_mass_adj, 1),
                "Coarse Aggregate 10mm": round(ca_10mm_mass_adj, 1),
            } if use_dual_ca else {}),
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

def hex_to_rgb(hex_color):
    """Convert a '#RRGGBB' hex string to an (r, g, b) tuple, with a safe fallback."""
    try:
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (0, 82, 204)

class BrandedPDF(FPDF):
    """FPDF subclass that stamps company/branding details on every page footer."""
    def footer(self):
        contact_parts = []
        if COMPANY_PHONE:
            contact_parts.append(f"Tel: {COMPANY_PHONE}")
        if COMPANY_EMAIL:
            contact_parts.append(f"Email: {COMPANY_EMAIL}")
        if COMPANY_WEBSITE:
            contact_parts.append(f"Web: {COMPANY_WEBSITE}")
        if COMPANY_ADDRESS:
            contact_parts.append(COMPANY_ADDRESS)
        contact_line = " | ".join(contact_parts)

        self.set_y(-24 if contact_line else -18)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.set_font("Arial", '', 8)
        self.set_text_color(120, 120, 120)
        footer_left = f"{CLIENT_NAME} | {FOOTER_NOTE}" if FOOTER_NOTE else CLIENT_NAME
        self.cell(0, 6, footer_left.encode('latin-1', errors='replace').decode('latin-1'), 0, 0, 'L')
        self.cell(0, 6, f"Page {self.page_no()}/{{nb}}", 0, 1, 'R')
        if contact_line:
            self.set_x(10)
            self.cell(0, 6, contact_line.encode('latin-1', errors='replace').decode('latin-1'), 0, 1, 'L')
        self.set_text_color(0, 0, 0)

def create_pdf_report_multiple(designs: list, project_name: str, client_name: str = "",
                                engineer_name: str = "", stamp_image_path: str = None) -> bytes:
    """Generate a comprehensive PDF report with all mix designs including parameter tables"""
    try:
        pdf = BrandedPDF()
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=22)
        
        def safe_text(text):
            if not isinstance(text, str):
                text = str(text)
            return text.encode('latin-1', errors='replace').decode('latin-1')

        def draw_table_row(col_widths, values, aligns=None, line_height=5, min_row_height=8, bold=False):
            """Draw one table row whose cells word-wrap to fit any amount of text,
            instead of overflowing a fixed single-line cell."""
            if aligns is None:
                aligns = ['L'] * len(values)
            pdf.set_font("Arial", 'B' if bold else '', 10)
            x_start = (pdf.w - sum(col_widths)) / 2

            def wrap(text, width):
                text = safe_text(text)
                usable = width - 2
                words = text.split(' ')
                lines, current = [], ""
                for word in words:
                    trial = (current + " " + word).strip()
                    if not current or pdf.get_string_width(trial) <= usable:
                        current = trial
                    else:
                        lines.append(current)
                        current = word
                if current:
                    lines.append(current)
                return lines or [""]

            wrapped = [wrap(v, w) for v, w in zip(values, col_widths)]
            n_lines = max(len(w) for w in wrapped)
            row_height = max(min_row_height, n_lines * line_height)

            if pdf.get_y() + row_height > pdf.h - pdf.b_margin:
                pdf.add_page()

            y_start = pdf.get_y()
            x = x_start
            for width, lines, align in zip(col_widths, wrapped, aligns):
                pdf.rect(x, y_start, width, row_height)
                pdf.set_xy(x, y_start + (row_height - len(lines) * line_height) / 2)
                for line in lines:
                    pdf.set_x(x)
                    pdf.cell(width, line_height, line, 0, 2, align)
                x += width
            pdf.set_y(y_start + row_height)

        # --- Cover Page ---
        pdf.add_page()
        accent_rgb = hex_to_rgb(PRIMARY_COLOR)

        # Top accent band (letterhead style)
        pdf.set_fill_color(*accent_rgb)
        pdf.rect(0, 0, pdf.w, 10, 'F')

        # Logo
        logo_bottom = 28
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                with Image.open(LOGO_PATH) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    temp_logo_path = os.path.join(tempfile.gettempdir(),
                                                f"temp_logo_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    img.save(temp_logo_path, format='JPEG', quality=95)
                    pdf.image(temp_logo_path, x=(pdf.w - 40) / 2, y=22, w=40)
                    os.unlink(temp_logo_path)
                logo_bottom = 22 + 40 + 8
            except Exception as e:
                st.error(f"Logo processing error: {str(e)}")

        pdf.set_y(logo_bottom)

        # Title block
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(*accent_rgb)
        pdf.cell(0, 14, safe_text("Concrete Mix Design Report"), 0, 1, 'C')
        pdf.set_text_color(90, 90, 90)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, safe_text(APP_TITLE), 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)

        pdf.ln(4)
        pdf.set_draw_color(*accent_rgb)
        pdf.set_line_width(0.6)
        pdf.line(50, pdf.get_y(), pdf.w - 50, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.set_draw_color(0, 0, 0)
        pdf.ln(12)

        # Document info panel
        info_rows = [("Project", project_name)]
        if client_name:
            info_rows.append(("Prepared For", client_name))
        info_rows.append(("Prepared By", CLIENT_NAME))
        info_rows.append(("Date Generated", datetime.now().strftime('%Y-%m-%d %H:%M')))
        info_rows.append(("Total Mix Designs", str(len(designs))))

        panel_w = 150
        label_w = 55
        row_h = 9
        x0 = (pdf.w - panel_w) / 2
        y0 = pdf.get_y()
        panel_h = row_h * len(info_rows)

        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x0, y0, panel_w, panel_h)
        for idx, (label, value) in enumerate(info_rows):
            y = y0 + idx * row_h
            if idx > 0:
                pdf.line(x0, y, x0 + panel_w, y)
            pdf.set_xy(x0 + 4, y)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(label_w - 4, row_h, safe_text(label), 0, 0, 'L')
            pdf.set_font("Arial", '', 11)
            pdf.cell(panel_w - label_w - 4, row_h, safe_text(value), 0, 0, 'L')
        pdf.set_draw_color(0, 0, 0)
        pdf.set_y(y0 + panel_h + 14)

        if FOOTER_NOTE:
            pdf.set_font("Arial", 'I', 10)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 8, safe_text(FOOTER_NOTE), 0, 1, 'C')
            pdf.set_text_color(0, 0, 0)

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
            
            col_widths = [80, 50, 30]
            draw_table_row(col_widths, ["Parameter", "Value", "Unit"], aligns=['L', 'C', 'C'], bold=True)
            
            for param, value in design['data'].items():
                if param not in ['Industrialized Factors', 'Construction Type', 'Production Method', 'Demould Strength']:
                    unit = {
                        "Target Mean Strength": "MPa",
                        "Water": "kg/m³",
                        "Cement": "kg/m³",
                        "Fine Aggregate": "kg/m³",
                        "Coarse Aggregate": "kg/m³",
                        "Coarse Aggregate 20mm": "kg/m³",
                        "Coarse Aggregate 10mm": "kg/m³",
                        "Air Content": "%",
                        "Admixture": "kg/m³"
                    }.get(param, "-")
                    draw_table_row(col_widths, [param, f"{value:.2f}", unit], aligns=['L', 'C', 'C'])

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
            
            # Design Parameters Table with proper headers
            param_col_widths = [80, 50, 30]
            draw_table_row(param_col_widths, ["Parameter", "Value", "Unit"], aligns=['L', 'C', 'C'], bold=True)
            
            # Material Properties
            is_dual_ca = params.get('use_dual_ca', False)
            material_properties = [
                ("Cement SG", f"{params['sg_cement']}", ""),
                ("Fine Aggregate SG", f"{params['sg_fa']}", ""),
                ("Coarse Aggregate SG", f"{params['sg_ca']}", ""),
                ("CA Unit Weight" + (" (10+20mm blend)" if is_dual_ca else ""),
                 f"{params.get('blend_unit_weight', params['unit_weight_ca']) if is_dual_ca else params['unit_weight_ca']}",
                 "kg/m³"),
            ]
            if is_dual_ca:
                material_properties.append(
                    ("CA Blend Split", f"{params.get('ca_20mm_pct', 100)}% 20mm / {100 - params.get('ca_20mm_pct', 100)}% 10mm", "")
                )
            material_properties.extend([
                ("FA Moisture", f"{params['moist_fa']}", "%"),
                ("CA Moisture", f"{params['moist_ca']}", "%")
            ])
            
            for param, value, unit in material_properties:
                draw_table_row(param_col_widths, [param, value, unit], aligns=['L', 'C', 'C'])
            
            # Mix Parameters
            mix_parameters = [
                ("f'c", f"{params['fck']}", "MPa"),
                ("Standard Deviation", f"{params['std_dev']}", "MPa"),
                ("Exposure Class", f"{params['exposure']}", ""),
                ("Max Aggregate Size", f"{params['max_agg_size']}", "mm"),
                ("Slump", f"{params['slump']}", "mm"),
                ("Air Entrained", f"{'Yes' if params['air_entrained'] else 'No'}", ""),
                ("Target Air Content", f"{params['air_content']}" if params['air_entrained'] else "N/A", "%"),
                ("w/c Ratio", f"{params['wcm']}" if not params.get('auto_wcm', True) else "Auto-derived (see result table)", ""),
                ("Admixture", f"{params['admixture']}", "%"),
                ("FA Fineness Modulus", f"{params['fm']}", "")
            ]
            
            for param, value, unit in mix_parameters:
                draw_table_row(param_col_widths, [param, value, unit], aligns=['L', 'C', 'C'])
            
            # Industrialized Parameters
            industrialized_parameters = [
                ("Construction Type", f"{params['construction_type']}", ""),
                ("Production Method", f"{params['production_method']}", ""),
                ("Early Strength Required", f"{'Yes' if params['early_strength_required'] else 'No'}", ""),
                ("Steam Curing", f"{'Yes' if params['steam_curing'] else 'No'}", ""),
                ("Target Demould Time", f"{params['target_demould_time']}", "hours")
            ]
            
            for param, value, unit in industrialized_parameters:
                draw_table_row(param_col_widths, [param, value, unit], aligns=['L', 'C', 'C'])

        # --- Certification / Sign-off Page ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, safe_text("Certification"), 0, 1, 'C')
        pdf.ln(4)

        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 7, safe_text(
            "This concrete mix design report has been reviewed and is certified as suitable "
            "for the stated project and construction requirements."
        ))
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(60, 8, safe_text("Engineer Name:"), 0, 0)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, safe_text(engineer_name), 'B', 1)
        pdf.ln(6)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(60, 8, safe_text("Date:"), 0, 0)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, safe_text(datetime.now().strftime('%Y-%m-%d')), 'B', 1)
        pdf.ln(15)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, safe_text("Signature / Stamp"), 0, 1)
        box_y = pdf.get_y()
        box_w, box_h = 70, 35
        if stamp_image_path and os.path.exists(stamp_image_path):
            try:
                pdf.image(stamp_image_path, x=15, y=box_y, w=box_w, h=box_h)
            except Exception:
                pdf.rect(15, box_y, box_w, box_h)
        else:
            pdf.rect(15, box_y, box_w, box_h)
        pdf.set_y(box_y + box_h + 8)

        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(120, 120, 120)
        prepared_by = f"Report prepared using {APP_TITLE} by {CLIENT_NAME}."
        if FOOTER_NOTE:
            prepared_by += f" {FOOTER_NOTE}"
        pdf.multi_cell(0, 5, safe_text(prepared_by))
        pdf.set_text_color(0, 0, 0)

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
            early_strength_required, steam_curing, target_demould_time, auto_wcm,
            use_dual_ca, ca_20mm_pct
        )
        if result:
            st.session_state['mix_designs'].append({
                'data': result,
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
                    'auto_wcm': auto_wcm,
                    'admixture': admixture,
                    'fm': fm,
                    'sg_cement': sg_cement,
                    'sg_fa': sg_fa,
                    'sg_ca': sg_ca,
                    'unit_weight_ca': unit_weight_ca,
                    'use_dual_ca': use_dual_ca,
                    'ca_20mm_pct': ca_20mm_pct,
                    'blend_unit_weight': unit_weight_ca if use_dual_ca else current_params.get('blend_unit_weight', 1650),
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
            st.markdown("**Auto-derive w/c from f'cr (ACI 211.1)**")
            auto_wcm = st.checkbox(
                "",
                st.session_state['mix_designs'][-1]['inputs'].get('auto_wcm', True),
                key="mod_auto_wcm"
            )
            
            st.markdown("**w/c Ratio**")
            wcm = st.number_input("", 0.3, 0.7, 
                                st.session_state['mix_designs'][-1]['inputs']['wcm'],
                                help="Used only when auto-derive is off.",
                                disabled=auto_wcm,
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
        
        st.markdown("**Coarse Aggregate Blend**")
        use_dual_ca = st.checkbox(
            "Use two CA sizes (10mm + 20mm blend)",
            st.session_state['mix_designs'][-1]['inputs'].get('use_dual_ca', False),
            key="mod_use_dual_ca"
        )

        if use_dual_ca:
            if max_agg_size != 20:
                st.warning("Dual-size blend assumes 20mm is the largest stone present — set **Max Aggregate Size** above to 20mm.")

            st.markdown("**20mm Fraction of Coarse Aggregate (%)**")
            ca_20mm_pct = st.slider(
                "", 0, 100,
                st.session_state['mix_designs'][-1]['inputs'].get('ca_20mm_pct', 60),
                help="Remainder is made up of 10mm stone. Solve this against your target grading envelope (e.g. ASTM C33) for the combined blend.",
                key="mod_ca_20mm_pct"
            )

            st.markdown("**Blended CA Unit Weight (kg/m³)**")
            unit_weight_ca = st.number_input(
                "", 1400, 1900,
                st.session_state['mix_designs'][-1]['inputs'].get('blend_unit_weight', 1650),
                help="Measure the dry-rodded unit weight of the actual combined 10+20mm blend per ASTM C29 — a well-graded blend packs tighter (higher unit weight) than either single size alone.",
                key="mod_blend_unit_weight"
            )
        else:
            ca_20mm_pct = 100
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
    
    # Single column layout since pie chart is removed
    st.markdown("**Mix Proportions:**")
    params_list = ["Target Mean Strength ft (MPa)", "Governing w/c Ratio", "Water (kg/m³)", "Cement (kg/m³)", 
                   "Fine Aggregate (kg/m³)", "Coarse Aggregate (kg/m³)"]
    values_list = [str(current_design['data']['Target Mean Strength']),
                   str(current_design['data']['Governing w/c Ratio']),
                   str(current_design['data']['Water']),
                   str(current_design['data']['Cement']),
                   str(current_design['data']['Fine Aggregate']),
                   str(current_design['data']['Coarse Aggregate'])]

    if 'Coarse Aggregate 20mm' in current_design['data']:
        params_list += ["   ↳ 20mm Fraction (kg/m³)", "   ↳ 10mm Fraction (kg/m³)"]
        values_list += [str(current_design['data']['Coarse Aggregate 20mm']),
                        str(current_design['data']['Coarse Aggregate 10mm'])]

    params_list += ["Air Content (%)", "Admixture (kg/m³)"]
    values_list += [str(current_design['data']['Air Content']), str(current_design['data']['Admixture'])]

    results_data = {"Parameter": params_list, "Value": values_list}
    
    if not all(results_data["Parameter"]) or not all(results_data["Value"]):
        st.error("Error: Table data is empty or invalid. Please check the mix design calculation.")
    else:
        # Convert to DataFrame with responsive settings
        df = pd.DataFrame(results_data)
        styled_df = df.style.set_properties(**{'font-weight': 'bold', 'text-align': 'center'})
        st.dataframe(
            styled_df, 
            use_container_width=True,
            height=min(len(results_data["Parameter"]) * 45 + 50, 400)  # Dynamic height
        )

    # --- Certification Details for PDF Report ---
    with st.expander("🖋️ Certification Details (for PDF Report)"):
        st.markdown("**Engineer Name**")
        engineer_name = st.text_input("", st.session_state.get('engineer_name', ''), key="engineer_name_input")
        st.session_state['engineer_name'] = engineer_name

        st.markdown("**Signature / Stamp Image (optional)**")
        stamp_file = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="stamp_upload")
        if stamp_file is not None:
            st.session_state['stamp_bytes'] = stamp_file.getvalue()
        if st.session_state.get('stamp_bytes'):
            st.image(st.session_state['stamp_bytes'], width=150, caption="Stamp preview")
        st.caption("Leave blank to print an empty signature box in the report for a physical wet stamp instead.")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Recalculate with Modified Parameters"):
            result = calculate_mix(
                fck, std_dev, exposure, max_agg_size, slump, air_entrained,
                air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
                unit_weight_ca, moist_fa, moist_ca, construction_type, production_method,
                early_strength_required, steam_curing, target_demould_time, auto_wcm,
                use_dual_ca, ca_20mm_pct
            )
            if result:
                st.session_state['mix_designs'][-1] = {
                    'data': result,
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
                        'auto_wcm': auto_wcm,
                        'admixture': admixture,
                        'fm': fm,
                        'sg_cement': sg_cement,
                        'sg_fa': sg_fa,
                        'sg_ca': sg_ca,
                        'unit_weight_ca': unit_weight_ca,
                        'use_dual_ca': use_dual_ca,
                        'ca_20mm_pct': ca_20mm_pct,
                        'blend_unit_weight': unit_weight_ca if use_dual_ca else st.session_state['mix_designs'][-1]['inputs'].get('blend_unit_weight', 1650),
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
                stamp_path = None
                if st.session_state.get('stamp_bytes'):
                    stamp_path = os.path.join(
                        tempfile.gettempdir(),
                        f"temp_stamp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
                    )
                    with open(stamp_path, 'wb') as f:
                        f.write(st.session_state['stamp_bytes'])
                pdf_data = create_pdf_report_multiple(
                    st.session_state['mix_designs'], project_name,
                    client_name=st.session_state.get('client_name', ''),
                    engineer_name=st.session_state.get('engineer_name', ''),
                    stamp_image_path=stamp_path
                )
                if stamp_path and os.path.exists(stamp_path):
                    os.unlink(stamp_path)
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
            st.markdown(f"**Target Strength:** {design['data']['Target Mean Strength']} MPa")
            st.markdown(f"**Governing w/c Ratio:** {design['data']['Governing w/c Ratio']}")
            st.markdown(f"**Construction Type:** {design['data']['Construction Type']}")
            st.markdown(f"**Water:** {design['data']['Water']} kg/m³")
            st.markdown(f"**Cement:** {design['data']['Cement']} kg/m³")
            st.markdown(f"**Fine Aggregate:** {design['data']['Fine Aggregate']} kg/m³")
            st.markdown(f"**Coarse Aggregate:** {design['data']['Coarse Aggregate']} kg/m³")
            if 'Coarse Aggregate 20mm' in design['data']:
                st.markdown(f"　↳ 20mm: {design['data']['Coarse Aggregate 20mm']} kg/m³ · 10mm: {design['data']['Coarse Aggregate 10mm']} kg/m³")
            st.markdown(f"**Air Content:** {design['data']['Air Content']}%")
            st.markdown(f"**Admixture:** {design['data']['Admixture']} kg/m³")

# --- Footer ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: var(--gray); font-size: 0.8rem;'>
    {FOOTER_NOTE} | {CLIENT_NAME} | Generated on {datetime.now().strftime('%Y-%m-%d')}
</div>
""", unsafe_allow_html=True)
