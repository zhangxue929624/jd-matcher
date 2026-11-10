"""validator模块测试：覆盖正常输入、边界、非法输入。"""
from src.validator import check_grounding, validate_schema

VALID_OUTPUT = {
    "score": 75,
    "matched": ["JD要求Python，简历有3年经验"],
    "missing": ["JD要求熟悉Spark"],
    "suggestions": ["建议1", "建议2", "建议3"],
}


def test_valid_output_passes():
    report = validate_schema(VALID_OUTPUT)
    assert report.ok, f"合法输出应通过校验，实际错误：{report.errors}"


def test_score_boundary_accepted():
    for score in (0, 100):
        data = {**VALID_OUTPUT, "score": score}
        assert validate_schema(data).ok, f"边界分数 {score} 应被接受"


def test_score_out_of_range_rejected():
    for score in (-1, 101):
        data = {**VALID_OUTPUT, "score": score}
        report = validate_schema(data)
        assert not report.ok, f"越界分数 {score} 应被拒绝"


def test_missing_field_rejected():
    data = {k: v for k, v in VALID_OUTPUT.items() if k != "missing"}
    report = validate_schema(data)
    assert not report.ok
    assert any("missing" in e for e in report.errors)


def test_empty_list_rejected():
    data = {**VALID_OUTPUT, "matched": []}
    assert not validate_schema(data).ok


def test_too_few_suggestions_rejected():
    data = {**VALID_OUTPUT, "suggestions": ["只有一条"]}
    assert not validate_schema(data).ok


def test_empty_string_item_rejected():
    data = {**VALID_OUTPUT, "matched": ["  "]}
    assert not validate_schema(data).ok


def test_grounding_passes_when_keyword_in_jd():
    jd = "要求：熟悉Spark和Hive，有大数据项目经验"
    output = {"missing": ["JD要求熟悉Spark"]}
    assert check_grounding(output, jd) == []


def test_grounding_flags_hallucinated_item():
    jd = "要求：熟悉Java开发，了解Spring框架"
    output = {"missing": ["JD要求精通CUDA编程"]}
    warnings = check_grounding(output, jd)
    assert len(warnings) == 1
    assert "存疑" in warnings[0]
