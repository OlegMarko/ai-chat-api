import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []
        self.metadata = []

    def add(self, vectors, texts, metadatas):
        self.index.add(np.array(vectors).astype("float32"))
        self.texts.extend(texts)
        self.metadata.extend(metadatas)

    def search(self, query_vector, k=3):
        _, indices = self.index.search(np.array([query_vector]).astype("float32"), k)

        results = []
        for i in indices[0]:
            if i < len(self.texts):
                results.append({"text": self.texts[i], "metadata": self.metadata[i]})

        return results
