"""Combine remapped survey data with a codebook workbook."""

from __future__ import annotations

import pandas as pd

from lib.excel_utils import sheets_to_excel_bytes


def load_codebook_sheets(uploaded_file) -> dict[str, pd.DataFrame]:
    return pd.read_excel(uploaded_file, sheet_name=None)


def build_combined_sheets(
    survey_df: pd.DataFrame,
    codebook_sheets: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    combined = {"Survey_Data": survey_df}

    for sheet_name, df in codebook_sheets.items():
        combined[str(sheet_name)] = df

    return combined


def combine_to_excel_bytes(
    survey_df: pd.DataFrame,
    codebook_sheets: dict[str, pd.DataFrame],
) -> bytes:
    sheets = build_combined_sheets(survey_df, codebook_sheets)

    return sheets_to_excel_bytes(sheets)


def output_stem_from_remapped_filename(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]

    return (
        stem.replace("_remapped_output", "")
        .replace(" ", "_")
        .lower()
    )
