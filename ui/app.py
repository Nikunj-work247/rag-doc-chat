import streamlit as st

from docchat.chain import RagChat, source_label
from docchat.config import settings
from docchat.ingestion import ingest_file

st.set_page_config(page_title=settings.app_title, page_icon="💬", layout="wide")


def new_chat() -> None:
    if "chat" in st.session_state:
        st.session_state.chat.reset()
    st.session_state.messages = []


# one RagChat (and one history) per browser session
if "chat" not in st.session_state:
    st.session_state.chat = RagChat()
if "messages" not in st.session_state:
    st.session_state.messages = []


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for i, src in enumerate(sources, 1):
            st.markdown(f"**[{i}] {src['label']}**")
            st.caption(src["text"])


with st.sidebar:
    st.header(settings.app_title)
    st.button("New chat", on_click=new_chat, use_container_width=True)

    st.divider()
    st.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF, TXT, or MD files",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        help="Upload files to expand the chatbot's knowledge base.",
    )

    if uploaded_files:
        if st.button("Index Documents", use_container_width=True, type="primary"):
            with st.spinner("Processing & embedding into vector store..."):
                settings.raw_dir.mkdir(parents=True, exist_ok=True)
                total_chunks = 0
                for file in uploaded_files:
                    saved_path = settings.raw_dir / file.name
                    saved_path.write_bytes(file.getbuffer())
                    chunks = ingest_file(saved_path)
                    total_chunks += chunks

                st.session_state.chat = RagChat()
                st.success(f"Indexed {len(uploaded_files)} file(s) ({total_chunks} chunks)!")
                st.rerun()

    st.divider()
    st.subheader("📚 Available Documents")
    existing_docs = (
        sorted([f.name for f in settings.raw_dir.glob("*") if f.suffix.lower() in {".pdf", ".txt", ".md"}])
        if settings.raw_dir.exists()
        else []
    )
    if existing_docs:
        for doc in existing_docs:
            st.markdown(f"• `{doc}`")
    else:
        st.caption("No documents in knowledge base yet.")

st.title(settings.app_title)

# replay the conversation so far
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("searched_for"):
            st.caption(f"Searched for: {msg['searched_for']}")
        if msg["content"]:
            st.markdown(msg["content"])
        else:
            st.warning("No answer was generated for this question.")
        render_sources(msg.get("sources", []))

# handle a new question
if prompt := st.chat_input("Ask a question about your documents"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching your documents..."):
            try:
                result = st.session_state.chat.ask(prompt)
            except Exception as exc:
                st.error(f"Something went wrong: {exc}")
                st.stop()

        searched_for = result["standalone"] if result["standalone"] != prompt else ""
        sources = [
            {"label": source_label(d), "text": d.page_content[: settings.snippet_chars]}
            for d in result["docs"]
        ]

        if searched_for:
            st.caption(f"Searched for: {searched_for}")
        if result["answer"]:
            st.markdown(result["answer"])
        else:
            st.warning("The model did not return an answer. Please review the retrieved sources below.")
        render_sources(sources)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": sources,
            "searched_for": searched_for,
        }
    )