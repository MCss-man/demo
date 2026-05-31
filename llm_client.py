import os
import json
import asyncio
from typing import Optional, Dict, List
from openai import OpenAI
from openai import APIError, AuthenticationError, RateLimitError
from github_pr_diff.file_utils import is_code_file, is_document_file, get_file_category, get_language_from_extension
from prompt_templates import (
    RISK_DETECTION_SYSTEM_PROMPT,
    RISK_DETECTION_USER_PROMPT,
    CONTEXT_ANALYSIS_SYSTEM_PROMPT,
    CONTEXT_ANALYSIS_USER_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    VERIFICATION_USER_PROMPT,
)

DEFAULT_API_KEY = "sk-df61dfcdc2b8463c99a5bc1ef97d759e"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "deepseek-v4-pro"

# 代码文件分析 prompt（深度分析）
CODE_ANALYSIS_SYSTEM_PROMPT = """你是一个资深的代码评审专家，具有多年开发经验，擅长发现代码中的 bug、安全漏洞、性能问题和代码异味。请严格输出 JSON 格式。"""

CODE_ANALYSIS_USER_PROMPT = """请深度分析以下代码变更：

文件: {filename}
语言: {language}
代码 diff:
{diff}

请输出严格的 JSON 格式，包含以下字段：
{{
  "file_category": "code",
  "language": "{language}",
  "summary": "一句话总结此修改的目的（20字以内）",
  "analysis_type": "代码分析",
  "findings": [
    {{
      "type": "bug/安全/性能/最佳实践/代码异味",
      "severity": "critical/high/medium/low",
      "description": "发现的问题描述",
      "location": "具体位置（如函数名、行号）",
      "suggestion": "可操作的修复建议"
    }}
  ],
  "suggestions": [
    "优化建议1",
    "优化建议2",
    "优化建议3"
  ]
}}

注意：只输出 JSON。如果没有发现问题，findings 为空数组。"""

# 文档文件分析 prompt（简单总结）
DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """你是一个文档评审专家，擅长总结文档变更内容。请严格输出 JSON 格式。"""

DOCUMENT_ANALYSIS_USER_PROMPT = """请总结以下文档变更：

文件: {filename}
文档 diff:
{diff}

请输出严格的 JSON 格式：
{{
  "file_category": "document",
  "summary": "一句话总结此文档修改的内容（20字以内）",
  "analysis_type": "文档总结",
  "findings": [],
  "suggestions": ["文档修改已确认"]
}}

注意：只输出 JSON。"""

# 二进制文件处理
BINARY_FILE_RESULT = {
    "file_category": "binary",
    "summary": "二进制文件，不支持分析",
    "analysis_type": "跳过",
    "findings": [],
    "suggestions": ["二进制文件已跳过分析"]
}

def parse_json_response(content: str) -> dict:
    """解析 LLM 返回的 JSON 响应，处理 Markdown 代码块包裹的情况"""
    if not content:
        raise json.JSONDecodeError("Empty response", "", 0)

    content = content.strip()

    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:])
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)

def get_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> OpenAI:
    """获取 OpenAI 客户端实例"""
   
    # 优先使用传入的 api_key，否则使用 DEFAULT_API_KEY（完全忽略环境变量）
    final_key = api_key if api_key is not None else DEFAULT_API_KEY
    final_base = base_url if base_url is not None else DEFAULT_BASE_URL
    return OpenAI(api_key=final_key, base_url=final_base)

def analyze_diff(
    filename: str, 
    diff: str, 
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL
) -> dict:
    """分析单个文件的 diff，根据文件类型使用不同的分析策略"""
    client = get_client(api_key)
    file_category = get_file_category(filename)
    
    # 根据文件类型选择不同的分析策略
    if file_category == 'binary':
        return BINARY_FILE_RESULT
    
    elif file_category == 'code':
        # 代码文件：深度分析
        language = get_language_from_extension(filename)
        system_prompt = CODE_ANALYSIS_SYSTEM_PROMPT
        user_prompt = CODE_ANALYSIS_USER_PROMPT.format(
            filename=filename,
            language=language,
            diff=diff
        )
    
    elif file_category == 'document':
        # 文档文件：简单总结
        system_prompt = DOCUMENT_ANALYSIS_SYSTEM_PROMPT
        user_prompt = DOCUMENT_ANALYSIS_USER_PROMPT.format(
            filename=filename,
            diff=diff
        )
    
    else:
        # 未知类型文件：简单处理
        return {
            "file_category": "unknown",
            "summary": f"不支持分析此类型文件: {filename}",
            "analysis_type": "跳过",
            "findings": [],
            "suggestions": ["此文件类型暂不支持分析"]
        }
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            # response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return parse_json_response(result)
    
    except AuthenticationError:
        return {"error": "API 密钥无效，请检查您的密钥"}
    except RateLimitError:
        return {"error": "请求频率超限，请稍后重试"}
    except APIError as e:
        return {"error": f"API 错误: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"无法解析 LLM 响应: {str(e)}"}
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}

