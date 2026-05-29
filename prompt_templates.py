# prompt_templates.py

SYSTEM_PROMPT = """你是一个资深的代码评审专家。请根据用户提供的代码 diff，输出严格的 JSON 格式，不要有任何其他文本。"""

USER_PROMPT_TEMPLATE = """代码文件: {filename}
修改的 diff:
{diff}

请分析此修改，输出 JSON，格式如下：
{
  "summary": "一句话总结此修改的目的（20字以内）",
  "suggestions": [
    "建议1（具体可操作）",
    "建议2",
    "建议3"
  ]
}
注意：只输出 JSON，不要输出其他内容。"""