# 🧱 ACI-Compliant Concrete Mix Design Optimizer (White-Label Edition)

This Streamlit web application calculates and visualizes concrete mix proportions based on the **ACI 211.1 method**. Built for civil and materials engineers, it supports branding customization, client deployment, and clean PDF/CSV exports — perfect for consultants, labs, and infrastructure teams.

---

## 🎯 Features
- ACI 211.1-compliant mix design calculator
- Adjustable for:
  - Exposure conditions (Mild, Moderate, Severe)
  - Air-entrained or non-air-entrained mixes
  - Moisture correction and admixture dosing
- Pie and bar chart visualizations of mix composition
- Download results as CSV
- **White-label ready** with custom branding support

---

## 🚀 White-Label Configuration

This app pulls custom branding from `branding.py`:

```python
CLIENT_NAME = "Your Company"
APP_TITLE = "Your Branded Mix Designer"
PRIMARY_COLOR = "#123456"
LOGO_PATH = "assets/logo.png"
FOOTER_NOTE = "© 2025 Your Company"
