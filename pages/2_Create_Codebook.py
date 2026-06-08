import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

from lib.app_shell import ensure_app_shell
from lib.codebook import (
    CODEBOOK_SHEET_ORDER,
    build_codebook_sheets,
    load_json_data,
    survey_id_from_data,
)
from lib.codebook_lss import build_codebook_sheets_from_lss
from lib.excel_utils import sheets_to_excel_bytes
from lib.ui import help_panel, page_header, render_file_card, section_title, stat_cards, tip_box

ensure_app_shell()

page_header(
    step=2,
    title="Create Codebook",
    subtitle=(
        "Turn a LimeSurvey export into a readable Excel dictionary "
        "with Groups, Questions, Subquestions, and Answers sheets."
    ),
)

help_panel(
    "What file do I need?",
    """
    Upload either:

    - **Full JSON** export from LimeSurvey (e.g. `limesurvey_survey_6074.json`), or
    - **LSS** survey structure export (e.g. `5149_dallas-tx-df-4_2023.lss`)

    **Output:** Excel codebook with four sheets — **Groups**, **Questions**,
    **Subquestions**, and **Answers** — including question group labels and
    cleaned question text.
    """,
)

section_title("Choose export type")

export_type = st.radio(
    "LimeSurvey export format",
    options=["JSON", "LSS"],
    horizontal=True,
    help="Use JSON for full JSON exports, or LSS for LimeSurvey structure files.",
)

uploaded_file = None
language = "en"

with st.container(border=True):
    if export_type == "JSON":
        uploaded_file = st.file_uploader(
            "LimeSurvey JSON export",
            type=["json"],
            help="Full survey definition export from LimeSurvey.",
        )
    else:
        language = st.selectbox(
            "Codebook language",
            options=["en", "es"],
            format_func=lambda value: "English" if value == "en" else "Spanish",
            help="Language used for group, question, and answer text in the LSS file.",
        )
        uploaded_file = st.file_uploader(
            "LimeSurvey LSS export",
            type=["lss"],
            help="Survey structure export from LimeSurvey.",
        )

if uploaded_file is not None:
    file_key = (export_type, uploaded_file.name, language)

    if st.session_state.get("codebook_file_key") != file_key:
        st.session_state["codebook_file_key"] = file_key
        st.session_state["codebook_results"] = None

    try:
        uploaded_file.seek(0)

        info_col1, info_col2 = st.columns(2)

        with info_col1:
            render_file_card("Source file", uploaded_file.name)

        with info_col2:
            if export_type == "JSON":
                data = load_json_data(uploaded_file)
                survey_id = survey_id_from_data(data)
                extra = (
                    [f"**Survey ID:** {survey_id}"]
                    if survey_id
                    else ["**Survey ID:** not found in file"]
                )
                render_file_card("Survey", extra_lines=extra)
            else:
                render_file_card(
                    "Language",
                    extra_lines=[f"**Selected:** {language.upper()}"],
                )

        st.success(f"{export_type} file loaded successfully.")

        if st.button(
            "Generate codebook",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Building codebook..."):
                if export_type == "JSON":
                    uploaded_file.seek(0)
                    data = load_json_data(uploaded_file)
                    sheets = build_codebook_sheets(data)
                else:
                    uploaded_file.seek(0)
                    sheets = build_codebook_sheets_from_lss(
                        uploaded_file,
                        language=language,
                    )

                stem = Path(uploaded_file.name).stem
                excel_bytes = sheets_to_excel_bytes(sheets)

                st.session_state["codebook_results"] = {
                    "sheets": sheets,
                    "excel_bytes": excel_bytes,
                    "output_name": f"{stem}_codebook.xlsx",
                }

    except Exception as error:
        st.error(f"Unable to read {export_type} file: {error}")

results = st.session_state.get("codebook_results")

if results is not None:
    sheets = results["sheets"]

    st.divider()
    section_title("Codebook summary")

    stat_cards([
        ("Groups", f"{len(sheets['Groups']):,}", "accent"),
        ("Questions", f"{len(sheets['Questions']):,}", "neutral"),
        ("Subquestions", f"{len(sheets['Subquestions']):,}", "success"),
        ("Answers", f"{len(sheets['Answers']):,}", "accent"),
    ])

    tab_groups, tab_questions, tab_subquestions, tab_answers = st.tabs(
        list(CODEBOOK_SHEET_ORDER),
    )

    with tab_groups:
        st.dataframe(sheets["Groups"].head(25), use_container_width=True)

    with tab_questions:
        st.dataframe(sheets["Questions"].head(25), use_container_width=True)

    with tab_subquestions:
        st.dataframe(sheets["Subquestions"].head(25), use_container_width=True)

    with tab_answers:
        st.dataframe(sheets["Answers"].head(25), use_container_width=True)

    st.divider()
    section_title("Download")

    tip_box(
        "Use this file on **Combine Package** with your remapped CSV from Step 1."
    )

    st.download_button(
        label="Download codebook (Excel)",
        data=results["excel_bytes"],
        file_name=results["output_name"],
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        type="primary",
        use_container_width=True,
    )
