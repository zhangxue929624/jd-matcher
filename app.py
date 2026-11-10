"""Streamlit界面：粘贴或上传JD和简历，展示分析、技能对比、改写结果。"""
import tempfile
from pathlib import Path

import streamlit as st

from src.analyzer import AnalysisError, analyze
from src.config import load_config
from src.file_parser import FileParseError, parse_file
from src.llm_client import LLMClient
from src.rewriter import rewrite_resume
from src.skills import analyze_skill_gap

st.set_page_config(page_title="JD匹配分析器", page_icon="💼")
st.title("💼 实习招聘JD匹配分析器")
st.caption("分析匹配度 → 技能差距集合运算 → 一键改写简历")


def load_text(label: str, key: str) -> str:
    """文本框 + 文件上传二选一，上传优先。"""
    text = st.text_area(label, height=180, key=key)
    uploaded = st.file_uploader(
        f"或上传文件（txt/md/pdf/docx）", type=["txt", "md", "pdf", "docx"], key=f"{key}_file"
    )
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        try:
            text = parse_file(tmp_path)
            st.success(f"已从 {uploaded.name} 提取 {len(text)} 字")
        except FileParseError as e:
            st.error(str(e))
    return text


jd_text = load_text("📋 职位描述（JD）", "jd")
resume_text = load_text("📄 你的简历", "resume")

if st.button("开始分析", type="primary"):
    try:
        client = LLMClient(load_config())
        with st.spinner("分析中（需调用3次模型，约半分钟）…"):
            result = analyze(jd_text, resume_text, client)
            gap = analyze_skill_gap(jd_text, resume_text, client)
            rewrite = rewrite_resume(resume_text, result.missing, client)
    except (AnalysisError, RuntimeError) as e:
        st.error(str(e))
    else:
        st.metric("匹配度评分", f"{result.score} / 100")

        tab1, tab2, tab3 = st.tabs(["📊 分析报告", "🧩 技能对比", "✍️ 简历改写"])

        with tab1:
            st.subheader("✅ 已满足的要求")
            for item in result.matched:
                st.markdown(f"- {item}")
            st.subheader("⚠️ 差距清单")
            for item in result.missing:
                st.markdown(f"- {item}")
            st.subheader("💡 修改建议")
            for item in result.suggestions:
                st.markdown(f"- {item}")
            for w in result.warnings:
                st.warning(w)

        with tab2:
            st.info("技能匹配由集合运算得出：交集=已掌握，差集=待补足（LLM只负责抽取，判定由Python完成）")
            col1, col2 = st.columns(2)
            col1.metric("JD要求技能数", len(gap.jd_skills))
            col2.metric("你已具备", f"{len(gap.matched)} / {len(gap.jd_skills)}")
            st.subheader("✅ 交集：已掌握")
            st.markdown("、".join(gap.matched) or "（无）")
            st.subheader("❌ 差集：待补足")
            st.markdown("、".join(gap.missing) or "（无）")
            with st.expander("查看全部抽取结果"):
                st.write("**JD技能：**", gap.jd_skills)
                st.write("**简历技能：**", gap.resume_skills)

        with tab3:
            st.text_area("改写后的简历", value=rewrite.rewritten, height=300)
            for w in rewrite.warnings:
                st.warning(w)
            if not rewrite.warnings:
                st.success("事实校验通过：原简历中的年份/数字/专有名词均保留")
