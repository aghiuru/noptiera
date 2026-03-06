import os
from pipeline import llm, store

DB_PATH = os.path.join(os.path.dirname(__file__), "..", ".index")


def run_search(query_text: str, top_k: int = 5, embed_model: str = None) -> list[dict]:
    embedding = llm.embed(query_text, model=embed_model)
    collection = store.get_collection(DB_PATH)
    results = store.query(collection, embedding, n_results=top_k)

    output = []
    for i, doc_id in enumerate(results["ids"][0]):
        output.append({
            "id": doc_id,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return output
