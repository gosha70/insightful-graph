import streamlit as st

def apply_page_config():
    try:
        st.set_page_config(
            page_title="Insightful Graph",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except st.errors.StreamlitAPIException:
        # already set on this page, ignore
        pass