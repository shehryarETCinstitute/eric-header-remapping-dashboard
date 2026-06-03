import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd
import streamlit as st

from lib.combine import (
    combine_to_excel_bytes,
    load_codebook_sheets,
    output_stem_from_remapped_filename,
)
from lib.ui import (
    help_panel,
    page_header,
    render_file_card,
    section_title,
    stat_cards,
    tip_box,
)

page_header(
    step=3,
    title="Combine Package",
    subtitle=(
        "Merge remapped survey responses and the codebook into one "
        "Excel workbook for delivery."
    ),
)

help_panel(
    "What files do I need?",
    """
    1. **Remapped survey CSV** — `*_remapped_output.csv` from Step 1

    2. **Codebook Excel** — `*_codebook.xlsx` from Step 2

    **Output:** One workbook with **Survey_Data** plus all codebook sheets.
    """,
)

section_title("Upload files")

with st.container(border=True):
    upload_col1, upload_col2 = st.columns(2)

    with upload_col1:
        remapped_file = st.file_uploader(
            "Remapped survey CSV",
            type=["csv"],
            help="Output from Header Remapping (Step 1).",
        )

    with upload_col2:
        codebook_file = st.file_uploader(
            "Codebook Excel",
            type=["xlsx", "xlsm"],
            help="Output from Create Codebook (Step 2).",
        )

if remapped_file is not None and codebook_file is not None:
    file_key = (remapped_file.name, codebook_file.name)

    if st.session_state.get("combine_file_key") != file_key:
        st.session_state["combine_file_key"] = file_key
        st.session_state["combine_results"] = None

    try:
        remapped_file.seek(0)
        codebook_file.seek(0)

        survey_df = pd.read_csv(remapped_file, low_memory=False)
        codebook_sheets = load_codebook_sheets(codebook_file)

        st.success("Both files loaded. Ready to combine.")

        section_title("File overview")

        col1, col2 = st.columns(2)

        with col1:
            render_file_card(
                "Remapped survey",
                remapped_file.name,
                len(survey_df),
                len(survey_df.columns),
            )

        with col2:
            sheet_list = ", ".join(codebook_sheets.keys())
            render_file_card(
                "Codebook",
                codebook_file.name,
                extra_lines=[f"**Sheets:** {sheet_list}"],
            )

        with st.expander("Preview remapped survey", expanded=False):
            st.dataframe(survey_df.head(10), use_container_width=True)

        if st.button(
            "Create combined package",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Building combined workbook..."):
                excel_bytes = combine_to_excel_bytes(
                    survey_df,
                    codebook_sheets,
                )

                output_stem = output_stem_from_remapped_filename(
                    remapped_file.name
                )

                sheet_names = ["Survey_Data", *codebook_sheets.keys()]

                st.session_state["combine_results"] = {
                    "excel_bytes": excel_bytes,
                    "output_name": f"{output_stem}_combined_package.xlsx",
                    "sheet_names": sheet_names,
                    "survey_rows": len(survey_df),
                    "survey_columns": len(survey_df.columns),
                }

    except Exception as error:
        st.error(f"Unable to process files: {error}")

results = st.session_state.get("combine_results")

if results is not None:
    st.divider()
    section_title("Package ready")

    stat_cards([
        ("Survey rows", f"{results['survey_rows']:,}", "accent"),
        ("Survey columns", f"{results['survey_columns']:,}", "neutral"),
        ("Total sheets", f"{len(results['sheet_names']):,}", "success"),
    ])

    st.markdown(f"**Sheets:** {', '.join(results['sheet_names'])}")

    st.divider()
    section_title("Download")

    tip_box("Combined deliverable is ready for download.")

    st.download_button(
        label="Download combined package (Excel)",
        data=results["excel_bytes"],
        file_name=results["output_name"],
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        type="primary",
        use_container_width=True,
    )
