"""ETC Survey Data Cleaning — entry point."""

import streamlit as st

from lib.app_shell import mark_app_shell_ready
from lib.ui import inject_global_theme, render_sidebar_links

st.set_page_config(
    page_title="ETC Survey Data Cleaning",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_theme()
render_sidebar_links()
mark_app_shell_ready()

page_remapping = st.Page(
    "pages/1_Header_Remapping.py",
    title="Header Remapping",
    icon=":material/swap_horiz:",
    default=True,
)
page_codebook = st.Page(
    "pages/2_Create_Codebook.py",
    title="Create Codebook",
    icon=":material/menu_book:",
)
page_combine = st.Page(
    "pages/3_Combine_Package.py",
    title="Combine Package",
    icon=":material/inventory_2:",
)

pages = st.navigation(
    [page_remapping, page_codebook, page_combine],
    position="hidden",
)

pages.run()
