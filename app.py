import streamlit as st
import os
import pandas as pd
from utils import read_csv_with_fallback, preprocess_sku, save_selected_handles
from ui import display_product_tiles

st.set_page_config(layout="wide")
st.title("🎉 Dropship Product & Inventory Manager")

product_folder = "product_files"
os.makedirs(product_folder, exist_ok=True)

if "selected_handles" not in st.session_state:
    st.session_state.selected_handles = set()

# ========== SIDEBAR ==========
st.sidebar.header("Upload Files")
uploaded_product_files = st.sidebar.file_uploader("Upload Product File(s)", type="csv", accept_multiple_files=True)
inventory_file = st.sidebar.file_uploader("Upload Inventory File", type="csv")

search_query = st.sidebar.text_input("🔍 Search Products", value="", key="search_box")

if st.sidebar.button("Clear Selection"):
    st.session_state.selected_handles.clear()
    save_selected_handles()

# ========== SAVE PRODUCT FILES ==========
if uploaded_product_files:
    for uploaded_file in uploaded_product_files:
        with open(os.path.join(product_folder, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
    st.success(f"{len(uploaded_product_files)} product file(s) uploaded and saved.")

# ========== LOAD & CLEAN PRODUCT FILES ==========
product_csvs = [f for f in os.listdir(product_folder) if f.endswith(".csv")]
product_dfs = []
for f in product_csvs:
    df = preprocess_sku(read_csv_with_fallback(os.path.join(product_folder, f)))
    if not df.empty:
        product_dfs.append(df)

product_df = pd.concat(product_dfs, ignore_index=True) if product_dfs else pd.DataFrame()
st.session_state.full_product_df = product_df.copy()

# ========== LOAD INVENTORY & BUILD LOOKUP ==========
if not product_df.empty and inventory_file:
    raw_inventory = read_csv_with_fallback(inventory_file)
    inventory_df = preprocess_sku(raw_inventory)
    inventory_df = inventory_df[inventory_df["Available"] > 20].copy()
    inventory_df = inventory_df.rename(columns={"Title": "Inventory Title"})

    lookup_df = inventory_df.merge(
        product_df[["SKU", "Image Src", "Body (HTML)"]],
        on="SKU", how="left"
    )
    st.session_state.lookup_inventory = lookup_df

# ========== DISPLAY PRODUCTS ==========
if "lookup_inventory" in st.session_state:
    merged = st.session_state.lookup_inventory
    if not merged.empty:
        display_product_tiles(merged, page_key="product", search_query=search_query)
    else:
        st.info("🔍 No matching products with inventory available.")
else:
    st.info("📤 Please upload product and inventory files to begin.")

# ========== DISPLAY SELECTED PRODUCTS ==========
if not product_df.empty and st.session_state.selected_handles:
    selected_preview = product_df[product_df["Handle"].isin(st.session_state.selected_handles)]
    if not selected_preview.empty:
        st.markdown("## ✅ Selected Products")
        display_product_tiles(selected_preview, page_key="selected")

        # Get selected handles
        selected_handles = selected_preview["Handle"].dropna().unique()

        # Filter product_df for matching handles
        export_product = (
            product_df[product_df["Handle"].isin(selected_handles)]
            .drop_duplicates()
            .sort_values("Handle")
        )

    # Download button
    st.download_button(
    "📦 Download Selected Product CSV",
    data=export_product.to_csv(index=False).encode("utf-8"),
    file_name="selected_products.csv"
    )

        st.download_button("📦 Download Selected Product CSV", data=export_product.to_csv(index=False).encode("utf-8"), file_name="selected_products.csv")

        selected_skus = selected_preview["SKU"].dropna().unique()
        if inventory_file is not None:
            inventory_file.seek(0)  # Reset pointer to beginning
            raw_inventory = pd.read_csv(inventory_file, encoding="ISO-8859-1")
        else:
            raw_inventory = pd.DataFrame()
        matched_inventory = raw_inventory[
            raw_inventory["SKU"].apply(lambda s: any(str(s).find(sku) == 0 for sku in selected_skus))
        ]
        st.download_button("📦 Download Matching Inventory CSV", data=matched_inventory.to_csv(index=False).encode("utf-8"), file_name="matching_inventory.csv")
