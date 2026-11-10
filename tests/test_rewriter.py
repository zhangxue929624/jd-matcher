"""rewriter模块测试：事实提取、事实保持校验、改写流程（mock）。"""
from unittest.mock import MagicMock

import pytest

from src.analyzer import AnalysisError
from src.llm_client import LLMError
from src.rewriter import check_facts_preserved, extract_facts, rewrite_resume

ORIGINAL = "2023年在ABC公司实习，用Python处理数据，效率提升30%，掌握SQL"


def test_extract_facts_finds_years_numbers_terms():
    facts = extract_facts(ORIGINAL)
    assert "2023" in facts
    assert "30%" in facts
    assert "ABC" in facts
    assert "Python" in facts


def test_facts_preserved_passes_when_all_kept():
    rewritten = "2023年于ABC公司实习，使用Python处理数据，效率提升30%，熟练掌握SQL"
    assert check_facts_preserved(ORIGINAL, rewritten) == []


def test_facts_preserved_flags_dropped_year():
    rewritten = "在某公司实习，使用Python处理数据，效率提升30%，掌握SQL"
    warnings = check_facts_preserved(ORIGINAL, rewritten)
    assert any("2023" in w for w in warnings)


def test_facts_preserved_flags_dropped_number():
    rewritten = "2023年在ABC公司实习，用Python处理数据，掌握SQL"
    warnings = check_facts_preserved(ORIGINAL, rewritten)
    assert any("30%" in w for w in warnings)


def test_rewrite_success():
    client = MagicMock()
    client.chat.return_value = "2023年在ABC公司实习，用Python处理数据，效率提升30%，精通SQL"
    result = rewrite_resume(ORIGINAL, ["缺Spark"], client)
    assert result.warnings == []


def test_rewrite_empty_input_rejected():
    with pytest.raises(AnalysisError, match="不能为空"):
        rewrite_resume("  ", ["缺Spark"], MagicMock())


def test_rewrite_empty_llm_output_rejected():
    client = MagicMock()
    client.chat.return_value = "   "
    with pytest.raises(AnalysisError, match="空改写稿"):
        rewrite_resume(ORIGINAL, ["缺Spark"], client)


def test_rewrite_api_failure_propagates():
    client = MagicMock()
    client.chat.side_effect = LLMError("模型响应超时，请稍后重试")
    with pytest.raises(AnalysisError, match="超时"):
        rewrite_resume(ORIGINAL, ["缺Spark"], client)
