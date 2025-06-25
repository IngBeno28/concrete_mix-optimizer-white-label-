# 🧱 ACI-Compliant Concrete Mix Design Optimizer (White-Label Edition)

This Streamlit web app calculates and visualizes concrete mix proportions based on the ACI 211.1 method. Ideal for civil and materials engineers, it supports branding customization and white-label deployment.

## 🎯 Features
- ACI 211.1-compliant design
- Air-entrained and non-air-entrained support
- Exposure classes and moisture correction
- Charts + CSV export
- White-label branding via `branding.py`

## 🚀 White-Label Setup

Edit `branding.py` to customize:

```python
CLIENT_NAME = "Your Company"
APP_TITLE = "Your Mix Designer"
PRIMARY_COLOR = "#123456"
LOGO_PATH = "assets/logo.png"
FOOTER_NOTE = "© 2025 Your Company"
```

## 🖥️ Installation

```bash
pip install -r requirements.txt
streamlit run aci_mix_designer.py
```

## 📜 License

This repository is under **CC BY-NC-ND 4.0**.  
No commercial use, resale, or modification allowed without permission.

© 2025 Automation_hub. Contact for white-label licensing.
