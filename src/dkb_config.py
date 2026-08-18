from pathlib import Path
import os
import json

DKB_USER = "dummy"
DKB_PASSWORD = "dummy"
tan_insert = True
debug = True
CC = "dummy"

FILE_NAME = "transactions_maerz_2026.csv"

MAIN_DIR = str(Path(__file__).resolve().parents[1])
DATA_DIR = os.path.join(MAIN_DIR, "data")
FILENAME_TRANSACTIONS = os.path.join(DATA_DIR, FILE_NAME)
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")
EQUITY_FILE = os.path.join(DATA_DIR, "equity.csv")
REFERENCE_VALUES_FILE = os.path.join(DATA_DIR, "reference_values.json")

def load_categories():
    if not os.path.exists(CATEGORIES_FILE):
        return {}
    with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_categories(categories_dict):
    with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(categories_dict, f, indent=2, ensure_ascii=False)

def load_reference_values():
    if not os.path.exists(REFERENCE_VALUES_FILE):
        return {}
    try:
        with open(REFERENCE_VALUES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_reference_values(ref_dict):
    os.makedirs(os.path.dirname(REFERENCE_VALUES_FILE), exist_ok=True)
    with open(REFERENCE_VALUES_FILE, 'w', encoding='utf-8') as f:
        json.dump(ref_dict, f, indent=2, ensure_ascii=False)