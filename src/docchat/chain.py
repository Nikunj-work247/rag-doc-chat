import re
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from .config import settings
from .retrieval import get_retriever

CONDENSE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Rewrite the user's latest message as a standalone question that can be "
            "understood without the chat history. Replace pronouns such as 'it' or "
            "'that' with what they refer to. If the message is already standalone, "
            "return it unchanged. Output only the question, nothing else.",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert assistant that provides comprehensive, in-depth, "
            "and well-structured explanations based only on the provided context.\n\n"
            "Guidelines:\n"
            "1. Depth & Completeness: Provide detailed, thorough explanations. Explain concepts, "
            "mechanisms, reasons, and nuances found in the documents rather than giving brief summaries.\n"
            "2. Structure: Organize your response logically using clear headings, bullet points, or numbered lists "
            "to make detailed information easy to follow.\n"
            "3. Grounding: Rely strictly on the facts present in the context. Do not invent or extrapolate beyond "
            "what the documents say. If the context does not contain enough information to answer fully, clearly state what is missing.\n"
            "4. Inline Citations: Cite the source chunks accurately using bracketed numbers like [1], [2] "
            "whenever stating specific facts or references from that passage.",
        ),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)

MAX_HISTORY_MESSAGES = 12 


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that reasoning models may emit."""
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "</think>" in text:
        text = text.split("</think>")[-1]
    elif "<think>" in text:
        text = text.split("<think>")[0]
    return text.strip()


def source_label(doc) -> str:
    name = Path(doc.metadata.get("source", "unknown")).name
    page = doc.metadata.get("page")
    return f"{name}, page {page + 1}" if isinstance(page, int) else name


def format_docs(docs) -> str:
    return "\n\n".join(
        f"[{i}] ({source_label(d)})\n{d.page_content}" for i, d in enumerate(docs, 1)
    )


class RagChat:
    def __init__(self):
        self.retriever = get_retriever()
        llm = ChatNVIDIA(
            model=settings.chat_model,
            temperature=0.2,
            max_completion_tokens=2048,
        )
        if hasattr(llm, "with_thinking_mode"):
            try:
                llm = llm.with_thinking_mode(enabled=False)
            except Exception:
                pass
        self.condense = CONDENSE_PROMPT | llm | StrOutputParser() | strip_thinking
        self.answer = ANSWER_PROMPT | llm | StrOutputParser() | strip_thinking
        self.history: list = []

    def reset(self) -> None:
        self.history = []

    def ask(self, question: str) -> dict:
        history = self.history[-MAX_HISTORY_MESSAGES:]

        # 1. turn a follow-up into a standalone question
        standalone = (
            self.condense.invoke({"history": history, "question": question})
            if history
            else question
        )

        # 2. retrieve using the standalone question
        docs = self.retriever.invoke(standalone)

        # 3. answer from the retrieved context
        answer = self.answer.invoke(
            {"context": format_docs(docs), "question": standalone}
        )

        self.history += [HumanMessage(question), AIMessage(answer)]
        return {"standalone": standalone, "docs": docs, "answer": answer}