# PLAN — 实现步骤与验证安排

## Step 1 项目骨架 + 配置
- 建目录、requirements.txt、.env存API Key
- 验证：`python -c "from src.config import load_config; print(load_config())"` 能读到配置

## Step 2 LLM客户端（llm_client.py）
- 封装DeepSeek调用（openai兼容SDK），含超时、重试、异常分类
- 验证：真实调用一次，打印返回内容；故意用错Key验证错误提示

## Step 3 Prompt设计 + 分析器（prompts.py / analyzer.py）
- Prompt要求LLM只输出指定JSON
- analyzer负责拼装prompt、调LLM、解析JSON
- 验证：真实JD+简历跑一次，人工检查输出合理性

## Step 4 输出校验（validator.py）
- JSON Schema校验（字段、类型、score范围0-100）
- 业务规则校验：missing中每条需在JD原文有依据（子串匹配，失败标"存疑"）
- 验证：pytest覆盖正常输出/缺字段/分数越界/幻觉条目

## Step 5 界面（app.py，Streamlit）
- 两个文本框粘贴JD和简历，按钮触发，展示评分+清单
- 验证：浏览器手动跑通完整流程，录屏素材

## Step 6 测试与效果评价
- 测试集：3组"明显匹配"、3组"明显不匹配"、5条真实JD
- 指标：JSON合格率、幻觉条目率、匹配组平均分 vs 不匹配组平均分
- 改进：对比改进Prompt前后的指标，写入测试记录
