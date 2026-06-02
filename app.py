import re
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="Header Remapping Dashboard",
    layout="wide"
)

st.title("Header Remapping Dashboard")

st.write(
    "Upload the survey file that needs new headers and the key file "
    "that contains the replacement headers."
)

# =========================================================
# FILE LOADING
# =========================================================

def load_file(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file, low_memory=False)

    elif file_name.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(uploaded_file)

    else:
        raise ValueError(
            "Unsupported file type. Please upload a CSV, XLSX, or XLSM file."
        )

# =========================================================
# IGNORE HEADERS
# =========================================================

IGNORE_HEADERS = {
    "ID",
    "Method",
    "Block Address",
    "Block Lon",
    "Block Lat",
    "ID_2"
}

# =========================================================
# HEADER-MATCHING HELPER FUNCTIONS
# =========================================================

def exact_bracket_key(header):

    match = re.search(
        r"(Q\d+[a-zA-Z]?\[\d+\])",
        str(header)
    )

    return match.group(1) if match else None


def base_letter_key(header):

    match = re.search(
        r"(Q\d+[a-zA-Z]+)",
        str(header)
    )

    return match.group(1) if match else None


def broad_q_key(header):

    match = re.search(
        r"(Q\d+)",
        str(header)
    )

    return match.group(1) if match else None


def has_brackets(header):

    return bool(
        re.search(r"\[\d+\]", str(header))
    )


def has_dash_pattern(header):

    return bool(
        re.search(r"Q\d+[a-zA-Z]?-\d+", str(header))
    )


def dash_keys(header):

    match = re.search(
        r"(Q\d+[a-zA-Z]?)-(\d+)",
        str(header)
    )

    if not match:
        return []

    base = match.group(1)
    number = match.group(2)

    base_question = re.search(r"(Q\d+)", base)

    if base_question:
        question_only = base_question.group(1)
    else:
        question_only = base

    return [
        # Primary:
        # Q23-8 -> Q23x8
        f"{base}x{number}",

        # Secondary:
        # Q23-8 -> Q23x99
        f"{question_only}x99",

        # Third fallback:
        # Q23-8 -> Q238
        f"{base}{number}"
    ]

# =========================================================
# MAIN REMAPPING FUNCTION
# =========================================================

def remap_headers(maps_df, key_df):

    maps_df = maps_df.copy()

    maps_headers = list(maps_df.columns)
    key_headers = list(key_df.columns)

    used_key_headers = set()

    replacement_log = []
    unmatched = []
    new_columns = []

    for old_header in maps_headers:

        matched = False
        old_text = str(old_header).strip()

        # -------------------------------------------------
        # IGNORE SELECTED HEADERS
        # -------------------------------------------------

        if old_text in IGNORE_HEADERS:

            unmatched.append({
                "Original Header": old_header,
                "Reason": "Ignored"
            })

            new_columns.append(old_header)

            continue

        # -------------------------------------------------
        # SPECIAL MATCH: ZIP
        # -------------------------------------------------

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
                        "Match Type": "ZIP Validation Match"
                    })

                    new_columns.append(candidate)
                    used_key_headers.add(candidate)
                    matched = True

                    break

        # -------------------------------------------------
        # SPECIAL MATCH: WARD
        # -------------------------------------------------

        if not matched and old_text.upper() == "WARD":

            for candidate in key_headers:

                candidate_text = str(candidate)

                if candidate in used_key_headers:
                    continue

                if candidate_text.startswith("Ward[L]"):

                    replacement_log.append({
                        "Original Header": old_header,
                        "Replacement Header": candidate,
                        "Match Type": "Ward Match"
                    })

                    new_columns.append(candidate)
                    used_key_headers.add(candidate)
                    matched = True

                    break

        # -------------------------------------------------
        # PASS 1: EXACT BRACKET MATCH
        # -------------------------------------------------

        bracket_key = exact_bracket_key(old_header)

        if bracket_key and not matched:

            for candidate in key_headers:

                candidate_text = str(candidate)

                if candidate in used_key_headers:
                    continue

                if bracket_key in candidate_text:

                    replacement_log.append({
                        "Original Header": old_header,
                        "Replacement Header": candidate,
                        "Match Type": "Exact Bracket Match"
                    })

                    new_columns.append(candidate)
                    used_key_headers.add(candidate)
                    matched = True

                    break

        # -------------------------------------------------
        # PASS 2: DASH MATCH
        # -------------------------------------------------

        if not matched:

            for dash_key in dash_keys(old_header):

                for candidate in key_headers:

                    candidate_text = str(candidate)

                    if candidate in used_key_headers:
                        continue

                    if dash_key in candidate_text:

                        replacement_log.append({
                            "Original Header": old_header,
                            "Replacement Header": candidate,
                            "Match Type": f"Dash Match ({dash_key})"
                        })

                        new_columns.append(candidate)
                        used_key_headers.add(candidate)
                        matched = True

                        break

                if matched:
                    break

        # -------------------------------------------------
        # STOP BAD FALLBACKS FOR DASH QUESTIONS
        # -------------------------------------------------

        if not matched and has_dash_pattern(old_header):

            unmatched.append({
                "Original Header": old_header,
                "Reason": "Dash Pattern With No Match"
            })

            new_columns.append(old_header)

            continue

        # -------------------------------------------------
        # PASS 3: LETTER FALLBACK
        # -------------------------------------------------

        if not matched and not has_brackets(old_header):

            letter_key = base_letter_key(old_header)

            if letter_key:

                for candidate in key_headers:

                    candidate_text = str(candidate)

                    if candidate in used_key_headers:
                        continue

                    if candidate_text.startswith(letter_key):

                        replacement_log.append({
                            "Original Header": old_header,
                            "Replacement Header": candidate,
                            "Match Type": "Letter Fallback"
                        })

                        new_columns.append(candidate)
                        used_key_headers.add(candidate)
                        matched = True

                        break

        # -------------------------------------------------
        # PASS 4: BROAD QUESTION FALLBACK
        # -------------------------------------------------

        if not matched and not has_brackets(old_header):

            question_key = broad_q_key(old_header)

            skip_broad_match = any([
                "allocated" in old_text.lower(),
                "$100" in old_text.lower(),
                "yes" in old_text.lower(),
                "no" in old_text.lower()
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
                            "Match Type": "Broad Q Fallback"
                        })

                        new_columns.append(candidate)
                        used_key_headers.add(candidate)
                        matched = True

                        break

        # -------------------------------------------------
        # NO MATCH
        # -------------------------------------------------

        if not matched:

            unmatched.append({
                "Original Header": old_header,
                "Reason": "No Match Found"
            })

            new_columns.append(old_header)

    maps_df.columns = new_columns

    replaced_df = pd.DataFrame(
        replacement_log,
        columns=[
            "Original Header",
            "Replacement Header",
            "Match Type"
        ]
    )

    unmatched_df = pd.DataFrame(
        unmatched,
        columns=[
            "Original Header",
            "Reason"
        ]
    )

    return maps_df, replaced_df, unmatched_df

