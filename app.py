import streamlit as st
import pandas as pd
import sys
import os

# Add the src directory to the system path to allow importing modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from utils import get_df_transactions, categorize_transactions
from dkb_config import load_categories, save_categories

st.set_page_config(page_title="DKB Monitor Analysis", layout="wide")

st.title("DKB Monitor Analysis")

# Load categories at the beginning of the app run
categories = load_categories()

tab1, tab2 = st.tabs(["Analysis", "Manage Categories"])

with tab1:
    st.markdown("Upload a CSV file containing your DKB transactions to analyze them.")

    uploaded_file = st.file_uploader("Select a CSV file", type="csv")
    months_parameter = st.number_input("Number of Months (for average calculation)", min_value=1, value=1, step=1)

    if uploaded_file is not None:
        if st.button("Run Analysis"):
            try:
                # We can pass the uploaded_file directly to get_df_transactions
                df = get_df_transactions(uploaded_file)
                categorized_df = categorize_transactions(df, categories)
                
                st.success("Analysis complete!")
                
                st.subheader("Summary")
                
                # Group by category, sum amounts
                summary_df = categorized_df.groupby('category')['amount'].sum().round(2).reset_index()
                summary_df.columns = ['Category', 'Total Sum (€)']
                
                # Calculate monthly average based on the selected number of months
                summary_df['Monthly Average (€)'] = (summary_df['Total Sum (€)'] / months_parameter).round(2)
                
                # Sort by the Total Sum (ascending since expenses are negative)
                summary_df = summary_df.sort_values(by='Total Sum (€)', ascending=True)
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    
                with col2:
                    # Create a bar chart. Set category as index for the chart
                    chart_data = summary_df.set_index('Category')
                    st.bar_chart(chart_data)
                      
                st.subheader("Uncategorized Transactions")
                df_uncategorized = categorized_df[categorized_df['category'] == 'uncategorized']
                st.dataframe(df_uncategorized, use_container_width=True)
                st.markdown("---")
                st.subheader("Categorized Transactions")
                df_categorized = categorized_df[categorized_df['category'] != 'uncategorized']
                
                selected_category = st.selectbox("Filter by Category", ["All"] + sorted(df_categorized['category'].unique().tolist()))
                
                if selected_category == "All":
                    st.dataframe(df_categorized, use_container_width=True)
                else:
                    st.dataframe(df_categorized[df_categorized['category'] == selected_category], use_container_width=True)
                
                # Provide a download button for the uncategorized transactions
                csv_data = df_uncategorized.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Uncategorized CSV",
                    data=csv_data,
                    file_name="uncategorized.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"An error occurred while processing the file: {e}")

with tab2:
    st.header("Manage Categories")
    
    st.subheader("Current Categories")
    st.json(categories)
    
    st.markdown("---")
    
    col_add_kw, col_add_cat = st.columns(2)
    
    with col_add_kw:
        st.subheader("Add Keyword to Existing Category")
        with st.form("add_keyword_form", clear_on_submit=True):
            selected_cat = st.selectbox("Select Category", options=list(categories.keys()))
            new_keyword = st.text_input("New Keyword")
            submit_keyword = st.form_submit_button("Add Keyword")
            
            if submit_keyword:
                if new_keyword:
                    new_keyword_lower = new_keyword.strip().lower()
                    # Check case-insensitively if it exists
                    existing_lower = [k.lower() for k in categories[selected_cat]]
                    if new_keyword_lower not in existing_lower:
                        categories[selected_cat].append(new_keyword_lower)
                        save_categories(categories)
                        st.success(f"Added '{new_keyword_lower}' to '{selected_cat}'!")
                        st.rerun()
                    else:
                        st.warning("Keyword already exists in this category.")
                else:
                    st.warning("Please enter a valid keyword.")
                    
    with col_add_cat:
        st.subheader("Create New Category")
        with st.form("add_category_form", clear_on_submit=True):
            new_cat_name = st.text_input("New Category Name")
            initial_keyword = st.text_input("Initial Keyword (Optional)")
            submit_cat = st.form_submit_button("Create Category")
            
            if submit_cat:
                if new_cat_name:
                    if new_cat_name not in categories:
                        initial_kw_list = [initial_keyword.strip().lower()] if initial_keyword else []
                        categories[new_cat_name] = initial_kw_list
                        save_categories(categories)
                        st.success(f"Created category '{new_cat_name}'!")
                        st.rerun()
                    else:
                        st.warning("Category already exists.")
                else:
                    st.warning("Please enter a valid category name.")
