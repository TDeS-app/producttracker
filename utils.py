import pandas as pd
import streamlit as st
import re
import json
import os
from io import BytesIO
from rapidfuzz import fuzz

# 🔍 Extract numeric portion from SKU
def extract_sku_number(s):
    match = re.search(r'\d+', str(s))
    return match.group() if match else None

# 📥 Read CSV with fallback and encoding support
def read_csv_with_fallback(file_path, fallback_path=None):
    try:
        return pd.read_csv(file_path, encoding="ISO-8859-1")
    except FileNotFoundError:
        if fallback_path:
            return pd.read_csv(fallback_path, encoding="ISO-8859-1")
        else:
            return pd.DataFrame()

# 🧹 Preprocess SKU column and standardize to 'SKU'
def preprocess_sku(df):
    if df is None or df.empty:
        st.warning("⚠️ Input DataFrame is empty or missing.")
        return pd.DataFrame()

    df = df.copy()
    df.columns = df.columns.str.strip()

    # Find SKU column
    sku_col = next((col for col in ['Variant SKU', 'SKU'] if col in df.columns), None)

    if sku_col is None:
        st.warning("⚠️ SKU column not found. Expected 'Variant SKU' or 'SKU'.")
        return pd.DataFrame()

    # Clean and unify SKU column
    df['SKU'] = df[sku_col].apply(extract_sku_number)

    if sku_col != 'SKU':
        df.drop(columns=[sku_col], inplace=True)

    return df[df['SKU'].notna() & (df['SKU'] != '')]

# 💾 Save selected handles to session state
def save_selected_handles():
    st.session_state.selected_handles = list(set(st.session_state.selected_handles))

