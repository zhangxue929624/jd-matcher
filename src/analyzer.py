"""分析器：编排完整业务流程（输入校验 → LLM调用 → 解析 → 输出校验）。"""
import json
from dataclasses import dataclass, field

from .llm_client import LLMClient, LLMError
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .validator import check_grounding, validate_schema


class AnalysisError(Exception):
    """分析流程失败的统一异常。"""


@dataclass
class AnalysisOutput:
    """最终交付给界面层的结果。"""
    score: int
    matched: list[str]
    missing: list[str]
    suggestions: list[str]
    warnings: list[str] = field(default_factory=list)


def _parse_json(text: str) -> dict:
    """从LLM返回文本中解析JSON，容忍markdown代码块包裹。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        result = json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        raise AnalysisError(f"模型返回的内容不是合法JSON：{e}") from e
    if not isinstance(result, dict):
        raise AnalysisError("模型返回的JSON不是对象结构")
    return result


def analyze(jd_text: str, resume_text: str, client: LLMClient) -> AnalysisOutput:
    """核心业务流程入口。

    流程：输入校验 → LLM调用 → JSON解析 → Schema校验 → 防幻觉检查
    任何一步失败都抛出带可读信息的异常，由界面层展示。
    """
    if not jd_text.strip():
        raise AnalysisError("JD内容不能为空")
    if not resume_text.strip():
        raise AnalysisError("简历内容不能为空")

    try:
        raw_text = client.chat(SYSTEM_PROMPT, build_user_prompt(jd_text, resume_text))
    except LLMError as e:
        raise AnalysisError(str(e)) from e

    raw_json = _parse_json(raw_text)

    report = validate_schema(raw_json)
    if not report.ok:
        raise AnalysisError("模型输出未通过格式校验：" + "；".join(report.errors))

    warnings = check_grounding(raw_json, jd_text)
    return AnalysisOutput(
        score=raw_json["score"],
        matched=raw_json["matched"],
        missing=raw_json["missing"],
        suggestions=raw_json["suggestions"],
        warnings=warnings,
    )