def analyze_pr_overview(diff_text: str, api_key: Optional[str] = None) -> dict:
    """分析完整 PR 的概览"""
    client = get_client(api_key=DEFAULT_API_KEY)
    # print("实际使用的api_key:", client.api_key)  # 调试用
    
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
注意：只输出合法的 JSON 对象，不要输出任何其他文本、注释或 Markdown 标记。"""
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            # response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return parse_json_response(result)
    
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}

def analyze_risks(
    diff_text: str, 
    api_key: Optional[str] = None,
    full_contents: Optional[Dict[str, str]] = None
) -> dict:
    """调用 LLM 进行风险检测，支持传递完整文件内容用于上下文分析"""
    client = get_client(api_key)
    
    files_content = ""
    if full_contents:
        for filename, content in full_contents.items():
            files_content += f"\n\n===== 文件: {filename} =====\n{content[:5000]}"
    
    # 简化的 prompt 模板，避免占位符不匹配
    system_prompt = """你是一个资深的代码安全专家和性能优化专家。请分析代码变更，输出严格的 JSON 格式，不要有其他文本。"""
    user_prompt = f"""代码变更 (diff):
{diff_text[:4000]}

请检测是否有风险，输出 JSON 格式：
{{
  "risks": [],
  "summary": {{
    "total_risks": 0,
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0
  }}
}}

注意：只输出 JSON。"""
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            # response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return parse_json_response(result)
    
    except AuthenticationError:
        return {"error": "API 密钥无效，请检查您的密钥", "risks": [], "summary": ""}
    except RateLimitError:
        return {"error": "请求频率超限，请稍后重试", "risks": [], "summary": ""}
    except APIError as e:
        return {"error": f"API 错误: {str(e)}", "risks": [], "summary": ""}
    except json.JSONDecodeError as e:
        return {"error": f"无法解析 LLM 响应: {str(e)}", "risks": [], "summary": ""}
    except Exception as e:
        return {"error": f"风险检测失败: {str(e)}", "risks": [], "summary": ""}

def analyze_context(diff_text: str, api_key: Optional[str] = None) -> dict:
    """调用 LLM 进行上下文关联分析"""
    client = get_client(api_key)
    
    # 简化的 prompt 模板，避免占位符不匹配
    system_prompt = """你是一个资深的代码架构师，擅长分析代码变更的影响范围。请输出严格的 JSON 格式，不要有其他文本。"""
    user_prompt = f"""代码变更 (diff):
{diff_text[:4000]}

请分析影响范围，输出 JSON 格式：
{{
  "affected_files": [],
  "call_relationships": [],
  "breaking_changes": [],
  "impact_assessment": {{
    "scope": "影响范围描述",
    "severity": "low",
    "migration_required": false,
    "migration_suggestion": ""
  }}
}}

注意：只输出 JSON。"""
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            # response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return parse_json_response(result)
    
    except AuthenticationError:
        return {"error": "API 密钥无效，请检查您的密钥", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except RateLimitError:
        return {"error": "请求频率超限，请稍后重试", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except APIError as e:
        return {"error": f"API 错误: {str(e)}", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except json.JSONDecodeError as e:
        return {"error": f"无法解析 LLM 响应: {str(e)}", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}
    except Exception as e:
        return {"error": f"上下文分析失败: {str(e)}", "affected_files": [], "call_relationships": [], "breaking_changes": [], "impact_assessment": ""}

def verify_risk(risk_description: str, diff_text: str, api_key: Optional[str] = None) -> dict:
    """对高风险项进行二次验证"""
    client = get_client(api_key)
    
    # 简化的 prompt 模板，避免占位符不匹配
    system_prompt = """你是一个资深的代码安全专家，擅长对代码问题进行二次验证。请输出严格的 JSON 格式，不要有其他文本。"""
    user_prompt = f"""风险描述:
{risk_description}

