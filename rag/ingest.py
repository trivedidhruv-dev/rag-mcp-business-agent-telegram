import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.retriever import get_vector_store

DOCUMENTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents")

def ingest_documents():
    print(f"Scanning for documents in: {DOCUMENTS_PATH}")
    
    if not os.path.exists(DOCUMENTS_PATH):
        os.makedirs(DOCUMENTS_PATH)
        print(f"Created directory: {DOCUMENTS_PATH}. Please add PDF/TXT files there.")
        return

    loaders = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
    }

    documents = []
    for file in os.listdir(DOCUMENTS_PATH):
        ext = os.path.splitext(file)[1].lower()
        if ext in loaders:
            file_path = os.path.join(DOCUMENTS_PATH, file)
            print(f"Loading: {file}")
            try:
                loader = loaders[ext](file_path)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {file}: {e}")

    if not documents:
        print("No documents found to ingest.")
        return

    print(f"Splitting {len(documents)} documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("Adding chunks to ChromaDB...")
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    print("Ingestion complete! ✅")

if __name__ == "__main__":
    ingest_documents()