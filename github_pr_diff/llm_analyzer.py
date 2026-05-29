import os
import json
from typing import Optional

try:
    from llm_client import analyze_diff
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class LLMAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
        self.available = LLM_AVAILABLE

    def analyze_diff(self, filename: str, diff: str) -> Optional[dict]:
        """分析 diff 内容，返回总结和建议"""
        if not self.available:
            return None
        
        try:
            result = analyze_diff(filename, diff)
            return result
        except Exception as e:
            print(f"LLM analysis error: {str(e)}")
            return None

    def analyze_pr_diff(self, diff_text: str) -> list:
        """分析完整的 PR diff，按文件分组返回分析结果"""
        if not self.available:
            return []
        
        results = []
        files = self._parse_diff(diff_text)
        
        for filename, file_diff in files.items():
            analysis = self.analyze_diff(filename, file_diff)
            if analysis:
                results.append({
                    "filename": filename,
                    "summary": analysis.get("summary", ""),
                    "suggestions": analysis.get("suggestions", [])
                })
        
        return results

    def _parse_diff(self, diff_text: str) -> dict:
        """解析 diff 文本，按文件分组"""
        files = {}
        current_file = None
        current_diff = []
        
        lines = diff_text.split('\n')
        for line in lines:
            if line.startswith('diff --git'):
                if current_file and current_diff:
                    files[current_file] = '\n'.join(current_diff)
                # 提取文件名
                parts = line.split()
                if len(parts) >= 3:
                    current_file = parts[2].replace('b/', '')
                current_diff = [line]
            elif current_file:
                current_diff.append(line)
        
        if current_file and current_diff:
            files[current_file] = '\n'.join(current_diff)
        
        return files
