import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

from lib.remapping import load_file, remap_headers
from lib.ui import (
    help_panel,
    page_header,
    render_file_card,
    section_title,
    stat_cards,
    tip_box,
)

page_header(
    step=1,
    title="Header Remapping",
    subtitle=(
        "Align PM survey column headers with LimeSurvey pipe-delimit codes. "
        "Upload both files, run remapping, then download your outputs."
    ),
)

help_panel(
    "What files do I need?",
    """
    **Mapping file** — PM export with headers to fix (CSV or Excel).

    **Key file** — Pipe Delimit CSV from Community Survey 6
    (Responses → Pipe Limited). Its column names are the target format.
    """,
)

section_title("Upload files")

with st.container(border=True):
    upload_col1, upload_col2 = st.columns(2)

    with upload_col1:
        mapping_file = st.file_uploader(
            "Survey file (needs mapping)",
            type=["csv", "xlsx", "xlsm"],
            help="PM export: CSV, XLSX, or XLSM",
        )

    with upload_col2:
        key_file = st.file_uploader(
            "Key file (pipe delimit)",
            type=["csv", "xlsx", "xlsm"],
            help="Community Survey 6 pipe-delimit export",
        )

if mapping_file is not None and key_file is not None:
    current_files = (mapping_file.name, key_file.name)

    if st.session_state.get("current_files") != current_files:
        st.session_state["current_files"] = current_files
        st.session_state["results"] = None

    try:
        maps_df = load_file(mapping_file)
        key_df = load_file(key_file)

        st.success("Both files loaded. Ready to remap.")

        section_title("File overview")

        col1, col2 = st.columns(2)

        with col1:
            render_file_card(
                "Survey file",
                mapping_file.name,
                len(maps_df),
                len(maps_df.columns),
            )

        with col2:
            render_file_card(
                "Key file",
                key_file.name,
                len(key_df),
                len(key_df.columns),
            )

        with st.expander("Preview uploaded files", expanded=False):
            preview_col1, preview_col2 = st.columns(2)

            with preview_col1:
                st.markdown("**Survey file**")
                st.dataframe(maps_df.head(10), use_container_width=True)

            with preview_col2:
                st.markdown("**Key file**")
                st.dataframe(key_df.head(10), use_container_width=True)

        if st.button(
            "Run header remapping",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Remapping headers..."):
                remapped_df, replaced_df, unmatched_df = remap_headers(
                    maps_df,
                    key_df,
                )

                st.session_state["results"] = {
                    "remapped_df": remapped_df,
                    "replaced_df": replaced_df,
                    "unmatched_df": unmatched_df,
                }

    except Exception as error:
        st.error(f"Unable to load the files: {error}")

results = st.session_state.get("results")

if results is not None:
    remapped_df = results["remapped_df"]
    replaced_df = results["replaced_df"]
    unmatched_df = results["unmatched_df"]

    ignored_count = unmatched_df["Reason"].eq("Ignored").sum()
    unmatched_count = len(unmatched_df) - ignored_count

    st.divider()
    section_title("Remapping results")

    stat_cards([
        ("Total headers", f"{len(remapped_df.columns):,}", "neutral"),
        ("Replaced", f"{len(replaced_df):,}", "success"),
        ("Unmatched", f"{unmatched_count:,}", "warning"),
        ("Ignored", f"{ignored_count:,}", "accent"),
    ])

    tab1, tab2, tab3 = st.tabs([
        "Unmatched",
        "Replaced",
        "Survey preview",
    ])

    with tab1:
        if unmatched_df.empty:
            st.success("Every header was matched.")
        else:
            st.dataframe(unmatched_df, use_container_width=True)

    with tab2:
        st.dataframe(replaced_df, use_container_width=True)

    with tab3:
        st.dataframe(remapped_df.head(25), use_container_width=True)

    st.divider()
    section_title("Download outputs")

    tip_box(
        "Next: use **Create Codebook** in the sidebar, then **Combine Package** "
        "for the final Excel deliverable."
    )

    safe_name = Path(mapping_file.name).stem.replace(" ", "_")

    download_col1, download_col2, download_col3 = st.columns(3)

    with download_col1:
        st.download_button(
            label="Remapped survey",
            data=remapped_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_name}_remapped_output.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with download_col2:
        st.download_button(
            label="Replaced headers log",
            data=replaced_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_name}_replaced_headers.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with download_col3:
        st.download_button(
            label="Unmatched headers log",
            data=unmatched_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_name}_unmatched_headers.csv",
            mime="text/csv",
            use_container_width=True,
        )
