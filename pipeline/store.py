import os
import chromadb

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


def get_collection(db_path: str):
    client = chromadb.PersistentClient(path=db_path)
    return client.get_or_create_collection("articles")


def add_document(collection, doc_id: str, embedding: list[float], metadata: dict):
    collection.add(ids=[doc_id], embeddings=[embedding], metadatas=[metadata])


def query(collection, embedding: list[float], n_results: int = 5):
    return collection.query(query_embeddings=[embedding], n_results=n_results)
