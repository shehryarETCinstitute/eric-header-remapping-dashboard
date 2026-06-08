"""Build codebook Excel sheets from LimeSurvey JSON or LSS exports."""

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

CODEBOOK_SHEET_ORDER = ("Groups", "Questions", "Subquestions", "Answers")


def readable_type(raw_type: Any, theme_name: Any = "") -> str:
    raw_type = str(raw_type or "").strip()
    theme_name = str(theme_name or "").strip()

    base = TYPE_LABELS.get(raw_type, f"Unknown ({raw_type})" if raw_type else "Unknown")

    if theme_name:
        return f"{base} ({theme_name})"

    return base


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


def first_value(record: dict, possible_keys: list[str], default: Any = "") -> Any:
    for key in possible_keys:
        value = record.get(key)

        if value is not None and str(value).strip() != "":
            return value

    return default


def question_sort_key(qcode: Any) -> int:
    match = re.match(r"Q(\d+)", str(qcode or ""), flags=re.IGNORECASE)

    if match:
        return int(match.group(1))

    return 999999


def group_sort_key(group_order: Any) -> int:
    try:
        return int(float(str(group_order).strip()))
    except (TypeError, ValueError):
        return 999999


def _sort_groups_df(groups_df: pd.DataFrame) -> pd.DataFrame:
    if groups_df.empty:
        return groups_df

    groups_df = groups_df.copy()
    groups_df["sort_order"] = groups_df["Group Order"].apply(group_sort_key)

    return (
        groups_df.drop_duplicates()
        .sort_values(by=["sort_order", "Question Group"])
        .drop(columns=["sort_order"])
    )


def _sort_by_group_and_question(
    df: pd.DataFrame,
    qgroup_order_lookup: dict[str, Any],
    extra_sort_columns: list[str],
) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["group_sort_order"] = (
        df["Question Code"].map(qgroup_order_lookup).apply(group_sort_key)
    )
    df["question_sort_order"] = df["Question Code"].apply(question_sort_key)

    return (
        df.drop_duplicates()
        .sort_values(
            by=["group_sort_order", "question_sort_order", *extra_sort_columns],
        )
        .drop(columns=["group_sort_order", "question_sort_order"])
    )


def build_codebook_sheets(data: dict) -> dict[str, pd.DataFrame]:
    """Return Groups, Questions, Subquestions, and Answers from JSON data."""

    groups = data.get("groups", [])
    questions = data.get("questions", [])
    subquestions = data.get("subquestions", [])
    answers = data.get("answers", [])

    group_name_lookup: dict[Any, str] = {}
    group_order_lookup: dict[Any, Any] = {}

    for group in groups:
        group_id = first_value(group, ["gid", "group_id", "id"])
        group_name = first_value(
            group,
            ["group_name_en", "group_name", "name_en", "name", "title"],
        )
        group_order = first_value(
            group,
            ["group_order", "group_order_id", "order", "sort_order"],
            default="",
        )

        group_name_lookup[group_id] = str(group_name).strip()
        group_order_lookup[group_id] = group_order

    qid_lookup: dict[Any, str] = {}
    qtype_lookup: dict[str, str] = {}
    qgroup_lookup: dict[str, str] = {}
    qgroup_order_lookup: dict[str, Any] = {}

    for question in questions:
        variable = str(question.get("title", "")).strip()
        qid = question.get("qid")
        group_id = first_value(question, ["gid", "group_id"])
        raw_type = str(question.get("type", "")).strip()
        theme_name = str(question.get("question_theme_name", "")).strip()

        qid_lookup[qid] = variable
        qtype_lookup[variable] = readable_type(raw_type, theme_name)
        qgroup_lookup[variable] = group_name_lookup.get(group_id, "")
        qgroup_order_lookup[variable] = group_order_lookup.get(group_id, "")

    group_rows = []

    for group in groups:
        group_id = first_value(group, ["gid", "group_id", "id"])

        group_rows.append({
            "Group Order": group_order_lookup.get(group_id, ""),
            "Question Group": group_name_lookup.get(group_id, ""),
        })

    groups_df = _sort_groups_df(
        pd.DataFrame(group_rows, columns=["Group Order", "Question Group"]),
    )

    question_rows = []

    for question in questions:
        variable = str(question.get("title", "")).strip()
        question_text = first_value(
            question,
            ["question_en", "question", "question_es"],
        )

        question_rows.append({
            "Question Group": qgroup_lookup.get(variable, ""),
            "Question Code": variable,
            "Question Text": clean_text(question_text),
            "Question Type": qtype_lookup.get(variable, ""),
        })

    questions_df = _sort_by_group_and_question(
        pd.DataFrame(
            question_rows,
            columns=[
                "Question Group",
                "Question Code",
                "Question Text",
                "Question Type",
            ],
        ),
        qgroup_order_lookup,
        ["Question Code"],
    )

    subquestion_rows = []

    for subquestion in subquestions:
        parent_variable = qid_lookup.get(subquestion.get("parent_qid"), "")
        subquestion_text = first_value(
            subquestion,
            ["question_en", "question", "question_es"],
        )

        subquestion_rows.append({
            "Question Group": qgroup_lookup.get(parent_variable, ""),
            "Question Code": parent_variable,
            "Subquestion Code": str(subquestion.get("title", "")).strip(),
            "Subquestion Text": clean_text(subquestion_text),
        })

    subquestions_df = _sort_by_group_and_question(
        pd.DataFrame(
            subquestion_rows,
            columns=[
                "Question Group",
                "Question Code",
                "Subquestion Code",
                "Subquestion Text",
            ],
        ),
        qgroup_order_lookup,
        ["Question Code", "Subquestion Code"],
    )

    answer_rows = []

    for answer in answers:
        parent_variable = qid_lookup.get(answer.get("qid"), "")
        answer_text = first_value(
            answer,
            ["answer_en", "answer", "answer_es"],
        )

        answer_rows.append({
            "Question Group": qgroup_lookup.get(parent_variable, ""),
            "Question Code": parent_variable,
            "Answer Code": str(answer.get("code", "")).strip(),
            "Answer Text": clean_text(answer_text),
        })

    answers_df = _sort_by_group_and_question(
        pd.DataFrame(
            answer_rows,
            columns=[
                "Question Group",
                "Question Code",
                "Answer Code",
                "Answer Text",
            ],
        ),
        qgroup_order_lookup,
        ["Question Code", "Answer Code"],
    )

    return {
        "Groups": groups_df,
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
