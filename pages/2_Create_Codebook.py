import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

from lib.codebook import (
    build_codebook_sheets,
    load_json_data,
    survey_id_from_data,
)
from lib.excel_utils import sheets_to_excel_bytes
from lib.ui import help_panel, page_header, render_file_card, section_title, stat_cards, tip_box

page_header(
    step=2,
    title="Create Codebook",
    subtitle=(
        "Turn a LimeSurvey full JSON export into a readable Excel dictionary "
        "with Questions, Subquestions, and Answers sheets."
    ),
)

help_panel(
    "What file do I need?",
    """
    Upload the **full JSON** export from LimeSurvey
    (e.g. `limesurvey_survey_6074.json`).

    **Output:** Excel codebook with three sheets — **Questions**,
    **Subquestions**, and **Answers** — with cleaned question text.
    """,
)

section_title("Upload JSON")

with st.container(border=True):
    json_file = st.file_uploader(
        "LimeSurvey JSON export",
        type=["json"],
        help="Full survey definition export from LimeSurvey.",
    )

if json_file is not None:
    file_key = json_file.name

    if st.session_state.get("codebook_file_key") != file_key:
        st.session_state["codebook_file_key"] = file_key
        st.session_state["codebook_results"] = None

    try:
        json_file.seek(0)
        data = load_json_data(json_file)
        survey_id = survey_id_from_data(data)

        st.success("JSON loaded successfully.")

        info_col1, info_col2 = st.columns(2)

        with info_col1:
            render_file_card("Source file", json_file.name)

        with info_col2:
            extra = (
                [f"**Survey ID:** {survey_id}"]
                if survey_id
                else ["**Survey ID:** not found in file"]
            )
            render_file_card("Survey", extra_lines=extra)

        if st.button(
            "Generate codebook",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Building codebook..."):
                sheets = build_codebook_sheets(data)

                stem = Path(json_file.name).stem
                excel_bytes = sheets_to_excel_bytes(sheets)

                st.session_state["codebook_results"] = {
                    "sheets": sheets,
                    "excel_bytes": excel_bytes,
                    "output_name": f"{stem}_codebook.xlsx",
                }

    except Exception as error:
        st.error(f"Unable to read JSON file: {error}")

results = st.session_state.get("codebook_results")

if results is not None:
    sheets = results["sheets"]

    st.divider()
    section_title("Codebook summary")

    stat_cards([
        ("Questions", f"{len(sheets['Questions']):,}", "accent"),
        ("Subquestions", f"{len(sheets['Subquestions']):,}", "neutral"),
        ("Answers", f"{len(sheets['Answers']):,}", "success"),
    ])

    tab1, tab2, tab3 = st.tabs([
        "Questions",
        "Subquestions",
        "Answers",
    ])

    with tab1:
        st.dataframe(sheets["Questions"].head(25), use_container_width=True)

    with tab2:
        st.dataframe(sheets["Subquestions"].head(25), use_container_width=True)

    with tab3:
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
