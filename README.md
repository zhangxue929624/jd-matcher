# 实习招聘 JD 匹配分析器

粘贴招聘 JD + 上传简历（PDF/DOCX/TXT），自动完成：

- **匹配分析**：匹配度评分、已满足要求、差距清单（每条结论可追溯到 JD/简历原文，疑似幻觉自动标注）
- **技能对比**：LLM 抽取技能，Python 集合运算得出"已掌握/待补足"
- **简历改写**：在不编造事实的前提下优化简历措辞，Python 校验年份/数字/专有名词不丢失

## 环境要求

- Python 3.10+
- 一个 LLM API Key（默认 DeepSeek，兼容 OpenAI 接口的其他服务也可用）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key：复制 .env.example 为 .env，填入你的密钥
#    DEEPSEEK_API_KEY=sk-xxxx

# 3. 启动应用（浏览器自动打开 http://localhost:8501）
python -m streamlit run app.py
```

## 运行测试

```bash
pip install pytest
python -m pytest tests/ -v
```

## 项目结构

```
app.py               # Streamlit 界面入口
src/
  config.py          # 配置加载（.env / 环境变量）
  llm_client.py      # LLM API 客户端（重试/异常处理）
  prompts.py         # 提示词模板
  analyzer.py        # 匹配分析流程
  validator.py       # 输出校验：结构/范围/枚举/防幻觉
  skills.py          # 技能抽取 + 集合运算
  rewriter.py        # 简历改写 + 事实保持校验
  file_parser.py     # PDF/DOCX/TXT 解析
tests/               # 39 个 pytest 用例
```

## 切换其他模型

本项目使用 OpenAI 兼容接口，在 `.env` 中可覆盖：

```
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

例如改用其他兼容服务，只需替换 BASE_URL 和 MODEL。
