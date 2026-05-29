import os
import json
from typing import Optional, List, Dict

try:
    from llm_client import analyze_diff, analyze_pr_overview, analyze_risks, analyze_context, verify_risk, analyze_full_review
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class LLMAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.available = LLM_AVAILABLE

    def analyze_single_file(self, filename: str, diff: str) -> Optional[dict]:
        """分析单个文件的 diff，返回总结和建议"""
        if not self.available:
            return {"error": "LLM 客户端不可用"}
        
        try:
            result = analyze_diff(filename, diff, api_key=self.api_key)
            return result
        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}

    def analyze_pr_by_files(self, diff_text: str) -> List[dict]:
        """分析完整的 PR diff，按文件分组返回分析结果"""
        if not self.available:
            return [{"error": "LLM 客户端不可用"}]
        
        results = []
        files = self._parse_diff(diff_text)
        
        for filename, file_diff in files.items():
            analysis = self.analyze_single_file(filename, file_diff)
            if analysis and "error" not in analysis:
                results.append({
                    "filename": filename,
                    "summary": analysis.get("summary", ""),
                    "suggestions": analysis.get("suggestions", [])
                })
            elif "error" in analysis:
                results.append({
                    "filename": filename,
                    "error": analysis["error"]
                })
        
        return results

    def analyze_pr_summary(self, diff_text: str) -> dict:
        """分析完整 PR 的概览摘要"""
        if not self.available:
            return {"error": "LLM 客户端不可用"}
        
        try:
            result = analyze_pr_overview(diff_text, api_key=self.api_key)
            return result
        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}

    def _parse_diff(self, diff_text: str) -> Dict[str, str]:
        """解析 diff 文本，按文件分组"""
        files = {}
        current_file = None
        current_diff = []
        
        lines = diff_text.split('\n')
        for line in lines:
            if line.startswith('diff --git'):
                if current_file and current_diff:
                    files[current_file] = '\n'.join(current_diff)
                parts = line.split()
                if len(parts) >= 3:
                    current_file = parts[2].replace('b/', '')
                current_diff = [line]
            elif current_file:
                current_diff.append(line)
        
        if current_file and current_diff:
            files[current_file] = '\n'.join(current_diff)
        
        return files

    def get_diff_statistics(self, diff_text: str) -> dict:
        """获取 diff 的统计信息"""
        lines = diff_text.split('\n')
        added = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        files = len(self._parse_diff(diff_text))
        
        return {
            "files_changed": files,
            "lines_added": added,
            "lines_removed": removed,
            "total_changes": added + removed
        }

    def analyze_risks(self, diff_text: str, min_confidence: str = "low") -> dict:
        """分析 diff 中的潜在风险"""
        if not self.available:
            return {"error": "LLM 客户端不可用"}

        try:
            result = analyze_risks(diff_text, min_confidence=min_confidence, api_key=self.api_key)
            return result
        except Exception as e:
            return {"error": f"风险分析失败: {str(e)}"}

    def analyze_context(self, diff_text: str) -> dict:
        """分析 diff 中的上下文关联"""
        if not self.available:
            return {"error": "LLM 客户端不可用"}

        try:
            result = analyze_context(diff_text, api_key=self.api_key)
            return result
        except Exception as e:
            return {"error": f"上下文分析失败: {str(e)}"}

    def verify_and_filter_risks(self, risks: List[dict], diff_text: str) -> List[dict]:
        """对高置信度风险进行二次验证，过滤未通过验证的风险项"""
        if not self.available:
            return risks

        filtered_risks = []

        for risk in risks:
            confidence = risk.get("confidence", "").lower()
            if confidence != "high":
                filtered_risks.append(risk)
                continue

            try:
                verification = verify_risk(risk, diff_text, api_key=self.api_key)
                if verification.get("verified", False):
                    filtered_risks.append(risk)
            except Exception:
                filtered_risks.append(risk)

        return filtered_risks

    def analyze_full_review(self, diff_text: str, min_confidence: str = "low") -> dict:
        """整合所有分析结果，返回完整的代码评审结果"""
        if not self.available:
            return {"error": "LLM 客户端不可用"}

        statistics = self.get_diff_statistics(diff_text)
        summary = self.analyze_pr_summary(diff_text)
        risks_result = self.analyze_risks(diff_text, min_confidence=min_confidence)
        context = self.analyze_context(diff_text)

        risks_list = risks_result.get("risks", []) if isinstance(risks_result, dict) else []
        if risks_list:
            verified_risks = self.verify_and_filter_risks(risks_list, diff_text)
            risks_list = verified_risks

        return {
            "statistics": statistics,
            "summary": summary,
            "risks": risks_list,
            "risks_summary": risks_result.get("summary", "") if isinstance(risks_result, dict) else "",
            "context": context
        }

    def filter_by_confidence(self, results: List[dict], min_confidence: str) -> List[dict]:
        """按置信度过滤结果"""
        confidence_order = {"low": 0, "medium": 1, "high": 2}
        min_level = confidence_order.get(min_confidence.lower(), 0)

        filtered = []
        for result in results:
            result_confidence = result.get("confidence", "").lower()
            result_level = confidence_order.get(result_confidence, 0)
            if result_level >= min_level:
                filtered.append(result)

        return filtered
