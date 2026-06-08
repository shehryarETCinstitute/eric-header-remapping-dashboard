"""Build codebook Excel sheets from a LimeSurvey LSS XML export."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Any

import pandas as pd

from lib.codebook import (
    clean_text,
    group_sort_key,
    question_sort_key,
    readable_type,
)


def safe_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def xml_section_rows(root: ET.Element, section_name: str) -> list[dict[str, str]]:
    section = root.find(section_name)

    if section is None:
        return []

    rows_element = section.find("rows")

    if rows_element is None:
        return []

    rows = []

    for row in rows_element.findall("row"):
        row_data = {}

        for child in row:
            row_data[child.tag] = safe_text(child.text)

        rows.append(row_data)

    return rows


def filter_old_format_rows(rows: list[dict[str, str]], language: str) -> list[dict[str, str]]:
    filtered_rows = []

    for row in rows:
        row_language = safe_text(row.get("language"))

        if not row_language or row_language == language:
            filtered_rows.append(row)

    return filtered_rows


def merge_localized_rows(
    base_rows: list[dict[str, str]],
    localization_rows: list[dict[str, str]],
    base_key: str,
    localization_key: str,
    localized_fields: list[str],
    language: str,
) -> list[dict[str, str]]:
    if not localization_rows:
        return filter_old_format_rows(base_rows, language)

    localization_lookup: dict[str, dict[str, str]] = {}

    for row in localization_rows:
        row_language = safe_text(row.get("language"))

        if row_language != language:
            continue

        lookup_id = safe_text(row.get(localization_key))

        if lookup_id:
            localization_lookup[lookup_id] = row

    merged_rows = []

    for base_row in base_rows:
        base_id = safe_text(base_row.get(base_key))
        localized_row = localization_lookup.get(base_id)

        if localized_row is None:
            continue

        merged_row = dict(base_row)

        for field in localized_fields:
            localized_value = safe_text(localized_row.get(field))

            if localized_value:
                merged_row[field] = localized_value
            elif field not in merged_row:
                merged_row[field] = ""

        merged_row["language"] = language
        merged_rows.append(merged_row)

    return merged_rows


def build_codebook_sheets_from_lss(
    uploaded_file,
    language: str = "en",
) -> dict[str, pd.DataFrame]:
    """Return Groups, Questions, Subquestions, and Answers from an LSS file."""

    raw = uploaded_file.read()

    if isinstance(raw, str):
        raw = raw.encode("utf-8")

    root = ET.parse(BytesIO(raw)).getroot()

    raw_groups = xml_section_rows(root, "groups")
    raw_questions = xml_section_rows(root, "questions")
    raw_subquestions = xml_section_rows(root, "subquestions")
    raw_answers = xml_section_rows(root, "answers")
    question_attributes = xml_section_rows(root, "question_attributes")
    group_l10ns = xml_section_rows(root, "group_l10ns")
    question_l10ns = xml_section_rows(root, "question_l10ns")
    answer_l10ns = xml_section_rows(root, "answer_l10ns")

    groups = merge_localized_rows(
        base_rows=raw_groups,
        localization_rows=group_l10ns,
        base_key="gid",
        localization_key="gid",
        localized_fields=["group_name", "description"],
        language=language,
    )

    questions = merge_localized_rows(
        base_rows=raw_questions,
        localization_rows=question_l10ns,
        base_key="qid",
        localization_key="qid",
        localized_fields=["question", "help"],
        language=language,
    )

    subquestions = merge_localized_rows(
        base_rows=raw_subquestions,
        localization_rows=question_l10ns,
        base_key="qid",
        localization_key="qid",
        localized_fields=["question", "help"],
        language=language,
    )

    answers = merge_localized_rows(
        base_rows=raw_answers,
        localization_rows=answer_l10ns,
        base_key="aid",
        localization_key="aid",
        localized_fields=["answer"],
        language=language,
    )

    template_lookup: dict[str, str] = {}

    for attribute in question_attributes:
        qid = safe_text(attribute.get("qid"))
        attribute_name = safe_text(attribute.get("attribute"))
        attribute_value = safe_text(attribute.get("value"))

        if attribute_name == "question_template":
            template_lookup[qid] = attribute_value

    group_name_lookup: dict[str, str] = {}
    group_order_lookup: dict[str, str] = {}

    for group in groups:
        group_id = safe_text(group.get("gid"))
        group_name_lookup[group_id] = safe_text(group.get("group_name"))
        group_order_lookup[group_id] = safe_text(group.get("group_order"))

    qid_lookup: dict[str, str] = {}
    qtype_lookup: dict[str, str] = {}
    qgroup_lookup: dict[str, str] = {}
    qgroup_order_lookup: dict[str, str] = {}

    for question in questions:
        variable = safe_text(question.get("title"))
        qid = safe_text(question.get("qid"))
        group_id = safe_text(question.get("gid"))
        raw_type = safe_text(question.get("type"))
        template_name = template_lookup.get(qid, "") or safe_text(
            question.get("question_theme_name"),
        )

        qid_lookup[qid] = variable
        qtype_lookup[variable] = readable_type(raw_type, template_name)
        qgroup_lookup[variable] = group_name_lookup.get(group_id, "")
        qgroup_order_lookup[variable] = group_order_lookup.get(group_id, "")

    group_rows = []

    for group in groups:
        group_id = safe_text(group.get("gid"))

        group_rows.append({
            "Group Order": group_order_lookup.get(group_id, ""),
            "Question Group": group_name_lookup.get(group_id, ""),
        })

    groups_df = pd.DataFrame(group_rows, columns=["Group Order", "Question Group"])

    if not groups_df.empty:
        groups_df["sort_order"] = groups_df["Group Order"].apply(group_sort_key)
        groups_df = (
            groups_df.drop_duplicates()
            .sort_values(by=["sort_order", "Question Group"])
            .drop(columns=["sort_order"])
        )

    question_rows = []

    for question in questions:
        variable = safe_text(question.get("title"))

        question_rows.append({
            "Question Group": qgroup_lookup.get(variable, ""),
            "Question Code": variable,
            "Question Text": clean_text(question.get("question")),
            "Question Type": qtype_lookup.get(variable, ""),
        })

    questions_df = pd.DataFrame(
        question_rows,
        columns=["Question Group", "Question Code", "Question Text", "Question Type"],
    )

    if not questions_df.empty:
        questions_df["group_sort_order"] = (
            questions_df["Question Code"].map(qgroup_order_lookup).apply(group_sort_key)
        )
        questions_df["question_sort_order"] = questions_df["Question Code"].apply(
            question_sort_key,
        )
        questions_df = (
            questions_df.drop_duplicates()
            .sort_values(
                by=["group_sort_order", "question_sort_order", "Question Code"],
            )
            .drop(columns=["group_sort_order", "question_sort_order"])
        )

    subquestion_rows = []

    for subquestion in subquestions:
        parent_qid = safe_text(subquestion.get("parent_qid"))
        parent_variable = qid_lookup.get(parent_qid, "")

        subquestion_rows.append({
            "Question Group": qgroup_lookup.get(parent_variable, ""),
            "Question Code": parent_variable,
            "Subquestion Code": safe_text(subquestion.get("title")),
            "Subquestion Text": clean_text(subquestion.get("question")),
        })

    subquestions_df = pd.DataFrame(
        subquestion_rows,
        columns=[
            "Question Group",
            "Question Code",
            "Subquestion Code",
            "Subquestion Text",
        ],
    )

    if not subquestions_df.empty:
        subquestions_df["group_sort_order"] = (
            subquestions_df["Question Code"].map(qgroup_order_lookup).apply(group_sort_key)
        )
        subquestions_df["question_sort_order"] = subquestions_df["Question Code"].apply(
            question_sort_key,
        )
        subquestions_df = (
            subquestions_df.drop_duplicates()
            .sort_values(
                by=[
                    "group_sort_order",
                    "question_sort_order",
                    "Question Code",
                    "Subquestion Code",
                ],
            )
            .drop(columns=["group_sort_order", "question_sort_order"])
        )

    answer_rows = []

    for answer in answers:
        qid = safe_text(answer.get("qid"))
        parent_variable = qid_lookup.get(qid, "")

        answer_rows.append({
            "Question Group": qgroup_lookup.get(parent_variable, ""),
            "Question Code": parent_variable,
            "Answer Code": safe_text(answer.get("code")),
            "Answer Text": clean_text(answer.get("answer")),
        })

    answers_df = pd.DataFrame(
        answer_rows,
        columns=["Question Group", "Question Code", "Answer Code", "Answer Text"],
    )

    if not answers_df.empty:
        answers_df["group_sort_order"] = (
            answers_df["Question Code"].map(qgroup_order_lookup).apply(group_sort_key)
        )
        answers_df["question_sort_order"] = answers_df["Question Code"].apply(
            question_sort_key,
        )
        answers_df = (
            answers_df.drop_duplicates()
            .sort_values(
                by=[
                    "group_sort_order",
                    "question_sort_order",
                    "Question Code",
                    "Answer Code",
                ],
            )
            .drop(columns=["group_sort_order", "question_sort_order"])
        )

    return {
        "Groups": groups_df,
        "Questions": questions_df,
        "Subquestions": subquestions_df,
        "Answers": answers_df,
    }
