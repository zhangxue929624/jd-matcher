"""技能图谱：LLM抽取技能，Python做集合运算（交集=已匹配，差集=差距）。

设计原则：匹配结论由可解释的集合运算得出，LLM只负责抽取，不直接判定匹配。
"""
from dataclasses import dataclass

from .analyzer import AnalysisError, _parse_json
from .llm_client import LLMClient, LLMError
from .prompts import SKILL_EXTRACTION_SYSTEM, build_skill_prompt


@dataclass
class SkillGap:
    """技能对比结果。"""
    jd_skills: list[str]
    resume_skills: list[str]
    matched: list[str]   # 交集：JD要求且简历具备
    missing: list[str]   # 差集：JD要求但简历缺失


def normalize_skills(skills: list[str]) -> list[str]:
    """归一化：去空白、转小写、去重，保持首次出现顺序。"""
    seen: set[str] = set()
    result: list[str] = []
    for s in skills:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    return result


def compute_gap(jd_skills: list[str], resume_skills: list[str]) -> SkillGap:
    """集合运算：matched = JD∩简历，missing = JD−简历。"""
    jd_norm = normalize_skills(jd_skills)
    resume_set = set(normalize_skills(resume_skills))
    matched = [s for s in jd_norm if s in resume_set]
    missing = [s for s in jd_norm if s not in resume_set]
    return SkillGap(
        jd_skills=jd_norm,
        resume_skills=sorted(resume_set),
        matched=matched,
        missing=missing,
    )


def extract_skills(text: str, source: str, client: LLMClient) -> list[str]:
    """调用LLM从文本中抽取技能列表。"""
    try:
        raw = client.chat(SKILL_EXTRACTION_SYSTEM, build_skill_prompt(text, source))
    except LLMError as e:
        raise AnalysisError(str(e)) from e
    data = _parse_json(raw)
    skills = data.get("skills")
    if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
        raise AnalysisError("技能抽取结果格式错误：应为 {\"skills\": [字符串...]}")
    return normalize_skills(skills)


def analyze_skill_gap(jd_text: str, resume_text: str, client: LLMClient) -> SkillGap:
    """完整流程：分别抽取JD和简历技能 → 集合运算。"""
    jd_skills = extract_skills(jd_text, "JD", client)
    resume_skills = extract_skills(resume_text, "简历", client)
    return compute_gap(jd_skills, resume_skills)
