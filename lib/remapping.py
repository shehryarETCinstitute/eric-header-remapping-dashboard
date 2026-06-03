"""Header remapping logic (Step 1)."""

from __future__ import annotations

import re

import pandas as pd

IGNORE_HEADERS = {
    "ID",
    "Method",
    "Block Address",
    "Block Lon",
    "Block Lat",
    "ID_2",
}


def load_file(uploaded_file) -> pd.DataFrame:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file, low_memory=False)

    if file_name.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(uploaded_file)

    raise ValueError(
        "Unsupported file type. Please upload a CSV, XLSX, or XLSM file."
    )


def exact_bracket_key(header: str) -> str | None:
    match = re.search(r"(Q\d+[a-zA-Z]?\[\d+\])", str(header))
    return match.group(1) if match else None


def base_letter_key(header: str) -> str | None:
    match = re.search(r"(Q\d+[a-zA-Z]+)", str(header))
    return match.group(1) if match else None


def broad_q_key(header: str) -> str | None:
    match = re.search(r"(Q\d+)", str(header))
    return match.group(1) if match else None


def has_brackets(header: str) -> bool:
    return bool(re.search(r"\[\d+\]", str(header)))


def has_dash_pattern(header: str) -> bool:
    return bool(re.search(r"Q\d+[a-zA-Z]?-\d+", str(header)))


def dash_keys(header: str) -> list[str]:
    match = re.search(r"(Q\d+[a-zA-Z]?)-(\d+)", str(header))

    if not match:
        return []

    base = match.group(1)
    number = match.group(2)
    base_question = re.search(r"(Q\d+)", base)
    question_only = base_question.group(1) if base_question else base

    return [
        f"{base}x{number}",
        f"{question_only}x99",
        f"{base}{number}",
    ]


def remap_headers(
    maps_df: pd.DataFrame,
    key_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    maps_df = maps_df.copy()

    maps_headers = list(maps_df.columns)
    key_headers = list(key_df.columns)

    used_key_headers: set[str] = set()
    replacement_log: list[dict] = []
    unmatched: list[dict] = []
    new_columns: list[str] = []

    for old_header in maps_headers:
        matched = False
        old_text = str(old_header).strip()

        if old_text in IGNORE_HEADERS:
            unmatched.append({
                "Original Header": old_header,
                "Reason": "Ignored",
            })
            new_columns.append(old_header)
            continue

        if old_text.upper() == "ZIP":
            for candidate in key_headers:
                candidate_text = str(candidate)

                if candidate in used_key_headers:
                    continue

                if (
                    "Validation[03]" in candidate_text
                    and "[Zip Code:" in candidate_text
                ):
                    replacement_log.append({
                        "Original Header": old_header,
                        "Replacement Header": candidate,
                        "Match Type": "ZIP Validation Match",
                    })
                    new_columns.append(candidate)
                    used_key_headers.add(candidate)
                    matched = True
                    break

        if not matched and old_text.upper() == "WARD":
            for candidate in key_headers:
                candidate_text = str(candidate)

                if candidate in used_key_headers:
                    continue

                if candidate_text.startswith("Ward[L]"):
                    replacement_log.append({
                        "Original Header": old_header,
                        "Replacement Header": candidate,
                        "Match Type": "Ward Match",
                    })
                    new_columns.append(candidate)
                    used_key_headers.add(candidate)
                    matched = True
                    break

        bracket_key = exact_bracket_key(old_header)

        if bracket_key and not matched:
            for candidate in key_headers:
                if candidate in used_key_headers:
                    continue

                if bracket_key in str(candidate):
                    replacement_log.append({
                        "Original Header": old_header,
                        "Replacement Header": candidate,
                        "Match Type": "Exact Bracket Match",
                    })
                    new_columns.append(candidate)
                    used_key_headers.add(candidate)
                    matched = True
                    break

        if not matched:
            for dash_key in dash_keys(old_header):
                for candidate in key_headers:
                    if candidate in used_key_headers:
                        continue

                    if dash_key in str(candidate):
                        replacement_log.append({
                            "Original Header": old_header,
                            "Replacement Header": candidate,
                            "Match Type": f"Dash Match ({dash_key})",
                        })
                        new_columns.append(candidate)
                        used_key_headers.add(candidate)
                        matched = True
                        break

                if matched:
                    break

        if not matched and has_dash_pattern(old_header):
            unmatched.append({
                "Original Header": old_header,
                "Reason": "Dash Pattern With No Match",
            })
            new_columns.append(old_header)
            continue

        if not matched and not has_brackets(old_header):
            letter_key = base_letter_key(old_header)

            if letter_key:
                for candidate in key_headers:
                    if candidate in used_key_headers:
                        continue

                    if str(candidate).startswith(letter_key):
                        replacement_log.append({
                            "Original Header": old_header,
                            "Replacement Header": candidate,
                            "Match Type": "Letter Fallback",
                        })
                        new_columns.append(candidate)
                        used_key_headers.add(candidate)
                        matched = True
                        break

        if not matched and not has_brackets(old_header):
            question_key = broad_q_key(old_header)

            skip_broad_match = any([
                "allocated" in old_text.lower(),
                "$100" in old_text.lower(),
                "yes" in old_text.lower(),
                "no" in old_text.lower(),
            ])

            if question_key and not skip_broad_match:
                for candidate in key_headers:
                    candidate_text = str(candidate)

                    if candidate in used_key_headers:
                        continue

                    if "[" not in candidate_text:
                        continue

                    if candidate_text.startswith(question_key):
                        replacement_log.append({
                            "Original Header": old_header,
                            "Replacement Header": candidate,
                            "Match Type": "Broad Q Fallback",
                        })
                        new_columns.append(candidate)
                        used_key_headers.add(candidate)
                        matched = True
                        break

        if not matched:
            unmatched.append({
                "Original Header": old_header,
                "Reason": "No Match Found",
            })
            new_columns.append(old_header)

    maps_df.columns = new_columns

    replaced_df = pd.DataFrame(
        replacement_log,
        columns=[
            "Original Header",
            "Replacement Header",
            "Match Type",
        ],
    )

    unmatched_df = pd.DataFrame(
        unmatched,
        columns=["Original Header", "Reason"],
    )

    return maps_df, replaced_df, unmatched_df
