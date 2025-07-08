import pandas as pd
import streamlit as st
import re
import json
import os
from io import BytesIO
from rapidfuzz import fuzz

def extract_sku_number(s):
    match = re.search(r'\d+', str(s))
    return match.group() if match else None

def read_csv_with_fallback(file_path, fallback_path=None):
    try:
        return pd.read_csv(file_path, encoding="ISO-8859-1")
    except FileNotFoundError:
        if fallback_path:
            return pd.read_csv(fallback_path, encoding="ISO-8859-1")
        else:
            return pd.DataFrame()

def preprocess_sku(df):
    if df is None or df.empty:
        st.warning("⚠️ Input DataFrame is empty or missing.")
        return pd.DataFrame()

    df = df.copy()
    df.columns = df.columns.str.strip()

    sku_col = next((col for col in ['Variant SKU', 'SKU'] if col in df.columns), None)
    if sku_col is None:
        st.warning("⚠️ SKU column not found.")
        return pd.DataFrame()

    df['SKU'] = df[sku_col].apply(extract_sku_number)
    if sku_col != 'SKU':
        df.drop(columns=[sku_col], inplace=True)

    # Clean Handle (for product data only; won't exist in inventory)
    if 'Handle' in df.columns:
        df['Handle'] = df['Handle'].astype(str).str.strip()
        df = df[df['Handle'].str.len() > 0]  # Remove empty strings
        df = df


def save_selected_handles():
    st.session_state.selected_handles = list(set(st.session_state.selected_handles))
