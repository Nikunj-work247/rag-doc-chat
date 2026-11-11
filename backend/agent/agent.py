from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.tools.document_search import document_search
from backend.agent.tools.web_search import web_search_tool
from backend.core.config import settings


def get_agent():
    """Create and return a LangChain tool-calling agent with document and web search tools."""
    llm = ChatNVIDIA(
        model=settings.chat_model,
        temperature=0.2,
        max_completion_tokens=2048,
    )
    tools = [document_search, web_search_tool]
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