代码变更 (diff):
{diff_text[:4000]}

请验证这个风险，输出 JSON 格式：
{{
  "verified": false,
  "confidence": "low",
  "reasoning": "验证过程说明",
  "refined_assessment": {{
    "severity": "low",
    "suggestion": "建议"
  }}
}}

注意：只输出 JSON。"""
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            # response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        return parse_json_response(result)
    
    except AuthenticationError:
        return {"verified": False, "confidence": "low", "reasoning": "API 密钥无效，请检查您的密钥"}
    except RateLimitError:
        return {"verified": False, "confidence": "low", "reasoning": "请求频率超限，请稍后重试"}
    except APIError as e:
        return {"verified": False, "confidence": "low", "reasoning": f"API 错误: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"verified": False, "confidence": "low", "reasoning": f"无法解析 LLM 响应: {str(e)}"}
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

async def analyze_full_review_async(diff_text: str, api_key: Optional[str] = None) -> dict:
    """异步并发执行所有分析任务"""
    loop = asyncio.get_event_loop()

    overview_task = loop.run_in_executor(None, analyze_pr_overview, diff_text, api_key)
    risks_task = loop.run_in_executor(None, analyze_risks, diff_text, api_key)
    context_task = loop.run_in_executor(None, analyze_context, diff_text, api_key)

    overview, risks_result, context_result = await asyncio.gather(
        overview_task, risks_task, context_task
    )

    verified_risks = []
    if "risks" in risks_result and isinstance(risks_result["risks"], list):
        for risk in risks_result["risks"]:
            if isinstance(risk, dict) and risk.get("severity") in ["高", "high", "critical"]:
                verification = await loop.run_in_executor(
                    None, verify_risk, risk.get("description", ""), diff_text, api_key
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
            "high_risks": len([r for r in risks_result.get("risks", []) if isinstance(r, dict) and r.get("severity") in ["高", "high", "critical"]]),
            "verified_high_risks": len(verified_risks),
            "affected_files_count": len(context_result.get("affected_files", [])),
            "breaking_changes_count": len(context_result.get("breaking_changes", []))
        }
    }

async def analyze_pr_by_files_async(diff_text: str, api_key: Optional[str] = None, max_files: int = 20) -> List[dict]:
    """异步并发分析多个文件"""
    from github_pr_diff.llm_analyzer import LLMAnalyzer

    analyzer = LLMAnalyzer(api_key=api_key)
    files = analyzer._parse_diff(diff_text)

    file_list = list(files.items())[:max_files]

    async def analyze_one_file(filename: str, file_diff: str) -> dict:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, analyzer.analyze_single_file, filename, file_diff)
        if result and "error" not in result:
            return {
                "filename": filename,
                "summary": result.get("summary", ""),
                "suggestions": result.get("suggestions", [])
            }
        return {"filename": filename, "error": result.get("error", "分析失败") if result else "无结果"}

    tasks = [analyze_one_file(fn, fd) for fn, fd in file_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r if isinstance(r, dict) else {"error": str(r)} for r in results]

if __name__ == "__main__":
    # 测试代码文件分析
    test_code_diff = """
-    def hello():
-        print("hello")
+    def hello(name):
+        print(f"hello {name}")
"""
    print("=" * 60)
    print("测试代码文件分析 (Python)")
    print("=" * 60)
    result = analyze_diff("utils.py", test_code_diff)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print()
    
    # 测试文档文件分析
    test_doc_diff = """
- # Hello
- Hello world
+ # Hello
+ Hello world
+ This is a new feature
"""
    print("=" * 60)
    print("测试文档文件分析 (.txt)")
    print("=" * 60)
    result = analyze_diff("README.txt", test_doc_diff)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print()
    
    # 测试二进制文件
    print("=" * 60)
    print("测试二进制文件分析")
    print("=" * 60)
    result = analyze_diff("logo.png", "")
    print(json.dumps(result, indent=2, ensure_ascii=False))