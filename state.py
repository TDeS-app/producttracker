import streamlit as st
import os
import json

SELECTION_FILE = "selected_handles.json"

def initialize_session_state():
    if 'selected_handles' not in st.session_state:
        if os.path.exists(SELECTION_FILE):
            with open(SELECTION_FILE, "r") as f:
                st.session_state.selected_handles = set(json.load(f))
        else:
            st.session_state.selected_handles = set()
    for key, default in {
        'product_df': None,
        'last_output_df': None,
        'merged_df_cache': None,
        'full_product_df': None,
        'product_page': 1,
        'selected_page': 1,
        'search_query': ""
