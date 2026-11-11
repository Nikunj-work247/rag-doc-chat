import re
from pathlib import Path

from langchain_community.cache import SQLiteCache
from langchain_core.globals import get_llm_cache, set_llm_cache
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from backend.agent.tools.web_search import web_search, format_web
from backend.core.config import settings
from backend.core.retrieval import get_retriever, get_vectorstore


def init_llm_cache() -> None:
    """Initialize persistent SQLite LLM cache if enabled in config."""
    if settings.llm_cache_enabled:
        settings.llm_cache_path.parent.mkdir(parents=True, exist_ok=True)
        set_llm_cache(SQLiteCache(database_path=str(settings.llm_cache_path)))


def clear_llm_cache() -> None:
    """Purge all cached LLM generations."""
    cache = get_llm_cache()
    if cache and hasattr(cache, "clear"):
        cache.clear()


# Initialize cache when the chain module is loaded
init_llm_cache()

CONDENSE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given the conversation history and the user's latest question, output a clean, standalone search query.\n"
            "Rules:\n"
            "- If the question is already clear and standalone, return it EXACTLY as is.\n"
            "- Only resolve pronouns (such as 'it', 'they', 'this', 'that') using the history.\n"
            "- NEVER answer the question, NEVER copy headings, and NEVER output summaries.\n"
            "- Output ONLY the short question/search query, nothing else.",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert document assistant. Answer the user's question using the numbered excerpts below.\n\n"
            "Rules & Formatting Guidelines:\n"
            "1. Comprehensiveness & Depth:\n"
            "   - If the user asks to SUMMARIZE, EXPLAIN, REVIEW, or give an OVERVIEW: Provide a rich, comprehensive, structured response in markdown. Use clear section headers, organized bullet points, and highlight key concepts, definitions, and takeaways. Do NOT give a short or superficial 2-sentence summary.\n"
            "   - If the user asks a specific question: Give a complete, clear explanation covering all relevant details present in the text.\n"
            "2. Grounding & Citations:\n"
            "   - Rely strictly on the information provided in the context. Never fabricate facts.\n"
            "   - Place citations like [1], [2] immediately following the facts or sentences they support.\n"
            "   - Only cite chunk numbers that actually exist in the context.\n"
            "3. Gap Handling:\n"
            "   - If the context only partially covers the question, explain what is present and explicitly note what is missing.\n"
            "4. Tone:\n"
            "   - Professional, objective, and well-structured. No preamble like 'Based on the provided excerpts'.",
        ),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)

def is_obviously_conversational(text: str) -> bool:
    """Fast deterministic check for greetings, introductions, and small talk."""
    q = text.lower().strip()
    clean_q = re.sub(r"[^\w\s]", "", q).strip()
    words = clean_q.split()
    if not words:
        return True

    first_word = words[0]
    greetings = {"hi", "hello", "hey", "hola", "sup", "howdy", "thanks", "thank", "bye", "goodbye"}
    if first_word in greetings and len(words) <= 5:
        return True

    # User introducing themselves or their profession
    intro_prefixes = ("my name is", "i am", "im ", "i'm ", "call me", "myself ")
    if any(clean_q.startswith(p) for p in intro_prefixes):
        if not any(w in clean_q for w in ["document", "pdf", "file", "summarize", "explain", "chapter", "algorithm", "tree", "formula"]):
            return True

    # Questions about what the assistant can do
    meta_questions = (
        "who are you", "what is your name", "what are you", "what can you do",
        "how can you help", "what questions can i ask", "what can i ask",
        "help me", "what is this", "what do you do",
    )
    if any(clean_q.startswith(p) for p in meta_questions):
        return True

    return False


ROUTE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a query intent classifier for a document chat assistant.\n"
            "Classify whether the user's latest query requires retrieving specific content from their uploaded documents.\n\n"
            "Output CHAT if the user is:\n"
            "- Introducing themselves, stating their name, profession, or background (e.g. 'my name is...', 'I am a developer')\n"
            "- Asking about the assistant or asking what they can ask\n"
            "- Making general conversational remarks, greetings, or pleasantries\n\n"
            "Output DOCS only if the user is:\n"
            "- Asking a specific question about technical concepts, definitions, or algorithms from the uploaded documents\n"
            "- Asking to summarize, outline, or explain the documents\n\n"
            "Respond with ONLY the single word CHAT or DOCS. No other text.",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a friendly, intelligent assistant in a document chat application.\n"
            "Currently uploaded files in the workspace: {doc_list}\n\n"
            "Guidelines:\n"
            "- Greetings, introductions, and small talk: Respond warmly, naturally, and concisely in 1 to 2 sentences.\n"
            "  * If the user introduces themselves (e.g., 'My name is Nikunj, I'm a software developer'): "
            "Acknowledge their name/background warmly in 1-2 friendly sentences, and briefly invite them to explore the uploaded documents (e.g., 'Nice to meet you, Nikunj! As a software developer, you might find the algorithms and engineering concepts in the uploaded documents especially interesting. What would you like to explore?').\n"
            "  * If asked 'what can I ask?', 'what topics are covered?': Suggest 3-4 interesting questions they can ask based on the files.\n"
            "- Never provide document summaries, unsolicited lectures, or citations in chat mode.\n"
            "- Keep your response brief, natural, and inviting.",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

