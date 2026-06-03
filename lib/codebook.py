"""Build codebook Excel sheets from a LimeSurvey full JSON export."""

from __future__ import annotations

import html
import json
import re
from typing import Any

import pandas as pd

TYPE_LABELS = {
    "S": "Short free text",
    "T": "Long free text",
    "N": "Numerical",
    "Q": "Multiple short text",
    "K": "Multiple numerical",
    "M": "Multiple choice",
    "L": "List radio",
    "F": "Array",
    "*": "Equation",
    "!": "Dropdown",
    "Y": "Yes/No",
    "R": "Ranking",
    "X": "Text display",
}


def readable_type(raw_type: str) -> str:
    raw_type = str(raw_type).strip()

    if raw_type in TYPE_LABELS:
        return TYPE_LABELS[raw_type]

    if raw_type:
        return f"Unknown {raw_type}"

    return "Unknown"


def clean_text(text: Any) -> str:
    text = str(text or "")

    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.split(
        r"\$\(document\)\.ready\s*\(",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    text = re.sub(
        r"(?:#[A-Za-z0-9_.\-{}]+|\.[A-Za-z0-9_.\-{}]+)"
        r"(?:\s+[A-Za-z0-9_.#\-{}]+)*"
        r"\s*\{[^{}]*\}",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\{[^{}]*(?:"
        r"\bif\s*\(|"
        r"\bis_empty\s*\(|"
        r"\bself\.|"
        r"\bSAVEDID\b|"
        r"\bNAOK\b"
        r")[^{}]*\}",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"\b(?:display|color|background-color|font-weight|"
        r"text-align|margin|margin-bottom|padding|width|height)"
        r"\s*:\s*[^;{}]+;",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def question_sort_key(qcode: str) -> int:
    match = re.match(r"Q(\d+)", str(qcode))

    if match:
        return int(match.group(1))

    return 999999


def _sort_and_dedupe(
    df: pd.DataFrame,
    sort_columns: list[str],
) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["sort_order"] = df["Question Code"].apply(question_sort_key)

    df = (
        df.drop_duplicates()
        .sort_values(by=["sort_order", *sort_columns])
        .drop(columns=["sort_order"])
    )

    return df


def build_codebook_sheets(data: dict) -> dict[str, pd.DataFrame]:
    """Return Questions, Subquestions, and Answers DataFrames from JSON data."""

    questions = data.get("questions", [])
    subquestions = data.get("subquestions", [])
    answers = data.get("answers", [])

    qid_lookup: dict[Any, str] = {}
    qtype_lookup: dict[str, str] = {}

    for q in questions:
        variable = str(q.get("title", "")).strip()
        qid_lookup[q.get("qid")] = variable
        qtype_lookup[variable] = readable_type(q.get("type", ""))

    question_rows = []

    for q in questions:
        variable = str(q.get("title", "")).strip()

        question_rows.append({
            "Question Code": variable,
            "Question Text": clean_text(q.get("question_en", "")),
            "Question Type": qtype_lookup.get(variable, ""),
        })

    questions_df = pd.DataFrame(
        question_rows,
        columns=["Question Code", "Question Text", "Question Type"],
    )

    questions_df = _sort_and_dedupe(questions_df, ["Question Code"])

    subquestion_rows = []

    for sq in subquestions:
        parent_variable = qid_lookup.get(sq.get("parent_qid"), "")

        subquestion_rows.append({
            "Question Code": parent_variable,
            "Subquestion Code": str(sq.get("title", "")).strip(),
            "Subquestion Text": clean_text(sq.get("question_en", "")),
        })

    subquestions_df = pd.DataFrame(
        subquestion_rows,
        columns=[
            "Question Code",
            "Subquestion Code",
            "Subquestion Text",
        ],
    )

    subquestions_df = _sort_and_dedupe(
        subquestions_df,
        ["Question Code", "Subquestion Code"],
    )

    answer_rows = []

    for ans in answers:
        parent_variable = qid_lookup.get(ans.get("qid"), "")

        answer_rows.append({
            "Question Code": parent_variable,
            "Answer Code": str(ans.get("code", "")).strip(),
            "Answer Text": clean_text(ans.get("answer_en", "")),
        })

    answers_df = pd.DataFrame(
        answer_rows,
        columns=["Question Code", "Answer Code", "Answer Text"],
    )

    answers_df = _sort_and_dedupe(
        answers_df,
        ["Question Code", "Answer Code"],
    )

    return {
        "Questions": questions_df,
        "Subquestions": subquestions_df,
        "Answers": answers_df,
    }


def load_json_data(uploaded_file) -> dict:
    raw = uploaded_file.read()

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    return json.loads(raw)


def survey_id_from_data(data: dict) -> str | None:
    survey = data.get("survey", {})

    sid = survey.get("sid")

    if sid is not None:
        return str(sid)

    return None
