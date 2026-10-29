from functools import lru_cache

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from .config import settings

@lru_cache
def get_embeddings() -> NVIDIAEmbeddings:
    return NVIDIAEmbeddings(model=settings.embedding_model)


@lru_cache
def get_client() -> QdrantClient:
    """One client per process (local mode locks the folder)."""
    if settings.qdrant_url:
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60,
            check_compatibility=False,
        )
    settings.vectorstore_dir.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(settings.vectorstore_dir))


def ensure_collection() -> None:
    client = get_client()
    if client.collection_exists(settings.collection_name):
        return
    # vector size depends on the embedding model, so measure it
    dim = len(get_embeddings().embed_query("dimension probe"))
    client.create_collection(
        collection_name=settings.collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )


def reset_collection() -> None:
    client = get_client()
    if client.collection_exists(settings.collection_name):
        client.delete_collection(settings.collection_name)


def get_vectorstore() -> QdrantVectorStore:
    ensure_collection()
    return QdrantVectorStore(
        client=get_client(),
        collection_name=settings.collection_name,
        embedding=get_embeddings(),
    )


def get_retriever():
    return get_vectorstore().as_retriever(search_kwargs={"k": settings.top_k})