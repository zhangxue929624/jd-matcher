"""skills模块测试：归一化、集合运算、LLM抽取（mock）。"""
import json
from unittest.mock import MagicMock

import pytest

from src.analyzer import AnalysisError
from src.skills import analyze_skill_gap, compute_gap, extract_skills, normalize_skills


def test_normalize_dedupes_and_lowercases():
    assert normalize_skills([" Python ", "python", "SQL", " sql", ""]) == ["python", "sql"]


def test_normalize_keeps_order():
    assert normalize_skills(["B", "A", "C"]) == ["b", "a", "c"]


def test_compute_gap_intersection_and_difference():
    gap = compute_gap(["Python", "SQL", "Spark"], ["python", "Excel"])
    assert gap.matched == ["python"]
    assert gap.missing == ["sql", "spark"]


def test_compute_gap_empty_jd():
    gap = compute_gap([], ["python"])
    assert gap.matched == [] and gap.missing == []


def test_compute_gap_full_match():
    gap = compute_gap(["python", "sql"], ["Python", "SQL", "Excel"])
    assert gap.missing == []


def _mock_client(responses: list[str]) -> MagicMock:
    client = MagicMock()
    client.chat.side_effect = responses
    return client


def test_extract_skills_success():
    client = _mock_client([json.dumps({"skills": ["Python", "SQL"]})])
    assert extract_skills("要求Python和SQL", "JD", client) == ["python", "sql"]


def test_extract_skills_bad_format_rejected():
    client = _mock_client([json.dumps({"skills": "Python"})])
    with pytest.raises(AnalysisError, match="格式错误"):
        extract_skills("text", "JD", client)


def test_analyze_skill_gap_calls_llm_twice():
    client = _mock_client([
        json.dumps({"skills": ["Python", "Spark"]}),   # JD
        json.dumps({"skills": ["python"]}),            # 简历
    ])
    gap = analyze_skill_gap("jd", "resume", client)
    assert client.chat.call_count == 2
    assert gap.matched == ["python"]
    assert gap.missing == ["spark"]
