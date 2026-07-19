import os
import datetime
import pandas as pd
import streamlit as st
import altair as alt
from dkb_config import EQUITY_FILE

COLUMNS = ['Date', 'Cash', 'Tagesgeld/XEON', 'Festgeld', 'Stocks', 'ETF', 'Risk Free %', 'Total']

def load_equity_data() -> pd.DataFrame:
    """
    Loads equity data from the CSV file.
    Returns a DataFrame with the standard columns, sorted by Date descending.
    """
    if not os.path.exists(EQUITY_FILE) or os.path.getsize(EQUITY_FILE) == 0:
        return pd.DataFrame(columns=COLUMNS)
    try:
        df = pd.read_csv(EQUITY_FILE)
        # Ensure all standard columns exist
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = 0.0 if col != 'Date' else pd.Timestamp.now().strftime('%Y-%m-%d')
        
        # Parse and standardize Date format
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        # Ensure numeric types
        numeric_cols = [c for c in COLUMNS if c != 'Date']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0)
        
        # Sort and clean index
        df = df.sort_values(by='Date', ascending=False).reset_index(drop=True)
        return df[COLUMNS]
    except Exception as e:
        st.error(f"Error loading equity data: {e}")
        return pd.DataFrame(columns=COLUMNS)

def save_equity_data(df: pd.DataFrame) -> bool:
    """
    Saves equity DataFrame to the CSV file.
    """
    try:
        os.makedirs(os.path.dirname(EQUITY_FILE), exist_ok=True)
        df_save = df.copy()
        
        # Standardize date and sort descending to ensure chronological consistency
        df_save['Date'] = pd.to_datetime(df_save['Date']).dt.strftime('%Y-%m-%d')
        df_save = df_save.sort_values(by='Date', ascending=False).reset_index(drop=True)
        
        # Calculate Delta year dynamically
        delta_year = []
        for i in range(len(df_save)):
            if i + 12 < len(df_save):
                delta = df_save.iloc[i]['Total'] - df_save.iloc[i + 12]['Total']
                delta_year.append(delta)
            else:
                delta_year.append(None)
        df_save['Delta year'] = delta_year

        # Calculate Delta month dynamically
        delta_month = []
        for i in range(len(df_save)):
            if i + 1 < len(df_save):
                delta = df_save.iloc[i]['Total'] - df_save.iloc[i + 1]['Total']
                delta_month.append(delta)
            else:
                delta_month.append(None)
        df_save['Delta month'] = delta_month
        
        # Format columns: integers (nullable Int64) for assets, total, and deltas, 1 decimal for percentage
        int_cols = ['Cash', 'Tagesgeld/XEON', 'Festgeld', 'Stocks', 'ETF', 'Total', 'Delta month', 'Delta year']
        for col in int_cols:
            if col in df_save.columns:
                df_save[col] = pd.to_numeric(df_save[col], errors='coerce').round(0).astype('Int64')
        if 'Risk Free %' in df_save.columns:
            df_save['Risk Free %'] = df_save['Risk Free %'].round(1)
            
        df_save.to_csv(EQUITY_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving equity data: {e}")
        return False

def render_equity_tab():
    st.header("Equity Visualization & Management")
    
    # 1. Load Data
    df = load_equity_data()
    
    # Proactively upgrade the CSV schema to save MoM/YoY deltas if they are missing
    try:
        raw_df = pd.read_csv(EQUITY_FILE)
        if 'Delta month' not in raw_df.columns or 'Delta year' not in raw_df.columns:
            save_equity_data(df)
    except Exception:
        pass
    
    # Calculate Delta year and Delta month dynamically
    if not df.empty:
        # YoY Delta
        delta_year = []
        for i in range(len(df)):
            # df is sorted descending by Date, so 12 rows before (older) is at index i + 12
            if i + 12 < len(df):
                delta = df.iloc[i]['Total'] - df.iloc[i + 12]['Total']
                delta_year.append(delta)
            else:
                delta_year.append(None)
        df['Delta year'] = delta_year

        # MoM Delta
        delta_month = []
        for i in range(len(df)):
            # df is sorted descending by Date, so previous month (older) is at index i + 1
            if i + 1 < len(df):
                delta = df.iloc[i]['Total'] - df.iloc[i + 1]['Total']
                delta_month.append(delta)
            else:
                delta_month.append(None)
        df['Delta month'] = delta_month
    
    # Inject custom CSS to make delete buttons small and cleanly aligned
    st.markdown("""
        <style>
        /* Make the container look glassy and premium */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.01) !important;
            border: 1px solid rgba(255, 255, 255, 0.07) !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
            border-radius: 12px !important;
            padding: 8px 12px !important;
        }
        /* Make delete buttons small, borderless, and centered */
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child button {
            padding: 0px !important;
            height: 24px !important;
            min-height: 24px !important;
            width: 24px !important;
            line-height: 24px !important;
            border: none !important;
            background-color: transparent !important;
            margin: 0px !important;
            font-size: 14px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: #ff453a !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child button:hover {
            background-color: rgba(255, 69, 58, 0.15) !important;
            border-radius: 6px !important;
            color: #ff6961 !important;
        }
        /* Style each row container (the horizontal blocks that are not inside a form) */
        div[data-testid="stHorizontalBlock"]:not(form *) {
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            padding: 8px 8px !important;
            margin-bottom: 0px !important;
            background-color: transparent !important;
        }
        /* Hover effect on rows */
        div[data-testid="stHorizontalBlock"]:not(form *):hover {
            background-color: rgba(255, 255, 255, 0.02) !important;
        }
        /* Remove border from the last row */
        div[data-testid="stHorizontalBlock"]:not(form *):last-of-type {
            border-bottom: none !important;
        }
        /* Vertically align ledger row text/content, excluding the entry form */
        div[data-testid="stHorizontalBlock"]:not(form *) > div[data-testid="column"] {
            display: flex !important;
            align-items: center !important;
            min-height: 35px !important;
        }
        /* Ensure clean font styling */
        div[data-testid="stHorizontalBlock"]:not(form *) p {
            font-family: 'Inter', -apple-system, sans-serif !important;
            font-size: 0.9rem !important;
            margin: 0 !important;
            color: #e2e2e7 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 2. Main Dashboard Visualizations (only if data exists, displayed first)
    if not df.empty:
        # Columns for charts and statistics card
        col_chart1, col_chart2, col_chart3 = st.columns([4, 3, 3])
        
        with col_chart1:
            st.subheader("Historical Net Worth Trend")
            if len(df) >= 2:
                df_chrono = df.sort_values(by='Date', ascending=True).copy()
                df_chrono['Risk Free'] = df_chrono['Cash'] + df_chrono['Tagesgeld/XEON'] + df_chrono['Festgeld']
                df_chrono['Risk Assets'] = df_chrono['Stocks'] + df_chrono['ETF']
                
                df_melted = df_chrono.melt(
                    id_vars=['Date'], 
                    value_vars=['Total', 'Risk Free', 'Risk Assets'],
                    var_name='Asset Type', 
                    value_name='Value (€)'
                )
                
                base = alt.Chart(df_melted).encode(
                    x=alt.X('Date:T', title='Date'),
                    y=alt.Y('Value (€):Q', title='Value (€)'),
                    color=alt.Color(
                        'Asset Type:N',
                        scale=alt.Scale(
                            domain=['Total', 'Risk Free', 'Risk Assets'],
                            range=['#09AB3B', '#29B6F6', '#AB47BC'] # Green, Light Blue, Purple
                        ),
                        legend=alt.Legend(title="Portfolio Segment")
                    )
                )
                
                lines = base.mark_line(strokeWidth=3, interpolate='monotone')
                points = base.mark_point(size=50, filled=True, opacity=1.0).encode(
                    tooltip=[
                        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
                        'Asset Type',
                        alt.Tooltip('Value (€)', format=',.0f')
                    ]
                )
                
                trend_chart = (lines + points).properties(
                    height=300
                )
                st.altair_chart(trend_chart, use_container_width=True)
            else:
                st.info("Add at least 2 historical entries to view the Net Worth Trend graph.")
                
        with col_chart2:
            st.subheader("Current Asset Allocation")
            latest = df.iloc[0]
            categories_list = ["Cash", "Tagesgeld/XEON", "Festgeld", "Stocks", "ETF"]
            values_list = [
                float(latest["Cash"]),
                float(latest["Tagesgeld/XEON"]),
                float(latest["Festgeld"]),
                float(latest["Stocks"]),
                float(latest["ETF"])
            ]
            chart_df = pd.DataFrame({
                "Asset Category": categories_list,
                "Value (€)": values_list
            })
            chart_df = chart_df[chart_df["Value (€)"] > 0]
            
            if not chart_df.empty:
                # Precompute percentages and labels for the chart
                total_val = chart_df["Value (€)"].sum()
                chart_df["Percentage"] = chart_df["Value (€)"] / total_val
                # Only show labels for slices >= 3% to avoid clutter
                chart_df["Label"] = chart_df["Percentage"].map(lambda p: f"{p*100:.1f}%" if p >= 0.03 else "")
                
                base = alt.Chart(chart_df).encode(
                    theta=alt.Theta(field="Value (€)", type="quantitative"),
                    color=alt.Color(
                        field="Asset Category", 
                        type="nominal",
                        scale=alt.Scale(
                            domain=["Cash", "Tagesgeld/XEON", "Festgeld", "Stocks", "ETF"],
                            range=["#29B6F6", "#26A69A", "#FFCA28", "#EF5350", "#FFA726"]
                        ),
                        legend=alt.Legend(title="Assets")
                    ),
                    tooltip=["Asset Category", alt.Tooltip("Value (€)", format=',.2f')]
                )
                
                donut = base.mark_arc(innerRadius=60, outerRadius=100)
                
                text = base.mark_text(radius=80, size=11, fill="white", fontWeight="bold").encode(
                    text=alt.Text(field="Label", type="nominal")
                )
                
                chart_layered = (donut + text).properties(
                    height=300
                )
                
                st.altair_chart(chart_layered, use_container_width=True)
            else:
                st.info("No asset values are positive to display allocation.")
                
        with col_chart3:
            st.subheader("Portfolio Records")
            
            # Calculate milestones dynamically
            idx_max_total = df['Total'].idxmax()
            max_total = df.loc[idx_max_total, 'Total']
            max_total_date = df.loc[idx_max_total, 'Date']
            
            idx_max_stocks = df['Stocks'].idxmax()
            max_stocks = df.loc[idx_max_stocks, 'Stocks']
            max_stocks_date = df.loc[idx_max_stocks, 'Date']
            
            idx_max_etf = df['ETF'].idxmax()
            max_etf = df.loc[idx_max_etf, 'ETF']
            max_etf_date = df.loc[idx_max_etf, 'Date']
            
            idx_min_total = df['Total'].idxmin()
            min_total = df.loc[idx_min_total, 'Total']
            min_total_date = df.loc[idx_min_total, 'Date']
            
            idx_min_stocks = df['Stocks'].idxmin()
            min_stocks = df.loc[idx_min_stocks, 'Stocks']
            min_stocks_date = df.loc[idx_min_stocks, 'Date']
            
            idx_min_etf = df['ETF'].idxmin()
            min_etf = df.loc[idx_min_etf, 'ETF']
            min_etf_date = df.loc[idx_min_etf, 'Date']
            
            html_stats = f"""
            <div style="background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 12px; padding: 18px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2); font-family: 'Inter', sans-serif;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <!-- Left Column: Max Records -->
                    <div>
                        <h5 style="margin: 0 0 14px 0; color: #30d158; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">All-Time Highs</h5>
                        <div style="margin-bottom: 12px;">
                            <div style="font-size: 0.75rem; color: #8e8e93; text-transform: uppercase; letter-spacing: 0.5px;">Total Equity</div>
                            <div style="font-size: 1.15rem; font-weight: bold; color: #ffffff;">€{max_total:,.0f}</div>
                            <div style="font-size: 0.7rem; color: #8e8e93; margin-top: 2px;">{max_total_date}</div>
                        </div>
                        <div style="margin-bottom: 12px;">
                            <div style="font-size: 0.75rem; color: #8e8e93; text-transform: uppercase; letter-spacing: 0.5px;">Stocks</div>
                            <div style="font-size: 1.05rem; font-weight: bold; color: #ffffff;">€{max_stocks:,.0f}</div>
                            <div style="font-size: 0.7rem; color: #8e8e93; margin-top: 2px;">{max_stocks_date}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #8e8e93; text-transform: uppercase; letter-spacing: 0.5px;">ETFs</div>
                            <div style="font-size: 1.05rem; font-weight: bold; color: #ffffff;">€{max_etf:,.0f}</div>
                            <div style="font-size: 0.7rem; color: #8e8e93; margin-top: 2px;">{max_etf_date}</div>
                        </div>
                    </div>
                    
                    <!-- Right Column: Min Records -->
                    <div>
                        <h5 style="margin: 0 0 14px 0; color: #ff453a; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">All-Time Lows</h5>
                        <div style="margin-bottom: 12px;">
                            <div style="font-size: 0.75rem; color: #8e8e93; text-transform: uppercase; letter-spacing: 0.5px;">Total Equity</div>
                            <div style="font-size: 1.15rem; font-weight: bold; color: #ffffff;">€{min_total:,.0f}</div>
                            <div style="font-size: 0.7rem; color: #8e8e93; margin-top: 2px;">{min_total_date}</div>
                        </div>
                        <div style="margin-bottom: 12px;">
                            <div style="font-size: 0.75rem; color: #8e8e93; text-transform: uppercase; letter-spacing: 0.5px;">Stocks</div>
                            <div style="font-size: 1.05rem; font-weight: bold; color: #ffffff;">€{min_stocks:,.0f}</div>
                            <div style="font-size: 0.7rem; color: #8e8e93; margin-top: 2px;">{min_stocks_date}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #8e8e93; text-transform: uppercase; letter-spacing: 0.5px;">ETFs</div>
                            <div style="font-size: 1.05rem; font-weight: bold; color: #ffffff;">€{min_etf:,.0f}</div>
                            <div style="font-size: 0.7rem; color: #8e8e93; margin-top: 2px;">{min_etf_date}</div>
                        </div>
                    </div>
                </div>
            </div>
            """
            st.html(html_stats)
            
        st.markdown("---")
    else:
        st.info("No equity history found. Add your first entry using the form below!")

    # Define defaults based on the latest entry
    if not df.empty:
        latest = df.iloc[0]
        default_cash = float(latest['Cash'])
        default_tagesgeld = float(latest['Tagesgeld/XEON'])
        default_festgeld = float(latest['Festgeld'])
        default_stocks = float(latest['Stocks'])
        default_etf = float(latest['ETF'])
    else:
        default_cash = 0.0
        default_tagesgeld = 0.0
        default_festgeld = 0.0
        default_stocks = 0.0
        default_etf = 0.0

    # 3. Add Entry Form (All inputs in a single line, displayed second)
    st.subheader("Add / Update Equity Entry")
    with st.form("add_equity_form", clear_on_submit=False):
        col_date, col_cash, col_tg, col_fg, col_st, col_etf = st.columns(6)
        with col_date:
            entry_date = st.date_input("Date", value=datetime.date.today())
        with col_cash:
            cash = st.number_input("Cash (€)", min_value=0.0, value=default_cash, step=100.0, format="%.2f")
        with col_tg:
            tagesgeld = st.number_input("Tagesgeld/XEON (€)", min_value=0.0, value=default_tagesgeld, step=100.0, format="%.2f")
        with col_fg:
            festgeld = st.number_input("Festgeld (€)", min_value=0.0, value=default_festgeld, step=100.0, format="%.2f")
        with col_st:
            stocks = st.number_input("Stocks (€)", min_value=0.0, value=default_stocks, step=100.0, format="%.2f")
        with col_etf:
            etf = st.number_input("ETF (€)", min_value=0.0, value=default_etf, step=100.0, format="%.2f")
            
        submit_btn = st.form_submit_button("Add Row to Top", use_container_width=True)
        
        if submit_btn:
            date_str = entry_date.strftime('%Y-%m-%d')
            total = cash + tagesgeld + festgeld + stocks + etf
            risk_free = cash + tagesgeld + festgeld
            risk_free_pct = (risk_free / total * 100.0) if total > 0 else 0.0
            
            new_row = {
                'Date': date_str,
                'Cash': cash,
                'Tagesgeld/XEON': tagesgeld,
                'Festgeld': festgeld,
                'Stocks': stocks,
                'ETF': etf,
                'Risk Free %': risk_free_pct,
                'Total': total
            }
            
            # Check if entry already exists for this date and overwrite if so
            if not df.empty and date_str in df['Date'].values:
                df = df[df['Date'] != date_str]
                msg_action = "updated entry for"
            else:
                msg_action = "added entry for"
            
            new_df = pd.DataFrame([new_row])
            df = pd.concat([new_df, df], ignore_index=True)
            
            if save_equity_data(df):
                st.success(f"Successfully {msg_action} {date_str}!")
                st.rerun()
            else:
                st.error("Failed to save the entry.")

    # 4. Display Table (Ledger, displayed last)
    if not df.empty:
        st.markdown("---")
        st.subheader("Current Equity Ledger")
        
        with st.container(border=True):
            # Display headers in columns
            headers = ["Date", "Cash", "Tagesgeld/XEON", "Festgeld", "Stocks", "ETF", "Risk Free %", "Total", "Delta month", "Delta year", ""]
            col_widths = [1.2, 0.9, 1.1, 0.9, 0.9, 0.9, 1.0, 1.1, 1.1, 1.1, 0.4]
            
            header_cols = st.columns(col_widths)
            for col, header in zip(header_cols, headers):
                col.markdown(f"<span style='color: #8e8e93; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>{header}</span>", unsafe_allow_html=True)
                
            # Line separator
            st.markdown("<hr style='margin: 6px 0 10px 0; border-color: rgba(255, 255, 255, 0.1);'>", unsafe_allow_html=True)
            
            # Display rows
            for idx, row in df.iterrows():
                row_cols = st.columns(col_widths)
                row_cols[0].write(row['Date'])
                row_cols[1].write(f"€{row['Cash']:,.0f}")
                row_cols[2].write(f"€{row['Tagesgeld/XEON']:,.0f}")
                row_cols[3].write(f"€{row['Festgeld']:,.0f}")
                row_cols[4].write(f"€{row['Stocks']:,.0f}")
                row_cols[5].write(f"€{row['ETF']:,.0f}")
                
                # Risk Free % styling (green if > 70%, orange otherwise)
                pct = row['Risk Free %']
                pct_color = "#30d158" if pct > 70.0 else "#ff9f0a"
                row_cols[6].markdown(f"<span style='color: {pct_color}; font-weight: 500;'>{pct:.1f}%</span>", unsafe_allow_html=True)
                
                row_cols[7].markdown(f"**€{row['Total']:,.0f}**")
                
                # Delta month column (index 8)
                delta_m_val = row['Delta month']
                if pd.isna(delta_m_val) or delta_m_val is None:
                    row_cols[8].write("-")
                else:
                    color = "#ff453a" if delta_m_val < 0 else "#30d158"
                    sign = "+" if delta_m_val > 0 else ""
                    row_cols[8].markdown(f"<span style='color: {color}; font-weight: 500;'>{sign}€{delta_m_val:,.0f}</span>", unsafe_allow_html=True)
                
                # Delta year column (index 9)
                delta_y_val = row['Delta year']
                if pd.isna(delta_y_val) or delta_y_val is None:
                    row_cols[9].write("-")
                else:
                    color = "#ff453a" if delta_y_val < 0 else "#30d158"
                    sign = "+" if delta_y_val > 0 else ""
                    row_cols[9].markdown(f"<span style='color: {color}; font-weight: 500;'>{sign}€{delta_y_val:,.0f}</span>", unsafe_allow_html=True)
                
                # Render small delete button (index 10)
                if row_cols[10].button("❌", key=f"del_{row['Date']}", help=f"Delete entry for {row['Date']}"):
                    df = df[df['Date'] != row['Date']]
                    if save_equity_data(df):
                        st.success(f"Deleted entry for {row['Date']}!")
                        st.rerun()
                    else:
                        st.error("Failed to delete the entry.")
                
        st.markdown("---")
