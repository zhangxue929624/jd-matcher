"""简历改写：LLM生成改写稿，Python校验事实未被篡改。

核心约束：改写只能优化表达，不得编造或改动事实（年份、数字、公司/学校名）。
"""
import re
from dataclasses import dataclass, field

from .analyzer import AnalysisError
from .llm_client import LLMClient, LLMError
from .prompts import REWRITE_SYSTEM, build_rewrite_prompt


@dataclass
class RewriteOutput:
    rewritten: str
    warnings: list[str] = field(default_factory=list)


def extract_facts(text: str) -> set[str]:
    """从文本提取可核验事实：年份、含数字的量化表述、大写缩写词。"""
    facts: set[str] = set()
    facts.update(re.findall(r"(?:19|20)\d{2}", text))                    # 年份
    facts.update(re.findall(r"\d+(?:\.\d+)?%?", text))                   # 数字/百分比
    facts.update(re.findall(r"(?<![A-Za-z0-9])[A-Z][A-Za-z0-9+#.]{1,}(?![A-Za-z0-9])", text))  # 专有名词缩写
    return facts


def check_facts_preserved(original: str, rewritten: str) -> list[str]:
    """校验：原简历中的事实必须出现在改写稿中，缺失则报警告。

    返回警告列表（不拦截，供人工核实）。
    局限：无法发现"数字被改成别的值"，只能发现"数字消失了"。
    """
    warnings: list[str] = []
    rewritten_lower = rewritten.lower()
    for fact in sorted(extract_facts(original)):
        if fact.lower() not in rewritten_lower:
            warnings.append(f"事实缺失：原简历中的 '{fact}' 未出现在改写稿中，请核实")
    return warnings


def rewrite_resume(resume_text: str, missing: list[str], client: LLMClient) -> RewriteOutput:
    """完整流程：LLM改写 → 事实保持校验。"""
    if not resume_text.strip():
        raise AnalysisError("简历内容不能为空")
    try:
        rewritten = client.chat(REWRITE_SYSTEM, build_rewrite_prompt(resume_text, missing), json_mode=False)
    except LLMError as e:
        raise AnalysisError(str(e)) from e
    rewritten = rewritten.strip()
    if not rewritten:
        raise AnalysisError("模型返回了空改写稿，请重试")
    return RewriteOutput(
        rewritten=rewritten,
        warnings=check_facts_preserved(resume_text, rewritten),
    )
