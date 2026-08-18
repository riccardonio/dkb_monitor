from dkb_robo import DKBRobo
import datetime
import pandas as pd

# import password and user and CC from dkb_config   
from dkb_config import DKB_USER, DKB_PASSWORD, CC


def get_start_end_time(delta_days=180):

    today = datetime.date.today().strftime('%Y-%m-%d')
    start = (datetime.date.today() - datetime.timedelta(days=delta_days)).strftime('%Y-%m-%d')

    return start, today


def get_transactions_list(cc=CC):

    with DKBRobo(dkb_user=DKB_USER, dkb_password=DKB_PASSWORD, mfa_device=2) as dkb:
        all_data = dkb.account_dic
        for k in all_data.keys():
                if all_data[k]["account"] == CC:
                        account_dictio = all_data[k]
                        start, today = get_start_end_time(delta_days=180)
                        transactions_list = dkb.get_transactions(account_dictio["transactions"], account_dictio["type"], start, today)
                        return transactions_list
        print(f"ERROR: Account {cc} not found!") 


def get_df_transactions(filepath):
      
    df = pd.read_csv(filepath, delimiter = ";", skiprows=4)
    cols_to_keep = ["Buchungsdatum", "Zahlungsempfänger*in", "Verwendungszweck", "Betrag (€)"]
    df_mini = df[cols_to_keep].copy()
    # join columns "Zahlungsempfänger*in", "Verwendungszweck" using .loc to prevent warnings
    df_mini.loc[:, "Zahlungsempfänger*in"] = df_mini["Zahlungsempfänger*in"].astype(str) + " " + df_mini["Verwendungszweck"].astype(str)
    df_mini = df_mini.drop(columns=["Verwendungszweck"])
    # rename the columns from german to english
    df_mini = df_mini.rename(columns={
    "Buchungsdatum": "date",
    "Zahlungsempfänger*in": "receiver",
    "Betrag (€)": "amount"
})
    df_mini["amount"] = df_mini["amount"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    
    # Filter out rows where the receiver contains Riccardo Parenti or Parenti Riccardo,
    # UNLESS the receiver also contains the keyword "gehalt"
    mask_name = df_mini['receiver'].str.contains('Riccardo Parenti|Parenti Riccardo|Parenti,Riccardo|Riccardo, Parenti', case=False, na=False)
    mask_keep = df_mini['receiver'].str.contains('Airbus|Kinderbetreeung|Darlehen', case=False, na=False)
    
    # Drop the row if it matches the name BUT does NOT contain 'gehalt'
    mask_to_drop = mask_name & ~mask_keep
    df_internal = df_mini[mask_to_drop].copy()
    df_mini = df_mini[~mask_to_drop]
    
    return df_mini, df_internal


def categorize_transactions(df, categories):
    """
    Categorizes transactions based on keywords in the 'receiver' column.

    Args:
        df: A pandas DataFrame with a 'receiver' column.
        categories: A dictionary where keys are category names and values are lists of keywords.

    Returns:
        A pandas DataFrame with an added 'category' column.  Returns None if input is invalid.

    """
    if not isinstance(df, pd.DataFrame) or 'receiver' not in df.columns:
        print("Error: Input must be a pandas DataFrame with a 'receiver' column.")
        return None
    if not isinstance(categories, dict):
        print("Error: Categories must be a dictionary.")
        return None

    df['category'] = 'uncategorized'  # Default category

    for category, keywords in categories.items():
        for keyword in keywords:
            df.loc[df['receiver'].str.contains(keyword, case=False), 'category'] = category

    return df


def generate_summary(categorized_df: pd.DataFrame, months: int) -> pd.DataFrame:
    """
    Groups categorized transactions by category, sums the amounts,
    calculates the monthly average, and sorts by total sum.
    """
    # Group by category, sum amounts
    summary_df = categorized_df.groupby('category')['amount'].sum().round(2).reset_index()
    summary_df.columns = ['Category', 'Total Sum (€)']
    
    # Calculate monthly average based on the selected number of months
    summary_df['Monthly Average (€)'] = (summary_df['Total Sum (€)'] / months).round(2)
    
    # Sort by the Total Sum (ascending since expenses are negative)
    summary_df = summary_df.sort_values(by='Total Sum (€)', ascending=True)
    return summary_df


def get_total_net(categorized_df: pd.DataFrame) -> float:
    """
    Calculates the total net transactions sum excluding ETFs.
    """
    return float(categorized_df[categorized_df['category'] != 'ETFs']['amount'].sum())


def add_keyword_to_category(categories: dict, selected_cat: str, new_keyword: str) -> tuple[bool, str]:
    """
    Validates and adds a new keyword to an existing category, saving the updated categories.
    Returns (success_bool, message).
    """
    from dkb_config import save_categories
    if not new_keyword:
        return False, "Please enter a valid keyword."
    
    new_keyword_lower = new_keyword.strip().lower()
    # Check case-insensitively if it exists
    existing_lower = [k.lower() for k in categories.get(selected_cat, [])]
    if new_keyword_lower not in existing_lower:
        categories[selected_cat].append(new_keyword_lower)
        save_categories(categories)
        return True, f"Added '{new_keyword_lower}' to '{selected_cat}'!"
    else:
        return False, "Keyword already exists in this category."


def create_category(categories: dict, new_cat_name: str, initial_keyword: str) -> tuple[bool, str]:
    """
    Validates and creates a new category with an optional initial keyword, saving categories.
    Returns (success_bool, message).
    """
    from dkb_config import save_categories
    if not new_cat_name:
        return False, "Please enter a valid category name."
    
    if new_cat_name not in categories:
        initial_kw_list = [initial_keyword.strip().lower()] if initial_keyword else []
        categories[new_cat_name] = initial_kw_list
        save_categories(categories)
        return True, f"Created category '{new_cat_name}'!"
    else:
        return False, "Category already exists."


def prepare_comparison_data(summary_df: pd.DataFrame, reference_dict: dict) -> pd.DataFrame:
    """
    Merges current analysis monthly averages with saved reference values
    and calculates differences per category.
    """
    if summary_df is None or summary_df.empty:
        current_map = {}
    else:
        current_map = dict(zip(summary_df['Category'], summary_df['Monthly Average (€)']))

    all_categories = sorted(list(set(current_map.keys()).union(set(reference_dict.keys()))))
    
    records = []
    for cat in all_categories:
        curr_val = round(float(current_map.get(cat, 0.0)), 2)
        ref_val = round(float(reference_dict.get(cat, 0.0)), 2)
        diff = round(curr_val - ref_val, 2)
        records.append({
            'Category': cat,
            'Current Monthly Avg (€)': curr_val,
            'Reference Monthly Avg (€)': ref_val,
            'Difference (€)': diff
        })
    
    comp_df = pd.DataFrame(records)
    if not comp_df.empty:
        comp_df = comp_df.sort_values(by='Current Monthly Avg (€)', ascending=True).reset_index(drop=True)
    return comp_df










