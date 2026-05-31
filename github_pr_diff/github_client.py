import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str = None, verify_ssl: bool = True):
        self.token = token or GITHUB_TOKEN
        self.verify_ssl = verify_ssl
        self.headers = {
            "Accept": "application/vnd.github.v3.diff",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(headers=self.headers, verify=self.verify_ssl, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def get_pr_diff_sync(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"{BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        with httpx.Client(headers=self.headers, verify=self.verify_ssl, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    async def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = None) -> str:
        url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
        if ref:
            url += f"?ref={ref}"
        headers = dict(self.headers)
        headers["Accept"] = "application/vnd.github.v3.raw"
        async with httpx.AsyncClient(headers=headers, verify=self.verify_ssl, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def get_file_content_sync(self, owner: str, repo: str, file_path: str, ref: str = None) -> str:
        url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
        if ref:
            url += f"?ref={ref}"
        headers = dict(self.headers)
        headers["Accept"] = "application/vnd.github.v3.raw"
        with httpx.Client(headers=headers, verify=self.verify_ssl, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
