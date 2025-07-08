# ========== DISPLAY SELECTED PRODUCTS ==========
if not product_df.empty and st.session_state.selected_handles:
    selected_preview = product_df[
        product_df["Handle"].isin(st.session_state.selected_handles)
    ]

    if not selected_preview.empty:
        st.markdown("## ✅ Selected Products")
        display_product_tiles(selected_preview, page_key="selected")

        # Get selected handles
        selected_handles = selected_preview["Handle"].dropna().unique()

        # 📦 Prepare product export: group + dedupe
        export_product = (
            product_df[product_df["Handle"].isin(selected_handles)]
            .sort_values("Handle")
            .drop_duplicates()
        )

        st.download_button(
            "📦 Download Selected Product CSV",
            data=export_product.to_csv(index=False).encode("utf-8"),
            file_name="selected_products.csv"
        )

        # 🧩 Prepare inventory export
        selected_skus = selected_preview["SKU"].dropna().unique()

        if inventory_file is not None:
            try:
                inventory_file.seek(0)
                raw_inventory = pd.read_csv(inventory_file, encoding="ISO-8859-1")
                sku_col = "Variant SKU" if "Variant SKU" in raw_inventory.columns else "SKU"

                matched_inventory = raw_inventory[
                    raw_inventory[sku_col].astype(str).apply(
                        lambda s: any(str(s).find(sku) == 0 for sku in selected_skus)
                    )
                ]

                st.download_button(
                    "📦 Download Matching Inventory CSV",
                    data=matched_inventory.to_csv(index=False).encode("utf-8"),
                    file_name="matching_inventory.csv"
                )
            except Exception as e:
                st.error(f"❌ Failed to export matching inventory: {e}")
