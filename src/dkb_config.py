from pathlib import Path
import os
import json


FILE_NAME = "transactions_maerz_2026.csv"

MAIN_DIR = str(Path(__file__).resolve().parents[1])
DATA_DIR = os.path.join(MAIN_DIR, "data")
FILENAME_TRANSACTIONS = os.path.join(DATA_DIR, FILE_NAME)
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")

def load_categories():
    if not os.path.exists(CATEGORIES_FILE):
        return {}
    with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_categories(categories_dict):
    with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(categories_dict, f, indent=2, ensure_ascii=False)