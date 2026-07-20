CLIENT_NAME = "Automation_hub Engineering Group Limited"
APP_TITLE = "Enhanced ACI 211.1 Concrete Mix Designer"
PRIMARY_COLOR = "#0052cc"
LOGO_PATH = "assets/2.png"  # Path to your logo file
LOGO_ALT_TEXT = f"{CLIENT_NAME} - {APP_TITLE}"
FOOTER_NOTE = "© 2025 ACI Mix Designer | Built for engineering precision"

# --- Company Contact Details ---
# Shown in the PDF report footer, cover page, and certification page.
# Leave any value as "" to omit that line from the report.
COMPANY_ADDRESS = "Plot 63/G Asuofua"       # e.g. "12 Independence Ave, Accra, Ghana"
COMPANY_PHONE = "+233501365879"         # e.g. "+233 20 000 0000"
COMPANY_EMAIL = "Wiafe1713@gmail.com"         # e.g. "info@automationhub.com"
COMPANY_WEBSITE = "Firstsky.com"       # e.g. "www.automationhub.com"
COMPANY_LICENSE_NO = ""    # e.g. company/firm registration or license number

# Responsive logo configuration
LOGO_CONFIG = {
    'default_width': 250,       # Base width in pixels
    'default_height': 80,       # Base height in pixels
    'mobile_width': 180,        # Width for mobile devices
    'max_width': 300,           # Maximum allowed width
    'min_width': 120,           # Minimum allowed width
    'breakpoint': 768,          # Screen width threshold (px) for mobile
    'formats': ['png', 'svg'],  # Preferred file formats (SVG recommended)
    'alt_text': LOGO_ALT_TEXT,
    'padding': '10px 0'         # CSS padding around logo
    
}
