try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import requests
from typing import List
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chroma_db")
COLLECTION_NAME = "business_docs"

class HFRouterEmbeddings(Embeddings):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://router.huggingface.co/hf-inference/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

    def _embed(self, texts: List[str]) -> List[List[float]]:
        response = requests.post(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"inputs": texts}
        )
        response.raise_for_status()
        return response.json()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]

def get_embeddings():
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable missing.")
    return HFRouterEmbeddings(api_key=hf_token)

_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        print("Initializing Vector Store...")
        embeddings = get_embeddings()
        _vector_store_instance = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
    return _vector_store_instance

def query_rag(query_text: str, k: int = 3):
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query_text, k=k)
    return [doc.page_content for doc in results]

if __name__ == "__main__":
    print(f"Chroma DB Path: {CHROMA_PATH}")
    store = get_vector_store()
    print("Vector store initialized successfully.")