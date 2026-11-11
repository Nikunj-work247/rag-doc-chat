from ddgs import DDGS
from langchain_core.tools import tool

from backend.core.config import settings


def web_search(query: str) -> list[dict]:
    """Search the web. Returns [] on any failure so the app never crashes."""
    try:
        with DDGS(timeout=settings.web_timeout_seconds) as ddgs:
            return list(ddgs.text(query, max_results=settings.web_max_results))
    except Exception:
        return []


def format_web(results: list[dict]) -> str:
    """Number the results so the model can cite them like [1], [2]."""
    return "\n\n".join(
        f"[{i}] ({r.get('title', '')} - {r.get('href', '')})\n{r.get('body', '')}"
        for i, r in enumerate(results, 1)
    )


@tool
def web_search_tool(query: str) -> str:
    """Search the live internet for recent facts, news, or topics not found in the documents."""
    results = web_search(query)
    if not results:
        return "No web results found."
    return format_web(results)