# =========================================================
# FILE UPLOADS
# =========================================================

mapping_file = st.file_uploader(
    "Upload the file that needs mapping",
    type=["csv", "xlsx", "xlsm"]
)

key_file = st.file_uploader(
    "Upload the key file",
    type=["csv", "xlsx", "xlsm"]
)

# =========================================================
# CLEAR OLD RESULTS WHEN NEW FILES ARE UPLOADED
# =========================================================

if mapping_file is not None and key_file is not None:

    current_files = (
        mapping_file.name,
        key_file.name
    )

    if st.session_state.get("current_files") != current_files:

        st.session_state["current_files"] = current_files
        st.session_state["results"] = None

# =========================================================
# LOAD AND PREVIEW FILES
# =========================================================

if mapping_file is not None and key_file is not None:

    try:
        maps_df = load_file(mapping_file)
        key_df = load_file(key_file)

        st.success("Both files were loaded successfully.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("File That Needs Mapping")
            st.write(f"**File:** {mapping_file.name}")
            st.write(f"**Rows:** {len(maps_df):,}")
            st.write(f"**Columns:** {len(maps_df.columns):,}")

        with col2:
            st.subheader("Key File")
            st.write(f"**File:** {key_file.name}")
            st.write(f"**Rows:** {len(key_df):,}")
            st.write(f"**Columns:** {len(key_df.columns):,}")

        with st.expander("Preview Uploaded Files"):

            preview_col1, preview_col2 = st.columns(2)

            with preview_col1:
                st.write("**File That Needs Mapping**")
                st.dataframe(
                    maps_df.head(10),
                    use_container_width=True
                )

            with preview_col2:
                st.write("**Key File**")
                st.dataframe(
                    key_df.head(10),
                    use_container_width=True
                )

        # =================================================
        # RUN BUTTON
        # =================================================

        if st.button(
            "Run Header Remapping",
            type="primary"
        ):

            with st.spinner("Remapping headers..."):

                remapped_df, replaced_df, unmatched_df = remap_headers(
                    maps_df,
                    key_df
                )

                st.session_state["results"] = {
                    "remapped_df": remapped_df,
                    "replaced_df": replaced_df,
                    "unmatched_df": unmatched_df
                }

    except Exception as error:

        st.error(f"Unable to load the files: {error}")

# =========================================================
# RESULTS
# =========================================================

results = st.session_state.get("results")

if results is not None:

    remapped_df = results["remapped_df"]
    replaced_df = results["replaced_df"]
    unmatched_df = results["unmatched_df"]

    ignored_count = (
        unmatched_df["Reason"]
        .eq("Ignored")
        .sum()
    )

    unmatched_count = len(unmatched_df) - ignored_count

    st.divider()
    st.header("Remapping Results")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Total Headers",
        f"{len(remapped_df.columns):,}"
    )

    metric2.metric(
        "Replaced Headers",
        f"{len(replaced_df):,}"
    )

    metric3.metric(
        "Unmatched Headers",
        f"{unmatched_count:,}"
    )

    metric4.metric(
        "Ignored Headers",
        f"{ignored_count:,}"
    )

    tab1, tab2, tab3 = st.tabs([
        "Unmatched Headers",
        "Replaced Headers",
        "Remapped Survey Preview"
    ])

    with tab1:

        if unmatched_df.empty:
            st.success("Every header was matched.")
        else:
            st.dataframe(
                unmatched_df,
                use_container_width=True
            )

    with tab2:

        st.dataframe(
            replaced_df,
            use_container_width=True
        )

    with tab3:

        st.dataframe(
            remapped_df.head(25),
            use_container_width=True
        )

    # =====================================================
    # DOWNLOAD BUTTONS
    # =====================================================

    st.subheader("Download Output Files")

    safe_name = (
        Path(mapping_file.name)
        .stem
        .replace(" ", "_")
    )

    download_col1, download_col2, download_col3 = st.columns(3)

    with download_col1:

        st.download_button(
            label="Download Remapped Survey",
            data=remapped_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_name}_remapped_output.csv",
            mime="text/csv"
        )

    with download_col2:

        st.download_button(
            label="Download Replaced Headers Log",
            data=replaced_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_name}_replaced_headers.csv",
            mime="text/csv"
        )

    with download_col3:

        st.download_button(
            label="Download Unmatched Headers Log",
            data=unmatched_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_name}_unmatched_headers.csv",
            mime="text/csv"
        )