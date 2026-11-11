from langchain_core.tools import tool
from backend.core.retrieval import get_retriever


@tool
def document_search(query: str) -> str:
    """Search the user's uploaded documents for relevant factual information."""
    retriever = get_retriever()
    docs = retriever.invoke(query)
    if not docs:
        return "NOT_FOUND_IN_DOCUMENTS"
    return "\n\n".join(f"[{i}] {d.page_content}" for i, d in enumerate(docs, 1))
