# --- [Previous imports and configurations remain unchanged] ---

# --- Main Application Logic ---
if not st.session_state.show_new_design:
    if st.button("🧪 Compute Industrialized Mix Design", key="compute_mix_button"):
        result = calculate_mix(
            fck, std_dev, exposure, max_agg_size, slump, air_entrained,
            air_content, wcm, admixture, fm, sg_cement, sg_fa, sg_ca,
            unit_weight_ca, moist_fa, moist_ca, construction_type, production_method,
            early_strength_required, steam_curing, target_demould_time
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
                    'moist_ca': moist_ca,
                    'construction_type': construction_type,
                    'production_method': production_method,
                    'early_strength_required': early_strength_required,
                    'steam_curing': steam_curing,
                    'target_demould_time': target_demould_time
                }
            })
            st.success("Industrialized mix design calculated and saved!")
            st.session_state.show_new_design = True
            st.rerun()
else:
    # Display current parameters with option to modify
    with st.expander("⚙️ Current Parameters (Click to Modify)", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**f'c (MPa)**")
            fck = st.number_input("", 10.0, 80.0, 
                                st.session_state.mix_designs[-1]['inputs']['fck'],
                                key="mod_fck")
            
            st.markdown("**Standard deviation (MPa)**")
            std_dev = st.number_input("", 3.0, 10.0, 
                                    st.session_state.mix_designs[-1]['inputs']['std_dev'],
                                    key="mod_std_dev")
            
            st.markdown("**Exposure Class**")
            exposure = st.selectbox("", list(ACI_EXPOSURE), 
                                  index=list(ACI_EXPOSURE).index(st.session_state.mix_designs[-1]['inputs']['exposure']),
                                  key="mod_exposure")

        with col2:
            st.markdown("**Max Aggregate Size (mm)**")
            max_agg_size = st.selectbox("", [10, 20, 40], 
                                      index=[10, 20, 40].index(st.session_state.mix_designs[-1]['inputs']['max_agg_size']),
                                      key="mod_max_agg_size")
            
            st.markdown("**Slump (mm)**")
            slump = st.slider("", 25, 200, 
                            st.session_state.mix_designs[-1]['inputs']['slump'],
                            key="mod_slump")
            
            st.markdown("**Air Entrained**")
            air_entrained = st.checkbox("", 
                                      st.session_state.mix_designs[-1]['inputs']['air_entrained'],
                                      key="mod_air_entrained")
            if air_entrained:
                st.markdown("**Target Air Content (%)**")
                air_content = st.slider("", 1.0, 8.0, 
                                      st.session_state.mix_designs[-1]['inputs']['air_content'],
                                      key="mod_air_content")
            else:
                air_content = 0.0

        with col3:
            st.markdown("**w/c Ratio**")
            wcm = st.number_input("", 0.3, 0.7, 
                                st.session_state.mix_designs[-1]['inputs']['wcm'],
                                key="mod_wcm")
            
            st.markdown("**Admixture (%)**")
            admixture = st.number_input("", 0.0, 5.0, 
                                      st.session_state.mix_designs[-1]['inputs']['admixture'],
                                      key="mod_admixture")
            
            st.markdown("**FA Fineness Modulus**")
            fm = st.slider("", 2.4, 3.0, 
                          st.session_state.mix_designs[-1]['inputs']['fm'], 
                          step=0.1,
                          key="mod_fm")

    # Material Properties (collapsed by default)
    with st.expander("🔬 Material Properties (Click to Modify)"):
        st.markdown("**Cement SG**")
        sg_cement = st.number_input("", 2.0, 3.5, 
                                  st.session_state.mix_designs[-1]['inputs']['sg_cement'],
                                  key="mod_sg_cement")
        
        st.markdown("**Fine Aggregate SG**")
        sg_fa = st.number_input("", 2.4, 2.8, 
                              st.session_state.mix_designs[-1]['inputs']['sg_fa'],
                              key="mod_sg_fa")
        
        st.markdown("**Coarse Aggregate SG**")
        sg_ca = st.number_input("", 2.4, 2.8, 
                              st.session_state.mix_designs[-1]['inputs']['sg_ca'],
                              key="mod_sg_ca")
        
        st.markdown("**CA Unit Weight (kg/m³)**")
        unit_weight_ca = st.number_input("", 1400, 1800, 
                                       st.session_state.mix_designs[-1]['inputs']['unit_weight_ca'],
                                       key="mod_unit_weight_ca")
        
        st.markdown("**FA Moisture (%)**")
        moist_fa = st.number_input("", 0.0, 10.0, 
                                 st.session_state.mix_designs[-1]['inputs']['moist_fa'],
                                 key="mod_moist_fa")
        
        st.markdown("**CA Moisture (%)**")
        moist_ca = st.number_input("", 0.0, 10.0, 
                                 st.session_state.mix_designs[-1]['inputs']['moist_ca'],
                                 key="mod_moist_ca")

    # Industrialized Construction Parameters (collapsed by default)
    with st.expander("🏭 Industrialized Construction Parameters (Click to Modify)"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Construction Type**")
            construction_type = st.selectbox(
                "", 
                list(CONSTRUCTION_TYPES.keys()),
                index=list(CONSTRUCTION_TYPES.keys()).index(st.session_state.mix_designs[-1]['inputs']['construction_type']),
                key="mod_construction_type"
            )
            
            st.markdown("**Production Method**")
            production_method = st.selectbox(
                "", 
                list(PRODUCTION_METHODS.keys()),
                index=list(PRODUCTION_METHODS.keys()).index(st.session_state.mix_designs[-1]['inputs']['production_method']),
                key="mod_production_method"
            )
        
        with col2:
            st.markdown("**Early Strength Required**")
            early_strength_required = st.checkbox(
                "", 
                st.session_state.mix_designs[-1]['inputs']['early_strength_required'],
                key="mod_early_strength_required"
            )
            
            st.markdown("**Steam Curing**")
            steam_curing = st.checkbox(
                "", 
                st.session_state.mix_designs[-1]['inputs']['steam_curing'],
                key="mod_steam_curing"
            )
            
            st.markdown("**Target Demould Time (hours)**")
            target_demould_time = st.slider(
                "", 
                4, 48, 
                st.session_state.mix_designs[-1]['inputs']['target_demould_time'],
                key="mod_target_demould_time"
            )

    # Display current mix design results
    current_design = st.session_state.mix_designs[-1]
    
    st.markdown("---")
    st.subheader("📊 Current Mix Design Results")
    
    # Display results in columns
    col1, col2 = st.columns([1, 1])
    
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
        st.table(results_data)

    with col2:
        # Chart type selection
        chart_type = st.radio("Chart Type", ["Pie", "Bar"], index=0, key="chart_type_radio")
        
        if chart_type == "Pie" and current_design['chart']:
            try:
                st.image(current_design['chart'], caption="Mix Composition", use_column_width=True)
            except Exception as e:
                st.error(f"Error displaying pie chart: {str(e)}")
        elif chart_type == "Bar":
            bar_chart_buf = generate_bar_chart(current_design['data'])
            if bar_chart_buf:
                try:
                    st.image(bar_chart_buf, caption="Mix Composition", use_column_width=True)
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
                st.session_state.mix_designs[-1] = {
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
            st.session_state.show_new_design = False
            st.rerun()
    
    with col3:
        if st.button("📄 Generate PDF Report"):
            if st.session_state.mix_designs:
                pdf_data = create_pdf_report_multiple(st.session_state.mix_designs, project_name)
                if pdf_data:
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_data,
                        file_name=f"concrete_mix_designs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("No mix designs to generate report")

# --- [Rest of the script remains unchanged] ---

# --- Chart Generation Functions ---
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
        fig, ax = plt.subplots(figsize=(10, 10))  # Increased size for better visibility
        
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
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none', transparent=False)  # Increased DPI
        buf.seek(0)
        plt.close(fig)
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
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none', transparent=False)  # Increased DPI
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        st.error(f"Bar chart generation error: {str(e)}")
        return None
