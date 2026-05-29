from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .github_client import GitHubClient
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


class PRDiffResponse(BaseModel):
    owner: str
    repo: str
    pr_number: int
    diff: str


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
