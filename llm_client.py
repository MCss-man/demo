import os
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key="sk-43f987dcc40f41ef8f4bfb8dfa8d93f8",  # 从环境变量读取
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def analyze_diff(filename: str, diff: str) -> dict:
    """分析单个文件的 diff，返回总结和3条建议"""
    response = client.chat.completions.create(
        # 选择 Qwen Turbo 模型
        model="qwen-turbo",
        messages=[
            {
                "role": "system",
                "content": "你是一个资深的代码评审专家。请根据用户提供的代码 diff，输出严格的 JSON 格式，不要有任何其他文本。"
            },
            {
                "role": "user",
                "content": f"""代码文件: {filename}
修改的 diff:
{diff}

请分析此修改，输出 JSON，格式如下：
{{
  "summary": "一句话总结此修改的目的（20字以内）",
  "suggestions": [
    "建议1（具体可操作）",
    "建议2",
    "建议3"
  ]
}}
注意：只输出 JSON，不要输出其他内容。"""
            }
        ],
        temperature=0.2,
        response_format={"type": "json_object"}  # 强制 JSON 输出
    )
    
    result = response.choices[0].message.content
    import json
    return json.loads(result)

# 测试（可选）
if __name__ == "__main__":
    test_diff = """
-    print("hello")
+    print("hello world")
"""
    print(analyze_diff("main.py", test_diff))