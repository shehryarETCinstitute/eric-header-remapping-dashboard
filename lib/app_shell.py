"""Shared app chrome for entrypoint and direct page loads."""

from __future__ import annotations

import streamlit as st

from lib.ui import inject_global_theme, render_sidebar_links


def ensure_app_shell() -> None:
    """Apply theme and sidebar on every page load and rerun.

    Must run on each page script because Streamlit Cloud can execute a
    ``pages/*.py`` file directly when the user follows a page URL or
    ``st.page_link``. A session-state guard caused the sidebar to disappear
    on the second navigation once the flag was set on the first page.
    """

    inject_global_theme()

    try:
        st.set_page_config(
            page_title="ETC Survey Data Cleaning",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass

    render_sidebar_links()
