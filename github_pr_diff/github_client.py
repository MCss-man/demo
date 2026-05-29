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
