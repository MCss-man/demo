from typing import Optional, Dict, Any


class AnalysisCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_cache_key(self, owner: str, repo: str, pr_number: int) -> str:
        return f"{owner}:{repo}:{pr_number}"

    def get(self, owner: str, repo: str, pr_number: int) -> Optional[dict]:
        key = self.get_cache_key(owner, repo, pr_number)
        return self._cache.get(key)

    def set(self, owner: str, repo: str, pr_number: int, data: dict) -> None:
        key = self.get_cache_key(owner, repo, pr_number)
        self._cache[key] = data

    def clear(self) -> None:
        self._cache.clear()


cache = AnalysisCache()