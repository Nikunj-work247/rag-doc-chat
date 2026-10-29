import uuid
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings
from .retrieval import get_vectorstore


def load_single_document(path: Path):
    if path.suffix.lower() == ".pdf":
        return PyPDFLoader(str(path)).load()
    elif path.suffix.lower() in {".txt", ".md"}:
        return TextLoader(str(path), encoding="utf-8").load()
    return []


def load_documents(folder: Path):
    docs = []
    for path in sorted(folder.glob("**/*")):
        if path.is_file():
            docs.extend(load_single_document(path))
    return docs


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )
    return splitter.split_documents(docs)


def chunk_id(chunk) -> str:
    """Deterministic ID so re-running ingest updates chunks instead of duplicating them."""
    meta = chunk.metadata
    key = f"{meta.get('source')}|{meta.get('page')}|{meta.get('start_index')}|{chunk.page_content}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def ingest_file(file_path: Path, batch_size: int = 32) -> int:
    """Ingest a single document into the vector store."""
    docs = load_single_document(file_path)
    if not docs:
        return 0
    chunks = split_documents(docs)
    store = get_vectorstore()
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        store.add_documents(batch, ids=[chunk_id(c) for c in batch])
    return len(chunks)


def ingest(folder: Path | None = None, batch_size: int = 32) -> int:
    folder = folder or settings.raw_dir
    docs = load_documents(folder)
    if not docs:
        raise SystemExit(f"No PDF/TXT/MD files found in {folder}")

    chunks = split_documents(docs)
    store = get_vectorstore()

    # add in batches to stay within API limits
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        store.add_documents(batch, ids=[chunk_id(c) for c in batch])

    return len(chunks)