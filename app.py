import pandas as pd
import streamlit as st
import os
import re
from utils import (
    read_csv_with_fallback, preprocess_sku, fuzzy_match_inventory,
    save_selected_handles, extract_sku_number
)
from ui import display_product_tiles
from state import initialize_session_state

st.set_page_config(layout="wide")
initialize_session_state()
st.title("🎉 Dropship Product & Inventory Manager")

# 📁 Create or reuse the product upload folder
product_folder = "product_files"
os.makedirs(product_folder, exist_ok=True)

# ========== SIDEBAR UPLOADS ==========
st.sidebar.header("Upload Files")
uploaded_product_files = st.sidebar.file_uploader("Upload Product File(s)", type="csv", accept_multiple_files=True)
inventory_file = st.sidebar.file_uploader("Upload Inventory File", type="csv")

search_query = st.sidebar.text_input("🔍 Search Products", value=st.session_state.search_query, key="search_box")
if search_query != st.session_state.search_query:
    st.session_state.search_query = search_query
    st.session_state.product_page = 1

if st.sidebar.button("Clear Selection"):
    st.session_state.selected_handles.clear()
    save_selected_handles()

# 💾 Save uploaded product files to folder
if uploaded_product_files:
    for uploaded_file in uploaded_product_files:
        with open(os.path.join(product_folder, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
    st.success(f"{len(uploaded_product_files)} product file(s) uploaded and saved.")

# ========== READ AND PROCESS PRODUCT FILES ==========
product_csvs = [f for f in os.listdir(product_folder) if f.endswith(".csv")]
product_dfs = [preprocess_sku(read_csv_with_fallback(os.path.join(product_folder, f))) for f in product_csvs]
full_product_df = pd.concat(product_dfs, ignore_index=True) if product_dfs else pd.DataFrame()

# Store for app access
st.session_state.full_product_df = full_product_df if not full_product_df.empty else None

# ========== READ AND FILTER INVENTORY ==========
if st.session_state.full_product_df is not None and inventory_file:
    inventory_df = preprocess_sku(read_csv_with_fallback(inventory_file))
    inventory_df = inventory_df[inventory_df["Available"] > 20].copy()

    # Match and merge on SKU
    merged_df = st.session_state.full_product_df.merge(inventory_df, on="SKU", how="inner")
    st.session_state.merged_df_cache = merged_df

# ========== DISPLAY PRODUCTS ==========
if st.session_state.merged_df_cache is not None:
    merged = st.session_state.merged_df_cache
    if not merged.empty:
        display_product_tiles(merged, page_key="product", search_query=st.session_state.search_query)
    else:
        st.info("🔍 No matching products with inventory available.")
else:
    st.info("📤 Please upload product and inventory files to begin.")

# ========== DISPLAY SELECTED PRODUCTS & EXPORT ==========
if st.session_state.full_product_df is not None:
    selected_preview = st.session_state.full_product_df[
        st.session_state.full_product_df['Handle'].isin(st.session_state.selected_handles)
    ]

    if not selected_preview.empty:
        st.markdown("## ✅ Selected Products")
        display_product_tiles(selected_preview, page_key="selected")

        # Download selected product CSV
        output_df = selected_preview.drop_duplicates().sort_values(by="Handle")
        csv_product = output_df.to_csv(index=False).encode("utf-8")
        st.download_button("📦 Download Selected Product CSV", data=csv_product, file_name="selected_products.csv")

        # Download matching inventory for selected SKUs
        if inventory_file:
            inventory_df = preprocess_sku(read_csv_with_fallback(inventory_file))
            selected_skus = selected_preview['SKU'].dropna().unique()
            matched_inventory = inventory_df[inventory_df['SKU'].isin(selected_skus)]
            csv_inventory = matched_inventory.to_csv(index=False).encode("utf-8")
            st.download_button("📦 Download Matching Inventory CSV", data=csv_inventory, file_name="matching_inventory.csv")
