import pandas as pd
import streamlit as st
from utils import (
    read_csv_with_fallback, preprocess_sku, fuzzy_match_inventory,
    save_selected_handles, extract_sku_number
)
from ui import display_product_tiles
from state import initialize_session_state

st.set_page_config(layout="wide")
st.title("🎉 Dropship Product & Inventory Manager")

initialize_session_state()

# Sidebar: Uploads and Search
st.sidebar.header("Upload Files")
product_files = st.sidebar.file_uploader("Upload Product File(s)", type="csv", accept_multiple_files=True)
inventory_file = st.sidebar.file_uploader("Upload Inventory File", type="csv")
search_query = st.sidebar.text_input("🔍 Search Products", value=st.session_state.search_query, key="search_box")

if search_query != st.session_state.search_query:
    st.session_state.search_query = search_query
    st.session_state.product_page = 1

if st.sidebar.button("Clear Selection"):
    st.session_state.selected_handles.clear()
    save_selected_handles()

# Load and process files
if product_files:
    product_folder = "product_files"  # Change this to your actual folder name

    # 🧹 Function to clean SKU by extracting the first number
    def clean_sku(s):
        match = re.search(r'\d+', str(s))
        return match.group() if match else None

    # 📦 Load and combine all product CSVs
    product_files = [f for f in os.listdir(product_folder) if f.endswith(".csv")]
    product_dfs = [pd.read_csv(os.path.join(product_folder, f)) for f in product_files]
    product_df = pd.concat(product_dfs, ignore_index=True)

    # 🧼 Clean product SKUs
    product_df["SKU"] = product_df["Variant SKU"].apply(clean_sku)
    product_df.drop(columns=["Variant SKU"], inplace=True)

    dfs = product_df
    st.session_state.full_product_df = pd.concat(dfs, ignore_index=True)

if product_files and inventory_file:
    # 📦 Load and clean inventory
    inventory_df = pd.read_csv("inventory.csv")
    inventory_df["SKU"] = inventory_df["SKU"].apply(clean_sku)

    # 🧮 Filter inventory to only items with Available > 20
    inventory_df = inventory_df[inventory_df["Available"] > 20].copy()
    
    merged_df = fuzzy_match_inventory(st.session_state.full_product_df, inventory_df)
    st.session_state.merged_df_cache = merged_df

# Display merged products
if st.session_state.merged_df_cache is not None:
    merged = st.session_state.merged_df_cache
    if not merged.empty:
        display_product_tiles(merged, page_key="product", search_query=st.session_state.search_query)
    else:
        st.info("🔍 No matching products with inventory available.")
else:
    st.info("📤 Please upload product and inventory files to begin.")

# Display selected products
if st.session_state.full_product_df is not None:
    selected_preview = st.session_state.full_product_df[
        st.session_state.full_product_df['Handle'].isin(st.session_state.selected_handles)
    ]
    if not selected_preview.empty:
        st.markdown("## ✅ Selected Products")
        display_product_tiles(selected_preview, page_key="selected")

        # Download selected products
        output_df = selected_preview.drop_duplicates().sort_values(by="Handle")
        csv_product = output_df.to_csv(index=False).encode("utf-8")
        st.download_button("📦 Download Selected Product CSV", data=csv_product, file_name="selected_products.csv")

        # Download matching inventory
        if inventory_file:
            inventory_df = preprocess_sku(read_csv_with_fallback(inventory_file))
            selected_skus = selected_preview['Variant SKU'].dropna().apply(extract_sku_number).unique()
            matched_inventory = inventory_df[inventory_df['sku_num'].isin(selected_skus)]
            csv_inventory = matched_inventory.to_csv(index=False).encode("utf-8")
            st.download_button("📦 Download Matching Inventory CSV", data=csv_inventory, file_name="matching_inventory.csv")
