from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import json
from .github_client import GitHubClient
from .llm_analyzer import LLMAnalyzer
from .cache import cache
import os

try:
    from llm_client import analyze_full_review_async, analyze_pr_by_files_async
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

app = FastAPI(title="GitHub PR Diff API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class PRDiffRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    token: str = None
    skip_ssl: bool = False
    llm_key: str = None
    min_confidence: str = "low"


class PRDiffResponse(BaseModel):
    owner: str
    repo: str
    pr_number: int
    diff: str


class FileAnalysis(BaseModel):
    filename: str
    summary: str
    suggestions: List[str]


class PRSummary(BaseModel):
    title: str
    files_changed: str
    changes_summary: str
    key_changes: List[str]
    risk_assessment: str
    overall_suggestion: str


class AnalysisResponse(BaseModel):
    owner: str
    repo: str
    pr_number: int
    statistics: dict
    summary: Optional[PRSummary] = None
    files: List[FileAnalysis] = []


@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "GitHub PR Diff API"}


@app.get("/pr/{owner}/{repo}/{pr_number}", response_model=PRDiffResponse)
async def get_pr_diff(
    owner: str,
    repo: str,
    pr_number: int,
    token: str = None,
    skip_ssl: bool = False,
):
    try:
        client = GitHubClient(token=token, verify_ssl=not skip_ssl)
        diff_text = await client.get_pr_diff(owner, repo, pr_number)
        return PRDiffResponse(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            diff=diff_text,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pr/diff", response_model=PRDiffResponse)
async def post_pr_diff(request: PRDiffRequest):
    try:
        client = GitHubClient(token=request.token, verify_ssl=not request.skip_ssl)
        diff_text = await client.get_pr_diff(request.owner, request.repo, request.pr_number)
        return PRDiffResponse(
            owner=request.owner,
            repo=request.repo,
            pr_number=request.pr_number,
            diff=diff_text,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pr/{owner}/{repo}/{pr_number}/analyze")
async def analyze_pr(
    owner: str,
    repo: str,
    pr_number: int,
    token: str = None,
    skip_ssl: bool = False,
    llm_key: str = None,
):
    try:
        client = GitHubClient(token=token, verify_ssl=not skip_ssl)
        diff_text = await client.get_pr_diff(owner, repo, pr_number)
        
        analyzer = LLMAnalyzer(api_key=llm_key)
        
        statistics = analyzer.get_diff_statistics(diff_text)
        summary = analyzer.analyze_pr_summary(diff_text)
        files = analyzer.analyze_pr_by_files(diff_text)
        
        response = {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "statistics": statistics,
            "summary": summary if "error" not in summary else None,
            "files": files
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def sse_generate_review(
    owner: str,
    repo: str,
    pr_number: int,
    token: str = None,
    skip_ssl: bool = False,
    llm_key: str = None,
    min_confidence: str = "low",
):
    """SSE 流式代码评审，逐步返回结果"""
    try:
        yield json.dumps({"status": "start", "message": "开始获取 PR 数据..."}) + "\n"

        client = GitHubClient(token=token, verify_ssl=not skip_ssl)
        diff_text = await client.get_pr_diff(owner, repo, pr_number)

        analyzer = LLMAnalyzer(api_key=llm_key)
        statistics = analyzer.get_diff_statistics(diff_text)

        yield json.dumps({"status": "progress", "step": "statistics", "data": statistics, "message": "统计信息获取完成"}) + "\n"

        if ASYNC_AVAILABLE:
            overview_task = analyze_full_review_async(diff_text, llm_key)
            files_task = analyze_pr_by_files_async(diff_text, llm_key, max_files=15)

            overview = None
            files_result = []

            try:
                overview = await overview_task
                yield json.dumps({"status": "progress", "step": "overview", "data": overview.get("summary", {}), "message": "概览分析完成"}) + "\n"
            except Exception as e:
                yield json.dumps({"status": "error", "step": "overview", "message": f"概览分析失败: {str(e)}"}) + "\n"

            try:
                files_result = await files_task
                yield json.dumps({"status": "progress", "step": "files", "data": files_result, "message": f"文件分析完成 ({len(files_result)} 个文件)"}) + "\n"
            except Exception as e:
                yield json.dumps({"status": "error", "step": "files", "message": f"文件分析失败: {str(e)}"}) + "\n"

            yield json.dumps({
                "status": "complete",
                "data": {
                    "owner": owner,
                    "repo": repo,
                    "pr_number": pr_number,
                    "statistics": statistics,
                    "summary": overview.get("summary", {}) if overview else {},
                    "risks": overview.get("risks", {}) if overview else {},
                    "context": overview.get("context", {}) if overview else {},
                    "files": files_result
                },
                "message": "分析完成"
            }) + "\n"
        else:
            yield json.dumps({"status": "error", "message": "异步模块不可用，使用同步模式"}) + "\n"

    except Exception as e:
        yield json.dumps({"status": "error", "message": f"错误: {str(e)}"}) + "\n"


@app.get("/pr/{owner}/{repo}/{pr_number}/review/stream")
async def get_pr_review_stream(
    owner: str,
    repo: str,
    pr_number: int,
    token: str = None,
    skip_ssl: bool = False,
    llm_key: str = None,
    min_confidence: str = "low",
):
    """流式代码评审 API - 使用 SSE 逐步返回结果"""
    return StreamingResponse(
        sse_generate_review(owner, repo, pr_number, token, skip_ssl, llm_key, min_confidence),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/pr/review/stream")
async def post_pr_review_stream(request: PRDiffRequest):
    """流式代码评审 API - POST 版本"""
    return StreamingResponse(
        sse_generate_review(
            request.owner,
            request.repo,
            request.pr_number,
            request.token,
            request.skip_ssl,
            request.llm_key,
            request.min_confidence
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/pr/{owner}/{repo}/{pr_number}/review")
async def get_pr_review(
    owner: str,
    repo: str,
    pr_number: int,
    token: str = None,
    skip_ssl: bool = False,
    llm_key: str = None,
    min_confidence: str = "low",
    no_cache: bool = False,
):
    try:
        if not no_cache:
            cached_data = cache.get(owner, repo, pr_number)
            if cached_data and "review" in cached_data:
                return cached_data["review"]

        client = GitHubClient(token=token, verify_ssl=not skip_ssl)
        diff_text = await client.get_pr_diff(owner, repo, pr_number)

        analyzer = LLMAnalyzer(api_key=llm_key)

        files_dict = analyzer._parse_diff(diff_text)
        file_paths = list(files_dict.keys())

        full_contents: Dict[str, str] = {}
        for file_path in file_paths[:10]:
            try:
                full_content = await client.get_file_content(owner, repo, file_path)
                full_contents[file_path] = full_content
            except Exception:
                pass

        review_result = analyzer.analyze_full_review(
            diff_text,
            min_confidence=min_confidence,
            full_contents=full_contents
        )

        files_result = analyzer.analyze_pr_by_files(diff_text)

        file_details: List[Dict] = []
        for filename, file_diff in files_dict.items():
            file_analysis = analyzer.analyze_single_file(filename, file_diff)
            file_suggestion = f"针对文件 {filename} 的建议: {file_analysis.get('summary', '')}"
            file_details.append({
                "filename": filename,
                "diff": file_diff,
                "summary": file_analysis.get("summary", ""),
                "suggestions": file_analysis.get("suggestions", []),
                "file_suggestion": file_suggestion
            })

        risk_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for risk in review_result.get("risks", []):
            severity = risk.get("severity", "").lower()
            if severity in risk_summary:
                risk_summary[severity] += 1

        response = {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "overview": review_result.get("statistics"),
            "overview_risk_summary": risk_summary,
            "summary": review_result.get("summary"),
            "risks": review_result.get("risks"),
            "files": files_result,
            "file_details": file_details,
            "context": review_result.get("context")
        }

        cached_data = cache.get(owner, repo, pr_number) or {}
        cached_data["review"] = response
        cache.set(owner, repo, pr_number, cached_data)

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pr/{owner}/{repo}/{pr_number}/risks")
async def get_pr_risks(
    owner: str,
    repo: str,
    pr_number: int,
    token: str = None,
    skip_ssl: bool = False,
    llm_key: str = None,
    min_confidence: str = "low",
    no_cache: bool = False,
):
    try:
        if not no_cache:
            cached_data = cache.get(owner, repo, pr_number)
            if cached_data and "risks" in cached_data:
                return cached_data["risks"]

        client = GitHubClient(token=token, verify_ssl=not skip_ssl)
        diff_text = await client.get_pr_diff(owner, repo, pr_number)

        analyzer = LLMAnalyzer(api_key=llm_key)

        statistics = analyzer.get_diff_statistics(diff_text)
        risks_result = analyzer.analyze_risks(diff_text, min_confidence=min_confidence)

        if risks_result.get("risks"):
            verified_risks = analyzer.verify_and_filter_risks(risks_result["risks"], diff_text)
            risks_result["risks"] = verified_risks

        response = {
            "risks": risks_result.get("risks", []),
            "summary": risks_result.get("summary", ""),
            "statistics": statistics
        }

        cached_data = cache.get(owner, repo, pr_number) or {}
        cached_data["risks"] = response
        cache.set(owner, repo, pr_number, cached_data)

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pr/{owner}/{repo}/{pr_number}/summary")
async def get_pr_summary(
    owner: str,
    repo: str,
    pr_number: int,
    token: str = None,
    skip_ssl: bool = False,
    llm_key: str = None,
    no_cache: bool = False,
):
    try:
        if not no_cache:
            cached_data = cache.get(owner, repo, pr_number)
            if cached_data and "summary" in cached_data:
                return cached_data["summary"]

        client = GitHubClient(token=token, verify_ssl=not skip_ssl)
        diff_text = await client.get_pr_diff(owner, repo, pr_number)

        analyzer = LLMAnalyzer(api_key=llm_key)

        summary_result = analyzer.analyze_pr_summary(diff_text)

        response = {
            "title": summary_result.get("title", ""),
            "files_changed": summary_result.get("files_changed", ""),
            "changes_summary": summary_result.get("changes_summary", ""),
            "key_changes": summary_result.get("key_changes", []),
            "risk_assessment": summary_result.get("risk_assessment", ""),
            "overall_suggestion": summary_result.get("overall_suggestion", "")
        }

        cached_data = cache.get(owner, repo, pr_number) or {}
        cached_data["summary"] = response
        cache.set(owner, repo, pr_number, cached_data)

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pr/review")
async def post_pr_review(request: PRDiffRequest):
    try:
        client = GitHubClient(token=request.token, verify_ssl=not request.skip_ssl)
        diff_text = await client.get_pr_diff(request.owner, request.repo, request.pr_number)

        analyzer = LLMAnalyzer(api_key=request.llm_key)

        review_result = analyzer.analyze_full_review(diff_text, min_confidence=request.min_confidence)

        return {
            "owner": request.owner,
            "repo": request.repo,
            "pr_number": request.pr_number,
            "statistics": review_result.get("statistics"),
            "summary": review_result.get("summary"),
            "risks": review_result.get("risks"),
            "context": review_result.get("context")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pr/risks")
async def post_pr_risks(request: PRDiffRequest):
    try:
        client = GitHubClient(token=request.token, verify_ssl=not request.skip_ssl)
        diff_text = await client.get_pr_diff(request.owner, request.repo, request.pr_number)

        analyzer = LLMAnalyzer(api_key=request.llm_key)

        statistics = analyzer.get_diff_statistics(diff_text)
        risks_result = analyzer.analyze_risks(diff_text, min_confidence=request.min_confidence)

        if risks_result.get("risks"):
            verified_risks = analyzer.verify_and_filter_risks(risks_result["risks"], diff_text)
            risks_result["risks"] = verified_risks

        return {
            "risks": risks_result.get("risks", []),
            "summary": risks_result.get("summary", ""),
            "statistics": statistics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pr/summary")
async def post_pr_summary(request: PRDiffRequest):
    try:
        client = GitHubClient(token=request.token, verify_ssl=not request.skip_ssl)
        diff_text = await client.get_pr_diff(request.owner, request.repo, request.pr_number)

        analyzer = LLMAnalyzer(api_key=request.llm_key)

        summary_result = analyzer.analyze_pr_summary(diff_text)

        return {
            "title": summary_result.get("title", ""),
            "files_changed": summary_result.get("files_changed", ""),
            "changes_summary": summary_result.get("changes_summary", ""),
            "key_changes": summary_result.get("key_changes", []),
            "risk_assessment": summary_result.get("risk_assessment", ""),
            "overall_suggestion": summary_result.get("overall_suggestion", "")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pr/analyze")
async def post_analyze_pr(request: PRDiffRequest):
    try:
        client = GitHubClient(token=request.token, verify_ssl=not request.skip_ssl)
        diff_text = await client.get_pr_diff(request.owner, request.repo, request.pr_number)
        
        analyzer = LLMAnalyzer(api_key=request.llm_key)
        
        statistics = analyzer.get_diff_statistics(diff_text)
        summary = analyzer.analyze_pr_summary(diff_text)
        files = analyzer.analyze_pr_by_files(diff_text)
        
        response = {
            "owner": request.owner,
            "repo": request.repo,
            "pr_number": request.pr_number,
            "statistics": statistics,
            "summary": summary if "error" not in summary else None,
            "files": files
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
