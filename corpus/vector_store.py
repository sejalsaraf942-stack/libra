from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False


class VectorStore(ABC):
    @abstractmethod
    def add(self, ids: List[str], vectors: np.ndarray, metadata: List[Dict]) -> None: ...
    @abstractmethod
    def search(self, vector: np.ndarray, k: int) -> List[Dict]: ...


class FaissVectorStore(VectorStore):
    def __init__(self, dim: int = 64):
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS not available")
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.meta: List[Dict] = []

    def _embed(self, text: str) -> np.ndarray:
        # Deterministic toy embedding (replace with real embeddings in prod)
        v = np.zeros(self.dim, dtype="float32")
        for i, ch in enumerate(text.lower()):
            v[i % self.dim] += (ord(ch) % 31) / 31.0
        n = np.linalg.norm(v) or 1.0
        return (v / n).astype("float32")

    def add(self, ids, vectors, metadata):
        self.index.add(vectors)
        self.meta.extend(metadata)

    def add_texts(self, texts, metadata):
        vs = np.array([self._embed(t) for t in texts], dtype="float32")
        self.add(list(range(len(texts))), vs, metadata)

    def search(self, vector, k):
        if self.index.ntotal == 0:
            return []
        D, I = self.index.search(vector.reshape(1, -1).astype("float32"), k)
        out = []
        for idx in I[0]:
            if idx < 0 or idx >= len(self.meta):
                continue
            out.append(self.meta[idx])
        return out

    def search_text(self, text, k=5):
        return self.search(self._embed(text), k)
