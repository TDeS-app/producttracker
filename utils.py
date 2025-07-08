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

def read_csv_with_fallback(uploaded_file):
    content = uploaded_file.read()
    for enc in ['utf-8-sig', 'ISO-8859-1', 'windows-1252']:
        try:
            return pd.read_csv(BytesIO(content), encoding=enc)
        except Exception:
            continue
    st.warning(f"⚠️ Could not read {uploaded_file.name} with common encodings.")
    return None

def extract_sku_number(sku):
    match = re.search(r'\d+', str(sku))
    return match.group() if match else ''

def preprocess_sku(df):
    if df is None:
        return pd.DataFrame()
    df = df.copy()
    sku_col = 'Variant SKU' if 'Variant SKU' in df.columns else 'SKU' if 'SKU' in df.columns else None
    if not sku_col:
        st.warning("⚠️ SKU column not found.")
        return pd.DataFrame()
    df['sku_num'] = df[sku_col].apply(extract_sku_number)
    return df[df['sku_num'].notna() & (df['sku_num'] != '')]

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
