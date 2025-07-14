streamlit_function = """
def show_pro_landing():
    st.markdown(\"\"\"
    <h1 style='text-align:center;'>ACI Concrete Mix Optimizer</h1>
    <p style='text-align:center;'>Stop Guessing Your Concrete Mix. Start Optimizing It.</p>

    <div style='max-width:960px;margin:auto;padding:2rem;'>

    <div style='background:#fff;padding:2rem;margin:2rem 0;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
      <h2>Design accurate, standards-based concrete mix proportions in minutes — no spreadsheets, no confusion, no wasted materials.</h2>
    </div>

    <div style='background:#fff;padding:2rem;margin:2rem 0;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
      <h3>🔍 Built by engineers. Powered by ACI.</h3>
      <ul>
        <li>📐 ACI 211-based mix design</li>
        <li>⚖️ Cement, water, aggregates, admixtures — fully calculated</li>
        <li>🧪 Custom slump, durability, strength class</li>
        <li>📁 PDF & Excel exports with branding</li>
        <li>🎯 100% online and instant</li>
      </ul>
    </div>

    <div style='background:#fff;padding:2rem;margin:2rem 0;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
      <h3>Use Cases</h3>
      <ul>
        <li>✔️ Field Engineers & QC Labs</li>
        <li>✔️ Construction Site Trials</li>
        <li>✔️ Grad Students / Research Labs</li>
      </ul>
    </div>

    <div style='background:#fff;padding:2rem;margin:2rem 0;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
      <h3>Pricing</h3>
      <div style='display:flex;gap:2rem;flex-wrap:wrap;'>
        <div style='background:#e0e0e0;border-radius:6px;padding:1rem;flex:1;min-width:200px;'>
          <h4>Free</h4>
          <p>1 design/session<br>PDF with watermark</p>
          <strong>GH₵0</strong>
        </div>
        <div style='background:#e0e0e0;border-radius:6px;padding:1rem;flex:1;min-width:200px;'>
          <h4>Pro</h4>
          <p>Unlimited designs<br>PDF & Excel<br>Custom branding</p>
          <strong>GH₵49/month</strong><br>
          <a href='https://flutterwave.com/pay/concretepro' target='_blank'>🔓 Upgrade to Pro</a><br>
          <a href='https://enhancedconcretemixdesign.streamlit.app/?access_key=your_super_secret_key' target='_blank'>🚀 Go to Pro Version</a>
        </div>
        <div style='background:#e0e0e0;border-radius:6px;padding:1rem;flex:1;min-width:200px;'>
          <h4>Institution</h4>
          <p>LMS-ready version<br>Multi-user access<br>Training documents</p>
          <strong>Contact Us</strong><br>
          <a href='mailto:support@acemixtools.com?subject=Institution%20Plan%20Request'>📩 Request Quote</a>
        </div>
      </div>
    </div>

    <a href='https://acemix.streamlit.app' target='_blank'>👉 Start Designing for Free</a><br>
    <a href='/sample-report.pdf' target='_blank'>📄 View Sample PDF Report</a>

    <div style='background:#fff;padding:2rem;margin:2rem 0;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
      <h3>What You’ll Save</h3>
      <ul>
        <li>⏱️ Hours of Excel formula headaches</li>
        <li>💸 Unnecessary cement & aggregate waste</li>
        <li>🤦‍♂️ Errors in hand-calculated mixes</li>
        <li>😤 Time lost to manual recalculations</li>
      </ul>
    </div>

    </div>
    <footer style='text-align:center;padding:1rem;font-size:0.9rem;color:#777;'>
      🧱 GHA Mix Optimizer | Built by a Civil Engineer, for Civil Engineers | 
      <a href='https://flutterwave.com/pay/concretepro' style='color: #007acc'>🔐 Unlock Pro Access</a>
    </footer>
    \"\"\", unsafe_allow_html=True)
"""

if __name__ == "__main__":
    show_pro_landing()