GRADE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You check whether document excerpts contain the information needed "
            "to answer a question. Reply with exactly one word: YES or NO.",
        ),
        ("human", "Question: {question}\n\nExcerpts:\n{context}"),
    ]
)

WEB_ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Answer the question using ONLY the numbered web results below.\n"
            "- Put a citation like [2] right after the sentence it supports.\n"
            "- Use only numbers that appear in the results.\n"
            "- If the results don't contain the answer, say so. Do not guess.\n"
            "- Match the length to the question.",
        ),
        ("human", "Web results:\n{context}\n\nQuestion: {question}"),
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


def clean_response(text: str) -> str:
    """Remove reasoning tags and any stray introductory summary fluff."""
    text = strip_thinking(text)
    # Strip any stray leading Summary or introductory preamble if the model emits it
    text = re.sub(
        r"^(?:\s*Summary:?\s*\n+|\s*In short[^\n]*\n+|\s*Based on [^\n]*\n+)+",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    return text


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
        self.vectorstore = get_vectorstore()
        self.retriever = get_retriever()

        # Large model — used only for the final answer (quality matters here)
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

        # Fast model for utility calls (route, condense) — uses chat_model unless fast_model is set in .env
        fast_model_name = settings.fast_model or settings.chat_model
        fast_llm = ChatNVIDIA(
            model=fast_model_name,
            temperature=0.0,
            max_completion_tokens=64,
        )

        # Chains — keep them pure without non-generator functions so streaming is not blocked
        self.condense = CONDENSE_PROMPT | fast_llm | StrOutputParser()
        self.answer = ANSWER_PROMPT | llm | StrOutputParser()
        self.route = ROUTE_PROMPT | fast_llm | StrOutputParser()
        self.chat = CHAT_PROMPT | llm | StrOutputParser()
        self.web_answer = WEB_ANSWER_PROMPT | llm | StrOutputParser()
        self.history: list = []

    def reset(self) -> None:
        self.history = []

    def get_uploaded_docs_summary(self) -> str:
        """List currently uploaded document filenames for meta conversational guidance."""
        if not settings.raw_dir.exists():
            return "No documents uploaded yet."
        files = [
            p.name for p in sorted(settings.raw_dir.glob("*"))
            if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".md"}
        ]
        return ", ".join(files) if files else "No documents uploaded yet."

    def _short_history(self, history):
        """Truncate old AI answers so long text doesn't confuse small prompts."""
        return [
            AIMessage(m.content[:150] + "...") if isinstance(m, AIMessage) else m
            for m in history
        ]

    def needs_documents(self, question: str, short_history) -> bool:
        if is_obviously_conversational(question):
            return False

        raw_verdict = self.route.invoke(
            {"history": short_history, "question": question}
        )
        verdict = strip_thinking(raw_verdict).strip().upper()
        if "CHAT" in verdict and "DOCS" not in verdict:
            return False
        if "DOCS" in verdict:
            return True
        return False

    def docs_are_relevant(self, question: str, docs) -> bool:
        """Return True if the retriever found at least one chunk — skip extra LLM grading call."""
        return len(docs) > 0

    def web_fallback(self, question: str) -> dict:
        """Fall back to web search when documents don't contain a relevant answer."""
        results = web_search(question)
        if not results:
            return {
                "answer": "I couldn't find relevant information in your documents or on the web.",
                "web_sources": [],
            }
        context = format_web(results)
        answer = self.web_answer.invoke({"context": context, "question": question})
        return {"answer": answer, "web_sources": results}

    def ask(self, question: str) -> dict:
        history = self.history[-MAX_HISTORY_MESSAGES:]
        short = self._short_history(history)

        # 0. normal conversation → answer directly, no retrieval
        if not self.needs_documents(question, short):
            doc_list = self.get_uploaded_docs_summary()
            answer = self.chat.invoke({
                "history": history,
                "question": question,
                "doc_list": doc_list,
            })
            self.history += [HumanMessage(question), AIMessage(answer)]
            return {"standalone": question, "docs": [], "answer": answer}

        # 1. turn a follow-up into a standalone question
        standalone = question
        if history:
            condensed = self.condense.invoke(
                {"history": short, "question": question}
            ).strip()
            if condensed and not condensed.startswith("#") and len(condensed) <= 250:
                standalone = condensed

        # 2. retrieve — expand context size for broad or summary queries
        is_summary = any(
            k in standalone.lower()
            for k in ["summar", "overview", "main point", "key takeaway", "topics", "outline", "what is this document about"]
        )
        if is_summary:
            docs = self.vectorstore.similarity_search(standalone, k=18)
        else:
            docs = self.retriever.invoke(standalone)

        # 3a. relevant chunks found → answer from documents
        if self.docs_are_relevant(standalone, docs):
            answer = self.answer.invoke(
                {"context": format_docs(docs), "question": standalone}
            )
            self.history += [HumanMessage(question), AIMessage(answer)]
            return {"standalone": standalone, "docs": docs, "answer": answer,
                    "source_type": "documents", "web_sources": []}

        # 3b. nothing relevant → say so, then search the web
        result = self.web_fallback(standalone)
        self.history += [HumanMessage(question), AIMessage(result["answer"])]
        return {"standalone": standalone, "docs": [], "answer": result["answer"],
                "source_type": "web", "web_sources": result["web_sources"]}

    def ask_stream(self, question: str):
        """Stream the generated answer token-by-token using pure LangChain streaming."""
        history = self.history[-MAX_HISTORY_MESSAGES:]
        short = self._short_history(history)

        # 0. normal conversation
        if not self.needs_documents(question, short):
            doc_list = self.get_uploaded_docs_summary()
            full_parts = []
            for chunk in self.chat.stream({
                "history": history,
                "question": question,
                "doc_list": doc_list,
            }):
                full_parts.append(chunk)
                yield chunk
            full_answer = "".join(full_parts)
            self.history += [HumanMessage(question), AIMessage(full_answer)]
            return

        # 1. turn a follow-up into a standalone question
        standalone = question
        if history:
            condensed = self.condense.invoke(
                {"history": short, "question": question}
            ).strip()
            if condensed and not condensed.startswith("#") and len(condensed) <= 250:
                standalone = condensed

        # 2. retrieve
        is_summary = any(
            k in standalone.lower()
            for k in ["summar", "overview", "main point", "key takeaway", "topics", "outline", "what is this document about"]
        )
        if is_summary:
            docs = self.vectorstore.similarity_search(standalone, k=18)
        else:
            docs = self.retriever.invoke(standalone)

        # 3a. stream answer from documents
        if self.docs_are_relevant(standalone, docs):
            full_parts = []
            for chunk in self.answer.stream({
                "context": format_docs(docs),
                "question": standalone,
            }):
                full_parts.append(chunk)
                yield chunk
            full_answer = "".join(full_parts)
            self.history += [HumanMessage(question), AIMessage(full_answer)]
            return

        # 3b. stream answer from web search
        results = web_search(standalone)
        if not results:
            msg = "I couldn't find relevant information in your documents or on the web."
            yield msg
            self.history += [HumanMessage(question), AIMessage(msg)]
            return

        context = format_web(results)
        full_parts = []
        for chunk in self.web_answer.stream({
            "context": context,
            "question": standalone,
        }):
            full_parts.append(chunk)
            yield chunk
        full_answer = "".join(full_parts)
        self.history += [HumanMessage(question), AIMessage(full_answer)]

    def ask_stream(self, question: str):
        """Stream the generated answer token-by-token using pure LangChain streaming."""
        history = self.history[-MAX_HISTORY_MESSAGES:]
        short = self._short_history(history)

        # 0. normal conversation
        if not self.needs_documents(question, short):
            doc_list = self.get_uploaded_docs_summary()
            full_parts = []
            for chunk in self.chat.stream({
                "history": history,
                "question": question,
                "doc_list": doc_list,
            }):
                full_parts.append(chunk)
                yield chunk
            full_answer = "".join(full_parts)
            self.history += [HumanMessage(question), AIMessage(full_answer)]
            return

        # 1. turn a follow-up into a standalone question
        standalone = question
        if history:
            condensed = self.condense.invoke(
                {"history": short, "question": question}
            ).strip()
            if condensed and not condensed.startswith("#") and len(condensed) <= 250:
                standalone = condensed

        # 2. retrieve
        is_summary = any(
            k in standalone.lower()
            for k in ["summar", "overview", "main point", "key takeaway", "topics", "outline", "what is this document about"]
        )
        if is_summary:
            docs = self.vectorstore.similarity_search(standalone, k=18)
        else:
            docs = self.retriever.invoke(standalone)

        # 3a. stream answer from documents
        if self.docs_are_relevant(standalone, docs):
            full_parts = []
            for chunk in self.answer.stream({
                "context": format_docs(docs),
                "question": standalone,
            }):
                full_parts.append(chunk)
                yield chunk
            full_answer = "".join(full_parts)
            self.history += [HumanMessage(question), AIMessage(full_answer)]
            return

        # 3b. stream answer from web search
        results = web_search(standalone)
        if not results:
            msg = "I couldn't find relevant information in your documents or on the web."
            yield msg
            self.history += [HumanMessage(question), AIMessage(msg)]
            return

        context = format_web(results)
        full_parts = []
        for chunk in self.web_answer.stream({
            "context": context,
            "question": standalone,
        }):
            full_parts.append(chunk)
            yield chunk
        full_answer = "".join(full_parts)
        self.history += [HumanMessage(question), AIMessage(full_answer)]
