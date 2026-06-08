"""Shared UI theme and layout helpers for the ETC dashboard."""

from __future__ import annotations

import html as html_module

import streamlit as st


def inject_global_theme() -> None:
    """Inject global CSS and sidebar behavior on every rerun.

    Streamlit clears injected styles on navigation, so we must not cache
    theme injection in session state.
    """

    st.markdown(
        """
        <style>
        .stApp {
            background: #f1f5f9;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            position: relative !important;
            background: linear-gradient(180deg, #0a1f38 0%, #0f2d4a 100%);
            display: flex !important;
            flex-direction: column !important;
            align-items: stretch !important;
        }

        /* Collapse row — full width, button aligned to the right edge */
        [data-testid="stSidebar"] *:has(> [data-testid="stSidebarCollapseButton"]),
        [data-testid="stSidebarHeader"] {
            display: flex !important;
            flex-direction: row !important;
            justify-content: flex-end !important;
            align-items: center !important;
            width: 100% !important;
            max-width: 100% !important;
            min-height: 2.5rem !important;
            padding: 0.5rem 0.85rem 0.35rem 0.85rem !important;
            margin: 0 !important;
            box-sizing: border-box !important;
            align-self: stretch !important;
        }

        button[data-testid="stSidebarCollapseButton"] {
            position: relative !important;
            left: auto !important;
            right: auto !important;
            top: auto !important;
            margin: 0 !important;
            transform: none !important;
            flex-shrink: 0 !important;
        }

        [data-testid="stSidebarUserContent"] {
            padding: 0.25rem 0.85rem 1rem 0.85rem !important;
        }

        /* Force light text everywhere in sidebar (Streamlit theme overrides) */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] a,
        [data-testid="stSidebar"] button {
            color: #e2e8f0;
        }

        /* Brand */
        [data-testid="stSidebar"] .etc-brand-title {
            color: #ffffff !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            line-height: 1.3 !important;
        }

        [data-testid="stSidebar"] .etc-brand-sub {
            color: #b8c5d6 !important;
            font-size: 0.8rem !important;
            margin: 0.15rem 0 0 0 !important;
        }

        [data-testid="stSidebar"] .etc-brand-divider {
            border: none;
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            margin: 0.65rem 0 0.75rem 0;
        }

        [data-testid="stSidebar"] .etc-nav-section {
            color: #b8c5d6 !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            margin: 0 0 0.35rem 0 !important;
            padding: 0 !important;
        }

        /* Custom page links (st.page_link) — icon + label when expanded */
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            color: #f1f5f9 !important;
            background-color: transparent !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            margin: 0.15rem 0 !important;
            border: 1px solid transparent !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"] {
            display: inline-flex !important;
            flex-shrink: 0 !important;
            font-size: 1.2rem !important;
        }

        body.etc-sidebar-icon-only [data-testid="stSidebar"] .etc-sidebar-text,
        body.etc-sidebar-icon-only [data-testid="stSidebar"] .etc-brand-divider,
        body.etc-sidebar-icon-only [data-testid="stSidebar"] .etc-nav-section {
            display: none !important;
        }

        body.etc-sidebar-icon-only [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p,
        body.etc-sidebar-icon-only [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] [data-testid="stMarkdownContainer"] {
            display: none !important;
        }

        body.etc-sidebar-icon-only [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            justify-content: center !important;
            padding: 0.55rem !important;
            min-height: 2.5rem !important;
        }

        /* Icon-only sidebar (collapsed / narrow) */
        :root {
            --etc-sidebar-collapsed-width: 4.5rem;
        }

        body.etc-sidebar-icon-only section[data-testid="stSidebar"] {
            transform: translateX(0) !important;
            visibility: visible !important;
            min-width: var(--etc-sidebar-collapsed-width) !important;
            max-width: var(--etc-sidebar-collapsed-width) !important;
            width: var(--etc-sidebar-collapsed-width) !important;
            overflow-x: hidden !important;
        }

        body.etc-sidebar-icon-only [data-testid="stSidebarUserContent"] {
            padding: 0.35rem 0.35rem 1rem 0.35rem !important;
        }

        body.etc-sidebar-icon-only [data-testid="stSidebar"] *:has(> [data-testid="stSidebarCollapseButton"]),
        body.etc-sidebar-icon-only [data-testid="stSidebarHeader"] {
            justify-content: center !important;
            padding: 0.5rem 0.25rem 0.35rem 0.25rem !important;
        }

        /* Keep main content aligned beside icon rail */
        body.etc-sidebar-icon-only [data-testid="stAppViewContainer"] > section.main,
        body.etc-sidebar-icon-only section.main {
            margin-left: var(--etc-sidebar-collapsed-width) !important;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border-color: rgba(255, 255, 255, 0.15) !important;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
            background-color: #0d9488 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border: 1px solid #14b8a6 !important;
            box-shadow: 0 2px 8px rgba(13, 148, 136, 0.35);
        }

        /* Sidebar collapse / expand buttons */
        [data-testid="stSidebar"] button[kind="header"],
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
            color: #ffffff !important;
            background: rgba(255, 255, 255, 0.15) !important;
            border: 1px solid rgba(255, 255, 255, 0.4) !important;
            border-radius: 6px !important;
        }

        [data-testid="stSidebar"] button[kind="header"] svg {
            fill: #ffffff !important;
            stroke: #ffffff !important;
        }

        /* Hide Streamlit built-in expand chevron in main area (sidebar rail has its own) */
        [data-testid="stExpandSidebarButton"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            min-width: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            position: absolute !important;
            left: -9999px !important;
        }

        /* Main content spacing */
        .main .block-container {
            padding-top: 1.5rem;
            max-width: 1100px;
        }

        /* Metrics */
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.65rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stMetric"] label {
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            color: #64748b !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-weight: 700 !important;
        }

        /* File upload */
        div[data-testid="stFileUploader"] section {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.75rem;
        }

        div[data-testid="stFileUploader"] section:hover {
            border-color: #0d9488;
        }

        div[data-testid="stFileUploader"] label {
            font-weight: 600 !important;
            color: #334155 !important;
        }

        /* Buttons */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #0d9488, #0f766e) !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.55rem 1.25rem !important;
        }

        .stButton button[kind="primary"]:hover {
            background: linear-gradient(135deg, #0f766e, #115e59) !important;
        }

        .stDownloadButton button {
            border-radius: 8px !important;
            font-weight: 500 !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: #e2e8f0;
            border-radius: 8px;
            padding: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.88rem;
        }

        .stTabs [aria-selected="true"] {
            background: #ffffff !important;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            font-weight: 600 !important;
            color: #334155 !important;
            background: #ffffff;
            border-radius: 8px;
        }

        details[data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            margin-bottom: 1rem;
        }

        /* Success messages */
        div[data-testid="stNotificationContentSuccess"] {
            background-color: #ecfdf5;
            color: #065f46;
        }

        /* Page hero banner (native HTML — faster than iframe) */
        .etc-hero {
            background: linear-gradient(120deg, #0a1f38 0%, #134e6f 55%, #0d9488 100%);
            border-radius: 14px;
            padding: 28px 32px;
            color: #ffffff;
            margin-bottom: 1rem;
        }

        .etc-hero .etc-hero-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }

        .etc-hero .etc-step-badge {
            background: rgba(255, 255, 255, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .etc-hero .etc-step-dots {
            display: flex;
            gap: 6px;
            align-items: center;
        }

        .etc-hero .etc-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.25);
        }

        .etc-hero .etc-dot.active {
            background: #5eead4;
            width: 24px;
            border-radius: 4px;
        }

        .etc-hero .etc-dot.done {
            background: rgba(94, 234, 212, 0.6);
        }

        .etc-hero h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            line-height: 1.2;
        }

        .etc-hero p {
            font-size: 15px;
            line-height: 1.55;
            color: #cbd5e1;
            margin: 0;
            max-width: 720px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.html(
        """
        <script>
        (function () {
            const ICON_COLLAPSE = "keyboard_double_arrow_left";
            const ICON_EXPAND = "keyboard_double_arrow_right";

            function setChevronIcon(node, ligature) {
                if (!node) return;
                node.textContent = ligature;
            }

            function fixSidebarChevron(sidebar, expanded) {
                const btn = sidebar.querySelector(
                    '[data-testid="stSidebarCollapseButton"]'
                );
                if (!btn) return;
                const ligature = expanded ? ICON_COLLAPSE : ICON_EXPAND;
                const icon = btn.querySelector('[data-testid="stIconMaterial"]');
                if (icon) {
                    setChevronIcon(icon, ligature);
                    return;
                }
                const fallback = btn.querySelector("span, i, svg");
                if (fallback) setChevronIcon(fallback, ligature);
            }

            function hideMainExpandButton() {
                document
                    .querySelectorAll(
                        '[data-testid="stExpandSidebarButton"], ' +
                        '[data-testid="collapsedControl"], ' +
                        '[data-testid="stSidebarCollapsedControl"]'
                    )
                    .forEach((el) => {
                        el.style.setProperty("display", "none", "important");
                        el.style.setProperty("visibility", "hidden", "important");
                        el.style.setProperty("pointer-events", "none", "important");
                    });
            }

            function syncSidebar() {
                const sidebar = document.querySelector(
                    'section[data-testid="stSidebar"]'
                );
                if (!sidebar) return;
                const expanded = sidebar.getAttribute("aria-expanded") !== "false";
                document.body.classList.toggle("etc-sidebar-icon-only", !expanded);
                fixSidebarChevron(sidebar, expanded);
                hideMainExpandButton();
            }

            if (window.__etcSidebarObserver) {
                window.__etcSidebarObserver.disconnect();
                window.__etcSidebarObserver = null;
            }

            syncSidebar();
            requestAnimationFrame(syncSidebar);
            setTimeout(syncSidebar, 120);

            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (sidebar) {
                window.__etcSidebarObserver = new MutationObserver(syncSidebar);
                window.__etcSidebarObserver.observe(sidebar, {
                    attributes: true,
                    attributeFilter: ["aria-expanded"],
                });
            }
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def inject_theme() -> None:
    inject_global_theme()


PAGE_REMAPPING = "pages/1_Header_Remapping.py"
PAGE_CODEBOOK = "pages/2_Create_Codebook.py"
PAGE_COMBINE = "pages/3_Combine_Package.py"


def render_sidebar_links() -> None:
    """Custom sidebar: icons + labels when open; icons only when collapsed."""

    with st.sidebar:
        st.markdown(
            """
            <div class="etc-sidebar-text">
                <p class="etc-brand-title">ETC Institute</p>
                <p class="etc-brand-sub">Survey Data Cleaning</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<hr class="etc-brand-divider etc-sidebar-text">', unsafe_allow_html=True)
        st.markdown(
            '<p class="etc-nav-section etc-sidebar-text">Survey pipeline</p>',
            unsafe_allow_html=True,
        )
        st.page_link(
            PAGE_REMAPPING,
            label="Header Remapping",
            icon=":material/swap_horiz:",
            help="Header Remapping",
        )
        st.page_link(
            PAGE_CODEBOOK,
            label="Create Codebook",
            icon=":material/menu_book:",
            help="Create Codebook",
        )
        st.page_link(
            PAGE_COMBINE,
            label="Combine Package",
            icon=":material/inventory_2:",
            help="Combine Package",
        )


def render_sidebar(
    page_remapping: st.Page,
    page_codebook: st.Page,
    page_combine: st.Page,
) -> None:
    render_sidebar_links()


def _step_dot_class(dot_step: int, current_step: int) -> str:
    if dot_step == current_step:
        return "active"
    if dot_step < current_step:
        return "done"
    return ""


def page_header(step: int, title: str, subtitle: str) -> None:
    safe_title = html_module.escape(title)
    safe_subtitle = html_module.escape(subtitle)
    dot1 = _step_dot_class(1, step)
    dot2 = _step_dot_class(2, step)
    dot3 = _step_dot_class(3, step)

    st.markdown(
        f"""
        <div class="etc-hero">
          <div class="etc-hero-row">
            <span class="etc-step-badge">Step {step} of 3</span>
            <div class="etc-step-dots">
              <div class="etc-dot {dot1}"></div>
              <div class="etc-dot {dot2}"></div>
              <div class="etc-dot {dot3}"></div>
            </div>
          </div>
          <h1>{safe_title}</h1>
          <p>{safe_subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(f"##### {text}")
    st.markdown(
        "<hr style='margin:0.4rem 0 1.25rem 0;border:none;border-top:1px solid #e2e8f0;'>",
        unsafe_allow_html=True,
    )


def upload_section() -> None:
    """Context manager wrapper via container."""
    return st.container(border=True)


def stat_cards(stats: list[tuple[str, str, str]]) -> None:
    cols = st.columns(len(stats))

    for col, (label, value, _tone) in zip(cols, stats):
        with col:
            st.metric(label=label, value=value)


def render_file_card(
    title: str,
    filename: str | None = None,
    rows: int | None = None,
    columns: int | None = None,
    extra_lines: list[str] | None = None,
) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")

        if filename:
            st.caption(filename)

        if rows is not None and columns is not None:
            c1, c2 = st.columns(2)
            c1.metric("Rows", f"{rows:,}")
            c2.metric("Columns", f"{columns:,}")

        if extra_lines:
            for line in extra_lines:
                st.markdown(line)


def tip_box(message: str) -> None:
    with st.container(border=True):
        st.markdown(message)


def help_panel(title: str, body_md: str) -> None:
    with st.expander(title, expanded=False):
        st.markdown(body_md)
