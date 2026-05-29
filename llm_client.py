import os
import json
from typing import Optional
from openai import OpenAI
from openai import APIError, AuthenticationError, RateLimitError
from prompt_templates import (
    RISK_DETECTION_SYSTEM_PROMPT,
    RISK_DETECTION_USER_PROMPT,
    CONTEXT_ANALYSIS_SYSTEM_PROMPT,
    CONTEXT_ANALYSIS_USER_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    VERIFICATION_USER_PROMPT,
)

DEFAULT_API_KEY = "sk-43f987dcc40f41ef8f4bfb8dfa8d93f8"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-turbo"

def get_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> OpenAI:
    """获取 OpenAI 客户端实例"""
    return OpenAI(
        api_key=api_key or os.environ.get("DASHSCOPE_API_KEY", DEFAULT_API_KEY),
        base_url=base_url or os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL),
    )

def analyze_diff(
    filename: str, 
    diff: str, 
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL
) -> dict:
    """分析单个文件的 diff，返回总结和建议"""
    client = get_client(api_key)
    
    system_prompt = """你是一个资深的代码评审专家。请根据用户提供的代码 diff，输出严格的 JSON 格式，不要有任何其他文本。"""
    
    user_prompt = f"""代码文件: {filename}
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
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return json.loads(result)
    
    except AuthenticationError:
        return {"error": "API 密钥无效，请检查您的密钥"}
    except RateLimitError:
        return {"error": "请求频率超限，请稍后重试"}
    except APIError as e:
        return {"error": f"API 错误: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "无法解析 LLM 响应"}
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}

def analyze_pr_overview(diff_text: str, api_key: Optional[str] = None) -> dict:
    """分析完整 PR 的概览"""
    client = get_client(api_key)
    
    system_prompt = """你是一个资深的代码评审专家。请根据用户提供的完整 PR diff，输出严格的 JSON 格式。"""
    
    user_prompt = f"""以下是一个 GitHub PR 的完整 diff：

{diff_text[:4000]}

请分析此 PR，输出 JSON，格式如下：
{{
  "title": "PR 主要修改内容概述（一句话）",
  "files_changed": "修改的文件数量",
  "changes_summary": "修改内容摘要",
  "key_changes": [
    "关键修改点1",
    "关键修改点2",
    "关键修改点3"
  ],
  "risk_assessment": "风险评估（低/中/高）",
  "overall_suggestion": "整体建议"
}}
注意：只输出 JSON，不要输出其他内容。"""
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return json.loads(result)
    
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}

def analyze_risks(diff_text: str, api_key: Optional[str] = None) -> dict:
    """调用 LLM 进行风险检测"""
    client = get_client(api_key)
    
    user_prompt = RISK_DETECTION_USER_PROMPT.format(diff_text=diff_text[:4000])
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": RISK_DETECTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return json.loads(result)
    
    except AuthenticationError:
        return {"error": "API 密钥无效，请检查您的密钥", "risks": [], "summary": ""}
    except RateLimitError:
        return {"error": "请求频率超限，请稍后重试", "risks": [], "summary": ""}
    except APIError as e:
        return {"error": f"API 错误: {str(e)}", "risks": [], "summary": ""}
    except json.JSONDecodeError:
        return {"error": "无法解析 LLM 响应", "risks": [], "summary": ""}
    except Exception as e:
        return {"error": f"风险检测失败: {str(e)}", "risks": [], "summary": ""}

def analyze_context(diff_text: str, api_key: Optional[str] = None) -> dict:
    """调用 LLM 进行上下文关联分析"""
    client = get_client(api_key)
    
    user_prompt = CONTEXT_ANALYSIS_USER_PROMPT.format(diff_text=diff_text[:4000])
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": CONTEXT_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return json.loads(result)
    
    except AuthenticationError:
        return {"error": "API 密钥无效，请检查您的密钥", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except RateLimitError:
        return {"error": "请求频率超限，请稍后重试", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except APIError as e:
        return {"error": f"API 错误: {str(e)}", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except json.JSONDecodeError:
        return {"error": "无法解析 LLM 响应", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except Exception as e:
        return {"error": f"上下文分析失败: {str(e)}", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}

def verify_risk(risk_description: str, diff_text: str, api_key: Optional[str] = None) -> dict:
    """对高风险项进行二次验证"""
    client = get_client(api_key)
    
    user_prompt = VERIFICATION_USER_PROMPT.format(
        risk_description=risk_description,
        diff_text=diff_text[:4000]
    )
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": VERIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return json.loads(result)
    
    except AuthenticationError:
        return {"verified": False, "confidence": "low", "reasoning": "API 密钥无效，请检查您的密钥"}
    except RateLimitError:
        return {"verified": False, "confidence": "low", "reasoning": "请求频率超限，请稍后重试"}
    except APIError as e:
        return {"verified": False, "confidence": "low", "reasoning": f"API 错误: {str(e)}"}
    except json.JSONDecodeError:
        return {"verified": False, "confidence": "low", "reasoning": "无法解析 LLM 响应"}
    except Exception as e:
        return {"verified": False, "confidence": "low", "reasoning": f"验证失败: {str(e)}"}

def analyze_full_review(diff_text: str, api_key: Optional[str] = None) -> dict:
    """整合所有分析结果，返回完整评审结果"""
    overview = analyze_pr_overview(diff_text, api_key)
    
    risks_result = analyze_risks(diff_text, api_key)
    
    context_result = analyze_context(diff_text, api_key)
    
    verified_risks = []
    if "risks" in risks_result and isinstance(risks_result["risks"], list):
        for risk in risks_result["risks"]:
            if isinstance(risk, dict) and risk.get("severity") == "高":
                verification = verify_risk(
                    risk.get("description", ""),
                    diff_text,
                    api_key
                )
                verified_risks.append({
                    "risk": risk,
                    "verification": verification
                })
    
    return {
        "overview": overview,
        "risks": risks_result,
        "context": context_result,
        "verified_risks": verified_risks,
        "summary": {
            "total_risks": len(risks_result.get("risks", [])),
            "high_risks": len([r for r in risks_result.get("risks", []) if isinstance(r, dict) and r.get("severity") == "高"]),
            "verified_high_risks": len(verified_risks),
            "affected_files_count": len(context_result.get("affected_files", [])),
            "breaking_changes_count": len(context_result.get("breaking_changes", []))
        }
    }

if __name__ == "__main__":
    test_diff = """
-    print("hello")
+    print("hello world")
"""
    print("测试单个文件分析:")
    print(json.dumps(analyze_diff("main.py", test_diff), indent=2, ensure_ascii=False))