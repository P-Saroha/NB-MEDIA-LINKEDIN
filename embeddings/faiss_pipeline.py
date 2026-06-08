import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class LinkedInFaissPipeline:

    def __init__(self, index_path, metadata_path):
        self.index = faiss.read_index(str(index_path))

        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def search(self, query: str, top_k: int = 3):

        query_embedding = self.model.encode([query])[0]
        query_embedding = np.array([query_embedding], dtype="float32")

        distances, indices = self.index.search(query_embedding, top_k)

        results = []

        for idx in indices[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx])

        return results