"""Shared app chrome for entrypoint and direct page loads on Streamlit Cloud."""

from __future__ import annotations

import streamlit as st

from lib.ui import inject_global_theme, render_sidebar_links

SHELL_FLAG = "_etc_app_shell_ready"


def mark_app_shell_ready() -> None:
    st.session_state[SHELL_FLAG] = True


def ensure_app_shell() -> None:
    """Inject theme on every rerun; sidebar when not already set by app.py."""

    inject_global_theme()

    if st.session_state.get(SHELL_FLAG):
        return

    try:
        st.set_page_config(
            page_title="ETC Survey Data Cleaning",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass

    render_sidebar_links()
    mark_app_shell_ready()
