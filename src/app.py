import streamlit as st

# The app is now in the src directory, so local modules can be imported directly.
from utils import (
    get_df_transactions,
    categorize_transactions,
    generate_summary,
    get_total_net,
    add_keyword_to_category,
    create_category,
    prepare_comparison_data,
)
from dkb_config import load_categories, load_reference_values, save_reference_values
from equity import render_equity_tab
import altair as alt

# Force reload to pick up equity.py changes
st.set_page_config(page_title="Personal Finance Assistant", layout="wide")

st.title("Personal Finance Assistant")

# Load categories at the beginning of the app run
categories = load_categories()

tab1, tab2, tab3 = st.tabs(["Expenses Analysis", "Manage Categories", "Assets"])

with tab1:
    st.markdown("Upload a CSV file containing your DKB transactions to analyze them.")

    # Restrict top controls to half of the screen width (50%)
    left_ctrl, _ = st.columns([1, 1])
    
    with left_ctrl:
        # Row 1: File Uploader, Number of Months, Save as Reference, Confirmation Message
        c1, c2, c3, c4 = st.columns([2.5, 1.2, 1.5, 2.0], vertical_alignment="bottom")
        with c1:
            uploaded_file = st.file_uploader("Select a CSV file", type="csv")
        with c2:
            months_parameter = st.number_input("Number of Months", min_value=1, value=1, step=1)
        with c3:
            has_analysis = 'analysis_data' in st.session_state
            save_ref = st.button("💾 Save as Reference", width="stretch", disabled=not has_analysis)
        with c4:
            msg_container = st.empty()
            
        # Row 2: Run Analysis button directly under the file upload field
        r2_c1, _ = st.columns([2.5, 4.7])
        with r2_c1:
            run_analysis = st.button("Run Analysis", width="stretch")

    if uploaded_file is not None and run_analysis:
        try:
            df, df_internal = get_df_transactions(uploaded_file)
            categorized_df = categorize_transactions(df, categories)
            summary_df = generate_summary(categorized_df, months_parameter)
            total_net = get_total_net(categorized_df)
            
            st.session_state['analysis_data'] = {
                'categorized_df': categorized_df,
                'summary_df': summary_df,
                'total_net': total_net,
                'df_internal': df_internal,
                'months_parameter': months_parameter,
                'filename': uploaded_file.name
            }
            msg_container.success("Analysis complete!")
        except Exception as e:
            msg_container.error(f"Error: {e}")

    if save_ref and 'analysis_data' in st.session_state:
        summary_df = st.session_state['analysis_data']['summary_df']
        ref_dict = dict(zip(summary_df['Category'], summary_df['Monthly Average (€)']))
        save_reference_values(ref_dict)
        msg_container.success("Reference values saved successfully!")

    if 'analysis_data' in st.session_state:
        analysis_data = st.session_state['analysis_data']
        categorized_df = analysis_data['categorized_df']
        summary_df = analysis_data['summary_df']
        total_net = analysis_data['total_net']
        df_internal = analysis_data['df_internal']
        
        # Load reference values automatically at each run
        reference_dict = load_reference_values()

        # Total Net (w/o ETFs) Banner constrained to 25% screen width
        net_col, _ = st.columns([1, 3])
        with net_col:
            net_color = "#ff4b4b" if total_net < 0 else "#09ab3b"
            st.markdown(
                f"""
                <div style="background-color: #262730; padding: 10px 16px; border-radius: 8px; border: 1px solid #333; text-align: center; margin: 10px 0 15px 0;">
                    <span style="font-size: 0.85rem; color: #8e8e93; font-weight: 500; display: block; margin-bottom: 2px;">Total Net (w/o ETFs) for Period</span>
                    <span style="font-size: 1.8rem; font-weight: bold; color: {net_color};">€{total_net:,.2f}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        col1, col2 = st.columns([0.8, 3.2])
        
        with col1:
            st.subheader("Summary")
            df_height = len(summary_df) * 35 + 38
            st.dataframe(
                summary_df,
                height=df_height,
                hide_index=True,
                column_config={
                    "Category": st.column_config.TextColumn("Category", width="small"),
                    "Total Sum (€)": st.column_config.NumberColumn("Total (€)", format="€%.2f", width="small"),
                    "Monthly Average (€)": st.column_config.NumberColumn("Monthly Avg (€)", format="€%.2f", width="small"),
                }
            )
        
        with col2:
            st.subheader("Monthly Average vs Reference Baseline")
            if not reference_dict:
                st.info("No reference values saved yet. Click **'💾 Save as Reference'** above to save the current analysis as your reference baseline.")
            else:
                comp_df = prepare_comparison_data(summary_df, reference_dict)
                # Exclude categories 'salary', 'gehalt', 'stipendio', 'etf', and 'etfs'
                comp_df_filtered = comp_df[~comp_df['Category'].str.lower().isin(['salary', 'gehalt', 'stipendio', 'etf', 'etfs'])].copy()
                
                # Make cost values positive for intuitive chart display
                comp_df_filtered['Current Monthly Avg (€)'] = comp_df_filtered['Current Monthly Avg (€)'].abs()
                comp_df_filtered['Reference Monthly Avg (€)'] = comp_df_filtered['Reference Monthly Avg (€)'].abs()
                comp_df_filtered['Difference (€)'] = (comp_df_filtered['Current Monthly Avg (€)'] - comp_df_filtered['Reference Monthly Avg (€)']).round(2)
                
                # Determine color: RED if current spending (positive) > reference average (positive), GREEN otherwise
                comp_df_filtered['BarColor'] = comp_df_filtered.apply(
                    lambda r: '#ff4b4b' if r['Current Monthly Avg (€)'] > r['Reference Monthly Avg (€)'] else '#09ab3b',
                    axis=1
                )

                dynamic_height = max(340, len(summary_df) * 35 + 38)
                chart_subcol, tbl_subcol = st.columns([2.5, 1.3])

                with chart_subcol:
                    st.markdown(
                        "<div style='font-size: 0.85rem; margin-bottom: 8px; color: #b0b0b0;'>"
                        "<span style='color:#ff4b4b; font-weight:bold;'>■</span> Higher cost than reference &nbsp;&nbsp;"
                        "<span style='color:#09ab3b; font-weight:bold;'>■</span> Lower/equal cost &nbsp;&nbsp;"
                        "<span style='color:#00E5FF; font-weight:bold;'>╍╍</span> Dotted Line = Reference Baseline"
                        "</div>",
                        unsafe_allow_html=True
                    )

                    bars = alt.Chart(comp_df_filtered).mark_bar().encode(
                        x=alt.X('Category:N', title='Category', sort=None),
                        y=alt.Y('Current Monthly Avg (€):Q', title='Monthly Average Cost (€)'),
                        color=alt.Color('BarColor:N', scale=None),
                        tooltip=[
                            alt.Tooltip('Category:N'),
                            alt.Tooltip('Current Monthly Avg (€):Q', title='Current Monthly Avg (€)', format=',.2f'),
                            alt.Tooltip('Reference Monthly Avg (€):Q', title='Reference Baseline (€)', format=',.2f'),
                            alt.Tooltip('Difference (€):Q', title='Difference (€)', format=',.2f')
                        ]
                    )
                    
                    ticks = alt.Chart(comp_df_filtered).mark_tick(
                        color='#00E5FF',
                        strokeDash=[4, 4],
                        size=35,
                        thickness=3.5
                    ).encode(
                        x=alt.X('Category:N', sort=None),
                        y=alt.Y('Reference Monthly Avg (€):Q'),
                        tooltip=[
                            alt.Tooltip('Category:N'),
                            alt.Tooltip('Reference Monthly Avg (€):Q', title='Reference Baseline (€)', format=',.2f')
                        ]
                    )

                    comp_chart = (bars + ticks).properties(
                        height=dynamic_height
                    )
                    st.altair_chart(comp_chart, width="stretch")
                
                with tbl_subcol:
                    st.dataframe(
                        comp_df_filtered.drop(columns=['BarColor'], errors='ignore'),
                        height=dynamic_height,
                        hide_index=True,
                        column_config={
                            "Category": st.column_config.TextColumn("Category", width="small"),
                            "Current Monthly Avg (€)": st.column_config.NumberColumn("Current (€)", format="€%.2f", width="small"),
                            "Reference Monthly Avg (€)": st.column_config.NumberColumn("Ref (€)", format="€%.2f", width="small"),
                            "Difference (€)": st.column_config.NumberColumn("Diff (€)", format="€%.2f", width="small"),
                        }
                    )
              
        df_uncategorized = categorized_df[categorized_df['category'] == 'uncategorized']
        df_categorized = categorized_df[categorized_df['category'] != 'uncategorized']
        
        tx_tab1, tx_tab2, tx_tab3 = st.tabs(["Uncategorized", "Categorized", "Internal"])
        
        with tx_tab1:
            st.subheader("Uncategorized Transactions")
            st.dataframe(df_uncategorized, width="stretch")
            
            # Provide a download button for the uncategorized transactions
            csv_data = df_uncategorized.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Uncategorized CSV",
                data=csv_data,
                file_name="uncategorized.csv",
                mime="text/csv"
            )
        
        with tx_tab2:
            st.subheader("Categorized Transactions")
            selected_category = st.selectbox("Filter by Category", ["All"] + sorted(df_categorized['category'].unique().tolist()))
            
            if selected_category == "All":
                st.dataframe(df_categorized, width="stretch")
            else:
                st.dataframe(df_categorized[df_categorized['category'] == selected_category], width="stretch")
        
        with tx_tab3:
            st.subheader("Internal Transactions")
            st.dataframe(df_internal, width="stretch")

with tab2:
    st.header("Manage Categories")
    
    col_add_kw, col_add_cat = st.columns(2)
    
    with col_add_kw:
        st.subheader("Add Keyword to Existing Category")
        with st.form("add_keyword_form", clear_on_submit=True):
            selected_cat = st.selectbox("Select Category", options=list(categories.keys()))
            new_keyword = st.text_input("New Keyword")
            submit_keyword = st.form_submit_button("Add Keyword")
            
            if submit_keyword:
                success, msg = add_keyword_to_category(categories, selected_cat, new_keyword)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)
                    
    with col_add_cat:
        st.subheader("Create New Category")
        with st.form("add_category_form", clear_on_submit=True):
            new_cat_name = st.text_input("New Category Name")
            initial_keyword = st.text_input("Initial Keyword (Optional)")
            submit_cat = st.form_submit_button("Create Category")
            
            if submit_cat:
                success, msg = create_category(categories, new_cat_name, initial_keyword)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)

    st.markdown("---")
    
    st.subheader("Current Categories")
    st.json(categories)

with tab3:
    render_equity_tab()
