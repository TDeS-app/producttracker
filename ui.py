import streamlit as st
from rapidfuzz import fuzz

PRODUCTS_PER_PAGE = 20

def display_product_tiles(merged_df, page_key="product", search_query=""):
    current_page = st.session_state.get(f"{page_key}_page", 1)
    grouped = merged_df.groupby("Handle")
    filtered_grouped = []

    if search_query:
        for handle, group in grouped:
            row_text = " ".join(group.astype(str).fillna("").values.flatten())
            if fuzz.partial_ratio(search_query.lower(), row_text.lower()) > 50:
                filtered_grouped.append((handle, group))
    else:
        filtered_grouped = list(grouped)

    total = len(filtered_grouped)
    start = (current_page - 1) * PRODUCTS_PER_PAGE
    end = start + PRODUCTS_PER_PAGE
    paginated_grouped = filtered_grouped[start:end]

    for handle, group in paginated_grouped:
        with st.container():
            cols = st.columns([0.1, 1.9])
            with cols[0]:
                checked = handle in st.session_state.selected_handles
                if st.checkbox("", value=checked, key=f"{page_key}_cb_{handle}"):
                    st.session_state.selected_handles.add(handle)
                else:
                    st.session_state.selected_handles.discard(handle)
            with cols[1]:
                name = group['Title'].iloc[0] if 'Title' in group.columns else handle
                available_col = [c for c in group.columns if 'Available' in c or 'On hand' in c]
                available = group[available_col[0]].iloc[0] if available_col else 'N/A'
                st.markdown(f"**{name}** - Available: {available}")
                with st.expander("Details"):
                    images = group['Image Src'].dropna().unique().tolist() if 'Image Src' in group.columns else []
                    if images:
                        st.image(images, width=100)
                    st.dataframe(group, use_container_width=True)

    total_pages = max(1, (total + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if current_page > 1:
            if st.button("⬅️ Previous", key=f"{page_key}_prev"):
                st.session_state[f"{page_key}_page"] -= 1
    with col2:
        if current_page < total_pages:
            if st.button("Next ➡️", key=f"{page_key}_next"):
                st.session_state[f"{page_key}_page"] += 1
    with col3:
        st.markdown(f"**Page {current_page} of {total_pages}**")
