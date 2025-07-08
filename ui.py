import streamlit as st
from rapidfuzz import fuzz

def display_product_tiles(merged_df, page_key="product", search_query=""):
    current_page_key = f"{page_key}_page"
    current_page = st.session_state.get(current_page_key, 1)

    # Group by Handle
    if "Handle" not in merged_df.columns:
        st.error("🚫 'Handle' column missing. Cannot display product tiles.")
        return

    grouped = merged_df.groupby("Handle")
    filtered_grouped = []

    for handle, group in grouped:
        title = group.iloc[0].get("Title", "")
        if search_query.lower() in title.lower() or search_query.lower() in handle.lower():
            filtered_grouped.append((handle, group))

    items_per_page = 12
    total_pages = max(1, (len(filtered_grouped) + items_per_page - 1) // items_per_page)
    current_page = min(current_page, total_pages)
    st.session_state[current_page_key] = current_page

    start = (current_page - 1) * items_per_page
    end = start + items_per_page
    page_items = filtered_grouped[start:end]

    cols = st.columns(3)
    for idx, (handle, group) in enumerate(page_items):
        with cols[idx % 3]:
            st.markdown(f"**{group.iloc[0].get('Title', 'No Title')}**")
            st.caption(f"Handle: `{handle}`")
            if st.button("Select", key=f"{page_key}_select_{handle}"):
                st.session_state.selected_handles.add(handle)

    # Pagination
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if current_page > 1:
            if st.button("⬅️ Prev", key=f"{page_key}_prev"):
                st.session_state[current_page_key] -= 1
    with col3:
        if current_page < total_pages:
            if st.button("Next ➡️", key=f"{page_key}_next"):
                st.session_state[current_page_key] += 1
