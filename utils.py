import pandas as pd
import re
import json
import os
from io import BytesIO
from rapidfuzz import fuzz
import streamlit as st

SELECTION_FILE = "selected_handles.json"

def save_selected_handles():
    with open(SELECTION_FILE, "w") as f:
        json.dump(list(st.session_state.selected_handles), f)

def read_csv_with_fallback(file_path, fallback_path=None):
    try:
        return pd.read_csv(file_path, encoding="ISO-8859-1")
    except FileNotFoundError:
        if fallback_path:
            return pd.read_csv(fallback_path, encoding="ISO-8859-1")
        else:
            return pd.DataFrame()


def extract_sku_number(sku):
    match = re.search(r'\d+', str(sku))
    return match.group() if match else ''

def preprocess_sku(df):
    if df is None or df.empty:
        st.warning("⚠️ Input DataFrame is empty or missing.")
        return pd.DataFrame()

    df = df.copy()
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces

    # Find SKU column
    sku_col = next((col for col in ['Variant SKU', 'SKU'] if col in df.columns), None)

    if sku_col is None:
        st.warning("⚠️ SKU column not found. Expected 'Variant SKU' or 'SKU'.")
        return pd.DataFrame()

    df['SKU'] = df[sku_col].apply(extract_sku_number)

    # Drop the old SKU column if needed
    if sku_col != 'SKU':
        df.drop(columns=[sku_col], inplace=True)

    # Keep rows with a valid, non-empty extracted SKU
    return df[df['SKU'].notna() & (df['SKU'] != '')]



def fuzzy_match_inventory(product_df, inventory_df):
    product_df = preprocess_sku(product_df)
    inventory_df = preprocess_sku(inventory_df)

    qty_cols = [c for c in inventory_df.columns if 'Available' in c or 'On hand' in c]
    if qty_cols:
        inventory_df['total_available'] = inventory_df[qty_cols].fillna(0).sum(axis=1)
        inventory_df = inventory_df[inventory_df['total_available'] > 0]

    merged_rows = []
    for _, prod_row in product_df.iterrows():
        sku = prod_row['sku_num']
        match = inventory_df[inventory_df['sku_num'] == sku]
        if not match.empty:
            best_match = match.iloc[0]
            merged_row = pd.concat([prod_row, best_match.drop(labels=product_df.columns.intersection(inventory_df.columns))])
        else:
            merged_row = prod_row
        merged_rows.append(merged_row)

    return pd.DataFrame(merged_rows)
