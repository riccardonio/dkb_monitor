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
    df_mini = df[cols_to_keep]
    # join columns "Zahlungsempfänger*in", "Verwendungszweck"
    df_mini["Zahlungsempfänger*in"] = df_mini["Zahlungsempfänger*in"].astype(str) + " " + df_mini["Verwendungszweck"].astype(str)
    df_mini = df_mini.drop(columns=["Verwendungszweck"])
    # rename the columns from german to english
    df_mini = df_mini.rename(columns={
    "Buchungsdatum": "date",
    "Zahlungsempfänger*in": "receiver",
    "Betrag (€)": "amount"
})
    df_mini["amount"] = df_mini["amount"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    return df_mini


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








