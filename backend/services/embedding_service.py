"""FAISS vector store management — per-user namespaced indexes with temporal metadata."""
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from config.settings import get_settings

settings = get_settings()


def get_embeddings() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def get_index_path(user_id: str) -> str:
    path = os.path.join(settings.faiss_index_path, user_id)
    os.makedirs(path, exist_ok=True)
    return path


async def upsert_to_faiss(
    user_id: str,
    chunks: list[str],
    file_id: str = "",
    upload_date: str = "",
) -> None:
    embeddings = get_embeddings()
    index_path = get_index_path(user_id)

    docs = [
        Document(
            page_content=chunk,
            metadata={"user_id": user_id, "file_id": file_id, "date": upload_date},
        )
        for chunk in chunks
    ]

    if os.path.exists(os.path.join(index_path, "index.faiss")):
        vs = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        vs.add_documents(docs)
    else:
        vs = FAISS.from_documents(docs, embeddings)

    vs.save_local(index_path)


def load_retriever(user_id: str):
    embeddings = get_embeddings()
    index_path = get_index_path(user_id)

    if not os.path.exists(os.path.join(index_path, "index.faiss")):
        return None

    vs = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    return vs.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.faiss_top_k},
    )
