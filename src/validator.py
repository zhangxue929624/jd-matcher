"""输出校验：JSON Schema校验 + 业务规则校验（防幻觉）。"""
import re

from pydantic import BaseModel, Field, ValidationError, field_validator


class AnalysisResult(BaseModel):
    """LLM输出的结构定义与硬性约束。"""

    score: int = Field(ge=0, le=100, description="匹配度评分")
    matched: list[str] = Field(min_length=1)
    missing: list[str] = Field(min_length=1)
    suggestions: list[str] = Field(min_length=3)

    @field_validator("matched", "missing", "suggestions")
    @classmethod
    def items_must_be_nonempty_strings(cls, v: list[str]) -> list[str]:
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("列表元素必须是非空字符串")
        return [item.strip() for item in v]


class ValidationReport:
    """校验结果：是否通过 + 问题列表。"""

    def __init__(self, ok: bool, errors: list[str], warnings: list[str]) -> None:
        self.ok = ok
        self.errors = errors
        self.warnings = warnings


def validate_schema(raw_json: dict) -> ValidationReport:
    """硬性校验：结构、类型、范围。不通过则整个输出不可用。"""
    try:
        AnalysisResult.model_validate(raw_json)
        return ValidationReport(ok=True, errors=[], warnings=[])
    except ValidationError as e:
        errors = [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()]
        return ValidationReport(ok=False, errors=errors, warnings=[])


def _is_grounded(item: str, jd_lower: str) -> bool:
    """判断单条missing是否在JD中有依据。

    规则（满足其一即认为有依据）：
    1. 条目中的英文/技术词（如 Spark、C++、SQL）出现在JD中
    2. 条目中文部分的任意4字滑窗出现在JD中
    """
    for token in re.findall(r"[A-Za-z][A-Za-z0-9+#.]{1,}", item):
        if token.lower() in jd_lower:
            return True
    zh = "".join(re.findall(r"[一-鿿]", item))
    if len(zh) < 4:
        return len(zh) >= 2 and zh in jd_lower
    return any(zh[i : i + 4] in jd_lower for i in range(len(zh) - 3))


def check_grounding(raw_json: dict, jd_text: str) -> list[str]:
    """业务规则校验：missing中的条目必须在JD原文中有依据。

    返回警告列表（不拦截输出，标记"存疑"供人工核实）。
    局限：基于子串/滑窗匹配，同义表达（如"熟悉SQL" vs "掌握数据库查询"）可能误报。
    """
    warnings: list[str] = []
    jd_lower = jd_text.lower()
    for item in raw_json.get("missing", []):
        if not _is_grounded(item, jd_lower):
            warnings.append(f"存疑：'{item}' 在JD原文中未找到明确依据，请人工核实")
    return warnings
