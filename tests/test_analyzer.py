"""analyzer模块测试：mock LLM客户端，覆盖正常/异常/非法输出场景。"""
import json
from unittest.mock import MagicMock

import pytest

from src.analyzer import AnalysisError, _parse_json, analyze
from src.llm_client import LLMError

JD = "要求：熟悉Python，了解数据分析，有SQL经验"
RESUME = "3年Python开发经验，做过数据分析项目"

GOOD_LLM_RESPONSE = json.dumps({
    "score": 80,
    "matched": ["JD要求Python，简历有3年经验"],
    "missing": ["JD要求有SQL经验"],
    "suggestions": ["补充SQL", "量化成果", "突出项目"],
}, ensure_ascii=False)


def _mock_client(response: str) -> MagicMock:
    client = MagicMock()
    client.chat.return_value = response
    return client


def test_parse_plain_json():
    assert _parse_json('{"score": 80}') == {"score": 80}


def test_parse_json_in_markdown_block():
    text = '```json\n{"score": 80}\n```'
    assert _parse_json(text) == {"score": 80}


def test_parse_invalid_json_raises():
    with pytest.raises(AnalysisError, match="合法JSON"):
        _parse_json("这不是JSON")


def test_analyze_success():
    result = analyze(JD, RESUME, _mock_client(GOOD_LLM_RESPONSE))
    assert result.score == 80
    assert len(result.suggestions) == 3


def test_analyze_empty_input_rejected():
    with pytest.raises(AnalysisError, match="不能为空"):
        analyze("", RESUME, _mock_client(GOOD_LLM_RESPONSE))
    with pytest.raises(AnalysisError, match="不能为空"):
        analyze(JD, "  ", _mock_client(GOOD_LLM_RESPONSE))


def test_analyze_api_failure_propagates():
    client = MagicMock()
    client.chat.side_effect = LLMError("模型响应超时，请稍后重试")
    with pytest.raises(AnalysisError, match="超时"):
        analyze(JD, RESUME, client)


def test_analyze_invalid_llm_json_rejected():
    with pytest.raises(AnalysisError, match="合法JSON"):
        analyze(JD, RESUME, _mock_client("模型胡言乱语"))


def test_analyze_schema_violation_rejected():
    bad = json.dumps({"score": 150, "matched": [], "missing": [], "suggestions": []})
    with pytest.raises(AnalysisError, match="格式校验"):
        analyze(JD, RESUME, _mock_client(bad))


def test_analyze_grounding_warning_kept():
    response = json.dumps({
        "score": 60,
        "matched": ["Python经验"],
        "missing": ["JD要求精通CUDA"],
        "suggestions": ["a", "b", "c"],
    }, ensure_ascii=False)
    result = analyze(JD, RESUME, _mock_client(response))
    assert len(result.warnings) == 1
    assert "存疑" in result.warnings[0]
