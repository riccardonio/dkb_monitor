
from dkb_config import FILENAME_TRANSACTIONS, categories
from utils import get_df_transactions, categorize_transactions

df = get_df_transactions(FILENAME_TRANSACTIONS)

categorized_df = categorize_transactions(df, categories)

food_transactions = categorized_df[categorized_df['category'] == 'food']
total_food_cost = round(food_transactions['amount'].sum() / 6, 2)
print(f"Monthly Total spent on food: {total_food_cost}")

# do the same for the category online_shopping
online_shopping_transactions = categorized_df[categorized_df['category'] == 'online_shopping']
total_food_cost = round(online_shopping_transactions['amount'].sum() / 6, 2)
print(f"Monthly Total spent on online_shopping: {total_food_cost}")


# print categorized_df where column category is unkknown
categorized_df[categorized_df['category'] == 'uncategorized'].to_csv("uncategorized.csv")

    