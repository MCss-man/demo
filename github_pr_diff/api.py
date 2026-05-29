from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from .github_client import GitHubClient
from .llm_analyzer import LLMAnalyzer
from .cache import cache
import os

app = FastAPI(title="GitHub PR Diff API", version="0.1.0")

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

        review_result = analyzer.analyze_full_review(diff_text, min_confidence=min_confidence)

        response = {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "statistics": review_result.get("statistics"),
            "summary": review_result.get("summary"),
            "risks": review_result.get("risks"),
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
